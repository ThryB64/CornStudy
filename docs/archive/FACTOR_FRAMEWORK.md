# Cadre des facteurs synthétiques

## Principe

Les facteurs synthétiques condensent 200+ variables brutes en 32 à 40 facteurs économiquement lisibles. Chaque facteur agrège plusieurs variables d'une même famille, pondérées par leur pertinence économique.

**Pourquoi des facteurs plutôt que les variables brutes ?**

1. **Réduction de dimensionnalité** — 248 colonnes créent de la multicolinéarité et des problèmes de régularisation.
2. **Lisibilité économique** — "factor_weather_stress = −0.8" est interprétable. "belt_tavg_anom_14d = 1.3°C" l'est moins dans un modèle multi-features.
3. **Stabilité** — Les facteurs sont plus stables dans le temps que les variables brutes individuelles.
4. **Anti-leakage** — Les z-scores sont expandants, calculés avec uniquement l'historique disponible à la date t.

---

## Les 9 familles de facteurs

### Famille 1 — market_momentum

**Signification économique :** la tendance récente des prix et l'élan haussier ou baissier.

| Facteur | Recette |
|---|---|
| `factor_market_short_momentum` | Returns 1j, 5j en z-score |
| `factor_market_medium_trend` | Returns 20j, 60j en z-score |
| `factor_market_technical` | RSI, distance aux bornes Bollinger |

**Hypothèse :** un marché haussier tend à continuer à court terme (momentum), mais mean-reverts à moyen terme.

---

### Famille 2 — market_volatility

**Signification économique :** le niveau d'incertitude et de nervosité du marché.

| Facteur | Recette |
|---|---|
| `factor_market_vol_regime` | Vol réalisée 20j, 60j en z-score expansant |
| `factor_market_vol_trend` | Variation de la volatilité |

**Hypothèse :** la volatilité élevée précède les grands mouvements. En saison de croissance, une volatilité élevée + météo stressante = signal fort.

---

### Famille 3 — wasde_supply_demand

**Signification économique :** le bilan offre/demande fondamental du marché US.

| Facteur | Recette |
|---|---|
| `factor_wasde_balance_tightness` | Stocks-to-use, ending stocks, supply minus use |
| `factor_wasde_yield_risk` | Yield vs tendance, surprises de rendement |
| `factor_wasde_demand_pull` | Total use, export demand, ethanol use |

**Hypothèse :** un ratio stocks/use bas crée une prime de rareté et une volatilité accrue. C'est le facteur le plus documenté dans la littérature USDA.

**Règle anti-leakage :** toutes les variables WASDE sont `shift(1)` sur les dates marché + forward-fill mensuel.

---

### Famille 4 — weather_belt_stress

**Signification économique :** l'impact agrégé de la météo sur le Corn Belt américain.

| Facteur | Recette |
|---|---|
| `factor_weather_belt_heat_stress` | Anomalie température pondérée par production |
| `factor_weather_belt_water_stress` | Anomalie précipitations, jours de sécheresse |
| `factor_weather_drought_composite` | Drought Monitor D0-D4 composite |

**Pondération :** les anomalies sont calculées par état, puis agrégées par poids de production ou de superficie.

**Saison :** les variables météo comptent surtout de mai à août. En hiver, elles doivent être proches de zéro ou ignorées.

---

### Famille 5 — production_fundamentals

**Signification économique :** la révision des estimations de production et de stocks.

| Facteur | Recette |
|---|---|
| `factor_production_yield_risk` | Yield weighted, YoY yield %, surprises |
| `factor_production_area_supply` | Area planted, area harvested, YoY % |
| `factor_stocks_seasonal_tightness` | Stocks décembre, mars, juin vs normes historiques |
| `factor_production_output_revision` | Révisions WASDE mois après mois |

**Note de colinéarité :** cette famille est partiellement redondante avec `wasde_supply_demand` car WASDE agrège déjà ces données. Sur Ridge, la redondance nuit. Sur LightGBM, l'effet est neutre ou légèrement positif grâce aux interactions non-linéaires.

---

### Famille 6 — macro_dollar_rates

**Signification économique :** l'environnement macroéconomique qui influence la compétitivité des exportations et le coût du capital.

| Facteur | Recette |
|---|---|
| `factor_macro_rates_pressure` | Taux Fed, taux réels, DGS10 en z-score |
| `factor_macro_inflation_signal` | CPI, inflation surprise, core CPI |

**Hypothèse :** un dollar fort rend les exportations US moins compétitives → pression baissière. Des taux réels élevés réduisent l'appétit au stockage spéculatif.

---

### Famille 7 — cot_positioning

**Signification économique :** le positionnement des grands acteurs financiers et commerciaux.

| Facteur | Recette |
|---|---|
| `factor_cot_speculative_pressure` | Managed money net, % OI, z-score 52 semaines |
| `factor_cot_commercial_hedge` | Producer/merchant net, ratio hedge/spec |
| `factor_cot_open_interest_momentum` | Variation OI, ratio OI/production |

**Hypothèse :** un positionnement spéculatif extrême (long ou short) précède souvent un retournement. Les commerciaux hedgers sont des "smart money" de long terme.

**Lag :** les données COT reflètent les positions du mardi, publiées le vendredi. Encoder un décalage de 3 jours.

---

### Famille 8 — seasonality

**Signification économique :** les effets réguliers liés au cycle agronomique annuel.

| Facteur | Recette |
|---|---|
| `factor_seasonality_fourier` | sin/cos de la position dans l'année (ordres 1, 2, 3) |
| `factor_seasonality_agro` | Saison (semis, croissance, récolte) encodée |
| `factor_seasonality_usda_proximity` | Jours avant/après prochain rapport USDA |

**Hypothèse :** le maïs a des patterns saisonniers très forts. Les prix montent souvent de l'hiver jusqu'au pic de l'été si la météo est mauvaise.

---

### Famille 9 — cross_commodity

**Signification économique :** les relations prix entre marchés liés.

| Facteur | Recette |
|---|---|
| `factor_cross_corn_soy` | Ratio corn/soy en z-score expansant |
| `factor_cross_corn_energy` | Ratio corn/oil, corn/gas |
| `factor_cross_fertilizer` | Prix engrais (naturellement corrélé au gas) |

**Hypothèse :** quand le maïs est trop cher vs le soja, les agriculteurs replantent en soja l'année suivante → force de rappel. Le ratio corn/oil influence la marge éthanol.

---

## Règles de construction

### Z-score expansant (obligatoire)

```python
def _expanding_z(series: pd.Series, min_periods: int = 252) -> pd.Series:
    mu = series.expanding(min_periods=min_periods).mean()
    sigma = series.expanding(min_periods=min_periods).std()
    return (series - mu) / sigma.replace(0, float("nan"))
```

Jamais de z-score sur une fenêtre fixe (rolling) : cela utilise de l'information future.

### Composantes signées

Chaque facteur est une somme pondérée de composantes signées :

```python
FactorRecipe(
    name="factor_wasde_balance_tightness",
    family="wasde_supply_demand",
    signed_components={
        "stu": -1.0,          # stocks/use bas → pression haussière → négatif
        "ending_stocks": -1.0,
        "supply_minus_use": 1.0,  # surplus → baissier → positif (convention inverse)
    }
)
```

**Convention de signe :** un facteur positif = force haussière sur le prix.

### Gestion des NaN

- Si une composante est NaN, elle est ignorée dans la somme.
- Si toutes les composantes sont NaN, le facteur vaut NaN.
- NaN dans les facteurs = feature manquante pour le modèle (traité par imputation médiane dans le pipeline).

---

## Facteurs cibles à ajouter

Ces facteurs sont documentés dans `IDEAS.md` mais pas encore construits :

| Facteur | Famille | Données nécessaires | Priorité |
|---|---|---|---|
| `factor_crop_condition_pressure` | weather_belt_stress | Crop Progress NASS | Haute |
| `factor_drought_severity` | weather_belt_stress | Drought Monitor | Haute |
| `factor_export_demand_surprise` | cross_commodity | FAS Export Sales | Haute |
| `factor_ethanol_demand_pull` | wasde_supply_demand | EIA éthanol (vraie API) | Haute |
| `factor_south_america_supply` | production_fundamentals | CONAB, Bolsa Cereales | Moyenne |
| `factor_basis_signal` | cross_commodity | Basis locale | Moyenne |

---

## Ablation study — résultats actuels

Résultats sur Ridge factors, horizon J+20, walk-forward out-of-sample.

| Famille retirée | Δ RMSE (positif = utile) | Interprétation |
|---|---|---|
| market_momentum | +0.0043 | Utile |
| wasde_supply_demand | +0.0038 | Utile |
| weather_belt_stress | +0.0031 | Utile, surtout saison |
| seasonality | +0.0019 | Utile |
| cross_commodity | +0.0012 | Marginalement utile |
| macro_dollar_rates | +0.0008 | Faiblement utile sur Ridge |
| cot_positioning | +0.0006 | Faiblement utile sur Ridge |
| market_volatility | −0.0002 | Neutre sur Ridge |
| production_fundamentals | −0.0039 | Redondant avec WASDE sur Ridge |

**Note :** les résultats Ridge ne s'appliquent pas à LightGBM. Production_fundamentals peut être utile pour LightGBM via interactions.

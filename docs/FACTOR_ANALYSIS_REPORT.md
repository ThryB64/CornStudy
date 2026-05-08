# Rapport d'analyse factorielle

- Généré le: `2026-05-08 12:30:51 UTC`
- Features source: `/home/cytech/Desktop/Etude Mais/data/processed/features.parquet`
- Facteurs: `/home/cytech/Desktop/Etude Mais/data/processed/factors.parquet`
- Métadonnées: `/home/cytech/Desktop/Etude Mais/data/processed/factors_metadata.json`

## 1) Synthèse

- Univers brut: **188** features, dont **188** candidates avec couverture suffisante.
- Vue factorielle: **26** facteurs synthétiques construits depuis **93** composants économiques.
- Les facteurs sont construits sans utiliser les targets; les targets servent seulement à l'évaluation temporelle et aux diagnostics.

## 2) Familles économiques

| Famille | Features brutes | Composants utilisés | Facteurs | Variables laissées hors recettes |
|---|---:|---:|---:|---:|
| `market_momentum` | 14 | 12 | 3 | 3 |
| `market_volatility` | 5 | 5 | 2 | 0 |
| `wasde_supply_demand` | 132 | 47 | 9 | 85 |
| `weather_belt_stress` | 16 | 14 | 4 | 2 |
| `macro_dollar_rates` | 0 | 0 | 0 | 0 |
| `seasonality` | 10 | 5 | 4 | 5 |
| `cross_commodity` | 10 | 10 | 4 | 0 |
| `others` | 1 | 0 | 0 | 0 |

## 3) Définition des facteurs

| Facteur | Famille | Composants | Lecture économique |
|---|---|---:|---|
| `factor_market_short_momentum` | `market_momentum` | 4 | Momentum court terme du maïs CBOT via rendements récents, RSI et MACD. |
| `factor_market_medium_trend` | `market_momentum` | 4 | Tendance moyenne via rendement 20 jours et structure des moyennes mobiles. |
| `factor_market_drawdown_recovery` | `market_momentum` | 4 | Position dans le range annuel; valeur élevée = prix éloigné des plus bas. |
| `factor_market_liquidity_volume` | `market_volatility` | 1 | Activité de marché anormale sur le contrat maïs. |
| `factor_market_volatility_pressure` | `market_volatility` | 4 | Expansion de volatilité et d'amplitude sur les futures maïs. |
| `factor_cross_soy_relative_value` | `cross_commodity` | 2 | Valorisation et co-mouvement du maïs relativement au soja. |
| `factor_cross_wheat_relative_value` | `cross_commodity` | 2 | Valorisation et co-mouvement du maïs relativement au blé. |
| `factor_cross_energy_link` | `cross_commodity` | 4 | Contexte énergie lié à l'éthanol et aux coûts d'intrants. |
| `factor_cross_dollar_pressure` | `cross_commodity` | 2 | Force du maïs relativement au proxy dollar US. |
| `factor_weather_heat_stress` | `weather_belt_stress` | 6 | Stress thermique du Corn Belt; valeur élevée = conditions plus chaudes. |
| `factor_weather_dryness_stress` | `weather_belt_stress` | 4 | Stress de sécheresse; valeur élevée = précipitations sous la normale. |
| `factor_weather_core_state_stress` | `weather_belt_stress` | 5 | Anomalie de température sur les principaux états du Corn Belt. |
| `factor_weather_cold_delay` | `weather_belt_stress` | 3 | Proxy de retard par froid; valeur élevée = températures sous la normale. |
| `factor_wasde_balance_tightness` | `wasde_supply_demand` | 6 | Tension du bilan US via stocks-to-use et mesures de surplus. |
| `factor_wasde_supply_risk` | `wasde_supply_demand` | 4 | Risque de rareté côté offre; valeur élevée = production/offre plus basse. |
| `factor_wasde_demand_exports` | `wasde_supply_demand` | 6 | Traction de demande via usage total, demande domestique et exports. |
| `factor_wasde_price_regime` | `wasde_supply_demand` | 4 | Régime de prix ferme USDA et changements récents. |
| `factor_wasde_tightness_surprise` | `wasde_supply_demand` | 6 | Surprise WASDE haussière si stocks ou stocks-to-use sortent sous l'attendu. |
| `factor_wasde_supply_surprise` | `wasde_supply_demand` | 6 | Surprise WASDE haussière si production ou offre totale est révisée en baisse. |
| `factor_wasde_demand_surprise` | `wasde_supply_demand` | 6 | Surprise WASDE haussière si usage ou exports sont révisés en hausse. |
| `factor_wasde_price_surprise` | `wasde_supply_demand` | 4 | Surprise du prix ferme USDA par rapport à l'historique et à la tendance. |
| `factor_wasde_revision_momentum` | `wasde_supply_demand` | 5 | Pression de révision mensuelle et annuelle sur les champs WASDE clés. |
| `factor_season_planting_window` | `seasonality` | 1 | Exposition calendaire à la fenêtre de semis. |
| `factor_season_pollination_window` | `seasonality` | 1 | Exposition calendaire à la fenêtre floraison/pollinisation. |
| `factor_season_harvest_window` | `seasonality` | 1 | Exposition calendaire à la fenêtre de récolte. |
| `factor_season_annual_cycle` | `seasonality` | 2 | Cycle annuel lissé via les termes Fourier mensuels. |

## 4) Protocole de comparaison

- Modèles comparés: `baseline_zero_return`, `raw_features_ridge`, `factor_model_ridge`.
- Même cible, mêmes dates et mêmes splits pour les trois modèles.
- Prétraitement: médiane apprise sur train uniquement, `StandardScaler` et `Ridge(alpha=1)`.
- `holdout_20`: dernier 20% de l'historique en test.
- `rolling_expanding_6m`: train expanding, fenêtres test d'environ 6 mois.

## 5) Résultats par horizon

| Horizon | Protocole | Modèle | RMSE | MAE | R2 | DA | N test |
|---:|---|---|---:|---:|---:|---:|---:|
| J+5 | `holdout_20` | `baseline_zero_return` | 0.04057 | 0.02838 | -0.00046 | 0.006 | 1238 |
| J+5 | `holdout_20` | `raw_features_ridge` | 0.04760 | 0.03676 | -0.37740 | 0.456 | 1238 |
| J+5 | `holdout_20` | `factor_model_ridge` | 0.03915 | 0.02756 | 0.06853 | 0.594 | 1238 |
| J+5 | `rolling_expanding_6m` | `baseline_zero_return` | 0.03603 | 0.02570 | -0.00001 | 0.006 | 2475 |
| J+5 | `rolling_expanding_6m` | `raw_features_ridge` | 0.06504 | 0.04224 | -2.25839 | 0.468 | 2475 |
| J+5 | `rolling_expanding_6m` | `factor_model_ridge` | 0.03559 | 0.02569 | 0.02422 | 0.549 | 2475 |
| J+10 | `holdout_20` | `baseline_zero_return` | 0.05739 | 0.04042 | -0.00105 | 0.002 | 1237 |
| J+10 | `holdout_20` | `raw_features_ridge` | 0.07082 | 0.05552 | -0.52457 | 0.455 | 1237 |
| J+10 | `holdout_20` | `factor_model_ridge` | 0.05352 | 0.03831 | 0.12929 | 0.613 | 1237 |
| J+10 | `rolling_expanding_6m` | `baseline_zero_return` | 0.05010 | 0.03586 | -0.00005 | 0.002 | 2473 |
| J+10 | `rolling_expanding_6m` | `raw_features_ridge` | 0.09886 | 0.06410 | -2.89380 | 0.479 | 2473 |
| J+10 | `rolling_expanding_6m` | `factor_model_ridge` | 0.04900 | 0.03574 | 0.04323 | 0.562 | 2473 |
| J+20 | `holdout_20` | `baseline_zero_return` | 0.08276 | 0.06204 | -0.00242 | 0.002 | 1235 |
| J+20 | `holdout_20` | `raw_features_ridge` | 0.11271 | 0.08762 | -0.85915 | 0.503 | 1235 |
| J+20 | `holdout_20` | `factor_model_ridge` | 0.07583 | 0.05676 | 0.15847 | 0.662 | 1235 |
| J+20 | `rolling_expanding_6m` | `baseline_zero_return` | 0.07228 | 0.05291 | -0.00014 | 0.005 | 2469 |
| J+20 | `rolling_expanding_6m` | `raw_features_ridge` | 0.15159 | 0.10207 | -3.39906 | 0.471 | 2469 |
| J+20 | `rolling_expanding_6m` | `factor_model_ridge` | 0.07225 | 0.05394 | 0.00068 | 0.590 | 2469 |
| J+30 | `holdout_20` | `baseline_zero_return` | 0.10219 | 0.07993 | -0.00366 | 0.002 | 1233 |
| J+30 | `holdout_20` | `raw_features_ridge` | 0.13891 | 0.10415 | -0.85428 | 0.543 | 1233 |
| J+30 | `holdout_20` | `factor_model_ridge` | 0.09214 | 0.07173 | 0.18411 | 0.649 | 1233 |
| J+30 | `rolling_expanding_6m` | `baseline_zero_return` | 0.08890 | 0.06647 | -0.00025 | 0.005 | 2465 |
| J+30 | `rolling_expanding_6m` | `raw_features_ridge` | 0.18920 | 0.12542 | -3.53020 | 0.467 | 2465 |
| J+30 | `rolling_expanding_6m` | `factor_model_ridge` | 0.08991 | 0.06939 | -0.02298 | 0.576 | 2465 |

## 6) Robustesse économique

| Horizon | Splits rolling | Fenêtre test rolling | RMSE facteur vs brut | DA facteur vs brut | RMSE facteur vs naïf |
|---:|---:|---|---:|---:|---:|
| J+5 | 20 | 2015-09-10 -> 2025-07-18 | -45.3% | +0.081 | -1.2% |
| J+10 | 20 | 2015-09-04 -> 2025-07-11 | -50.4% | +0.083 | -2.2% |
| J+20 | 20 | 2015-08-27 -> 2025-06-26 | -52.3% | +0.119 | -0.0% |
| J+30 | 20 | 2015-08-19 -> 2025-06-11 | -52.5% | +0.109 | +1.1% |

Lecture: la baseline zéro-retour reste dure à battre en RMSE sur des rendements courts, ce qui signale une espérance de retour faible et bruitée. L'intérêt des facteurs se juge donc aussi sur la stabilité, le hit-rate directionnel et la lisibilité économique.

## 7) Importance par famille

### J+5

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.815 |
| `market_momentum` | 0.110 |
| `seasonality` | 0.026 |
| `cross_commodity` | 0.026 |
| `weather_belt_stress` | 0.014 |
| `market_volatility` | 0.008 |
| `others` | 0.001 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.264 |
| `weather_belt_stress` | 0.224 |
| `cross_commodity` | 0.176 |
| `seasonality` | 0.141 |
| `market_momentum` | 0.110 |
| `market_volatility` | 0.086 |

### J+10

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.820 |
| `market_momentum` | 0.091 |
| `seasonality` | 0.034 |
| `cross_commodity` | 0.034 |
| `weather_belt_stress` | 0.012 |
| `market_volatility` | 0.008 |
| `others` | 0.002 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.235 |
| `weather_belt_stress` | 0.197 |
| `cross_commodity` | 0.166 |
| `seasonality` | 0.164 |
| `market_momentum` | 0.148 |
| `market_volatility` | 0.092 |

### J+20

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.877 |
| `market_momentum` | 0.059 |
| `cross_commodity` | 0.036 |
| `seasonality` | 0.010 |
| `weather_belt_stress` | 0.009 |
| `market_volatility` | 0.007 |
| `others` | 0.001 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.269 |
| `seasonality` | 0.209 |
| `cross_commodity` | 0.186 |
| `market_momentum` | 0.182 |
| `weather_belt_stress` | 0.083 |
| `market_volatility` | 0.071 |

### J+30

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.895 |
| `market_momentum` | 0.045 |
| `cross_commodity` | 0.033 |
| `seasonality` | 0.012 |
| `market_volatility` | 0.008 |
| `weather_belt_stress` | 0.007 |
| `others` | 0.001 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.281 |
| `seasonality` | 0.236 |
| `cross_commodity` | 0.215 |
| `market_momentum` | 0.141 |
| `weather_belt_stress` | 0.076 |
| `market_volatility` | 0.051 |

## 8) Lecture par horizon

### J+5

- Sur J+5, le modèle factoriel est -45.3% en RMSE vs features brutes et -1.2% vs zéro-retour; son hit-rate directionnel est +0.081 vs brut.
- Lecture économique dominante: wasde_supply_demand (81%), market_momentum (11%), seasonality (3%). Les facteurs les plus actifs sont `factor_weather_heat_stress`, `factor_cross_wheat_relative_value`, `factor_weather_core_state_stress`.
- La contribution météo est faiblement concentrée sur l'été (corrélation absolue moyenne été 0.020 vs hors été 0.040).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.468.

### J+10

- Sur J+10, le modèle factoriel est -50.4% en RMSE vs features brutes et -2.2% vs zéro-retour; son hit-rate directionnel est +0.083 vs brut.
- Lecture économique dominante: wasde_supply_demand (82%), market_momentum (9%), seasonality (3%). Les facteurs les plus actifs sont `factor_weather_heat_stress`, `factor_cross_wheat_relative_value`, `factor_market_drawdown_recovery`.
- La contribution météo est davantage concentrée en été (corrélation absolue moyenne été 0.047 vs hors été 0.038).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.587.

### J+20

- Sur J+20, le modèle factoriel est -52.3% en RMSE vs features brutes et -0.0% vs zéro-retour; son hit-rate directionnel est +0.119 vs brut.
- Lecture économique dominante: wasde_supply_demand (88%), market_momentum (6%), cross_commodity (4%). Les facteurs les plus actifs sont `factor_cross_wheat_relative_value`, `factor_market_drawdown_recovery`, `factor_season_annual_cycle`.
- La contribution météo est davantage concentrée en été (corrélation absolue moyenne été 0.045 vs hors été 0.043).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.841.

### J+30

- Sur J+30, le modèle factoriel est -52.5% en RMSE vs features brutes et +1.1% vs zéro-retour; son hit-rate directionnel est +0.109 vs brut.
- Lecture économique dominante: wasde_supply_demand (89%), market_momentum (4%), cross_commodity (3%). Les facteurs les plus actifs sont `factor_cross_wheat_relative_value`, `factor_season_annual_cycle`, `factor_wasde_supply_risk`.
- La contribution météo est davantage concentrée en été (corrélation absolue moyenne été 0.080 vs hors été 0.034).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.650.

## 9) Facteurs dominants

### J+5

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_weather_heat_stress` | 0.00521 |
| `factor_cross_wheat_relative_value` | 0.00385 |
| `factor_weather_core_state_stress` | 0.00371 |
| `factor_cross_dollar_pressure` | 0.00337 |
| `factor_season_pollination_window` | 0.00318 |
| `factor_season_annual_cycle` | 0.00309 |
| `factor_market_drawdown_recovery` | 0.00289 |
| `factor_wasde_supply_risk` | 0.00288 |
| `factor_market_liquidity_volume` | 0.00261 |
| `factor_wasde_tightness_surprise` | 0.00216 |

### J+10

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_weather_heat_stress` | 0.00882 |
| `factor_cross_wheat_relative_value` | 0.00850 |
| `factor_market_drawdown_recovery` | 0.00768 |
| `factor_season_pollination_window` | 0.00748 |
| `factor_weather_core_state_stress` | 0.00619 |
| `factor_season_annual_cycle` | 0.00596 |
| `factor_wasde_supply_risk` | 0.00585 |
| `factor_market_liquidity_volume` | 0.00488 |
| `factor_cross_dollar_pressure` | 0.00412 |
| `factor_market_medium_trend` | 0.00372 |

### J+20

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_cross_wheat_relative_value` | 0.01776 |
| `factor_market_drawdown_recovery` | 0.01458 |
| `factor_season_annual_cycle` | 0.01364 |
| `factor_wasde_supply_risk` | 0.01228 |
| `factor_season_pollination_window` | 0.00715 |
| `factor_wasde_balance_tightness` | 0.00642 |
| `factor_weather_core_state_stress` | 0.00635 |
| `factor_market_medium_trend` | 0.00633 |
| `factor_market_volatility_pressure` | 0.00600 |
| `factor_market_short_momentum` | 0.00579 |

### J+30

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_cross_wheat_relative_value` | 0.02563 |
| `factor_season_annual_cycle` | 0.01949 |
| `factor_wasde_supply_risk` | 0.01761 |
| `factor_market_drawdown_recovery` | 0.01485 |
| `factor_wasde_balance_tightness` | 0.01273 |
| `factor_season_harvest_window` | 0.00979 |
| `factor_market_short_momentum` | 0.00964 |
| `factor_wasde_price_regime` | 0.00770 |
| `factor_season_planting_window` | 0.00761 |
| `factor_cross_dollar_pressure` | 0.00669 |

## 10) Conclusion et prochaine étape

- La vue factorielle est maintenant plus petite, stable et lisible que les 188 features brutes.
- À ce stade, les facteurs ne doivent pas être jugés comme une promesse de RMSE: ils servent surtout à expliquer les familles de risque qui déplacent le prix.
- Prochaine expérimentation incrémentale: ajouter une seule source prioritaire (`EIA ethanol`), relancer ce rapport, mesurer le gain marginal, puis seulement ensuite tester `CFTC COT` et `USDA Crop Progress`.
- Après chaque source: relancer `features`, `targets`, `audit`, `train`, `stack`, `backtest`, `validate_outputs.py`, puis ce rapport.

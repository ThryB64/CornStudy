# Rapport d'analyse factorielle

- Généré le: `2026-05-08 18:11:51 UTC`
- Features source: `/home/cytech/Desktop/Etude Mais/data/processed/features.parquet`
- Facteurs: `/home/cytech/Desktop/Etude Mais/data/processed/factors.parquet`
- Métadonnées: `/home/cytech/Desktop/Etude Mais/data/processed/factors_metadata.json`

## 1) Synthèse

- Univers brut: **305** features, dont **305** candidates avec couverture suffisante.
- Vue factorielle: **36** facteurs synthétiques construits depuis **130** composants économiques.
- Les facteurs sont construits sans utiliser les targets; les targets servent seulement à l'évaluation temporelle et aux diagnostics.

## 2) Familles économiques

| Famille | Features brutes | Composants utilisés | Facteurs | Variables laissées hors recettes |
|---|---:|---:|---:|---:|
| `market_momentum` | 14 | 12 | 3 | 3 |
| `market_volatility` | 5 | 5 | 2 | 0 |
| `wasde_supply_demand` | 132 | 47 | 9 | 85 |
| `weather_belt_stress` | 16 | 14 | 4 | 2 |
| `production_fundamentals` | 42 | 20 | 4 | 26 |
| `ethanol_demand` | 1 | 1 | 1 | 0 |
| `macro_dollar_rates` | 10 | 7 | 2 | 3 |
| `cot_positioning` | 56 | 9 | 3 | 47 |
| `seasonality` | 10 | 5 | 4 | 5 |
| `cross_commodity` | 10 | 10 | 4 | 0 |
| `others` | 9 | 0 | 0 | 4 |

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
| `factor_production_yield_risk` | `production_fundamentals` | 4 | Risque de rendement ; valeur élevée = rendement sous la normale (haussier prix). |
| `factor_production_area_supply` | `production_fundamentals` | 4 | Pression d'offre via surfaces ; valeur élevée = plus grandes surfaces (baissier). |
| `factor_stocks_seasonal_tightness` | `production_fundamentals` | 8 | Tension des stocks trimestriels (Grain Stocks NASS) ; valeur élevée = stocks bas (haussier). |
| `factor_production_output_revision` | `production_fundamentals` | 4 | Révision de la production nationale ; valeur élevée = production révisée en baisse (haussier). |
| `factor_macro_rates_pressure` | `macro_dollar_rates` | 4 | Pression monétaire ; valeur élevée = taux réels hauts (baissier pour les matières premières). |
| `factor_macro_inflation_signal` | `macro_dollar_rates` | 3 | Signal inflationniste ; valeur élevée = inflation forte (haussier pour les matières premières). |
| `factor_ethanol_margin_signal` | `ethanol_demand` | 1 | Signal de marge éthanol ; valeur élevée = pétrole cher relativement au maïs, donc demande potentiellement soutenue. |
| `factor_cot_speculative_pressure` | `cot_positioning` | 4 | Pression spéculative nette des Managed Money (haussier si net long élevé). |
| `factor_cot_commercial_hedge` | `cot_positioning` | 3 | Position nette des producteurs/commerciaux (inverse : net short élevé = offre abondante). |
| `factor_cot_open_interest_momentum` | `cot_positioning` | 2 | Dynamique de l'open interest ; expansion = intérêt croissant du marché. |

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
| J+5 | `holdout_20` | `raw_features_ridge` | 0.22547 | 0.18725 | -29.89795 | 0.440 | 1238 |
| J+5 | `holdout_20` | `factor_model_ridge` | 0.04126 | 0.03039 | -0.03484 | 0.475 | 1238 |
| J+5 | `rolling_expanding_6m` | `baseline_zero_return` | 0.03603 | 0.02570 | -0.00001 | 0.006 | 2475 |
| J+5 | `rolling_expanding_6m` | `raw_features_ridge` | 0.11140 | 0.07263 | -8.56093 | 0.486 | 2475 |
| J+5 | `rolling_expanding_6m` | `factor_model_ridge` | 0.03641 | 0.02652 | -0.02140 | 0.491 | 2475 |
| J+10 | `holdout_20` | `baseline_zero_return` | 0.05739 | 0.04042 | -0.00105 | 0.002 | 1237 |
| J+10 | `holdout_20` | `raw_features_ridge` | 0.27856 | 0.23279 | -22.58835 | 0.424 | 1237 |
| J+10 | `holdout_20` | `factor_model_ridge` | 0.05934 | 0.04496 | -0.07051 | 0.496 | 1237 |
| J+10 | `rolling_expanding_6m` | `baseline_zero_return` | 0.05010 | 0.03586 | -0.00005 | 0.002 | 2473 |
| J+10 | `rolling_expanding_6m` | `raw_features_ridge` | 0.15158 | 0.10170 | -8.15457 | 0.483 | 2473 |
| J+10 | `rolling_expanding_6m` | `factor_model_ridge` | 0.05149 | 0.03806 | -0.05636 | 0.507 | 2473 |
| J+20 | `holdout_20` | `baseline_zero_return` | 0.08276 | 0.06204 | -0.00242 | 0.002 | 1235 |
| J+20 | `holdout_20` | `raw_features_ridge` | 0.28699 | 0.23579 | -11.05329 | 0.441 | 1235 |
| J+20 | `holdout_20` | `factor_model_ridge` | 0.09567 | 0.07481 | -0.33932 | 0.494 | 1235 |
| J+20 | `rolling_expanding_6m` | `baseline_zero_return` | 0.07228 | 0.05291 | -0.00014 | 0.005 | 2469 |
| J+20 | `rolling_expanding_6m` | `raw_features_ridge` | 0.18770 | 0.13576 | -5.74492 | 0.484 | 2469 |
| J+20 | `rolling_expanding_6m` | `factor_model_ridge` | 0.07741 | 0.05795 | -0.14701 | 0.533 | 2469 |
| J+30 | `holdout_20` | `baseline_zero_return` | 0.10219 | 0.07993 | -0.00366 | 0.002 | 1233 |
| J+30 | `holdout_20` | `raw_features_ridge` | 0.37681 | 0.32375 | -12.64526 | 0.401 | 1233 |
| J+30 | `holdout_20` | `factor_model_ridge` | 0.12642 | 0.10014 | -0.53586 | 0.485 | 1233 |
| J+30 | `rolling_expanding_6m` | `baseline_zero_return` | 0.08890 | 0.06647 | -0.00025 | 0.005 | 2465 |
| J+30 | `rolling_expanding_6m` | `raw_features_ridge` | 0.20873 | 0.15712 | -4.51387 | 0.491 | 2465 |
| J+30 | `rolling_expanding_6m` | `factor_model_ridge` | 0.09689 | 0.07445 | -0.18817 | 0.517 | 2465 |

## 6) Robustesse économique

| Horizon | Splits rolling | Fenêtre test rolling | RMSE facteur vs brut | DA facteur vs brut | RMSE facteur vs naïf |
|---:|---:|---|---:|---:|---:|
| J+5 | 20 | 2015-09-10 -> 2025-07-18 | -67.3% | +0.005 | +1.1% |
| J+10 | 20 | 2015-09-04 -> 2025-07-11 | -66.0% | +0.025 | +2.8% |
| J+20 | 20 | 2015-08-27 -> 2025-06-26 | -58.8% | +0.048 | +7.1% |
| J+30 | 20 | 2015-08-19 -> 2025-06-11 | -53.6% | +0.026 | +9.0% |

Lecture: la baseline zéro-retour reste dure à battre en RMSE sur des rendements courts, ce qui signale une espérance de retour faible et bruitée. L'intérêt des facteurs se juge donc aussi sur la stabilité, le hit-rate directionnel et la lisibilité économique.

## 7) Importance par famille

### J+5

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.381 |
| `cot_positioning` | 0.233 |
| `production_fundamentals` | 0.203 |
| `market_momentum` | 0.059 |
| `macro_dollar_rates` | 0.050 |
| `others` | 0.034 |
| `seasonality` | 0.015 |
| `cross_commodity` | 0.013 |
| `weather_belt_stress` | 0.007 |
| `market_volatility` | 0.005 |
| `ethanol_demand` | 0.000 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.172 |
| `weather_belt_stress` | 0.168 |
| `cross_commodity` | 0.156 |
| `market_momentum` | 0.122 |
| `seasonality` | 0.089 |
| `ethanol_demand` | 0.083 |
| `macro_dollar_rates` | 0.067 |
| `cot_positioning` | 0.059 |
| `production_fundamentals` | 0.044 |
| `market_volatility` | 0.040 |

### J+10

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.388 |
| `cot_positioning` | 0.233 |
| `production_fundamentals` | 0.204 |
| `macro_dollar_rates` | 0.051 |
| `market_momentum` | 0.041 |
| `others` | 0.039 |
| `seasonality` | 0.018 |
| `cross_commodity` | 0.012 |
| `weather_belt_stress` | 0.010 |
| `market_volatility` | 0.004 |
| `ethanol_demand` | 0.000 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.176 |
| `market_momentum` | 0.157 |
| `weather_belt_stress` | 0.150 |
| `cross_commodity` | 0.137 |
| `seasonality` | 0.101 |
| `ethanol_demand` | 0.082 |
| `macro_dollar_rates` | 0.065 |
| `cot_positioning` | 0.058 |
| `market_volatility` | 0.045 |
| `production_fundamentals` | 0.030 |

### J+20

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.486 |
| `production_fundamentals` | 0.192 |
| `cot_positioning` | 0.191 |
| `others` | 0.040 |
| `macro_dollar_rates` | 0.035 |
| `market_momentum` | 0.026 |
| `cross_commodity` | 0.010 |
| `weather_belt_stress` | 0.010 |
| `seasonality` | 0.008 |
| `market_volatility` | 0.004 |
| `ethanol_demand` | 0.000 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.195 |
| `market_momentum` | 0.171 |
| `cross_commodity` | 0.128 |
| `seasonality` | 0.103 |
| `ethanol_demand` | 0.098 |
| `weather_belt_stress` | 0.087 |
| `cot_positioning` | 0.079 |
| `macro_dollar_rates` | 0.066 |
| `production_fundamentals` | 0.051 |
| `market_volatility` | 0.023 |

### J+30

| Famille brute | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.525 |
| `production_fundamentals` | 0.193 |
| `cot_positioning` | 0.172 |
| `others` | 0.029 |
| `macro_dollar_rates` | 0.021 |
| `cross_commodity` | 0.018 |
| `market_momentum` | 0.016 |
| `seasonality` | 0.011 |
| `weather_belt_stress` | 0.008 |
| `market_volatility` | 0.005 |
| `ethanol_demand` | 0.001 |

| Famille factorielle | Part coefficient Ridge |
|---|---:|
| `wasde_supply_demand` | 0.198 |
| `market_momentum` | 0.145 |
| `cross_commodity` | 0.141 |
| `ethanol_demand` | 0.111 |
| `cot_positioning` | 0.105 |
| `seasonality` | 0.105 |
| `weather_belt_stress` | 0.072 |
| `macro_dollar_rates` | 0.066 |
| `production_fundamentals` | 0.048 |
| `market_volatility` | 0.009 |

## 8) Lecture par horizon

### J+5

- Sur J+5, le modèle factoriel est -67.3% en RMSE vs features brutes et +1.1% vs zéro-retour; son hit-rate directionnel est +0.005 vs brut.
- Lecture économique dominante: wasde_supply_demand (38%), cot_positioning (23%), production_fundamentals (20%). Les facteurs les plus actifs sont `factor_ethanol_margin_signal`, `factor_weather_heat_stress`, `factor_market_drawdown_recovery`.
- La contribution météo est faiblement concentrée sur l'été (corrélation absolue moyenne été 0.020 vs hors été 0.040).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.468.

### J+10

- Sur J+10, le modèle factoriel est -66.0% en RMSE vs features brutes et +2.8% vs zéro-retour; son hit-rate directionnel est +0.025 vs brut.
- Lecture économique dominante: wasde_supply_demand (39%), cot_positioning (23%), production_fundamentals (20%). Les facteurs les plus actifs sont `factor_market_drawdown_recovery`, `factor_ethanol_margin_signal`, `factor_weather_heat_stress`.
- La contribution météo est davantage concentrée en été (corrélation absolue moyenne été 0.047 vs hors été 0.038).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.587.

### J+20

- Sur J+20, le modèle factoriel est -58.8% en RMSE vs features brutes et +7.1% vs zéro-retour; son hit-rate directionnel est +0.048 vs brut.
- Lecture économique dominante: wasde_supply_demand (49%), production_fundamentals (19%), cot_positioning (19%). Les facteurs les plus actifs sont `factor_market_drawdown_recovery`, `factor_ethanol_margin_signal`, `factor_macro_inflation_signal`.
- La contribution météo est davantage concentrée en été (corrélation absolue moyenne été 0.045 vs hors été 0.043).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.841.

### J+30

- Sur J+30, le modèle factoriel est -53.6% en RMSE vs features brutes et +9.0% vs zéro-retour; son hit-rate directionnel est +0.026 vs brut.
- Lecture économique dominante: wasde_supply_demand (52%), production_fundamentals (19%), cot_positioning (17%). Les facteurs les plus actifs sont `factor_ethanol_margin_signal`, `factor_market_drawdown_recovery`, `factor_cot_speculative_pressure`.
- La contribution météo est davantage concentrée en été (corrélation absolue moyenne été 0.080 vs hors été 0.034).
- Le bloc WASDE-surprises seul a un R2 rolling de -0.650.

## 9) Facteurs dominants

### J+5

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_ethanol_margin_signal` | 0.00662 |
| `factor_weather_heat_stress` | 0.00608 |
| `factor_market_drawdown_recovery` | 0.00594 |
| `factor_macro_inflation_signal` | 0.00442 |
| `factor_weather_core_state_stress` | 0.00399 |
| `factor_cross_energy_link` | 0.00364 |
| `factor_cross_wheat_relative_value` | 0.00336 |
| `factor_cot_speculative_pressure` | 0.00311 |
| `factor_wasde_supply_risk` | 0.00308 |
| `factor_season_pollination_window` | 0.00303 |

### J+10

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_market_drawdown_recovery` | 0.01461 |
| `factor_ethanol_margin_signal` | 0.01249 |
| `factor_weather_heat_stress` | 0.01120 |
| `factor_macro_inflation_signal` | 0.00865 |
| `factor_cross_wheat_relative_value` | 0.00807 |
| `factor_weather_core_state_stress` | 0.00778 |
| `factor_season_pollination_window` | 0.00716 |
| `factor_wasde_supply_risk` | 0.00687 |
| `factor_cross_energy_link` | 0.00668 |
| `factor_cot_speculative_pressure` | 0.00583 |

### J+20

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_market_drawdown_recovery` | 0.03103 |
| `factor_ethanol_margin_signal` | 0.02882 |
| `factor_macro_inflation_signal` | 0.01849 |
| `factor_cross_wheat_relative_value` | 0.01751 |
| `factor_cot_speculative_pressure` | 0.01550 |
| `factor_wasde_supply_risk` | 0.01521 |
| `factor_cross_energy_link` | 0.01501 |
| `factor_season_annual_cycle` | 0.01149 |
| `factor_weather_heat_stress` | 0.01140 |
| `factor_wasde_price_regime` | 0.01125 |

### J+30

| Facteur | Coefficient absolu standardisé |
|---|---:|
| `factor_ethanol_margin_signal` | 0.04366 |
| `factor_market_drawdown_recovery` | 0.03842 |
| `factor_cot_speculative_pressure` | 0.02744 |
| `factor_macro_inflation_signal` | 0.02556 |
| `factor_cross_wheat_relative_value` | 0.02527 |
| `factor_cross_energy_link` | 0.02166 |
| `factor_wasde_supply_risk` | 0.02156 |
| `factor_wasde_balance_tightness` | 0.01957 |
| `factor_wasde_price_regime` | 0.01932 |
| `factor_season_annual_cycle` | 0.01615 |

## 10) Conclusion et prochaine étape

- La vue factorielle est maintenant plus petite, stable et lisible que les 305 features brutes.
- À ce stade, les facteurs ne doivent pas être jugés comme une promesse de RMSE: ils servent surtout à expliquer les familles de risque qui déplacent le prix.
- Prochaine expérimentation incrémentale: ajouter une seule source prioritaire (`EIA ethanol`), relancer ce rapport, mesurer le gain marginal, puis seulement ensuite tester `CFTC COT` et `USDA Crop Progress`.
- Après chaque source: relancer `features`, `targets`, `audit`, `train`, `stack`, `backtest`, `validate_outputs.py`, puis ce rapport.

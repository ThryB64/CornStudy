# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-06-01 05:20:34 UTC`
- Période étudiée: `2000-10-25` -> `2025-07-25`
- Données: 6192 observations, 370 features brutes, 19 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2025-06-26): **SELL_NOW**, fraction de vente 70%, régime `bull`.
- Cash price estimé: 3.99 USD/bu ; q50 J+20: 3.92 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `elasticnet_factors` | `factors` | 0.03495 | 0.02545 | 0.0593 | 0.548 | 2015-09-10 -> 2025-07-18 |
| J+5 | `bayesian_ridge_factors` | `factors` | 0.03497 | 0.02560 | 0.0577 | 0.542 | 2015-09-10 -> 2025-07-18 |
| J+5 | `extratrees_factors` | `factors` | 0.03498 | 0.02529 | 0.0573 | 0.537 | 2015-09-10 -> 2025-07-18 |
| J+5 | `lasso_factors` | `factors` | 0.03500 | 0.02529 | 0.0563 | 0.551 | 2015-09-10 -> 2025-07-18 |
| J+5 | `ridge_factors` | `factors` | 0.03501 | 0.02573 | 0.0556 | 0.541 | 2015-09-10 -> 2025-07-18 |
| J+5 | `rf_factors` | `factors` | 0.03549 | 0.02591 | 0.0297 | 0.520 | 2015-09-10 -> 2025-07-18 |
| J+5 | `baseline_zero_return` | `none` | 0.03603 | 0.02570 | -0.0000 | 0.006 | 2015-09-10 -> 2025-07-18 |
| J+5 | `baseline_momentum_20d` | `none` | 0.03603 | 0.02570 | -0.0000 | 0.006 | 2015-09-10 -> 2025-07-18 |
| J+5 | `baseline_historical_mean` | `none` | 0.03604 | 0.02567 | -0.0009 | 0.523 | 2015-09-10 -> 2025-07-18 |
| J+5 | `hgb_factors` | `factors` | 0.03615 | 0.02661 | -0.0068 | 0.504 | 2015-09-10 -> 2025-07-18 |
| J+5 | `baseline_seasonal_naive` | `none` | 0.03643 | 0.02616 | -0.0226 | 0.526 | 2015-09-10 -> 2025-07-18 |
| J+5 | `xgb_factors` | `factors` | 0.03663 | 0.02685 | -0.0336 | 0.510 | 2015-09-10 -> 2025-07-18 |
| J+5 | `sarimax_seasonal` | `timeseries` | 0.03685 | 0.02636 | -0.0460 | 0.477 | 2015-09-10 -> 2025-07-18 |
| J+5 | `lgbm_factors` | `factors` | 0.03699 | 0.02753 | -0.0540 | 0.510 | 2015-09-10 -> 2025-07-18 |
| J+5 | `arima_auto` | `timeseries` | 0.03766 | 0.02640 | -0.0928 | 0.513 | 2015-09-10 -> 2025-07-18 |
| J+5 | `ridge_raw` | `raw` | 0.10433 | 0.07166 | -7.3849 | 0.484 | 2015-09-10 -> 2025-07-18 |
| J+5 | `garch_vol` | `timeseries` | 0.10608 | 0.10049 | -7.6685 | 0.497 | 2015-09-10 -> 2025-07-18 |
| J+10 | `lasso_factors` | `factors` | 0.04714 | 0.03470 | 0.1146 | 0.587 | 2015-09-04 -> 2025-07-11 |
| J+10 | `elasticnet_factors` | `factors` | 0.04732 | 0.03502 | 0.1080 | 0.590 | 2015-09-04 -> 2025-07-11 |
| J+10 | `bayesian_ridge_factors` | `factors` | 0.04744 | 0.03522 | 0.1033 | 0.581 | 2015-09-04 -> 2025-07-11 |
| J+10 | `ridge_factors` | `factors` | 0.04751 | 0.03535 | 0.1006 | 0.579 | 2015-09-04 -> 2025-07-11 |
| J+10 | `extratrees_factors` | `factors` | 0.04760 | 0.03501 | 0.0973 | 0.559 | 2015-09-04 -> 2025-07-11 |
| J+10 | `rf_factors` | `factors` | 0.04828 | 0.03550 | 0.0715 | 0.572 | 2015-09-04 -> 2025-07-11 |
| J+10 | `hgb_factors` | `factors` | 0.04959 | 0.03659 | 0.0203 | 0.537 | 2015-09-04 -> 2025-07-11 |
| J+10 | `baseline_zero_return` | `none` | 0.05010 | 0.03586 | -0.0001 | 0.002 | 2015-09-04 -> 2025-07-11 |
| J+10 | `baseline_momentum_20d` | `none` | 0.05010 | 0.03586 | -0.0001 | 0.002 | 2015-09-04 -> 2025-07-11 |
| J+10 | `baseline_historical_mean` | `none` | 0.05014 | 0.03581 | -0.0016 | 0.528 | 2015-09-04 -> 2025-07-11 |
| J+10 | `xgb_factors` | `factors` | 0.05027 | 0.03725 | -0.0070 | 0.538 | 2015-09-04 -> 2025-07-11 |
| J+10 | `baseline_seasonal_naive` | `none` | 0.05130 | 0.03663 | -0.0484 | 0.531 | 2015-09-04 -> 2025-07-11 |
| J+10 | `lgbm_factors` | `factors` | 0.05148 | 0.03811 | -0.0560 | 0.527 | 2015-09-04 -> 2025-07-11 |
| J+10 | `sarimax_seasonal` | `timeseries` | 0.06823 | 0.04290 | -0.8549 | 0.494 | 2015-09-04 -> 2025-07-11 |
| J+10 | `arima_auto` | `timeseries` | 0.07049 | 0.04457 | -0.9797 | 0.506 | 2015-09-04 -> 2025-07-11 |
| J+10 | `garch_vol` | `timeseries` | 0.11229 | 0.10302 | -4.0241 | 0.493 | 2015-09-04 -> 2025-07-11 |
| J+10 | `ridge_raw` | `raw` | 0.15179 | 0.10688 | -8.1800 | 0.481 | 2015-09-04 -> 2025-07-11 |
| J+20 | `extratrees_factors` | `factors` | 0.06615 | 0.04845 | 0.1623 | 0.602 | 2015-08-27 -> 2025-06-26 |
| J+20 | `lasso_factors` | `factors` | 0.06665 | 0.04972 | 0.1496 | 0.616 | 2015-08-27 -> 2025-06-26 |
| J+20 | `elasticnet_factors` | `factors` | 0.06705 | 0.05023 | 0.1392 | 0.610 | 2015-08-27 -> 2025-06-26 |
| J+20 | `bayesian_ridge_factors` | `factors` | 0.06733 | 0.05058 | 0.1321 | 0.611 | 2015-08-27 -> 2025-06-26 |
| J+20 | `ridge_factors` | `factors` | 0.06753 | 0.05076 | 0.1271 | 0.607 | 2015-08-27 -> 2025-06-26 |
| J+20 | `rf_factors` | `factors` | 0.06903 | 0.05110 | 0.0878 | 0.620 | 2015-08-27 -> 2025-06-26 |
| J+20 | `xgb_factors` | `factors` | 0.06971 | 0.05202 | 0.0698 | 0.607 | 2015-08-27 -> 2025-06-26 |
| J+20 | `baseline_seasonal_naive` | `none` | 0.07105 | 0.05259 | 0.0337 | 0.555 | 2015-08-27 -> 2025-06-26 |
| J+20 | `hgb_factors` | `factors` | 0.07116 | 0.05293 | 0.0305 | 0.578 | 2015-08-27 -> 2025-06-26 |
| J+20 | `lgbm_factors` | `factors` | 0.07199 | 0.05398 | 0.0080 | 0.562 | 2015-08-27 -> 2025-06-26 |
| J+20 | `baseline_zero_return` | `none` | 0.07228 | 0.05291 | -0.0001 | 0.005 | 2015-08-27 -> 2025-06-26 |
| J+20 | `baseline_momentum_20d` | `none` | 0.07228 | 0.05291 | -0.0001 | 0.005 | 2015-08-27 -> 2025-06-26 |
| J+20 | `baseline_historical_mean` | `none` | 0.07238 | 0.05281 | -0.0028 | 0.533 | 2015-08-27 -> 2025-06-26 |
| J+20 | `garch_vol` | `timeseries` | 0.12363 | 0.10924 | -1.9260 | 0.471 | 2015-08-27 -> 2025-06-26 |
| J+20 | `arima_auto` | `timeseries` | 0.21781 | 0.11935 | -8.0818 | 0.511 | 2015-08-27 -> 2025-06-26 |
| J+20 | `ridge_raw` | `raw` | 0.25700 | 0.17684 | -11.6448 | 0.461 | 2015-08-27 -> 2025-06-26 |
| J+20 | `sarimax_seasonal` | `timeseries` | 0.31336 | 0.21379 | -17.7981 | 0.526 | 2015-08-27 -> 2025-06-26 |
| J+30 | `lasso_factors` | `factors` | 0.08035 | 0.06181 | 0.1830 | 0.632 | 2015-08-19 -> 2025-06-11 |
| J+30 | `elasticnet_factors` | `factors` | 0.08086 | 0.06249 | 0.1725 | 0.630 | 2015-08-19 -> 2025-06-11 |
| J+30 | `bayesian_ridge_factors` | `factors` | 0.08101 | 0.06272 | 0.1694 | 0.631 | 2015-08-19 -> 2025-06-11 |
| J+30 | `ridge_factors` | `factors` | 0.08130 | 0.06298 | 0.1635 | 0.627 | 2015-08-19 -> 2025-06-11 |
| J+30 | `extratrees_factors` | `factors` | 0.08160 | 0.06233 | 0.1574 | 0.600 | 2015-08-19 -> 2025-06-11 |
| J+30 | `baseline_seasonal_naive` | `none` | 0.08475 | 0.06370 | 0.0909 | 0.583 | 2015-08-19 -> 2025-06-11 |
| J+30 | `hgb_factors` | `factors` | 0.08490 | 0.06514 | 0.0877 | 0.596 | 2015-08-19 -> 2025-06-11 |
| J+30 | `xgb_factors` | `factors` | 0.08506 | 0.06530 | 0.0843 | 0.619 | 2015-08-19 -> 2025-06-11 |
| J+30 | `rf_factors` | `factors` | 0.08580 | 0.06509 | 0.0683 | 0.587 | 2015-08-19 -> 2025-06-11 |
| J+30 | `lgbm_factors` | `factors` | 0.08677 | 0.06665 | 0.0472 | 0.603 | 2015-08-19 -> 2025-06-11 |
| J+30 | `baseline_zero_return` | `none` | 0.08890 | 0.06647 | -0.0002 | 0.005 | 2015-08-19 -> 2025-06-11 |
| J+30 | `baseline_momentum_20d` | `none` | 0.08890 | 0.06647 | -0.0002 | 0.005 | 2015-08-19 -> 2025-06-11 |
| J+30 | `baseline_historical_mean` | `none` | 0.08909 | 0.06635 | -0.0045 | 0.534 | 2015-08-19 -> 2025-06-11 |
| J+30 | `garch_vol` | `timeseries` | 0.13136 | 0.11037 | -1.1837 | 0.469 | 2015-08-19 -> 2025-06-11 |
| J+30 | `ridge_raw` | `raw` | 0.30873 | 0.21641 | -11.0633 | 0.425 | 2015-08-19 -> 2025-06-11 |
| J+30 | `arima_auto` | `timeseries` | 0.52116 | 0.26746 | -33.3751 | 0.477 | 2015-08-19 -> 2025-06-11 |
| J+30 | `sarimax_seasonal` | `timeseries` | 0.63066 | 0.37642 | -49.3364 | 0.488 | 2015-08-19 -> 2025-06-11 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `raw_signal` | 0.213 | -0.00028 |
| J+5 | `wasde_supply_demand` | 0.195 | -0.00043 |
| J+5 | `weather_belt_stress` | 0.183 | 0.00007 |
| J+5 | `cross_commodity` | 0.121 | -0.00025 |
| J+5 | `positioning` | 0.084 | -0.00038 |
| J+5 | `market_momentum` | 0.064 | 0.00004 |
| J+5 | `macro_dollar_rates` | 0.063 | -0.00022 |
| J+5 | `seasonality` | 0.048 | 0.00013 |
| J+5 | `weather_advanced` | 0.021 | -0.00011 |
| J+5 | `wasde_surprises_z` | 0.008 | -0.00000 |
| J+5 | `market_volatility` | 0.002 | 0.00001 |
| J+10 | `wasde_supply_demand` | 0.236 | -0.00162 |
| J+10 | `raw_signal` | 0.213 | -0.00072 |
| J+10 | `weather_belt_stress` | 0.144 | -0.00052 |
| J+10 | `cross_commodity` | 0.125 | -0.00076 |
| J+10 | `market_momentum` | 0.071 | 0.00009 |
| J+10 | `seasonality` | 0.064 | 0.00040 |
| J+10 | `macro_dollar_rates` | 0.062 | -0.00041 |
| J+10 | `positioning` | 0.060 | -0.00070 |
| J+10 | `wasde_surprises_z` | 0.012 | -0.00001 |
| J+10 | `weather_advanced` | 0.007 | -0.00004 |
| J+10 | `market_volatility` | 0.006 | 0.00004 |
| J+20 | `raw_signal` | 0.211 | -0.00028 |
| J+20 | `wasde_supply_demand` | 0.194 | -0.00226 |
| J+20 | `market_momentum` | 0.137 | 0.00032 |
| J+20 | `weather_belt_stress` | 0.128 | 0.00010 |
| J+20 | `cross_commodity` | 0.119 | -0.00155 |
| J+20 | `positioning` | 0.079 | -0.00226 |
| J+20 | `market_volatility` | 0.047 | 0.00076 |
| J+20 | `macro_dollar_rates` | 0.041 | -0.00041 |
| J+20 | `seasonality` | 0.035 | 0.00055 |
| J+20 | `wasde_surprises_z` | 0.006 | -0.00000 |
| J+20 | `weather_advanced` | 0.003 | 0.00000 |
| J+30 | `raw_signal` | 0.168 | 0.00008 |
| J+30 | `market_momentum` | 0.167 | 0.00041 |
| J+30 | `wasde_supply_demand` | 0.164 | -0.00136 |
| J+30 | `positioning` | 0.146 | -0.00252 |
| J+30 | `weather_belt_stress` | 0.114 | -0.00065 |
| J+30 | `seasonality` | 0.071 | 0.00207 |
| J+30 | `market_volatility` | 0.054 | 0.00093 |
| J+30 | `cross_commodity` | 0.050 | -0.00084 |
| J+30 | `macro_dollar_rates` | 0.043 | -0.00032 |
| J+30 | `wasde_surprises_z` | 0.015 | -0.00001 |
| J+30 | `weather_advanced` | 0.009 | -0.00003 |

## Top facteurs Ridge

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.213 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.163 |
| J+5 | `factor_cross_commodity` | `cross_commodity` | 0.121 |
| J+5 | `factor_drought_severity` | `weather_belt_stress` | 0.072 |
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.063 |
| J+5 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.063 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.059 |
| J+5 | `factor_positioning` | `positioning` | 0.056 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.213 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.190 |
| J+10 | `factor_cross_commodity` | `cross_commodity` | 0.125 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.070 |
| J+10 | `factor_seasonality` | `seasonality` | 0.064 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.062 |
| J+10 | `factor_positioning` | `positioning` | 0.057 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.054 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.211 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.134 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.134 |
| J+20 | `factor_cross_commodity` | `cross_commodity` | 0.119 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.088 |
| J+20 | `factor_positioning` | `positioning` | 0.071 |
| J+20 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.060 |
| J+20 | `factor_market_volatility` | `market_volatility` | 0.047 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.168 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.152 |
| J+30 | `factor_positioning` | `positioning` | 0.112 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.106 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.095 |
| J+30 | `factor_seasonality` | `seasonality` | 0.071 |
| J+30 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.069 |
| J+30 | `factor_market_volatility` | `market_volatility` | 0.054 |

## Top facteurs SHAP

| Horizon | Facteur | Famille | Part mean(|SHAP|) |
|---:|---|---|---:|
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.135 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.122 |
| J+5 | `factor_curve_structure` | `market_momentum` | 0.105 |
| J+5 | `factor_positioning` | `positioning` | 0.103 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.078 |
| J+5 | `factor_drought_severity` | `weather_belt_stress` | 0.064 |
| J+5 | `factor_raw_signal` | `raw_signal` | 0.060 |
| J+5 | `factor_market_volatility` | `market_volatility` | 0.053 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.141 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.121 |
| J+10 | `factor_positioning` | `positioning` | 0.107 |
| J+10 | `factor_curve_structure` | `market_momentum` | 0.103 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.092 |
| J+10 | `factor_seasonality` | `seasonality` | 0.063 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.060 |
| J+10 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.051 |
| J+20 | `factor_positioning` | `positioning` | 0.164 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.114 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.103 |
| J+20 | `factor_curve_structure` | `market_momentum` | 0.095 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.078 |
| J+20 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.073 |
| J+20 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.069 |
| J+20 | `factor_seasonality` | `seasonality` | 0.058 |
| J+30 | `factor_positioning` | `positioning` | 0.169 |
| J+30 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.113 |
| J+30 | `factor_seasonality` | `seasonality` | 0.098 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.097 |
| J+30 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.084 |
| J+30 | `factor_curve_structure` | `market_momentum` | 0.080 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.058 |
| J+30 | `factor_market_breadth` | `positioning` | 0.048 |

## Intervalles CQR

| Horizon | Couverture réalisée | Largeur moyenne | N test |
|---:|---:|---:|---:|
| J+5 | 0.909 / cible 0.900 | 0.11287 | 2475 |
| J+10 | 0.909 / cible 0.900 | 0.15566 | 2473 |
| J+20 | 0.912 / cible 0.900 | 0.23607 | 2469 |
| J+30 | 0.903 / cible 0.900 | 0.27522 | 2465 |

Lecture: la CQR est exécutée et calibrée, mais la couverture réalisée reste sous 90% sur ce backtest, signe d'une forte dérive temporelle. Le résultat est donc utilisable comme diagnostic, pas comme garantie opérationnelle parfaite.

## Couverture sources

| Source | Statut | Features | Priorité |
|---|---|---:|---:|
| `eia_ethanol` | `active_in_features` | 2 | 1 |
| `cftc_cot_corn` | `active_in_features` | 69 | 2 |
| `usda_nass_crop_progress` | `enabled_not_in_features` | 0 | 3 |
| `usda_nass_crop_condition` | `enabled_not_in_features` | 0 | 4 |
| `usda_fas_export_sales` | `enabled_not_in_features` | 0 | 5 |
| `us_drought_monitor` | `planned` | 0 | 6 |
| `usda_wasde` | `active_in_features` | 132 | 7 |
| `openmeteo_states` | `active_in_features` | 19 | 8 |
| `agreste_france` | `planned` | 0 | 50 |
| `asia_tenders` | `planned` | 0 | 50 |
| `bcr_argentina` | `planned` | 0 | 50 |
| `brazil_export_inspections` | `planned` | 0 | 50 |
| `brazil_fob_prices` | `planned` | 0 | 50 |
| `brent` | `enabled_not_in_features` | 0 | 50 |
| `cbot_corn` | `active_in_features` | 30 | 50 |
| `cbot_oats` | `active_in_features` | 30 | 50 |
| `cbot_soy` | `active_in_features` | 2 | 50 |
| `cbot_wheat` | `active_in_features` | 3 | 50 |

## État réel d'implémentation

Ce tableau distingue ce qui est effectivement codé et exécuté de ce qui est prévu ou partiellement implémenté. Aucun élément n'est décrit comme implémenté s'il ne l'est pas.

| Fonctionnalité | Statut | Note |
|---|---|---|
| Collecte données (WASDE, FRED, NASS, OpenMeteo) | ✅ Implémenté | Collecteurs et tables locales validés |
| Anti-leakage (5 checks, |corr|>0.97) | ✅ Implémenté | Audit automatisé à chaque build |
| Cibles y_logret_h{5,10,20,30} | ✅ Implémenté | Expanding quantile, anti-leakage |
| Features brutes | ✅ Implémenté | 370 colonnes |
| Facteurs synthétiques | ✅ Implémenté | 19 facteurs, expanding z-scores |
| Walk-forward temporel | ✅ Implémenté | Train historique, tests par blocs, embargo par horizon |
| Benchmark modèles | ✅ Implémenté | Ridge, ElasticNet, RF, HGB ; boosters si installés |
| Stacking Ridge sur meta-database | ⚠️ Hors rapport walk-forward | Disponible via `mais stack` ; non inclus dans les benchmarks de cette étude. |
| Intervalles de confiance (split-conformal) | ✅ Implémenté | Moyenne covered_90 ≈ 0.890. |
| Régime de marché (bull/bear/range) | ⚠️ Partiel | Méthode : markov_2state ; labels observés : ['bear', 'bull']. |
| Décision agriculteur (SELL/STORE/WAIT) | ✅ Implémenté | Moteur YAML paramétrable |
| Importance par coefficient Ridge | ✅ Implémenté | Ablation par famille |
| Analyse SHAP | ✅ Implémenté | 76 lignes SHAP dans l'export. |
| Conformalized Quantile Regression (CQR) | ✅ Implémenté | Couverture empirique moyenne 0.908 (objectif projet ≥0.88). |
| Régime Markov-switching | ⚠️ Fallback | Statsmodels MarkovRegression, fallback rule-based si échec. |
| EIA éthanol dans features | ⚠️ Proxy intégré | Proxy marge énergie/maïs sans clé EIA ; vraie EIA activable avec clé API. |
| CFTC COT — fichier interim | ✅ Présent | `data/interim/cftc_cot.parquet`. |
| CFTC COT — colonnes features (`cot_mm_net`) | ✅ Présent | 69 colonnes `cot_*`. |
| CFTC COT — impact mesuré (ablation) | ⚠️ Non mesuré | Pas d'ablation COT dédiée dans ce rapport. |
| NDVI / indices de végétation satellite | ❌ Non implémenté | Hors périmètre actuel. |
| ENSO / El Niño | ❌ Non implémenté | Hors périmètre actuel. |
| Optuna LightGBM | ⚠️ Désactivé par défaut | Disponible via build_professional_study(optimize=True), désactivé sur le build normal. |
| XGBoost/LightGBM | ✅ Benchmark | Benchmark walk-forward : LightGBM, XGBoost actifs. |

## Conclusion opérationnelle

Le projet dispose d'une architecture solide et d'une base technique propre. Les modèles actifs (RF, HGB sur facteurs) surpassent le zéro-return baseline sur la précision directionnelle (55–60% à J+20/30). Les familles production_fundamentals, ethanol_demand, cot_positioning et macro_dollar_rates sont intégrées sans fuite temporelle. Leur valeur ajoutée doit se lire par horizon : certaines informations sont redondantes avec WASDE en Ridge, mais utiles pour les modèles non linéaires et pour l'explication économique.

Prochaines étapes par ordre de priorité : (1) fournir une vraie clé EIA pour remplacer le proxy éthanol ; (2) mesurer l'ablation CFTC/EIA source par source ; (3) ajouter USDA Crop Progress ; (4) intégrer LightGBM/XGBoost au stacking historique si le gain walk-forward est stable.

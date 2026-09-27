# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-09-27 15:07:09 UTC`
- Période étudiée: `2000-10-25` -> `2026-09-25`
- Données: 6486 observations, 375 features brutes, 19 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2026-08-27): **SELL_THIRDS_OVER_60_DAYS**, fraction de vente 33%, régime `bull`.
- Cash price estimé: 5.08 USD/bu ; q50 J+20: 5.24 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `extratrees_factors` | `factors` | 0.03464 | 0.02506 | 0.0649 | 0.562 | 2016-05-23 -> 2026-09-18 |
| J+5 | `elasticnet_factors` | `factors` | 0.03476 | 0.02495 | 0.0583 | 0.578 | 2016-05-23 -> 2026-09-18 |
| J+5 | `bayesian_ridge_factors` | `factors` | 0.03479 | 0.02499 | 0.0564 | 0.572 | 2016-05-23 -> 2026-09-18 |
| J+5 | `ridge_factors` | `factors` | 0.03481 | 0.02504 | 0.0556 | 0.570 | 2016-05-23 -> 2026-09-18 |
| J+5 | `lasso_factors` | `factors` | 0.03482 | 0.02498 | 0.0548 | 0.585 | 2016-05-23 -> 2026-09-18 |
| J+5 | `hgb_factors` | `factors` | 0.03503 | 0.02550 | 0.0436 | 0.558 | 2016-05-23 -> 2026-09-18 |
| J+5 | `rf_factors` | `factors` | 0.03507 | 0.02535 | 0.0411 | 0.538 | 2016-05-23 -> 2026-09-18 |
| J+5 | `xgb_factors` | `factors` | 0.03517 | 0.02546 | 0.0359 | 0.546 | 2016-05-23 -> 2026-09-18 |
| J+5 | `lgbm_factors` | `factors` | 0.03554 | 0.02625 | 0.0156 | 0.525 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_zero_return` | `none` | 0.03582 | 0.02558 | -0.0002 | 0.007 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_momentum_20d` | `none` | 0.03582 | 0.02558 | -0.0002 | 0.007 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_historical_mean` | `none` | 0.03584 | 0.02556 | -0.0012 | 0.523 | 2016-05-23 -> 2026-09-18 |
| J+5 | `sarimax_seasonal` | `timeseries` | 0.03617 | 0.02607 | -0.0198 | 0.505 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_seasonal_naive` | `none` | 0.03628 | 0.02599 | -0.0258 | 0.545 | 2016-05-23 -> 2026-09-18 |
| J+5 | `arima_auto` | `timeseries` | 0.03656 | 0.02596 | -0.0418 | 0.521 | 2016-05-23 -> 2026-09-18 |
| J+5 | `ridge_raw` | `raw` | 0.08479 | 0.05741 | -4.6045 | 0.548 | 2016-05-23 -> 2026-09-18 |
| J+5 | `garch_vol` | `timeseries` | 0.09851 | 0.08972 | -6.5647 | 0.503 | 2016-05-23 -> 2026-09-18 |
| J+10 | `extratrees_factors` | `factors` | 0.04698 | 0.03414 | 0.1191 | 0.615 | 2016-05-18 -> 2026-09-11 |
| J+10 | `lasso_factors` | `factors` | 0.04722 | 0.03412 | 0.1102 | 0.611 | 2016-05-18 -> 2026-09-11 |
| J+10 | `elasticnet_factors` | `factors` | 0.04728 | 0.03427 | 0.1079 | 0.608 | 2016-05-18 -> 2026-09-11 |
| J+10 | `bayesian_ridge_factors` | `factors` | 0.04734 | 0.03441 | 0.1056 | 0.609 | 2016-05-18 -> 2026-09-11 |
| J+10 | `ridge_factors` | `factors` | 0.04741 | 0.03454 | 0.1029 | 0.604 | 2016-05-18 -> 2026-09-11 |
| J+10 | `hgb_factors` | `factors` | 0.04758 | 0.03449 | 0.0963 | 0.576 | 2016-05-18 -> 2026-09-11 |
| J+10 | `xgb_factors` | `factors` | 0.04822 | 0.03492 | 0.0720 | 0.558 | 2016-05-18 -> 2026-09-11 |
| J+10 | `lgbm_factors` | `factors` | 0.04852 | 0.03554 | 0.0605 | 0.552 | 2016-05-18 -> 2026-09-11 |
| J+10 | `rf_factors` | `factors` | 0.04886 | 0.03506 | 0.0470 | 0.587 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_zero_return` | `none` | 0.05007 | 0.03580 | -0.0005 | 0.006 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_momentum_20d` | `none` | 0.05007 | 0.03580 | -0.0005 | 0.006 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_historical_mean` | `none` | 0.05011 | 0.03572 | -0.0023 | 0.536 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_seasonal_naive` | `none` | 0.05140 | 0.03663 | -0.0543 | 0.549 | 2016-05-18 -> 2026-09-11 |
| J+10 | `sarimax_seasonal` | `timeseries` | 0.07963 | 0.04407 | -1.5306 | 0.460 | 2016-05-18 -> 2026-09-11 |
| J+10 | `arima_auto` | `timeseries` | 0.08776 | 0.04706 | -2.0739 | 0.540 | 2016-05-18 -> 2026-09-11 |
| J+10 | `garch_vol` | `timeseries` | 0.10268 | 0.09118 | -3.2075 | 0.540 | 2016-05-18 -> 2026-09-11 |
| J+10 | `ridge_raw` | `raw` | 0.13626 | 0.09305 | -6.4105 | 0.531 | 2016-05-18 -> 2026-09-11 |
| J+20 | `elasticnet_factors` | `factors` | 0.06594 | 0.04891 | 0.1772 | 0.647 | 2016-05-10 -> 2026-08-27 |
| J+20 | `lasso_factors` | `factors` | 0.06596 | 0.04877 | 0.1768 | 0.652 | 2016-05-10 -> 2026-08-27 |
| J+20 | `bayesian_ridge_factors` | `factors` | 0.06605 | 0.04908 | 0.1746 | 0.643 | 2016-05-10 -> 2026-08-27 |
| J+20 | `ridge_factors` | `factors` | 0.06616 | 0.04920 | 0.1718 | 0.641 | 2016-05-10 -> 2026-08-27 |
| J+20 | `extratrees_factors` | `factors` | 0.06726 | 0.04972 | 0.1439 | 0.608 | 2016-05-10 -> 2026-08-27 |
| J+20 | `rf_factors` | `factors` | 0.06953 | 0.05190 | 0.0853 | 0.601 | 2016-05-10 -> 2026-08-27 |
| J+20 | `hgb_factors` | `factors` | 0.06999 | 0.05195 | 0.0732 | 0.588 | 2016-05-10 -> 2026-08-27 |
| J+20 | `lgbm_factors` | `factors` | 0.07022 | 0.05243 | 0.0671 | 0.591 | 2016-05-10 -> 2026-08-27 |
| J+20 | `xgb_factors` | `factors` | 0.07044 | 0.05193 | 0.0611 | 0.601 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_zero_return` | `none` | 0.07272 | 0.05369 | -0.0008 | 0.005 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_momentum_20d` | `none` | 0.07272 | 0.05369 | -0.0008 | 0.005 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_historical_mean` | `none` | 0.07287 | 0.05354 | -0.0047 | 0.545 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_seasonal_naive` | `none` | 0.07304 | 0.05444 | -0.0096 | 0.572 | 2016-05-10 -> 2026-08-27 |
| J+20 | `garch_vol` | `timeseries` | 0.12052 | 0.09962 | -1.7485 | 0.505 | 2016-05-10 -> 2026-08-27 |
| J+20 | `arima_auto` | `timeseries` | 0.19683 | 0.10652 | -6.3310 | 0.572 | 2016-05-10 -> 2026-08-27 |
| J+20 | `ridge_raw` | `raw` | 0.25237 | 0.16107 | -11.0518 | 0.521 | 2016-05-10 -> 2026-08-27 |
| J+20 | `sarimax_seasonal` | `timeseries` | 0.38727 | 0.21194 | -27.3789 | 0.510 | 2016-05-10 -> 2026-08-27 |
| J+30 | `elasticnet_factors` | `factors` | 0.07912 | 0.06015 | 0.2161 | 0.650 | 2016-05-02 -> 2026-08-13 |
| J+30 | `bayesian_ridge_factors` | `factors` | 0.07912 | 0.06022 | 0.2160 | 0.647 | 2016-05-02 -> 2026-08-13 |
| J+30 | `ridge_factors` | `factors` | 0.07918 | 0.06033 | 0.2148 | 0.646 | 2016-05-02 -> 2026-08-13 |
| J+30 | `lasso_factors` | `factors` | 0.07922 | 0.06003 | 0.2140 | 0.654 | 2016-05-02 -> 2026-08-13 |
| J+30 | `extratrees_factors` | `factors` | 0.08139 | 0.06175 | 0.1704 | 0.629 | 2016-05-02 -> 2026-08-13 |
| J+30 | `lgbm_factors` | `factors` | 0.08309 | 0.06459 | 0.1354 | 0.602 | 2016-05-02 -> 2026-08-13 |
| J+30 | `hgb_factors` | `factors` | 0.08367 | 0.06400 | 0.1233 | 0.636 | 2016-05-02 -> 2026-08-13 |
| J+30 | `rf_factors` | `factors` | 0.08439 | 0.06604 | 0.1081 | 0.593 | 2016-05-02 -> 2026-08-13 |
| J+30 | `xgb_factors` | `factors` | 0.08522 | 0.06599 | 0.0904 | 0.613 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_seasonal_naive` | `none` | 0.08781 | 0.06666 | 0.0343 | 0.614 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_zero_return` | `none` | 0.08940 | 0.06760 | -0.0010 | 0.004 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_momentum_20d` | `none` | 0.08940 | 0.06760 | -0.0010 | 0.004 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_historical_mean` | `none` | 0.08967 | 0.06739 | -0.0070 | 0.552 | 2016-05-02 -> 2026-08-13 |
| J+30 | `garch_vol` | `timeseries` | 0.14144 | 0.11773 | -1.5052 | 0.484 | 2016-05-02 -> 2026-08-13 |
| J+30 | `ridge_raw` | `raw` | 0.33468 | 0.21475 | -13.0281 | 0.506 | 2016-05-02 -> 2026-08-13 |
| J+30 | `arima_auto` | `timeseries` | 0.61448 | 0.28229 | -46.2878 | 0.568 | 2016-05-02 -> 2026-08-13 |
| J+30 | `sarimax_seasonal` | `timeseries` | 0.96877 | 0.53238 | -116.5356 | 0.494 | 2016-05-02 -> 2026-08-13 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `raw_signal` | 0.211 | -0.00029 |
| J+5 | `wasde_supply_demand` | 0.161 | 0.00162 |
| J+5 | `weather_belt_stress` | 0.150 | 0.00068 |
| J+5 | `positioning` | 0.139 | 0.00137 |
| J+5 | `cross_commodity` | 0.116 | 0.00004 |
| J+5 | `market_momentum` | 0.107 | -0.00002 |
| J+5 | `seasonality` | 0.050 | -0.00016 |
| J+5 | `market_volatility` | 0.032 | -0.00010 |
| J+5 | `macro_dollar_rates` | 0.022 | 0.00002 |
| J+5 | `weather_advanced` | 0.009 | 0.00003 |
| J+5 | `wasde_surprises_z` | 0.003 | 0.00001 |
| J+10 | `raw_signal` | 0.202 | 0.00034 |
| J+10 | `wasde_supply_demand` | 0.175 | 0.00372 |
| J+10 | `positioning` | 0.152 | 0.00253 |
| J+10 | `weather_belt_stress` | 0.134 | 0.00166 |
| J+10 | `cross_commodity` | 0.104 | 0.00039 |
| J+10 | `market_momentum` | 0.097 | -0.00024 |
| J+10 | `seasonality` | 0.064 | -0.00075 |
| J+10 | `market_volatility` | 0.031 | -0.00021 |
| J+10 | `macro_dollar_rates` | 0.026 | 0.00010 |
| J+10 | `wasde_surprises_z` | 0.012 | 0.00000 |
| J+10 | `weather_advanced` | 0.002 | -0.00001 |
| J+20 | `raw_signal` | 0.186 | 0.00445 |
| J+20 | `wasde_supply_demand` | 0.169 | 0.00760 |
| J+20 | `weather_belt_stress` | 0.150 | 0.00339 |
| J+20 | `market_momentum` | 0.139 | -0.00122 |
| J+20 | `positioning` | 0.127 | 0.00422 |
| J+20 | `cross_commodity` | 0.112 | 0.00232 |
| J+20 | `market_volatility` | 0.058 | -0.00100 |
| J+20 | `weather_advanced` | 0.023 | 0.00023 |
| J+20 | `seasonality` | 0.023 | -0.00133 |
| J+20 | `macro_dollar_rates` | 0.012 | 0.00046 |
| J+20 | `wasde_surprises_z` | 0.001 | 0.00000 |
| J+30 | `wasde_supply_demand` | 0.164 | 0.00668 |
| J+30 | `positioning` | 0.161 | 0.01044 |
| J+30 | `market_momentum` | 0.157 | -0.00273 |
| J+30 | `raw_signal` | 0.155 | 0.00313 |
| J+30 | `weather_belt_stress` | 0.140 | 0.00363 |
| J+30 | `cross_commodity` | 0.072 | 0.00153 |
| J+30 | `market_volatility` | 0.059 | -0.00193 |
| J+30 | `seasonality` | 0.053 | -0.00517 |
| J+30 | `weather_advanced` | 0.037 | 0.00171 |
| J+30 | `macro_dollar_rates` | 0.001 | -0.00007 |
| J+30 | `wasde_surprises_z` | 0.001 | 0.00000 |

## Top facteurs Ridge

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.211 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.129 |
| J+5 | `factor_cross_commodity` | `cross_commodity` | 0.116 |
| J+5 | `factor_positioning` | `positioning` | 0.094 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.086 |
| J+5 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.061 |
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.060 |
| J+5 | `factor_seasonality` | `seasonality` | 0.050 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.202 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.130 |
| J+10 | `factor_cross_commodity` | `cross_commodity` | 0.104 |
| J+10 | `factor_positioning` | `positioning` | 0.090 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.089 |
| J+10 | `factor_seasonality` | `seasonality` | 0.064 |
| J+10 | `factor_market_breadth` | `positioning` | 0.062 |
| J+10 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.061 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.186 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.130 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.113 |
| J+20 | `factor_cross_commodity` | `cross_commodity` | 0.112 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.098 |
| J+20 | `factor_positioning` | `positioning` | 0.083 |
| J+20 | `factor_market_volatility` | `market_volatility` | 0.058 |
| J+20 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.056 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.155 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.148 |
| J+30 | `factor_positioning` | `positioning` | 0.112 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.104 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.095 |
| J+30 | `factor_cross_commodity` | `cross_commodity` | 0.072 |
| J+30 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.069 |
| J+30 | `factor_market_volatility` | `market_volatility` | 0.059 |

## Top facteurs SHAP

| Horizon | Facteur | Famille | Part mean(|SHAP|) |
|---:|---|---|---:|
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.200 |
| J+5 | `factor_positioning` | `positioning` | 0.163 |
| J+5 | `factor_curve_structure` | `market_momentum` | 0.093 |
| J+5 | `factor_market_breadth` | `positioning` | 0.087 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.069 |
| J+5 | `factor_raw_signal` | `raw_signal` | 0.061 |
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.061 |
| J+5 | `factor_weather_advanced` | `weather_advanced` | 0.047 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.206 |
| J+10 | `factor_positioning` | `positioning` | 0.191 |
| J+10 | `factor_seasonality` | `seasonality` | 0.125 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.068 |
| J+10 | `factor_curve_structure` | `market_momentum` | 0.051 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.044 |
| J+10 | `factor_market_breadth` | `positioning` | 0.039 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.039 |
| J+20 | `factor_seasonality` | `seasonality` | 0.180 |
| J+20 | `factor_positioning` | `positioning` | 0.110 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.109 |
| J+20 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.106 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.073 |
| J+20 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.061 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.061 |
| J+20 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.054 |
| J+30 | `factor_seasonality` | `seasonality` | 0.250 |
| J+30 | `factor_positioning` | `positioning` | 0.147 |
| J+30 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.109 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.085 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.082 |
| J+30 | `factor_cross_commodity` | `cross_commodity` | 0.054 |
| J+30 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.042 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.042 |

## Intervalles CQR

| Horizon | Couverture réalisée | Largeur moyenne | N test |
|---:|---:|---:|---:|
| J+5 | 0.908 / cible 0.900 | 0.11101 | 2593 |
| J+10 | 0.912 / cible 0.900 | 0.15316 | 2591 |
| J+20 | 0.896 / cible 0.900 | 0.22827 | 2587 |
| J+30 | 0.896 / cible 0.900 | 0.27201 | 2583 |

Lecture: la CQR est exécutée et calibrée, mais la couverture réalisée reste sous 90% sur ce backtest, signe d'une forte dérive temporelle. Le résultat est donc utilisable comme diagnostic, pas comme garantie opérationnelle parfaite.

## Couverture sources

| Source | Statut | Features | Priorité |
|---|---|---:|---:|
| `eia_ethanol` | `active_in_features` | 2 | 1 |
| `cftc_cot_corn` | `active_in_features` | 69 | 2 |
| `usda_nass_crop_progress` | `enabled_not_in_features` | 0 | 3 |
| `usda_nass_crop_condition` | `enabled_not_in_features` | 0 | 4 |
| `usda_fas_export_sales` | `enabled_not_in_features` | 0 | 5 |
| `us_drought_monitor` | `enabled_not_in_features` | 0 | 6 |
| `usda_wasde` | `active_in_features` | 132 | 7 |
| `openmeteo_states` | `active_in_features` | 24 | 8 |
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
| Features brutes | ✅ Implémenté | 375 colonnes |
| Facteurs synthétiques | ✅ Implémenté | 19 facteurs, expanding z-scores |
| Walk-forward temporel | ✅ Implémenté | Train historique, tests par blocs, embargo par horizon |
| Benchmark modèles | ✅ Implémenté | Ridge, ElasticNet, RF, HGB ; boosters si installés |
| Stacking Ridge sur meta-database | ⚠️ Hors rapport walk-forward | Disponible via `mais stack` ; non inclus dans les benchmarks de cette étude. |
| Intervalles de confiance (split-conformal) | ✅ Implémenté | Moyenne covered_90 ≈ 0.892. |
| Régime de marché (bull/bear/range) | ⚠️ Partiel | Méthode : markov_2state ; labels observés : ['bear', 'bull']. |
| Décision agriculteur (SELL/STORE/WAIT) | ✅ Implémenté | Moteur YAML paramétrable |
| Importance par coefficient Ridge | ✅ Implémenté | Ablation par famille |
| Analyse SHAP | ✅ Implémenté | 76 lignes SHAP dans l'export. |
| Conformalized Quantile Regression (CQR) | ✅ Implémenté | Couverture empirique moyenne 0.903 (objectif projet ≥0.88). |
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

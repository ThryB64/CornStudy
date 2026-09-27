# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-09-27 16:35:20 UTC`
- Période étudiée: `2000-10-25` -> `2026-09-25`
- Données: 6486 observations, 375 features brutes, 19 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2026-08-27): **SELL_THIRDS**, fraction de vente 33%, régime `bull`.
- Cash price estimé: 5.08 USD/bu ; q50 J+20: 5.23 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `extratrees_factors` | `factors` | 0.03453 | 0.02482 | 0.0708 | 0.583 | 2016-05-23 -> 2026-09-18 |
| J+5 | `elasticnet_factors` | `factors` | 0.03480 | 0.02489 | 0.0557 | 0.583 | 2016-05-23 -> 2026-09-18 |
| J+5 | `bayesian_ridge_factors` | `factors` | 0.03483 | 0.02494 | 0.0545 | 0.577 | 2016-05-23 -> 2026-09-18 |
| J+5 | `rf_factors` | `factors` | 0.03484 | 0.02512 | 0.0540 | 0.559 | 2016-05-23 -> 2026-09-18 |
| J+5 | `lasso_factors` | `factors` | 0.03484 | 0.02491 | 0.0540 | 0.586 | 2016-05-23 -> 2026-09-18 |
| J+5 | `ridge_factors` | `factors` | 0.03490 | 0.02503 | 0.0507 | 0.580 | 2016-05-23 -> 2026-09-18 |
| J+5 | `hgb_factors` | `factors` | 0.03546 | 0.02573 | 0.0197 | 0.555 | 2016-05-23 -> 2026-09-18 |
| J+5 | `lgbm_factors` | `factors` | 0.03568 | 0.02620 | 0.0079 | 0.537 | 2016-05-23 -> 2026-09-18 |
| J+5 | `xgb_factors` | `factors` | 0.03574 | 0.02594 | 0.0042 | 0.545 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_zero_return` | `none` | 0.03582 | 0.02558 | -0.0002 | 0.007 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_momentum_20d` | `none` | 0.03582 | 0.02558 | -0.0002 | 0.007 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_historical_mean` | `none` | 0.03584 | 0.02556 | -0.0012 | 0.523 | 2016-05-23 -> 2026-09-18 |
| J+5 | `sarimax_seasonal` | `timeseries` | 0.03617 | 0.02607 | -0.0198 | 0.505 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_seasonal_naive` | `none` | 0.03628 | 0.02599 | -0.0258 | 0.545 | 2016-05-23 -> 2026-09-18 |
| J+5 | `arima_auto` | `timeseries` | 0.03656 | 0.02596 | -0.0418 | 0.521 | 2016-05-23 -> 2026-09-18 |
| J+5 | `ridge_raw` | `raw` | 0.08480 | 0.05738 | -4.6051 | 0.550 | 2016-05-23 -> 2026-09-18 |
| J+5 | `garch_vol` | `timeseries` | 0.09851 | 0.08972 | -6.5647 | 0.503 | 2016-05-23 -> 2026-09-18 |
| J+10 | `extratrees_factors` | `factors` | 0.04676 | 0.03375 | 0.1273 | 0.621 | 2016-05-18 -> 2026-09-11 |
| J+10 | `lasso_factors` | `factors` | 0.04726 | 0.03403 | 0.1087 | 0.616 | 2016-05-18 -> 2026-09-11 |
| J+10 | `elasticnet_factors` | `factors` | 0.04727 | 0.03422 | 0.1084 | 0.617 | 2016-05-18 -> 2026-09-11 |
| J+10 | `bayesian_ridge_factors` | `factors` | 0.04727 | 0.03436 | 0.1082 | 0.611 | 2016-05-18 -> 2026-09-11 |
| J+10 | `ridge_factors` | `factors` | 0.04737 | 0.03455 | 0.1043 | 0.607 | 2016-05-18 -> 2026-09-11 |
| J+10 | `hgb_factors` | `factors` | 0.04738 | 0.03437 | 0.1042 | 0.599 | 2016-05-18 -> 2026-09-11 |
| J+10 | `rf_factors` | `factors` | 0.04772 | 0.03419 | 0.0912 | 0.599 | 2016-05-18 -> 2026-09-11 |
| J+10 | `xgb_factors` | `factors` | 0.04773 | 0.03438 | 0.0909 | 0.593 | 2016-05-18 -> 2026-09-11 |
| J+10 | `lgbm_factors` | `factors` | 0.04810 | 0.03521 | 0.0765 | 0.585 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_zero_return` | `none` | 0.05007 | 0.03580 | -0.0005 | 0.006 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_momentum_20d` | `none` | 0.05007 | 0.03580 | -0.0005 | 0.006 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_historical_mean` | `none` | 0.05011 | 0.03572 | -0.0023 | 0.536 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_seasonal_naive` | `none` | 0.05140 | 0.03663 | -0.0543 | 0.549 | 2016-05-18 -> 2026-09-11 |
| J+10 | `sarimax_seasonal` | `timeseries` | 0.07963 | 0.04407 | -1.5306 | 0.460 | 2016-05-18 -> 2026-09-11 |
| J+10 | `arima_auto` | `timeseries` | 0.08776 | 0.04706 | -2.0739 | 0.540 | 2016-05-18 -> 2026-09-11 |
| J+10 | `garch_vol` | `timeseries` | 0.10268 | 0.09118 | -3.2075 | 0.540 | 2016-05-18 -> 2026-09-11 |
| J+10 | `ridge_raw` | `raw` | 0.13423 | 0.09229 | -6.1911 | 0.535 | 2016-05-18 -> 2026-09-11 |
| J+20 | `lasso_factors` | `factors` | 0.06585 | 0.04863 | 0.1795 | 0.655 | 2016-05-10 -> 2026-08-27 |
| J+20 | `elasticnet_factors` | `factors` | 0.06591 | 0.04881 | 0.1779 | 0.655 | 2016-05-10 -> 2026-08-27 |
| J+20 | `bayesian_ridge_factors` | `factors` | 0.06600 | 0.04895 | 0.1756 | 0.654 | 2016-05-10 -> 2026-08-27 |
| J+20 | `ridge_factors` | `factors` | 0.06617 | 0.04914 | 0.1715 | 0.655 | 2016-05-10 -> 2026-08-27 |
| J+20 | `extratrees_factors` | `factors` | 0.06680 | 0.04920 | 0.1556 | 0.638 | 2016-05-10 -> 2026-08-27 |
| J+20 | `rf_factors` | `factors` | 0.06796 | 0.05100 | 0.1260 | 0.612 | 2016-05-10 -> 2026-08-27 |
| J+20 | `lgbm_factors` | `factors` | 0.06842 | 0.05107 | 0.1141 | 0.621 | 2016-05-10 -> 2026-08-27 |
| J+20 | `hgb_factors` | `factors` | 0.06854 | 0.05074 | 0.1110 | 0.619 | 2016-05-10 -> 2026-08-27 |
| J+20 | `xgb_factors` | `factors` | 0.06924 | 0.05096 | 0.0929 | 0.620 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_zero_return` | `none` | 0.07272 | 0.05369 | -0.0008 | 0.005 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_momentum_20d` | `none` | 0.07272 | 0.05369 | -0.0008 | 0.005 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_historical_mean` | `none` | 0.07287 | 0.05354 | -0.0047 | 0.545 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_seasonal_naive` | `none` | 0.07304 | 0.05444 | -0.0096 | 0.572 | 2016-05-10 -> 2026-08-27 |
| J+20 | `garch_vol` | `timeseries` | 0.12052 | 0.09962 | -1.7485 | 0.505 | 2016-05-10 -> 2026-08-27 |
| J+20 | `arima_auto` | `timeseries` | 0.19683 | 0.10652 | -6.3310 | 0.572 | 2016-05-10 -> 2026-08-27 |
| J+20 | `ridge_raw` | `raw` | 0.25153 | 0.15964 | -10.9721 | 0.530 | 2016-05-10 -> 2026-08-27 |
| J+20 | `sarimax_seasonal` | `timeseries` | 0.38727 | 0.21194 | -27.3789 | 0.510 | 2016-05-10 -> 2026-08-27 |
| J+30 | `lasso_factors` | `factors` | 0.07827 | 0.05906 | 0.2328 | 0.661 | 2016-05-02 -> 2026-08-13 |
| J+30 | `elasticnet_factors` | `factors` | 0.07841 | 0.05942 | 0.2301 | 0.652 | 2016-05-02 -> 2026-08-13 |
| J+30 | `bayesian_ridge_factors` | `factors` | 0.07852 | 0.05965 | 0.2279 | 0.648 | 2016-05-02 -> 2026-08-13 |
| J+30 | `ridge_factors` | `factors` | 0.07869 | 0.05991 | 0.2246 | 0.646 | 2016-05-02 -> 2026-08-13 |
| J+30 | `hgb_factors` | `factors` | 0.07963 | 0.06168 | 0.2058 | 0.655 | 2016-05-02 -> 2026-08-13 |
| J+30 | `extratrees_factors` | `factors` | 0.08028 | 0.06078 | 0.1928 | 0.654 | 2016-05-02 -> 2026-08-13 |
| J+30 | `lgbm_factors` | `factors` | 0.08178 | 0.06325 | 0.1625 | 0.628 | 2016-05-02 -> 2026-08-13 |
| J+30 | `rf_factors` | `factors` | 0.08226 | 0.06493 | 0.1526 | 0.617 | 2016-05-02 -> 2026-08-13 |
| J+30 | `xgb_factors` | `factors` | 0.08311 | 0.06332 | 0.1349 | 0.607 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_seasonal_naive` | `none` | 0.08781 | 0.06666 | 0.0343 | 0.614 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_zero_return` | `none` | 0.08940 | 0.06760 | -0.0010 | 0.004 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_momentum_20d` | `none` | 0.08940 | 0.06760 | -0.0010 | 0.004 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_historical_mean` | `none` | 0.08967 | 0.06739 | -0.0070 | 0.552 | 2016-05-02 -> 2026-08-13 |
| J+30 | `garch_vol` | `timeseries` | 0.14144 | 0.11773 | -1.5052 | 0.484 | 2016-05-02 -> 2026-08-13 |
| J+30 | `ridge_raw` | `raw` | 0.33388 | 0.21412 | -12.9610 | 0.509 | 2016-05-02 -> 2026-08-13 |
| J+30 | `arima_auto` | `timeseries` | 0.61448 | 0.28229 | -46.2878 | 0.568 | 2016-05-02 -> 2026-08-13 |
| J+30 | `sarimax_seasonal` | `timeseries` | 0.96877 | 0.53238 | -116.5356 | 0.494 | 2016-05-02 -> 2026-08-13 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `raw_signal` | 0.198 | 0.00183 |
| J+5 | `wasde_supply_demand` | 0.158 | 0.00068 |
| J+5 | `market_momentum` | 0.128 | 0.00042 |
| J+5 | `weather_belt_stress` | 0.122 | 0.00085 |
| J+5 | `positioning` | 0.117 | 0.00105 |
| J+5 | `cross_commodity` | 0.117 | 0.00075 |
| J+5 | `seasonality` | 0.093 | -0.00022 |
| J+5 | `macro_dollar_rates` | 0.029 | 0.00009 |
| J+5 | `market_volatility` | 0.023 | -0.00007 |
| J+5 | `weather_advanced` | 0.016 | 0.00008 |
| J+5 | `wasde_surprises_z` | 0.001 | -0.00000 |
| J+10 | `wasde_supply_demand` | 0.201 | 0.00186 |
| J+10 | `raw_signal` | 0.179 | 0.00418 |
| J+10 | `positioning` | 0.129 | 0.00167 |
| J+10 | `market_momentum` | 0.113 | 0.00069 |
| J+10 | `seasonality` | 0.110 | -0.00098 |
| J+10 | `weather_belt_stress` | 0.107 | 0.00181 |
| J+10 | `cross_commodity` | 0.096 | 0.00155 |
| J+10 | `macro_dollar_rates` | 0.030 | 0.00027 |
| J+10 | `market_volatility` | 0.019 | -0.00012 |
| J+10 | `wasde_surprises_z` | 0.008 | -0.00001 |
| J+10 | `weather_advanced` | 0.008 | 0.00010 |
| J+20 | `wasde_supply_demand` | 0.181 | 0.00265 |
| J+20 | `raw_signal` | 0.170 | 0.01036 |
| J+20 | `market_momentum` | 0.154 | 0.00115 |
| J+20 | `weather_belt_stress` | 0.128 | 0.00357 |
| J+20 | `positioning` | 0.113 | 0.00243 |
| J+20 | `cross_commodity` | 0.105 | 0.00461 |
| J+20 | `seasonality` | 0.070 | -0.00329 |
| J+20 | `market_volatility` | 0.047 | -0.00080 |
| J+20 | `macro_dollar_rates` | 0.018 | 0.00099 |
| J+20 | `weather_advanced` | 0.013 | 0.00005 |
| J+20 | `wasde_surprises_z` | 0.002 | -0.00001 |
| J+30 | `market_momentum` | 0.172 | 0.00105 |
| J+30 | `raw_signal` | 0.171 | 0.01434 |
| J+30 | `wasde_supply_demand` | 0.150 | 0.00180 |
| J+30 | `positioning` | 0.132 | 0.00776 |
| J+30 | `weather_belt_stress` | 0.118 | 0.00511 |
| J+30 | `cross_commodity` | 0.098 | 0.00607 |
| J+30 | `seasonality` | 0.079 | -0.00886 |
| J+30 | `market_volatility` | 0.045 | -0.00160 |
| J+30 | `weather_advanced` | 0.024 | 0.00124 |
| J+30 | `macro_dollar_rates` | 0.008 | 0.00067 |
| J+30 | `wasde_surprises_z` | 0.003 | 0.00001 |

## Top facteurs Ridge

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.198 |
| J+5 | `factor_cross_commodity` | `cross_commodity` | 0.117 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.098 |
| J+5 | `factor_seasonality` | `seasonality` | 0.093 |
| J+5 | `factor_positioning` | `positioning` | 0.080 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.079 |
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.055 |
| J+5 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.052 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.179 |
| J+10 | `factor_seasonality` | `seasonality` | 0.110 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.106 |
| J+10 | `factor_cross_commodity` | `cross_commodity` | 0.096 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.083 |
| J+10 | `factor_positioning` | `positioning` | 0.078 |
| J+10 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.063 |
| J+10 | `factor_market_breadth` | `positioning` | 0.052 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.170 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.123 |
| J+20 | `factor_cross_commodity` | `cross_commodity` | 0.105 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.093 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.081 |
| J+20 | `factor_positioning` | `positioning` | 0.075 |
| J+20 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.074 |
| J+20 | `factor_seasonality` | `seasonality` | 0.070 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.171 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.137 |
| J+30 | `factor_cross_commodity` | `cross_commodity` | 0.098 |
| J+30 | `factor_positioning` | `positioning` | 0.093 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.080 |
| J+30 | `factor_seasonality` | `seasonality` | 0.079 |
| J+30 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.077 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.068 |

## Top facteurs SHAP

| Horizon | Facteur | Famille | Part mean(|SHAP|) |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.180 |
| J+5 | `factor_positioning` | `positioning` | 0.152 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.114 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.083 |
| J+5 | `factor_market_breadth` | `positioning` | 0.064 |
| J+5 | `factor_seasonality` | `seasonality` | 0.062 |
| J+5 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.056 |
| J+5 | `factor_curve_structure` | `market_momentum` | 0.056 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.139 |
| J+10 | `factor_seasonality` | `seasonality` | 0.129 |
| J+10 | `factor_positioning` | `positioning` | 0.120 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.118 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.085 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.078 |
| J+10 | `factor_curve_structure` | `market_momentum` | 0.057 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.057 |
| J+20 | `factor_seasonality` | `seasonality` | 0.196 |
| J+20 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.147 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.103 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.092 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.068 |
| J+20 | `factor_positioning` | `positioning` | 0.061 |
| J+20 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.059 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.051 |
| J+30 | `factor_seasonality` | `seasonality` | 0.255 |
| J+30 | `factor_positioning` | `positioning` | 0.117 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.088 |
| J+30 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.085 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.071 |
| J+30 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.061 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.061 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.045 |

## Intervalles CQR

| Horizon | Couverture réalisée | Largeur moyenne | N test |
|---:|---:|---:|---:|
| J+5 | 0.904 / cible 0.900 | 0.10797 | 2593 |
| J+10 | 0.910 / cible 0.900 | 0.15055 | 2591 |
| J+20 | 0.904 / cible 0.900 | 0.22428 | 2587 |
| J+30 | 0.901 / cible 0.900 | 0.27232 | 2583 |

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
| Conformalized Quantile Regression (CQR) | ✅ Implémenté | Couverture empirique moyenne 0.905 (objectif projet ≥0.88). |
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

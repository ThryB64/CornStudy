# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-09-27 17:30:01 UTC`
- Période étudiée: `2000-10-25` -> `2026-09-25`
- Données: 6486 observations, 395 features brutes, 19 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2026-08-27): **SELL_THIRDS**, fraction de vente 33%, régime `bull`.
- Cash price estimé: 5.08 USD/bu ; q50 J+20: 5.24 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `extratrees_factors` | `factors` | 0.03465 | 0.02494 | 0.0642 | 0.569 | 2016-05-23 -> 2026-09-18 |
| J+5 | `elasticnet_factors` | `factors` | 0.03489 | 0.02497 | 0.0509 | 0.590 | 2016-05-23 -> 2026-09-18 |
| J+5 | `lasso_factors` | `factors` | 0.03490 | 0.02496 | 0.0503 | 0.584 | 2016-05-23 -> 2026-09-18 |
| J+5 | `bayesian_ridge_factors` | `factors` | 0.03500 | 0.02507 | 0.0450 | 0.592 | 2016-05-23 -> 2026-09-18 |
| J+5 | `ridge_factors` | `factors` | 0.03512 | 0.02520 | 0.0384 | 0.594 | 2016-05-23 -> 2026-09-18 |
| J+5 | `hgb_factors` | `factors` | 0.03535 | 0.02557 | 0.0261 | 0.546 | 2016-05-23 -> 2026-09-18 |
| J+5 | `rf_factors` | `factors` | 0.03541 | 0.02556 | 0.0224 | 0.559 | 2016-05-23 -> 2026-09-18 |
| J+5 | `xgb_factors` | `factors` | 0.03573 | 0.02590 | 0.0047 | 0.554 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_zero_return` | `none` | 0.03582 | 0.02558 | -0.0002 | 0.007 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_momentum_20d` | `none` | 0.03582 | 0.02558 | -0.0002 | 0.007 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_historical_mean` | `none` | 0.03584 | 0.02556 | -0.0012 | 0.523 | 2016-05-23 -> 2026-09-18 |
| J+5 | `lgbm_factors` | `factors` | 0.03588 | 0.02632 | -0.0037 | 0.543 | 2016-05-23 -> 2026-09-18 |
| J+5 | `sarimax_seasonal` | `timeseries` | 0.03617 | 0.02607 | -0.0198 | 0.505 | 2016-05-23 -> 2026-09-18 |
| J+5 | `baseline_seasonal_naive` | `none` | 0.03628 | 0.02599 | -0.0258 | 0.545 | 2016-05-23 -> 2026-09-18 |
| J+5 | `arima_auto` | `timeseries` | 0.03656 | 0.02596 | -0.0418 | 0.521 | 2016-05-23 -> 2026-09-18 |
| J+5 | `ridge_raw` | `raw` | 0.08815 | 0.06040 | -5.0565 | 0.520 | 2016-05-23 -> 2026-09-18 |
| J+5 | `garch_vol` | `timeseries` | 0.09851 | 0.08972 | -6.5647 | 0.503 | 2016-05-23 -> 2026-09-18 |
| J+10 | `extratrees_factors` | `factors` | 0.04672 | 0.03392 | 0.1289 | 0.625 | 2016-05-18 -> 2026-09-11 |
| J+10 | `lasso_factors` | `factors` | 0.04732 | 0.03416 | 0.1062 | 0.614 | 2016-05-18 -> 2026-09-11 |
| J+10 | `elasticnet_factors` | `factors` | 0.04742 | 0.03440 | 0.1025 | 0.611 | 2016-05-18 -> 2026-09-11 |
| J+10 | `bayesian_ridge_factors` | `factors` | 0.04755 | 0.03464 | 0.0978 | 0.613 | 2016-05-18 -> 2026-09-11 |
| J+10 | `ridge_factors` | `factors` | 0.04768 | 0.03487 | 0.0926 | 0.617 | 2016-05-18 -> 2026-09-11 |
| J+10 | `rf_factors` | `factors` | 0.04797 | 0.03442 | 0.0818 | 0.580 | 2016-05-18 -> 2026-09-11 |
| J+10 | `xgb_factors` | `factors` | 0.04837 | 0.03487 | 0.0662 | 0.601 | 2016-05-18 -> 2026-09-11 |
| J+10 | `hgb_factors` | `factors` | 0.04849 | 0.03518 | 0.0617 | 0.590 | 2016-05-18 -> 2026-09-11 |
| J+10 | `lgbm_factors` | `factors` | 0.04907 | 0.03600 | 0.0391 | 0.568 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_zero_return` | `none` | 0.05007 | 0.03580 | -0.0005 | 0.006 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_momentum_20d` | `none` | 0.05007 | 0.03580 | -0.0005 | 0.006 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_historical_mean` | `none` | 0.05011 | 0.03572 | -0.0023 | 0.536 | 2016-05-18 -> 2026-09-11 |
| J+10 | `baseline_seasonal_naive` | `none` | 0.05140 | 0.03663 | -0.0543 | 0.549 | 2016-05-18 -> 2026-09-11 |
| J+10 | `sarimax_seasonal` | `timeseries` | 0.07963 | 0.04407 | -1.5306 | 0.460 | 2016-05-18 -> 2026-09-11 |
| J+10 | `arima_auto` | `timeseries` | 0.08776 | 0.04706 | -2.0739 | 0.540 | 2016-05-18 -> 2026-09-11 |
| J+10 | `garch_vol` | `timeseries` | 0.10268 | 0.09118 | -3.2075 | 0.540 | 2016-05-18 -> 2026-09-11 |
| J+10 | `ridge_raw` | `raw` | 0.14331 | 0.09526 | -7.1971 | 0.503 | 2016-05-18 -> 2026-09-11 |
| J+20 | `lasso_factors` | `factors` | 0.06622 | 0.04895 | 0.1702 | 0.667 | 2016-05-10 -> 2026-08-27 |
| J+20 | `elasticnet_factors` | `factors` | 0.06648 | 0.04936 | 0.1636 | 0.666 | 2016-05-10 -> 2026-08-27 |
| J+20 | `bayesian_ridge_factors` | `factors` | 0.06672 | 0.04963 | 0.1576 | 0.661 | 2016-05-10 -> 2026-08-27 |
| J+20 | `ridge_factors` | `factors` | 0.06692 | 0.04989 | 0.1525 | 0.659 | 2016-05-10 -> 2026-08-27 |
| J+20 | `extratrees_factors` | `factors` | 0.06720 | 0.04987 | 0.1456 | 0.646 | 2016-05-10 -> 2026-08-27 |
| J+20 | `rf_factors` | `factors` | 0.06956 | 0.05206 | 0.0845 | 0.618 | 2016-05-10 -> 2026-08-27 |
| J+20 | `xgb_factors` | `factors` | 0.07018 | 0.05164 | 0.0680 | 0.606 | 2016-05-10 -> 2026-08-27 |
| J+20 | `hgb_factors` | `factors` | 0.07030 | 0.05235 | 0.0648 | 0.607 | 2016-05-10 -> 2026-08-27 |
| J+20 | `lgbm_factors` | `factors` | 0.07098 | 0.05308 | 0.0466 | 0.601 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_zero_return` | `none` | 0.07272 | 0.05369 | -0.0008 | 0.005 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_momentum_20d` | `none` | 0.07272 | 0.05369 | -0.0008 | 0.005 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_historical_mean` | `none` | 0.07287 | 0.05354 | -0.0047 | 0.545 | 2016-05-10 -> 2026-08-27 |
| J+20 | `baseline_seasonal_naive` | `none` | 0.07304 | 0.05444 | -0.0096 | 0.572 | 2016-05-10 -> 2026-08-27 |
| J+20 | `garch_vol` | `timeseries` | 0.12052 | 0.09962 | -1.7485 | 0.505 | 2016-05-10 -> 2026-08-27 |
| J+20 | `arima_auto` | `timeseries` | 0.19683 | 0.10652 | -6.3310 | 0.572 | 2016-05-10 -> 2026-08-27 |
| J+20 | `ridge_raw` | `raw` | 0.28273 | 0.17818 | -14.1259 | 0.520 | 2016-05-10 -> 2026-08-27 |
| J+20 | `sarimax_seasonal` | `timeseries` | 0.38727 | 0.21194 | -27.3789 | 0.510 | 2016-05-10 -> 2026-08-27 |
| J+30 | `lasso_factors` | `factors` | 0.07899 | 0.06002 | 0.2187 | 0.671 | 2016-05-02 -> 2026-08-13 |
| J+30 | `elasticnet_factors` | `factors` | 0.07947 | 0.06071 | 0.2091 | 0.672 | 2016-05-02 -> 2026-08-13 |
| J+30 | `bayesian_ridge_factors` | `factors` | 0.07976 | 0.06111 | 0.2033 | 0.669 | 2016-05-02 -> 2026-08-13 |
| J+30 | `ridge_factors` | `factors` | 0.07999 | 0.06141 | 0.1986 | 0.669 | 2016-05-02 -> 2026-08-13 |
| J+30 | `extratrees_factors` | `factors` | 0.08182 | 0.06234 | 0.1616 | 0.629 | 2016-05-02 -> 2026-08-13 |
| J+30 | `xgb_factors` | `factors` | 0.08334 | 0.06364 | 0.1302 | 0.618 | 2016-05-02 -> 2026-08-13 |
| J+30 | `hgb_factors` | `factors` | 0.08446 | 0.06572 | 0.1065 | 0.616 | 2016-05-02 -> 2026-08-13 |
| J+30 | `lgbm_factors` | `factors` | 0.08534 | 0.06587 | 0.0880 | 0.629 | 2016-05-02 -> 2026-08-13 |
| J+30 | `rf_factors` | `factors` | 0.08539 | 0.06695 | 0.0870 | 0.615 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_seasonal_naive` | `none` | 0.08781 | 0.06666 | 0.0343 | 0.614 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_zero_return` | `none` | 0.08940 | 0.06760 | -0.0010 | 0.004 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_momentum_20d` | `none` | 0.08940 | 0.06760 | -0.0010 | 0.004 | 2016-05-02 -> 2026-08-13 |
| J+30 | `baseline_historical_mean` | `none` | 0.08967 | 0.06739 | -0.0070 | 0.552 | 2016-05-02 -> 2026-08-13 |
| J+30 | `garch_vol` | `timeseries` | 0.14144 | 0.11773 | -1.5052 | 0.484 | 2016-05-02 -> 2026-08-13 |
| J+30 | `ridge_raw` | `raw` | 0.37939 | 0.23838 | -17.0261 | 0.510 | 2016-05-02 -> 2026-08-13 |
| J+30 | `arima_auto` | `timeseries` | 0.61448 | 0.28229 | -46.2878 | 0.568 | 2016-05-02 -> 2026-08-13 |
| J+30 | `sarimax_seasonal` | `timeseries` | 0.96877 | 0.53238 | -116.5356 | 0.494 | 2016-05-02 -> 2026-08-13 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `wasde_supply_demand` | 0.181 | 0.00028 |
| J+5 | `raw_signal` | 0.162 | 0.00120 |
| J+5 | `positioning` | 0.138 | 0.00110 |
| J+5 | `weather_belt_stress` | 0.136 | 0.00069 |
| J+5 | `market_momentum` | 0.122 | 0.00046 |
| J+5 | `seasonality` | 0.114 | 0.00008 |
| J+5 | `cross_commodity` | 0.065 | 0.00030 |
| J+5 | `market_volatility` | 0.036 | -0.00003 |
| J+5 | `macro_dollar_rates` | 0.030 | 0.00015 |
| J+5 | `weather_advanced` | 0.014 | 0.00006 |
| J+5 | `wasde_surprises_z` | 0.001 | -0.00000 |
| J+10 | `wasde_supply_demand` | 0.216 | 0.00056 |
| J+10 | `raw_signal` | 0.147 | 0.00316 |
| J+10 | `positioning` | 0.146 | 0.00189 |
| J+10 | `seasonality` | 0.130 | 0.00008 |
| J+10 | `weather_belt_stress` | 0.120 | 0.00165 |
| J+10 | `market_momentum` | 0.112 | 0.00123 |
| J+10 | `cross_commodity` | 0.050 | 0.00064 |
| J+10 | `market_volatility` | 0.033 | -0.00001 |
| J+10 | `macro_dollar_rates` | 0.033 | 0.00058 |
| J+10 | `wasde_surprises_z` | 0.008 | -0.00001 |
| J+10 | `weather_advanced` | 0.006 | 0.00006 |
| J+20 | `wasde_supply_demand` | 0.188 | 0.00054 |
| J+20 | `market_momentum` | 0.151 | 0.00342 |
| J+20 | `raw_signal` | 0.139 | 0.00818 |
| J+20 | `weather_belt_stress` | 0.138 | 0.00442 |
| J+20 | `positioning` | 0.126 | 0.00224 |
| J+20 | `seasonality` | 0.083 | -0.00189 |
| J+20 | `cross_commodity` | 0.063 | 0.00232 |
| J+20 | `market_volatility` | 0.058 | 0.00001 |
| J+20 | `macro_dollar_rates` | 0.034 | 0.00106 |
| J+20 | `weather_advanced` | 0.016 | 0.00014 |
| J+20 | `wasde_surprises_z` | 0.002 | -0.00000 |
| J+30 | `market_momentum` | 0.165 | 0.00401 |
| J+30 | `wasde_supply_demand` | 0.152 | 0.00120 |
| J+30 | `positioning` | 0.146 | 0.00712 |
| J+30 | `raw_signal` | 0.142 | 0.01344 |
| J+30 | `weather_belt_stress` | 0.126 | 0.00647 |
| J+30 | `seasonality` | 0.092 | -0.00725 |
| J+30 | `cross_commodity` | 0.057 | 0.00341 |
| J+30 | `market_volatility` | 0.054 | -0.00061 |
| J+30 | `macro_dollar_rates` | 0.037 | 0.00092 |
| J+30 | `weather_advanced` | 0.026 | 0.00149 |
| J+30 | `wasde_surprises_z` | 0.003 | 0.00002 |

## Top facteurs Ridge

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.162 |
| J+5 | `factor_seasonality` | `seasonality` | 0.114 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.099 |
| J+5 | `factor_positioning` | `positioning` | 0.097 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.097 |
| J+5 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.072 |
| J+5 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.068 |
| J+5 | `factor_cross_commodity` | `cross_commodity` | 0.065 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.147 |
| J+10 | `factor_seasonality` | `seasonality` | 0.130 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.106 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.101 |
| J+10 | `factor_positioning` | `positioning` | 0.092 |
| J+10 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.083 |
| J+10 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.071 |
| J+10 | `factor_market_breadth` | `positioning` | 0.055 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.143 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.139 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.103 |
| J+20 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.090 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.087 |
| J+20 | `factor_positioning` | `positioning` | 0.086 |
| J+20 | `factor_seasonality` | `seasonality` | 0.083 |
| J+20 | `factor_cross_commodity` | `cross_commodity` | 0.063 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.155 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.142 |
| J+30 | `factor_positioning` | `positioning` | 0.104 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.098 |
| J+30 | `factor_seasonality` | `seasonality` | 0.092 |
| J+30 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.090 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.062 |
| J+30 | `factor_cross_commodity` | `cross_commodity` | 0.057 |

## Top facteurs SHAP

| Horizon | Facteur | Famille | Part mean(|SHAP|) |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.231 |
| J+5 | `factor_positioning` | `positioning` | 0.142 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.106 |
| J+5 | `factor_curve_structure` | `market_momentum` | 0.067 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.066 |
| J+5 | `factor_market_breadth` | `positioning` | 0.062 |
| J+5 | `factor_seasonality` | `seasonality` | 0.056 |
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.050 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.224 |
| J+10 | `factor_seasonality` | `seasonality` | 0.147 |
| J+10 | `factor_positioning` | `positioning` | 0.119 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.106 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.059 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.054 |
| J+10 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.046 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.040 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.216 |
| J+20 | `factor_seasonality` | `seasonality` | 0.188 |
| J+20 | `factor_positioning` | `positioning` | 0.113 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.082 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.073 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.068 |
| J+20 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.045 |
| J+20 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.043 |
| J+30 | `factor_seasonality` | `seasonality` | 0.272 |
| J+30 | `factor_positioning` | `positioning` | 0.159 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.135 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.084 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.059 |
| J+30 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.058 |
| J+30 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.047 |
| J+30 | `factor_cross_commodity` | `cross_commodity` | 0.041 |

## Intervalles CQR

| Horizon | Couverture réalisée | Largeur moyenne | N test |
|---:|---:|---:|---:|
| J+5 | 0.902 / cible 0.900 | 0.10741 | 2593 |
| J+10 | 0.906 / cible 0.900 | 0.15057 | 2591 |
| J+20 | 0.909 / cible 0.900 | 0.22596 | 2587 |
| J+30 | 0.905 / cible 0.900 | 0.27370 | 2583 |

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
| `brazil_exports` | `enabled_not_in_features` | 0 | 50 |
| `brazil_fob_prices` | `planned` | 0 | 50 |
| `brent` | `enabled_not_in_features` | 0 | 50 |
| `cbot_corn` | `active_in_features` | 30 | 50 |
| `cbot_curve_archive` | `active_in_features` | 30 | 50 |
| `cbot_oats` | `active_in_features` | 30 | 50 |

## État réel d'implémentation

Ce tableau distingue ce qui est effectivement codé et exécuté de ce qui est prévu ou partiellement implémenté. Aucun élément n'est décrit comme implémenté s'il ne l'est pas.

| Fonctionnalité | Statut | Note |
|---|---|---|
| Collecte données (WASDE, FRED, NASS, OpenMeteo) | ✅ Implémenté | Collecteurs et tables locales validés |
| Anti-leakage (5 checks, |corr|>0.97) | ✅ Implémenté | Audit automatisé à chaque build |
| Cibles y_logret_h{5,10,20,30} | ✅ Implémenté | Expanding quantile, anti-leakage |
| Features brutes | ✅ Implémenté | 395 colonnes |
| Facteurs synthétiques | ✅ Implémenté | 19 facteurs, expanding z-scores |
| Walk-forward temporel | ✅ Implémenté | Train historique, tests par blocs, embargo par horizon |
| Benchmark modèles | ✅ Implémenté | Ridge, ElasticNet, RF, HGB ; boosters si installés |
| Stacking Ridge sur meta-database | ⚠️ Hors rapport walk-forward | Disponible via `mais stack` ; non inclus dans les benchmarks de cette étude. |
| Intervalles de confiance (split-conformal) | ✅ Implémenté | Moyenne covered_90 ≈ 0.893. |
| Régime de marché (bull/bear/range) | ⚠️ Partiel | Méthode : markov_2state ; labels observés : ['bear', 'bull']. |
| Décision agriculteur (SELL/STORE/WAIT) | ✅ Implémenté | Moteur YAML paramétrable |
| Importance par coefficient Ridge | ✅ Implémenté | Ablation par famille |
| Analyse SHAP | ✅ Implémenté | 76 lignes SHAP dans l'export. |
| Conformalized Quantile Regression (CQR) | ✅ Implémenté | Couverture empirique moyenne 0.906 (objectif projet ≥0.88). |
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

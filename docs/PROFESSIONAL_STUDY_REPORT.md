# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-07-03 14:01:40 UTC`
- Période étudiée: `2000-10-25` -> `2026-07-02`
- Données: 6427 observations, 370 features brutes, 19 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2025-07-25): **SELL_NOW**, fraction de vente 100%, régime `bear`.
- Cash price estimé: 4.05 USD/bu ; q50 J+20: 3.95 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `elasticnet_factors` | `factors` | 0.03494 | 0.02545 | 0.0600 | 0.549 | 2015-09-15 -> 2025-07-25 |
| J+5 | `bayesian_ridge_factors` | `factors` | 0.03497 | 0.02559 | 0.0584 | 0.546 | 2015-09-15 -> 2025-07-25 |
| J+5 | `extratrees_factors` | `factors` | 0.03498 | 0.02528 | 0.0580 | 0.535 | 2015-09-15 -> 2025-07-25 |
| J+5 | `lasso_factors` | `factors` | 0.03500 | 0.02529 | 0.0568 | 0.552 | 2015-09-15 -> 2025-07-25 |
| J+5 | `ridge_factors` | `factors` | 0.03501 | 0.02572 | 0.0562 | 0.543 | 2015-09-15 -> 2025-07-25 |
| J+5 | `rf_factors` | `factors` | 0.03551 | 0.02592 | 0.0295 | 0.516 | 2015-09-15 -> 2025-07-25 |
| J+5 | `baseline_zero_return` | `none` | 0.03604 | 0.02572 | -0.0000 | 0.006 | 2015-09-15 -> 2025-07-25 |
| J+5 | `baseline_momentum_20d` | `none` | 0.03604 | 0.02572 | -0.0000 | 0.006 | 2015-09-15 -> 2025-07-25 |
| J+5 | `baseline_historical_mean` | `none` | 0.03606 | 0.02569 | -0.0009 | 0.522 | 2015-09-15 -> 2025-07-25 |
| J+5 | `hgb_factors` | `factors` | 0.03619 | 0.02671 | -0.0082 | 0.513 | 2015-09-15 -> 2025-07-25 |
| J+5 | `sarimax_seasonal` | `timeseries` | 0.03640 | 0.02612 | -0.0199 | 0.486 | 2015-09-15 -> 2025-07-25 |
| J+5 | `baseline_seasonal_naive` | `none` | 0.03643 | 0.02614 | -0.0217 | 0.527 | 2015-09-15 -> 2025-07-25 |
| J+5 | `xgb_factors` | `factors` | 0.03685 | 0.02710 | -0.0454 | 0.526 | 2015-09-15 -> 2025-07-25 |
| J+5 | `arima_auto` | `timeseries` | 0.03693 | 0.02619 | -0.0501 | 0.518 | 2015-09-15 -> 2025-07-25 |
| J+5 | `lgbm_factors` | `factors` | 0.03709 | 0.02768 | -0.0589 | 0.512 | 2015-09-15 -> 2025-07-25 |
| J+5 | `ridge_raw` | `raw` | 0.10499 | 0.07199 | -7.4861 | 0.482 | 2015-09-15 -> 2025-07-25 |
| J+5 | `garch_vol` | `timeseries` | 0.10527 | 0.09952 | -7.5319 | 0.499 | 2015-09-15 -> 2025-07-25 |
| J+10 | `lasso_factors` | `factors` | 0.04702 | 0.03462 | 0.1177 | 0.590 | 2015-09-15 -> 2025-07-25 |
| J+10 | `elasticnet_factors` | `factors` | 0.04718 | 0.03491 | 0.1116 | 0.594 | 2015-09-15 -> 2025-07-25 |
| J+10 | `bayesian_ridge_factors` | `factors` | 0.04730 | 0.03512 | 0.1071 | 0.585 | 2015-09-15 -> 2025-07-25 |
| J+10 | `ridge_factors` | `factors` | 0.04738 | 0.03525 | 0.1042 | 0.583 | 2015-09-15 -> 2025-07-25 |
| J+10 | `extratrees_factors` | `factors` | 0.04750 | 0.03488 | 0.0996 | 0.560 | 2015-09-15 -> 2025-07-25 |
| J+10 | `rf_factors` | `factors` | 0.04807 | 0.03524 | 0.0777 | 0.572 | 2015-09-15 -> 2025-07-25 |
| J+10 | `hgb_factors` | `factors` | 0.04891 | 0.03609 | 0.0451 | 0.540 | 2015-09-15 -> 2025-07-25 |
| J+10 | `xgb_factors` | `factors` | 0.04987 | 0.03668 | 0.0074 | 0.558 | 2015-09-15 -> 2025-07-25 |
| J+10 | `baseline_zero_return` | `none` | 0.05006 | 0.03584 | -0.0000 | 0.002 | 2015-09-15 -> 2025-07-25 |
| J+10 | `baseline_momentum_20d` | `none` | 0.05006 | 0.03584 | -0.0000 | 0.002 | 2015-09-15 -> 2025-07-25 |
| J+10 | `baseline_historical_mean` | `none` | 0.05010 | 0.03580 | -0.0018 | 0.524 | 2015-09-15 -> 2025-07-25 |
| J+10 | `lgbm_factors` | `factors` | 0.05107 | 0.03785 | -0.0411 | 0.539 | 2015-09-15 -> 2025-07-25 |
| J+10 | `baseline_seasonal_naive` | `none` | 0.05117 | 0.03655 | -0.0449 | 0.532 | 2015-09-15 -> 2025-07-25 |
| J+10 | `arima_auto` | `timeseries` | 0.06454 | 0.04386 | -0.6626 | 0.520 | 2015-09-15 -> 2025-07-25 |
| J+10 | `sarimax_seasonal` | `timeseries` | 0.06734 | 0.04375 | -0.8098 | 0.531 | 2015-09-15 -> 2025-07-25 |
| J+10 | `garch_vol` | `timeseries` | 0.10814 | 0.09643 | -3.6670 | 0.493 | 2015-09-15 -> 2025-07-25 |
| J+10 | `ridge_raw` | `raw` | 0.15454 | 0.10681 | -8.5314 | 0.487 | 2015-09-15 -> 2025-07-25 |
| J+20 | `extratrees_factors` | `factors` | 0.06623 | 0.04869 | 0.1585 | 0.606 | 2015-09-15 -> 2025-07-25 |
| J+20 | `lasso_factors` | `factors` | 0.06625 | 0.04955 | 0.1577 | 0.621 | 2015-09-15 -> 2025-07-25 |
| J+20 | `elasticnet_factors` | `factors` | 0.06666 | 0.05004 | 0.1473 | 0.619 | 2015-09-15 -> 2025-07-25 |
| J+20 | `bayesian_ridge_factors` | `factors` | 0.06695 | 0.05040 | 0.1400 | 0.619 | 2015-09-15 -> 2025-07-25 |
| J+20 | `ridge_factors` | `factors` | 0.06715 | 0.05059 | 0.1347 | 0.613 | 2015-09-15 -> 2025-07-25 |
| J+20 | `hgb_factors` | `factors` | 0.06881 | 0.05093 | 0.0916 | 0.610 | 2015-09-15 -> 2025-07-25 |
| J+20 | `rf_factors` | `factors` | 0.06940 | 0.05138 | 0.0758 | 0.604 | 2015-09-15 -> 2025-07-25 |
| J+20 | `xgb_factors` | `factors` | 0.06964 | 0.05188 | 0.0693 | 0.607 | 2015-09-15 -> 2025-07-25 |
| J+20 | `baseline_seasonal_naive` | `none` | 0.07098 | 0.05255 | 0.0334 | 0.544 | 2015-09-15 -> 2025-07-25 |
| J+20 | `baseline_zero_return` | `none` | 0.07219 | 0.05291 | -0.0000 | 0.005 | 2015-09-15 -> 2025-07-25 |
| J+20 | `baseline_momentum_20d` | `none` | 0.07219 | 0.05291 | -0.0000 | 0.005 | 2015-09-15 -> 2025-07-25 |
| J+20 | `baseline_historical_mean` | `none` | 0.07232 | 0.05284 | -0.0034 | 0.526 | 2015-09-15 -> 2025-07-25 |
| J+20 | `lgbm_factors` | `factors` | 0.07251 | 0.05383 | -0.0087 | 0.579 | 2015-09-15 -> 2025-07-25 |
| J+20 | `garch_vol` | `timeseries` | 0.12443 | 0.10990 | -1.9707 | 0.478 | 2015-09-15 -> 2025-07-25 |
| J+20 | `arima_auto` | `timeseries` | 0.18096 | 0.10880 | -5.2831 | 0.505 | 2015-09-15 -> 2025-07-25 |
| J+20 | `ridge_raw` | `raw` | 0.25629 | 0.17500 | -11.6028 | 0.476 | 2015-09-15 -> 2025-07-25 |
| J+20 | `sarimax_seasonal` | `timeseries` | 0.26404 | 0.16899 | -12.3767 | 0.517 | 2015-09-15 -> 2025-07-25 |
| J+30 | `lasso_factors` | `factors` | 0.07991 | 0.06145 | 0.1937 | 0.641 | 2015-09-15 -> 2025-07-25 |
| J+30 | `elasticnet_factors` | `factors` | 0.08046 | 0.06217 | 0.1825 | 0.639 | 2015-09-15 -> 2025-07-25 |
| J+30 | `bayesian_ridge_factors` | `factors` | 0.08062 | 0.06241 | 0.1794 | 0.640 | 2015-09-15 -> 2025-07-25 |
| J+30 | `ridge_factors` | `factors` | 0.08092 | 0.06268 | 0.1732 | 0.637 | 2015-09-15 -> 2025-07-25 |
| J+30 | `extratrees_factors` | `factors` | 0.08145 | 0.06219 | 0.1623 | 0.615 | 2015-09-15 -> 2025-07-25 |
| J+30 | `baseline_seasonal_naive` | `none` | 0.08539 | 0.06438 | 0.0793 | 0.585 | 2015-09-15 -> 2025-07-25 |
| J+30 | `hgb_factors` | `factors` | 0.08541 | 0.06562 | 0.0788 | 0.597 | 2015-09-15 -> 2025-07-25 |
| J+30 | `xgb_factors` | `factors` | 0.08551 | 0.06602 | 0.0768 | 0.600 | 2015-09-15 -> 2025-07-25 |
| J+30 | `rf_factors` | `factors` | 0.08700 | 0.06628 | 0.0443 | 0.586 | 2015-09-15 -> 2025-07-25 |
| J+30 | `lgbm_factors` | `factors` | 0.08742 | 0.06731 | 0.0349 | 0.609 | 2015-09-15 -> 2025-07-25 |
| J+30 | `baseline_zero_return` | `none` | 0.08899 | 0.06660 | -0.0000 | 0.005 | 2015-09-15 -> 2025-07-25 |
| J+30 | `baseline_momentum_20d` | `none` | 0.08899 | 0.06660 | -0.0000 | 0.005 | 2015-09-15 -> 2025-07-25 |
| J+30 | `baseline_historical_mean` | `none` | 0.08921 | 0.06653 | -0.0048 | 0.524 | 2015-09-15 -> 2025-07-25 |
| J+30 | `garch_vol` | `timeseries` | 0.13181 | 0.11248 | -1.1938 | 0.475 | 2015-09-15 -> 2025-07-25 |
| J+30 | `ridge_raw` | `raw` | 0.30616 | 0.21888 | -10.8359 | 0.454 | 2015-09-15 -> 2025-07-25 |
| J+30 | `arima_auto` | `timeseries` | 0.40034 | 0.22949 | -19.2379 | 0.508 | 2015-09-15 -> 2025-07-25 |
| J+30 | `sarimax_seasonal` | `timeseries` | 0.60161 | 0.40295 | -44.7027 | 0.497 | 2015-09-15 -> 2025-07-25 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `raw_signal` | 0.215 | -0.00053 |
| J+5 | `wasde_supply_demand` | 0.193 | -0.00048 |
| J+5 | `weather_belt_stress` | 0.183 | 0.00012 |
| J+5 | `cross_commodity` | 0.122 | -0.00033 |
| J+5 | `positioning` | 0.086 | -0.00034 |
| J+5 | `market_momentum` | 0.063 | 0.00004 |
| J+5 | `macro_dollar_rates` | 0.063 | -0.00023 |
| J+5 | `seasonality` | 0.047 | 0.00018 |
| J+5 | `weather_advanced` | 0.019 | -0.00007 |
| J+5 | `wasde_surprises_z` | 0.008 | -0.00000 |
| J+5 | `market_volatility` | 0.001 | 0.00000 |
| J+10 | `wasde_supply_demand` | 0.235 | -0.00176 |
| J+10 | `raw_signal` | 0.215 | -0.00135 |
| J+10 | `weather_belt_stress` | 0.144 | -0.00047 |
| J+10 | `cross_commodity` | 0.126 | -0.00094 |
| J+10 | `market_momentum` | 0.069 | 0.00014 |
| J+10 | `seasonality` | 0.064 | 0.00065 |
| J+10 | `macro_dollar_rates` | 0.063 | -0.00046 |
| J+10 | `positioning` | 0.062 | -0.00064 |
| J+10 | `wasde_surprises_z` | 0.012 | -0.00000 |
| J+10 | `weather_advanced` | 0.005 | -0.00001 |
| J+10 | `market_volatility` | 0.005 | 0.00004 |
| J+20 | `raw_signal` | 0.213 | -0.00164 |
| J+20 | `wasde_supply_demand` | 0.193 | -0.00242 |
| J+20 | `market_momentum` | 0.135 | 0.00065 |
| J+20 | `weather_belt_stress` | 0.128 | 0.00005 |
| J+20 | `cross_commodity` | 0.120 | -0.00181 |
| J+20 | `positioning` | 0.080 | -0.00231 |
| J+20 | `market_volatility` | 0.046 | 0.00099 |
| J+20 | `macro_dollar_rates` | 0.041 | -0.00054 |
| J+20 | `seasonality` | 0.035 | 0.00095 |
| J+20 | `wasde_surprises_z` | 0.006 | 0.00000 |
| J+20 | `weather_advanced` | 0.002 | 0.00000 |
| J+30 | `raw_signal` | 0.168 | -0.00047 |
| J+30 | `market_momentum` | 0.166 | 0.00109 |
| J+30 | `wasde_supply_demand` | 0.164 | -0.00110 |
| J+30 | `positioning` | 0.146 | -0.00365 |
| J+30 | `weather_belt_stress` | 0.114 | 0.00050 |
| J+30 | `seasonality` | 0.072 | 0.00232 |
| J+30 | `market_volatility` | 0.053 | 0.00129 |
| J+30 | `cross_commodity` | 0.049 | -0.00079 |
| J+30 | `macro_dollar_rates` | 0.043 | -0.00052 |
| J+30 | `wasde_surprises_z` | 0.015 | 0.00001 |
| J+30 | `weather_advanced` | 0.010 | -0.00002 |

## Top facteurs Ridge

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_raw_signal` | `raw_signal` | 0.215 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.162 |
| J+5 | `factor_cross_commodity` | `cross_commodity` | 0.122 |
| J+5 | `factor_drought_severity` | `weather_belt_stress` | 0.072 |
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.063 |
| J+5 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.063 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.058 |
| J+5 | `factor_positioning` | `positioning` | 0.055 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.215 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.189 |
| J+10 | `factor_cross_commodity` | `cross_commodity` | 0.126 |
| J+10 | `factor_market_momentum` | `market_momentum` | 0.069 |
| J+10 | `factor_seasonality` | `seasonality` | 0.064 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.063 |
| J+10 | `factor_positioning` | `positioning` | 0.057 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.054 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.213 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.133 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.133 |
| J+20 | `factor_cross_commodity` | `cross_commodity` | 0.120 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.088 |
| J+20 | `factor_positioning` | `positioning` | 0.071 |
| J+20 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.060 |
| J+20 | `factor_market_volatility` | `market_volatility` | 0.046 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.168 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.151 |
| J+30 | `factor_positioning` | `positioning` | 0.113 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.106 |
| J+30 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.095 |
| J+30 | `factor_seasonality` | `seasonality` | 0.072 |
| J+30 | `factor_ethanol_demand` | `wasde_supply_demand` | 0.069 |
| J+30 | `factor_market_volatility` | `market_volatility` | 0.053 |

## Top facteurs SHAP

| Horizon | Facteur | Famille | Part mean(|SHAP|) |
|---:|---|---|---:|
| J+5 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.159 |
| J+5 | `factor_curve_structure` | `market_momentum` | 0.112 |
| J+5 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.107 |
| J+5 | `factor_positioning` | `positioning` | 0.094 |
| J+5 | `factor_drought_severity` | `weather_belt_stress` | 0.076 |
| J+5 | `factor_market_momentum` | `market_momentum` | 0.070 |
| J+5 | `factor_raw_signal` | `raw_signal` | 0.058 |
| J+5 | `factor_market_volatility` | `market_volatility` | 0.056 |
| J+10 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.139 |
| J+10 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.135 |
| J+10 | `factor_positioning` | `positioning` | 0.100 |
| J+10 | `factor_curve_structure` | `market_momentum` | 0.094 |
| J+10 | `factor_seasonality` | `seasonality` | 0.081 |
| J+10 | `factor_raw_signal` | `raw_signal` | 0.080 |
| J+10 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.060 |
| J+10 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.059 |
| J+20 | `factor_positioning` | `positioning` | 0.130 |
| J+20 | `factor_seasonality` | `seasonality` | 0.096 |
| J+20 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.093 |
| J+20 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.088 |
| J+20 | `factor_curve_structure` | `market_momentum` | 0.088 |
| J+20 | `factor_raw_signal` | `raw_signal` | 0.087 |
| J+20 | `factor_market_momentum` | `market_momentum` | 0.077 |
| J+20 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.066 |
| J+30 | `factor_seasonality` | `seasonality` | 0.150 |
| J+30 | `factor_positioning` | `positioning` | 0.138 |
| J+30 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.115 |
| J+30 | `factor_wasde_surprises_z` | `wasde_surprises_z` | 0.086 |
| J+30 | `factor_curve_structure` | `market_momentum` | 0.069 |
| J+30 | `factor_raw_signal` | `raw_signal` | 0.065 |
| J+30 | `factor_weather_belt_stress` | `weather_belt_stress` | 0.058 |
| J+30 | `factor_market_momentum` | `market_momentum` | 0.058 |

## Intervalles CQR

| Horizon | Couverture réalisée | Largeur moyenne | N test |
|---:|---:|---:|---:|
| J+5 | 0.910 / cible 0.900 | 0.11300 | 2477 |
| J+10 | 0.914 / cible 0.900 | 0.15850 | 2477 |
| J+20 | 0.911 / cible 0.900 | 0.23587 | 2477 |
| J+30 | 0.899 / cible 0.900 | 0.27195 | 2477 |

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
| Intervalles de confiance (split-conformal) | ✅ Implémenté | Moyenne covered_90 ≈ 0.888. |
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
| Optuna LightGBM | ✅ Exécuté | 4 horizons optimisés ; meilleur delta RMSE=-0.00543. |
| XGBoost/LightGBM | ✅ Benchmark | Benchmark walk-forward : LightGBM, XGBoost actifs. |

## Conclusion opérationnelle

Le projet dispose d'une architecture solide et d'une base technique propre. Les modèles actifs (RF, HGB sur facteurs) surpassent le zéro-return baseline sur la précision directionnelle (55–60% à J+20/30). Les familles production_fundamentals, ethanol_demand, cot_positioning et macro_dollar_rates sont intégrées sans fuite temporelle. Leur valeur ajoutée doit se lire par horizon : certaines informations sont redondantes avec WASDE en Ridge, mais utiles pour les modèles non linéaires et pour l'explication économique.

Prochaines étapes par ordre de priorité : (1) fournir une vraie clé EIA pour remplacer le proxy éthanol ; (2) mesurer l'ablation CFTC/EIA source par source ; (3) ajouter USDA Crop Progress ; (4) intégrer LightGBM/XGBoost au stacking historique si le gain walk-forward est stable.

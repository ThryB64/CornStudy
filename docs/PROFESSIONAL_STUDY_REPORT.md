# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-05-08 16:44:34 UTC`
- Période étudiée: `2000-10-25` -> `2025-07-25`
- Données: 6192 observations, 248 features brutes, 32 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2025-06-26): **SELL_THIRDS**, fraction de vente 33%, régime `range`.
- Cash price estimé: 3.99 USD/bu ; q50 J+20: 4.05 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `elasticnet_factors` | `factors` | 0.03562 | 0.02574 | 0.0228 | 0.521 | 2015-09-10 -> 2025-07-18 |
| J+5 | `rf_factors` | `factors` | 0.03567 | 0.02570 | 0.0199 | 0.542 | 2015-09-10 -> 2025-07-18 |
| J+5 | `hgb_factors` | `factors` | 0.03584 | 0.02605 | 0.0107 | 0.536 | 2015-09-10 -> 2025-07-18 |
| J+5 | `ridge_factors` | `factors` | 0.03594 | 0.02608 | 0.0052 | 0.516 | 2015-09-10 -> 2025-07-18 |
| J+5 | `baseline_zero_return` | `none` | 0.03603 | 0.02570 | -0.0000 | 0.006 | 2015-09-10 -> 2025-07-18 |
| J+5 | `ridge_raw` | `raw` | 0.08498 | 0.05592 | -4.5628 | 0.483 | 2015-09-10 -> 2025-07-18 |
| J+10 | `rf_factors` | `factors` | 0.04910 | 0.03569 | 0.0396 | 0.526 | 2015-09-04 -> 2025-07-11 |
| J+10 | `elasticnet_factors` | `factors` | 0.04922 | 0.03619 | 0.0348 | 0.532 | 2015-09-04 -> 2025-07-11 |
| J+10 | `hgb_factors` | `factors` | 0.04952 | 0.03604 | 0.0230 | 0.531 | 2015-09-04 -> 2025-07-11 |
| J+10 | `ridge_factors` | `factors` | 0.04984 | 0.03670 | 0.0105 | 0.533 | 2015-09-04 -> 2025-07-11 |
| J+10 | `baseline_zero_return` | `none` | 0.05010 | 0.03586 | -0.0001 | 0.002 | 2015-09-04 -> 2025-07-11 |
| J+10 | `ridge_raw` | `raw` | 0.12553 | 0.08291 | -5.2780 | 0.508 | 2015-09-04 -> 2025-07-11 |
| J+20 | `hgb_factors` | `factors` | 0.06909 | 0.05211 | 0.0862 | 0.579 | 2015-08-27 -> 2025-06-26 |
| J+20 | `rf_factors` | `factors` | 0.06978 | 0.05130 | 0.0679 | 0.563 | 2015-08-27 -> 2025-06-26 |
| J+20 | `elasticnet_factors` | `factors` | 0.07215 | 0.05445 | 0.0035 | 0.545 | 2015-08-27 -> 2025-06-26 |
| J+20 | `baseline_zero_return` | `none` | 0.07228 | 0.05291 | -0.0001 | 0.005 | 2015-08-27 -> 2025-06-26 |
| J+20 | `ridge_factors` | `factors` | 0.07371 | 0.05589 | -0.0403 | 0.535 | 2015-08-27 -> 2025-06-26 |
| J+20 | `ridge_raw` | `raw` | 0.21154 | 0.13833 | -7.5664 | 0.527 | 2015-08-27 -> 2025-06-26 |
| J+30 | `hgb_factors` | `factors` | 0.08552 | 0.06464 | 0.0744 | 0.598 | 2015-08-19 -> 2025-06-11 |
| J+30 | `rf_factors` | `factors` | 0.08689 | 0.06489 | 0.0446 | 0.573 | 2015-08-19 -> 2025-06-11 |
| J+30 | `baseline_zero_return` | `none` | 0.08890 | 0.06647 | -0.0002 | 0.005 | 2015-08-19 -> 2025-06-11 |
| J+30 | `elasticnet_factors` | `factors` | 0.09066 | 0.07072 | -0.0402 | 0.531 | 2015-08-19 -> 2025-06-11 |
| J+30 | `ridge_factors` | `factors` | 0.09268 | 0.07262 | -0.0871 | 0.518 | 2015-08-19 -> 2025-06-11 |
| J+30 | `ridge_raw` | `raw` | 0.27266 | 0.18565 | -8.4086 | 0.507 | 2015-08-19 -> 2025-06-11 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `weather_belt_stress` | 0.259 | -0.00028 |
| J+5 | `wasde_supply_demand` | 0.196 | -0.00026 |
| J+5 | `cross_commodity` | 0.152 | -0.00019 |
| J+5 | `seasonality` | 0.134 | 0.00048 |
| J+5 | `market_momentum` | 0.111 | -0.00034 |
| J+5 | `production_fundamentals` | 0.070 | -0.00017 |
| J+5 | `market_volatility` | 0.045 | -0.00028 |
| J+5 | `macro_dollar_rates` | 0.033 | -0.00009 |
| J+10 | `weather_belt_stress` | 0.242 | -0.00041 |
| J+10 | `wasde_supply_demand` | 0.186 | -0.00136 |
| J+10 | `market_momentum` | 0.157 | -0.00167 |
| J+10 | `seasonality` | 0.151 | 0.00043 |
| J+10 | `cross_commodity` | 0.139 | -0.00043 |
| J+10 | `production_fundamentals` | 0.050 | -0.00118 |
| J+10 | `market_volatility` | 0.039 | -0.00009 |
| J+10 | `macro_dollar_rates` | 0.036 | -0.00032 |
| J+20 | `market_momentum` | 0.199 | -0.00460 |
| J+20 | `wasde_supply_demand` | 0.188 | -0.00288 |
| J+20 | `seasonality` | 0.175 | -0.00046 |
| J+20 | `weather_belt_stress` | 0.151 | -0.00019 |
| J+20 | `cross_commodity` | 0.146 | -0.00028 |
| J+20 | `production_fundamentals` | 0.077 | -0.00391 |
| J+20 | `macro_dollar_rates` | 0.044 | -0.00094 |
| J+20 | `market_volatility` | 0.020 | 0.00042 |
| J+30 | `wasde_supply_demand` | 0.183 | -0.00496 |
| J+30 | `seasonality` | 0.173 | -0.00037 |
| J+30 | `cross_commodity` | 0.171 | -0.00102 |
| J+30 | `weather_belt_stress` | 0.163 | 0.00066 |
| J+30 | `market_momentum` | 0.162 | -0.00752 |
| J+30 | `production_fundamentals` | 0.090 | -0.00680 |
| J+30 | `macro_dollar_rates` | 0.047 | -0.00132 |
| J+30 | `market_volatility` | 0.012 | 0.00041 |

## Top facteurs

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_weather_heat_stress` | `weather_belt_stress` | 0.121 |
| J+5 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.118 |
| J+5 | `factor_season_pollination_window` | `seasonality` | 0.064 |
| J+5 | `factor_market_drawdown_recovery` | `market_momentum` | 0.062 |
| J+5 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.059 |
| J+5 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.055 |
| J+5 | `factor_season_annual_cycle` | `seasonality` | 0.051 |
| J+5 | `factor_wasde_supply_risk` | `wasde_supply_demand` | 0.040 |
| J+10 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.117 |
| J+10 | `factor_weather_heat_stress` | `weather_belt_stress` | 0.097 |
| J+10 | `factor_market_drawdown_recovery` | `market_momentum` | 0.088 |
| J+10 | `factor_season_pollination_window` | `seasonality` | 0.070 |
| J+10 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.067 |
| J+10 | `factor_season_annual_cycle` | `seasonality` | 0.057 |
| J+10 | `factor_wasde_supply_risk` | `wasde_supply_demand` | 0.048 |
| J+10 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.045 |
| J+20 | `factor_market_drawdown_recovery` | `market_momentum` | 0.112 |
| J+20 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.087 |
| J+20 | `factor_season_annual_cycle` | `seasonality` | 0.078 |
| J+20 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.077 |
| J+20 | `factor_wasde_supply_risk` | `wasde_supply_demand` | 0.068 |
| J+20 | `factor_market_medium_trend` | `market_momentum` | 0.051 |
| J+20 | `factor_weather_heat_stress` | `weather_belt_stress` | 0.045 |
| J+20 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.044 |
| J+30 | `factor_market_drawdown_recovery` | `market_momentum` | 0.101 |
| J+30 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.097 |
| J+30 | `factor_season_annual_cycle` | `seasonality` | 0.088 |
| J+30 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.076 |
| J+30 | `factor_wasde_supply_risk` | `wasde_supply_demand` | 0.074 |
| J+30 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.060 |
| J+30 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.057 |
| J+30 | `factor_weather_heat_stress` | `weather_belt_stress` | 0.048 |

## Couverture sources

| Source | Statut | Features | Priorité |
|---|---|---:|---:|
| `eia_ethanol` | `planned` | 0 | 1 |
| `cftc_cot_corn` | `planned` | 0 | 2 |
| `usda_nass_crop_progress` | `active_in_features` | 50 | 3 |
| `usda_nass_crop_condition` | `active_in_features` | 50 | 4 |
| `usda_fas_export_sales` | `planned` | 0 | 5 |
| `us_drought_monitor` | `planned` | 0 | 6 |
| `usda_wasde` | `active_in_features` | 132 | 7 |
| `openmeteo_states` | `active_in_features` | 16 | 8 |
| `bcr_argentina` | `planned` | 0 | 50 |
| `brent` | `enabled_not_in_features` | 0 | 50 |
| `cbot_corn` | `active_in_features` | 30 | 50 |
| `cbot_oats` | `active_in_features` | 30 | 50 |
| `cbot_soy` | `active_in_features` | 2 | 50 |
| `cbot_wheat` | `active_in_features` | 2 | 50 |
| `conab_brazil` | `planned` | 0 | 50 |
| `fred_macro` | `active_in_features` | 10 | 50 |
| `ice_dxy` | `active_in_features` | 2 | 50 |
| `noaa_oni` | `planned` | 0 | 50 |

## État réel d'implémentation

Ce tableau distingue ce qui est effectivement codé et exécuté de ce qui est prévu ou partiellement implémenté. Aucun élément n'est décrit comme implémenté s'il ne l'est pas.

| Fonctionnalité | Statut | Note |
|---|---|---|
| Collecte données (WASDE, FRED, NASS, OpenMeteo) | ✅ Implémenté | 11 collecteurs actifs |
| Anti-leakage (5 checks, |corr|>0.97) | ✅ Implémenté | Audit automatisé à chaque build |
| Cibles y_logret_h{5,10,20,30} | ✅ Implémenté | Expanding quantile, anti-leakage |
| Features brutes (marché, météo belt, WASDE, FRED, NASS) | ✅ Implémenté | 248 colonnes |
| Facteurs synthétiques (8 familles) | ✅ Implémenté | 32 facteurs, expanding z-scores |
| Walk-forward avec embargo 30j | ✅ Implémenté | 8 ans train initial, step 21j |
| Benchmark modèles (Ridge/RF/ElasticNet/HGB) | ✅ Implémenté | 4 horizons, walk-forward |
| Stacking Ridge sur meta-database | ✅ Implémenté | 6 modèles de base |
| Intervalles de confiance (split-conformal) | ✅ Implémenté | Rolling window 252j, couverture ~90% |
| Régime de marché (bull/bear/range) | ✅ Implémenté | Règles déterministes sur return_60d + vol |
| Décision agriculteur (SELL/STORE/WAIT) | ✅ Implémenté | Moteur YAML paramétrable |
| Importance par coefficient Ridge | ✅ Implémenté | Ablation par famille |
| Analyse SHAP | ❌ Non implémenté | Prévu — actuellement : coef Ridge uniquement |
| Conformalized Quantile Regression (CQR) | ❌ Non implémenté | Prévu — actuellement : split-conformal symétrique |
| Régime Markov-switching | ❌ Non implémenté | Prévu — actuellement : seuils rule-based |
| EIA éthanol dans features | ❌ Non intégré | Collecteur présent, non câblé |
| CFTC COT dans features | ❌ Non intégré | Collecteur stub présent, non câblé |
| NDVI / indices de végétation satellite | ❌ Non implémenté | Hors périmètre actuel |
| ENSO / El Niño | ❌ Non implémenté | Hors périmètre actuel |
| XGBoost/LightGBM dans meta-database | ⚠️ Partiel | Dans benchmarks mais pas dans la meta-database |

## Conclusion opérationnelle

Le projet dispose d'une architecture solide et d'une base technique propre. Les modèles actifs (RF, HGB sur facteurs) surpassent le zéro-return baseline sur la précision directionnelle (55–60% à J+20/30). Les nouvelles familles production_fundamentals et macro_dollar_rates sont intégrées mais montrent une redondance partielle avec WASDE (colinéarité Ridge). L'effet net est neutre sur Ridge, légèrement positif sur HGB à J+30 (+0.4pp DA).

Prochaines étapes par ordre de priorité : (1) intégrer EIA éthanol et CFTC COT dans features ; (2) ajouter XGBoost/LightGBM à la meta-database ; (3) implémenter SHAP réel ; (4) implémenter CQR ; (5) régime Markov-switching.

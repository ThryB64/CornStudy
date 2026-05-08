# Étude professionnelle du prix du maïs CBOT

- Générée le: `2026-05-08 18:13:51 UTC`
- Période étudiée: `2000-10-25` -> `2025-07-25`
- Données: 6192 observations, 305 features brutes, 36 facteurs.

## Synthèse

L'application condense les déterminants du maïs CBOT en facteurs économiques, compare plusieurs familles de modèles en walk-forward avec embargo, estime un régime de marché exploitable et transforme les prévisions en décision agricole.
- Dernière décision (2025-06-26): **SELL_NOW**, fraction de vente 70%, régime `bull`.
- Cash price estimé: 3.99 USD/bu ; q50 J+20: 4.00 USD/bu.

## Benchmark modèles

| Horizon | Modèle | Input | RMSE | MAE | R2 | DA | Période test |
|---:|---|---|---:|---:|---:|---:|---|
| J+5 | `baseline_zero_return` | `none` | 0.03603 | 0.02570 | -0.0000 | 0.006 | 2015-09-10 -> 2025-07-18 |
| J+5 | `elasticnet_factors` | `factors` | 0.03605 | 0.02611 | -0.0013 | 0.497 | 2015-09-10 -> 2025-07-18 |
| J+5 | `rf_factors` | `factors` | 0.03669 | 0.02656 | -0.0373 | 0.512 | 2015-09-10 -> 2025-07-18 |
| J+5 | `ridge_factors` | `factors` | 0.03679 | 0.02690 | -0.0429 | 0.488 | 2015-09-10 -> 2025-07-18 |
| J+5 | `hgb_factors` | `factors` | 0.03702 | 0.02674 | -0.0558 | 0.520 | 2015-09-10 -> 2025-07-18 |
| J+5 | `xgb_factors` | `factors` | 0.03751 | 0.02755 | -0.0836 | 0.511 | 2015-09-10 -> 2025-07-18 |
| J+5 | `lgbm_factors` | `factors` | 0.03754 | 0.02743 | -0.0856 | 0.509 | 2015-09-10 -> 2025-07-18 |
| J+5 | `ridge_raw` | `raw` | 0.10379 | 0.07445 | -7.2980 | 0.484 | 2015-09-10 -> 2025-07-18 |
| J+10 | `baseline_zero_return` | `none` | 0.05010 | 0.03586 | -0.0001 | 0.002 | 2015-09-04 -> 2025-07-11 |
| J+10 | `rf_factors` | `factors` | 0.05065 | 0.03721 | -0.0220 | 0.501 | 2015-09-04 -> 2025-07-11 |
| J+10 | `hgb_factors` | `factors` | 0.05099 | 0.03744 | -0.0357 | 0.529 | 2015-09-04 -> 2025-07-11 |
| J+10 | `elasticnet_factors` | `factors` | 0.05128 | 0.03788 | -0.0478 | 0.505 | 2015-09-04 -> 2025-07-11 |
| J+10 | `xgb_factors` | `factors` | 0.05146 | 0.03789 | -0.0550 | 0.519 | 2015-09-04 -> 2025-07-11 |
| J+10 | `lgbm_factors` | `factors` | 0.05227 | 0.03861 | -0.0886 | 0.503 | 2015-09-04 -> 2025-07-11 |
| J+10 | `ridge_factors` | `factors` | 0.05244 | 0.03886 | -0.0956 | 0.504 | 2015-09-04 -> 2025-07-11 |
| J+10 | `ridge_raw` | `raw` | 0.14069 | 0.10321 | -6.8862 | 0.482 | 2015-09-04 -> 2025-07-11 |
| J+20 | `rf_factors` | `factors` | 0.07181 | 0.05302 | 0.0127 | 0.561 | 2015-08-27 -> 2025-06-26 |
| J+20 | `baseline_zero_return` | `none` | 0.07228 | 0.05291 | -0.0001 | 0.005 | 2015-08-27 -> 2025-06-26 |
| J+20 | `lgbm_factors` | `factors` | 0.07228 | 0.05361 | -0.0002 | 0.579 | 2015-08-27 -> 2025-06-26 |
| J+20 | `hgb_factors` | `factors` | 0.07324 | 0.05510 | -0.0268 | 0.551 | 2015-08-27 -> 2025-06-26 |
| J+20 | `xgb_factors` | `factors` | 0.07343 | 0.05478 | -0.0322 | 0.563 | 2015-08-27 -> 2025-06-26 |
| J+20 | `elasticnet_factors` | `factors` | 0.07706 | 0.05769 | -0.1368 | 0.525 | 2015-08-27 -> 2025-06-26 |
| J+20 | `ridge_factors` | `factors` | 0.07915 | 0.05919 | -0.1994 | 0.529 | 2015-08-27 -> 2025-06-26 |
| J+20 | `ridge_raw` | `raw` | 0.20077 | 0.14839 | -6.7163 | 0.471 | 2015-08-27 -> 2025-06-26 |
| J+30 | `rf_factors` | `factors` | 0.08756 | 0.06504 | 0.0298 | 0.583 | 2015-08-19 -> 2025-06-11 |
| J+30 | `xgb_factors` | `factors` | 0.08837 | 0.06608 | 0.0116 | 0.560 | 2015-08-19 -> 2025-06-11 |
| J+30 | `baseline_zero_return` | `none` | 0.08890 | 0.06647 | -0.0002 | 0.005 | 2015-08-19 -> 2025-06-11 |
| J+30 | `lgbm_factors` | `factors` | 0.08974 | 0.06653 | -0.0192 | 0.587 | 2015-08-19 -> 2025-06-11 |
| J+30 | `hgb_factors` | `factors` | 0.09006 | 0.06776 | -0.0265 | 0.573 | 2015-08-19 -> 2025-06-11 |
| J+30 | `elasticnet_factors` | `factors` | 0.09798 | 0.07485 | -0.2149 | 0.510 | 2015-08-19 -> 2025-06-11 |
| J+30 | `ridge_factors` | `factors` | 0.10086 | 0.07713 | -0.2874 | 0.508 | 2015-08-19 -> 2025-06-11 |
| J+30 | `ridge_raw` | `raw` | 0.25590 | 0.19509 | -7.2880 | 0.451 | 2015-08-19 -> 2025-06-11 |

## Contribution des familles factorielles

| Horizon | Famille | Part coef Ridge | Delta RMSE sans famille |
|---:|---|---:|---:|
| J+5 | `weather_belt_stress` | 0.224 | -0.00025 |
| J+5 | `wasde_supply_demand` | 0.159 | -0.00010 |
| J+5 | `cross_commodity` | 0.159 | 0.00002 |
| J+5 | `market_momentum` | 0.120 | -0.00010 |
| J+5 | `seasonality` | 0.117 | 0.00038 |
| J+5 | `cot_positioning` | 0.052 | 0.00017 |
| J+5 | `production_fundamentals` | 0.052 | 0.00001 |
| J+5 | `ethanol_demand` | 0.051 | 0.00036 |
| J+5 | `macro_dollar_rates` | 0.037 | -0.00001 |
| J+5 | `market_volatility` | 0.030 | -0.00034 |
| J+10 | `weather_belt_stress` | 0.200 | -0.00031 |
| J+10 | `market_momentum` | 0.166 | -0.00083 |
| J+10 | `wasde_supply_demand` | 0.161 | -0.00113 |
| J+10 | `cross_commodity` | 0.152 | 0.00009 |
| J+10 | `seasonality` | 0.139 | 0.00027 |
| J+10 | `ethanol_demand` | 0.049 | 0.00125 |
| J+10 | `macro_dollar_rates` | 0.040 | 0.00002 |
| J+10 | `production_fundamentals` | 0.035 | -0.00077 |
| J+10 | `market_volatility` | 0.029 | -0.00039 |
| J+10 | `cot_positioning` | 0.028 | 0.00045 |
| J+20 | `market_momentum` | 0.193 | -0.00206 |
| J+20 | `cross_commodity` | 0.168 | 0.00121 |
| J+20 | `wasde_supply_demand` | 0.149 | -0.00280 |
| J+20 | `seasonality` | 0.146 | -0.00014 |
| J+20 | `weather_belt_stress` | 0.109 | -0.00002 |
| J+20 | `cot_positioning` | 0.068 | 0.00248 |
| J+20 | `ethanol_demand` | 0.065 | 0.00402 |
| J+20 | `production_fundamentals` | 0.048 | -0.00261 |
| J+20 | `macro_dollar_rates` | 0.047 | 0.00003 |
| J+20 | `market_volatility` | 0.007 | 0.00000 |
| J+30 | `cross_commodity` | 0.186 | 0.00162 |
| J+30 | `market_momentum` | 0.155 | -0.00386 |
| J+30 | `wasde_supply_demand` | 0.136 | -0.00497 |
| J+30 | `seasonality` | 0.134 | 0.00095 |
| J+30 | `weather_belt_stress` | 0.108 | 0.00054 |
| J+30 | `cot_positioning` | 0.105 | 0.00423 |
| J+30 | `ethanol_demand` | 0.072 | 0.00622 |
| J+30 | `production_fundamentals` | 0.050 | -0.00358 |
| J+30 | `macro_dollar_rates` | 0.048 | -0.00024 |
| J+30 | `market_volatility` | 0.006 | 0.00007 |

## Top facteurs Ridge

| Horizon | Facteur | Famille | Part coef Ridge |
|---:|---|---|---:|
| J+5 | `factor_weather_heat_stress` | `weather_belt_stress` | 0.105 |
| J+5 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.093 |
| J+5 | `factor_market_drawdown_recovery` | `market_momentum` | 0.070 |
| J+5 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.056 |
| J+5 | `factor_season_pollination_window` | `seasonality` | 0.054 |
| J+5 | `factor_ethanol_margin_signal` | `ethanol_demand` | 0.051 |
| J+5 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.047 |
| J+5 | `factor_season_annual_cycle` | `seasonality` | 0.043 |
| J+10 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.097 |
| J+10 | `factor_market_drawdown_recovery` | `market_momentum` | 0.097 |
| J+10 | `factor_weather_heat_stress` | `weather_belt_stress` | 0.090 |
| J+10 | `factor_season_pollination_window` | `seasonality` | 0.063 |
| J+10 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.060 |
| J+10 | `factor_season_annual_cycle` | `seasonality` | 0.051 |
| J+10 | `factor_ethanol_margin_signal` | `ethanol_demand` | 0.049 |
| J+10 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.048 |
| J+20 | `factor_market_drawdown_recovery` | `market_momentum` | 0.115 |
| J+20 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.071 |
| J+20 | `factor_ethanol_margin_signal` | `ethanol_demand` | 0.065 |
| J+20 | `factor_season_annual_cycle` | `seasonality` | 0.064 |
| J+20 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.056 |
| J+20 | `factor_wasde_supply_risk` | `wasde_supply_demand` | 0.052 |
| J+20 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.045 |
| J+20 | `factor_market_medium_trend` | `market_momentum` | 0.044 |
| J+30 | `factor_market_drawdown_recovery` | `market_momentum` | 0.103 |
| J+30 | `factor_cross_wheat_relative_value` | `cross_commodity` | 0.074 |
| J+30 | `factor_ethanol_margin_signal` | `ethanol_demand` | 0.072 |
| J+30 | `factor_season_annual_cycle` | `seasonality` | 0.066 |
| J+30 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.058 |
| J+30 | `factor_wasde_supply_risk` | `wasde_supply_demand` | 0.052 |
| J+30 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.051 |
| J+30 | `factor_weather_core_state_stress` | `weather_belt_stress` | 0.051 |

## Top facteurs SHAP

| Horizon | Facteur | Famille | Part mean(|SHAP|) |
|---:|---|---|---:|
| J+5 | `factor_season_annual_cycle` | `seasonality` | 0.107 |
| J+5 | `factor_market_short_momentum` | `market_momentum` | 0.084 |
| J+5 | `factor_wasde_supply_surprise` | `wasde_supply_demand` | 0.070 |
| J+5 | `factor_cot_open_interest_momentum` | `cot_positioning` | 0.065 |
| J+5 | `factor_wasde_revision_momentum` | `wasde_supply_demand` | 0.059 |
| J+5 | `factor_cross_soy_relative_value` | `cross_commodity` | 0.042 |
| J+5 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.040 |
| J+5 | `factor_market_liquidity_volume` | `market_volatility` | 0.037 |
| J+10 | `factor_season_annual_cycle` | `seasonality` | 0.127 |
| J+10 | `factor_wasde_revision_momentum` | `wasde_supply_demand` | 0.093 |
| J+10 | `factor_market_short_momentum` | `market_momentum` | 0.077 |
| J+10 | `factor_cot_open_interest_momentum` | `cot_positioning` | 0.057 |
| J+10 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.054 |
| J+10 | `factor_wasde_price_regime` | `wasde_supply_demand` | 0.053 |
| J+10 | `factor_market_liquidity_volume` | `market_volatility` | 0.043 |
| J+10 | `factor_season_pollination_window` | `seasonality` | 0.041 |
| J+20 | `factor_season_annual_cycle` | `seasonality` | 0.179 |
| J+20 | `factor_wasde_demand_exports` | `wasde_supply_demand` | 0.091 |
| J+20 | `factor_macro_inflation_signal` | `macro_dollar_rates` | 0.062 |
| J+20 | `factor_wasde_revision_momentum` | `wasde_supply_demand` | 0.056 |
| J+20 | `factor_market_medium_trend` | `market_momentum` | 0.053 |
| J+20 | `factor_market_short_momentum` | `market_momentum` | 0.049 |
| J+20 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.046 |
| J+20 | `factor_stocks_seasonal_tightness` | `production_fundamentals` | 0.041 |
| J+30 | `factor_season_annual_cycle` | `seasonality` | 0.169 |
| J+30 | `factor_wasde_demand_exports` | `wasde_supply_demand` | 0.143 |
| J+30 | `factor_macro_inflation_signal` | `macro_dollar_rates` | 0.102 |
| J+30 | `factor_wasde_revision_momentum` | `wasde_supply_demand` | 0.057 |
| J+30 | `factor_market_short_momentum` | `market_momentum` | 0.049 |
| J+30 | `factor_wasde_balance_tightness` | `wasde_supply_demand` | 0.041 |
| J+30 | `factor_cross_dollar_pressure` | `cross_commodity` | 0.039 |
| J+30 | `factor_stocks_seasonal_tightness` | `production_fundamentals` | 0.035 |

## Intervalles CQR

| Horizon | Couverture réalisée | Largeur moyenne | N test |
|---:|---:|---:|---:|
| J+5 | 0.844 / cible 0.900 | 0.10078 | 1547 |
| J+10 | 0.814 / cible 0.900 | 0.12762 | 1546 |
| J+20 | 0.760 / cible 0.900 | 0.16836 | 1544 |
| J+30 | 0.784 / cible 0.900 | 0.21954 | 1541 |

Lecture: la CQR est exécutée et calibrée, mais la couverture réalisée reste sous 90% sur ce backtest, signe d'une forte dérive temporelle. Le résultat est donc utilisable comme diagnostic, pas comme garantie opérationnelle parfaite.

## Couverture sources

| Source | Statut | Features | Priorité |
|---|---|---:|---:|
| `eia_ethanol` | `proxy_in_features` | 1 | 1 |
| `cftc_cot_corn` | `active_in_features` | 56 | 2 |
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
| Collecte données (WASDE, FRED, NASS, OpenMeteo) | ✅ Implémenté | Collecteurs et tables locales validés |
| Anti-leakage (5 checks, |corr|>0.97) | ✅ Implémenté | Audit automatisé à chaque build |
| Cibles y_logret_h{5,10,20,30} | ✅ Implémenté | Expanding quantile, anti-leakage |
| Features brutes | ✅ Implémenté | 305 colonnes |
| Facteurs synthétiques | ✅ Implémenté | 36 facteurs, expanding z-scores |
| Walk-forward temporel | ✅ Implémenté | Train historique, tests par blocs, embargo par horizon |
| Benchmark modèles | ✅ Implémenté | Ridge, ElasticNet, RF, HGB, LightGBM/XGBoost si installés |
| Stacking Ridge sur meta-database | ✅ Implémenté | 6 modèles de base |
| Intervalles de confiance (split-conformal) | ✅ Implémenté | Rolling window 252j, couverture ~90% |
| Régime de marché (bull/bear/range) | ✅ Implémenté | Méthode actuelle : markov_switching |
| Décision agriculteur (SELL/STORE/WAIT) | ✅ Implémenté | Moteur YAML paramétrable |
| Importance par coefficient Ridge | ✅ Implémenté | Ablation par famille |
| Analyse SHAP | ✅ Implémenté | 144 lignes SHAP |
| Conformalized Quantile Regression (CQR) | ✅ Implémenté | LightGBM quantile + calibration conforme ; couverture réalisée reportée ci-dessus |
| Régime Markov-switching | ✅ Implémenté | Statsmodels MarkovRegression, fallback rule-based si échec |
| EIA éthanol dans features | ⚠️ Proxy intégré | Proxy marge énergie/maïs sans clé EIA ; vraie EIA activable avec clé API |
| CFTC COT dans features | ✅ Implémenté | CFTC historique public, publication laggée dans les features |
| NDVI / indices de végétation satellite | ❌ Non implémenté | Hors périmètre actuel |
| ENSO / El Niño | ❌ Non implémenté | Hors périmètre actuel |
| XGBoost/LightGBM | ✅ Benchmark / ⚠️ meta | Dans benchmarks et SHAP ; non ajouté au stacking historique |

## Conclusion opérationnelle

Le projet dispose d'une architecture solide et d'une base technique propre. Les modèles actifs (RF, HGB sur facteurs) surpassent le zéro-return baseline sur la précision directionnelle (55–60% à J+20/30). Les familles production_fundamentals, ethanol_demand, cot_positioning et macro_dollar_rates sont intégrées sans fuite temporelle. Leur valeur ajoutée doit se lire par horizon : certaines informations sont redondantes avec WASDE en Ridge, mais utiles pour les modèles non linéaires et pour l'explication économique.

Prochaines étapes par ordre de priorité : (1) fournir une vraie clé EIA pour remplacer le proxy éthanol ; (2) mesurer l'ablation CFTC/EIA source par source ; (3) ajouter USDA Crop Progress ; (4) intégrer LightGBM/XGBoost au stacking historique si le gain walk-forward est stable.

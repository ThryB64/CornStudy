# EMA STUDY — Rapport de Synthèse Final

> Source exploratoire (Barchart proxy). Résultats expérimentaux. Non validés sur données officielles Euronext.
> `source_quality = exploratoire_barchart_proxy` ; `verdict_data = NO_RELIABLE_PERIOD_ML`.

**Phrase directrice :** CBOT explique la tendance mondiale. EMA révèle la prime européenne via le basis.

## Conclusions principales

- EMA et CBOT sont cointégrées (EG p=7.3e-7). La transmission CBOT → EMA est forte, surtout structurelle et contemporaine.
- La décomposition retour EMA (R²=93.6% avec CBOT+basis_chg) est descriptive/contemporaine, non prédictive.
- Le basis EMA/CBOT est stationnaire (ADF) avec φ=0.97, demi-vie 22j. Hit rate H60=85%.
- 49 chocs EU identifiés à 3σ — la composante résiduelle EU est petite (~0.4% std).
- Granger EMA→CBOT : NON CONFIRMÉ en validation OOF robuste (2022-driven).
- Direction EMA brute : NO_GO (DA<0.55). Signal uniquement sur basis reversion (DA=0.786 walk-forward).
- CQR prix EMA : CQR_PRICE_NO_GO (coverage H20=79.2%, H60=80.4%, objectif 90% non atteint).

## Tableau des verdicts

| Finding | Verdict | Evidence |
|---|---|---|
| Données EMA : source exploratoire | EXPLORATOIRE | Verdict ML: NO_RELIABLE_PERIOD |
| Invariant série ajustée | VALIDÉ | raw - adj == cum_adj (tolérance 0.01) |
| Cointégration EMA/CBOT | CONFIRMÉ | EG p=7.28e-07 |
| CBOT → EMA (Granger) | STRUCTUREL | p=9.09e-16 in-sample ; relation surtout contemporaine |
| EMA → CBOT (Granger OOF) | NON CONFIRMÉ | VALID-GRANGER-01 : 2022-driven, non confirmé OOF |
| R² retour EMA (CBOT + basis) | DESCRIPTIF | R²=0.936 (contemporain) |
| Chocs EU (résidu 3σ) | 49 DÉTECTÉS | n=49 |
| Basis mean-reversion H60 | SIGNAL FORT | Hit rate=85.0% |
| Direction EMA brute H20 | NO_GO | DA < 0.55 OOF, cohérent avec DA=0.4673 |
| Direction basis reversion | GO_SIGNAL | Best DA=0.786 |
| CQR prix EMA | NO_GO | Coverage H20=79.2%, H60=80.4% < objectif 90% |
| Courbe EMA multi-maturité | PARTIELLE | 1.25 contrats/date ; 14.9% des dates avec >=2 contrats |

## Métriques clés

| Métrique | Valeur |
|---|---|
| data_total_rows | 4818 |
| source_quality | exploratoire_barchart_proxy |
| verdict_data | NO_RELIABLE_PERIOD_ML |
| data_verdict_ml | NO_RELIABLE_PERIOD |
| data_pct_2plus_contracts | 0.1486556359875905 |
| series_invariant_holds | True |
| series_coverage_rate | 0.7903112567282939 |
| rolls_n_rolls | 68 |
| rolls_avg_gap_eur_t | 9.830882352941176 |
| rolls_pct_H60_with_roll | 0.9890435297601421 |
| coint_eg_p_value | 7.281906868064884e-07 |
| coint_eg_confirmed | True |
| vecm_half_life_days | 83.31880688942961 |
| granger_cbot_to_ema_p | 9.090903513886355e-16 |
| granger_ema_to_cbot_p_insample | 2.586045099289057e-06 |
| r2_cbot_only | 0.21145774646354976 |
| r2_cbot_basis | 0.9355204532238496 |
| incremental_r2_basis | 0.7240627067602998 |
| eu_shocks_3sigma | 49 |
| eu_residual_adf | stationary |
| basis_mean_eur_t | 37.24520818385883 |
| basis_ar1_phi | 0.9700988347697848 |
| basis_half_life_days | 22.832949485411824 |
| basis_mr_h60_hitrate | 0.8502994011976048 |
| granger_oof_verdict | REJECTED |
| direction_best_da | 0.7859918000953424 |
| direction_best_target | y_up_h20_basis_reversion |
| direction_overall_verdict | GO_SIGNAL |
| vol_mean_annual | 0.19559152156219478 |
| vol_har_r2 | 0.013463945666503774 |

## Artefacts produits

- `artefacts/ema_study/ema_project_overview.json`
- `artefacts/ema_study/ema_data_audit_v2.json`
- `artefacts/ema_study/ema_contracts_rolls.json`
- `artefacts/ema_study/ema_continuous_series.json`
- `artefacts/ema_study/ema_cbot_cointegration.json`
- `artefacts/ema_study/ema_return_decomposition.json`
- `artefacts/ema_study/ema_residual_study.json`
- `artefacts/ema_study/ema_basis_formal.json`
- `artefacts/ema_study/ema_granger_validation.json`
- `artefacts/ema_study/ema_direction_benchmark.json`
- `artefacts/ema_study/ema_event_study.json`
- `artefacts/ema_study/ema_feature_importance.json`
- `artefacts/ema_study/ema_volatility.json`
- `artefacts/ema_study/ema_price_forecast.json`
- `artefacts/ema_study/ema_weekly_benchmark.json`

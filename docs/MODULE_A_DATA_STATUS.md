# Module A — Data Status

Ce rapport classe chaque signal du Module A en `real`, `proxy`, `missing` ou `manual`.
Il sert à éviter qu'un proxy ou un placeholder soit lu comme une donnée économique validée.

## Synthèse

- Cible évaluée : `y_up_h20_ema`.
- Période features : jusqu'au 2022-12-31 (5549 lignes).
- Fenêtre de couverture effective : 2562 lignes avec cible non nulle.
- Signaux audités : 12.
- Couverture moyenne : 55.5%.
- Couverture moyenne pondérée par les poids calibrés : 57.3%.
- Statuts : `manual`=1, `missing`=2, `proxy`=5, `real`=4.
- Décisions : `DOCUMENTER_MANUEL`=1, `GARDER`=3, `GARDER_COMME_PROXY`=4, `GARDER_PRIORITAIRE`=1, `REMPLACER`=2, `REMPLACER_PRIORITE`=1.

## Table des signaux

| Signal | Bloc | Statut | Source active | Couverture | DA seul hebdo | Poids | Décision | Note |
|---|---|---:|---|---:|---:|---:|---|---|
| bilan_mondial | offre_mondiale | real | wasde_stocks_to_use_calc_z | 100.0% | 51.0% | 0.061 | GARDER | WASDE stocks/use data. |
| bilan_stocks_eu | offre_mondiale | proxy | ema_cbot_basis_zscore_52w | 95.0% | 53.1% | 0.096 | GARDER_COMME_PROXY | EMA-CBOT basis used as proxy for European tightness, not true EU stocks. |
| crop_condition_eu | offre_mondiale | proxy | crop_ge_zscore_seasonal | 43.8% | 48.7% | 0.057 | GARDER_COMME_PROXY | US crop condition and drought proxies, not EC MARS or EU crop condition. |
| brazil_supply_pressure | offre_competiteurs | proxy | corn_soy_ratio | 100.0% | 53.8% | 0.075 | GARDER_COMME_PROXY | Derived from cross-market/WASDE proxies, not a full Brazil local dataset. |
| ukraine_corridor | offre_competiteurs | manual | NA | 0.0% | 47.9% | 0.030 | DOCUMENTER_MANUEL | Manual placeholder; must be documented at report time. |
| us_crop_condition | offre_competiteurs | real | crop_ge_zscore_seasonal | 43.8% | 48.7% | 0.070 | GARDER | USDA crop condition/drought data. |
| china_demand | demande_mondiale | missing | export_china_pct_total | 0.0% | 47.9% | 0.103 | REMPLACER | US export/WASDE proxy for China demand when available. |
| wasde_surprise | demande_mondiale | real | wasde_ending_stocks_surprise_vs_5y | 100.0% | 56.7% | 0.169 | GARDER_PRIORITAIRE | WASDE surprise features. |
| export_pace_eu | demande_mondiale | missing | export_pace_vs_5y_avg | 0.0% | 47.9% | 0.105 | REMPLACER | Fallback export pace proxy; not true EU export pace. |
| cot_positioning | positionnement_structure | real | cot_mm_pct_oi_percentile | 75.9% | 48.5% | 0.076 | GARDER | CFTC COT positioning data. |
| futures_structure | positionnement_structure | proxy | ema_backwardation_flag/ema_contango_flag/ema_roll_yield_ann | 10.4% | 41.6% | 0.104 | REMPLACER_PRIORITE | Partial EMA front/basis/liquidity fragments, not a complete futures curve. |
| eur_usd_competitive | positionnement_structure | proxy | cbot_eur_t | 97.2% | 50.6% | 0.055 | GARDER_COMME_PROXY | Derived competitiveness proxy from CBOT EUR/t and EMA relative strength. |

## Garde-fous

- Les signaux `proxy` restent utilisables pour le contexte, mais doivent être libellés comme proxies.
- Les signaux `missing` doivent être remplacés par une vraie source ou exclus des conclusions fortes.
- Les signaux `manual` doivent être documentés explicitement dans chaque rapport produit.
- Les signaux de structure futures EMA restent des fragments front/basis/liquidité, pas une courbe complète.

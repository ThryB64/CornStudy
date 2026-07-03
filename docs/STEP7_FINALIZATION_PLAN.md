# Étape 7 — Plan de finalisation (score de vente CBOT)

Date : 2026-06-13. Clôture de l'étude. **On n'intègre que les briques validées** (étapes
5 bis / 6). Aucune nouvelle recherche, aucune famille rejetée, aucun modèle complexe, aucun
tuning sur le holdout 2024+.

## 1. Objectif final
- **On ne prédit plus le prix exact** du maïs CBOT (la random walk reste imbattable en RMSE,
  étape 6).
- **On construit un score de vente / direction / risque H40-H90** : aide à la **décision de
  commercialisation** d'un agriculteur.
- **Le score est indicatif**. Ce n'est **pas** un bot de trading, jamais de short, jamais de
  levier, jamais de rachat spéculatif. Sorties = aide à la vente.

## 2. Signaux intégrés (uniquement `final_selected_features.csv`)
| Bloc | Variables | Horizon | Rôle |
|---|---|---|---|
| Crop Condition | `cond_gd_ex_anom`, `cond_dev5y`, `cond_poor_vp` | H90 | direction (cœur) |
| WASDE stocks-to-use | `s2u_z`, `s2u_pctile`, `s2u_slow_chg` | H40 | direction |
| Saison | `base_sin`, `base_cos` | H40/H90 | porte une part de l'edge |
| Volatilité (HAR) | `rv_w`, `rv_m`, `rv_q` + HAR forecast | H20-H90 | risque / gate |
| Gate vol | `vol_filter_high_decile` | H90 | neutralise le régime où le signal s'inverse |
| Régimes | `regime_uptrend`, `regime_low_vol`, `regime_bilan_extreme` | H90 | **confiance seulement** |

`egarch_vol` : optionnel (import `arch` en try/except) ; **HAR est le défaut** pour garder le
paquet principal sans dépendance lourde. Les régimes sont **post-hoc** (risque moyen) → ils
ne modulent que la **confiance**, ils ne sont pas le modèle directionnel.

## 3. Signaux exclus (documentation seulement)
REJECT : météo réalisée (brute/lags/extrême), COT, surprise WASDE proxy, éthanol/DDG proxy,
trend-following, stacking, deep learning. DATA_BLOCKED / FUTURE_DATA_REQUIRED : futures curve,
basis, OU mean-reversion, satellite, météo prévue, options, consensus WASDE. **Jamais intégrés
comme variables ; cités uniquement comme REJECT / DATA_BLOCKED dans la doc.**

## 4. Architecture
| Fichier | Rôle |
|---|---|
| `src/mais/indicator/cbot_sale_score_features.py` | features anti-fuite (port des transforms validés) |
| `src/mais/indicator/cbot_sale_score_model.py` | logit L2 parcimonieux par horizon + HAR vol + régimes |
| `src/mais/indicator/cbot_sale_score.py` | orchestrateur : compose direction/risque/confiance → recommandation |
| `src/mais/indicator/cbot_sale_score_backtest.py` | backtest décisionnel vendeur (pas de bot) |
| `src/mais/indicator/cbot_sale_score_report.py` | génération du rapport final |
| `config/cbot_sale_score.yaml` | configuration officielle (horizons, variables, seuils, sorties, version) |
| `tests/test_cbot_sale_score*.py` | anti-fuite, sorties, config, reproductibilité |
| CLI `mais sale-score` + cible `make sale-score` | relance |

**Choix d'emplacement** : `src/mais/indicator/` (le score est un indicateur d'aide à la
décision ; cohérent avec `direction.py`, `structural_indicator_v9.py`). Le module orchestre
ses propres données (mêmes sources internes : `data/interim/market.parquet`,
`data/raw/usda_nass_crop_condition/crop_progress.parquet`, vintage WASDE EXT026 = source
anti-fuite). On **lit** le vintage externe, on ne le **modifie pas**.

Sorties dans `artefacts/final_cbot_sale_score/` : `final_score_timeseries.{parquet,csv}`,
`final_score_latest.json`, `final_holdout_2024_metrics.csv`, `final_backtest_decisions.csv`,
`final_backtest_summary.json`, `final_feature_dictionary.csv`, `final_model_coefficients.csv`,
`final_report.md`.

## 5. Protocole holdout 2024+
- Frontière : `HOLDOUT_START = 2024-01-01`. **Non utilisé** aux étapes 1-6.
- **Features figées** avant holdout (depuis `final_selected_features.csv`).
- **Seuils figés** dans `config/cbot_sale_score.yaml` (ou calibrés uniquement sur ≤2023).
- Entraînement/calibration : **données ≤ 2023 uniquement**. Le gate de vol (décile 90) est
  estimé sur ≤2023 puis **gelé**.
- Évaluation : **une seule fois** sur 2024+. Aucune itération, aucun choix de variable ou de
  seuil après avoir regardé le holdout.
- Baselines comparées : marché seul, saison seule, crop seule, WASDE seule, random walk /
  base-rate ; et pour le backtest : vente 100 % récolte, vente par tiers, DCA mensuel.

## 6. Règles anti-fuite (rappel `anti_leak_rules.md`)
1. Cible directionnelle = **vraie ligne de marché** `index[i+h]` (PAS `date + h jours`) —
   corrigé étape 5 bis, re-testé ici par un test unitaire.
2. WASDE disponible à `publication + 1 jour ouvré` (vintage EXT026).
3. Crop Condition disponible **après publication** (lundi → +2 j).
4. Standardisation/imputation/sélection **train-only**, z/percentiles **expandants** `shift(1)`.
5. Pas de split aléatoire ; walk-forward expandant, refit annuel purgé.
6. **Holdout 2024+ jamais utilisé pour entraîner/sélectionner/tuner.**

## 7. Métriques finales
- **Direction** : DA, balanced accuracy, ROC-AUC, Brier, calibration, matrice de confusion,
  précision/rappel hausse & baisse.
- **Décision** : nombre de signaux par classe, prix moyen obtenu vs baselines, années
  gagnantes/perdantes, max regret, faux signaux, périodes évitées par le gate vol.
- **Risque** : vol réalisée après signal, drawdown moyen, impact du gate.

## 8. Risques
- Edge **modeste** (DM non significatif, IC chevauchant le marché) → score = aide, pas vérité.
- Régimes **post-hoc** → confiance seulement, à valider en forward.
- Holdout court (~1 an : 2024-01 → 2025-07, borné par la fin des prix) → puissance limitée ;
  conclusion à formuler prudemment.

## 9. Critères de validation finale
- **VALIDATED** : anti-fuite OK, tests passent, holdout ne détruit pas le signal, score plus
  utile qu'une baseline simple (direction ou risque), limites documentées, aucune promesse de
  prix.
- **FRAGILE** : holdout mitigé / signal faible / backtest instable / dépend de quelques années.
- **RESEARCH_ONLY** : signal intéressant mais non utilisable opérationnellement.
- **NOT_VALIDATED** : holdout échoue, anti-fuite échoue, ne bat aucune baseline, la conclusion
  de l'étape 6 ne survit pas.

Le verdict réel sera fixé **après** le run holdout (section H), sans cacher un mauvais résultat.

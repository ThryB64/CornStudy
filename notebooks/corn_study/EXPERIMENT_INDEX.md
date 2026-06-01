# Experiment Index — Corn Study

Journal central des expériences de recherche. Chaque ligne doit résumer une hypothèse testée, la méthode utilisée, le résultat observé et la décision prise pour la suite de l'étude.

## Statuts

Statuts autorisés : `successful`, `neutral`, `failed`, `active`

## Expériences

| ID | Date | Notebook | Hypothèse | Méthode | Résultat | Décision | Statut |
|---|---|---|---|---|---|---|---|
| EXP-017 | 2026-05-16 | `notebooks/corn_study/main/07_ablation_feature_selection.ipynb` | Certaines familles de facteurs ajoutent du signal marginal réel. | One-out, family-only, VIF et stabilité temporelle pré-2023. | Familles utiles : `positioning`, `drought_severity`, `ethanol_demand`. | Retenir le featureset GARDER pour IND-06. | neutral |
| EXP-016 | 2026-05-16 | `notebooks/corn_study/main/08_context_analysis.ipynb` | Le signal varie fortement selon saison, WASDE, régime et volatilité. | Walk-forward pré-2023 puis métriques DA/AUC/Brier par contexte. | Poches principales : `volatilite=low_vol`, `stocks=stocks_tendus`, `tendance=ranging`. | Contextes exploratoires à valider IND-08. | neutral |
| EXP-015 | 2026-05-15 | `notebooks/corn_study/experiments/oracle_analysis.ipynb` | Les drivers futurs bornent le signal directionnel maximal. | Oracle variables futures + benchmark logistique walk-forward sur y_up_h20. | Variables HIGH : `oracle_wasde_ending_stocks_surprise`. | Prioriser ces familles pour IND-06. | neutral |
| EXP-014 | 2026-05-15 | `notebooks/corn_study/main/04_targets_reformulation.ipynb` | La direction et les fortes variations sont plus exploitables que le retour continu. | Walk-forward 5 splits sur 96 cibles, modèles Ridge/RF/LGBM et baselines saison/momentum. | Cibles retenues : `y_down_gt_5pct_h20`, `y_up_gt_5pct_h20`, `y_down_gt_3pct_h10`. | Sélectionner ces cibles pour IND-04. | neutral |
| EXP-001 | 2026-05-09 | Pipeline features | Les familles COT, EIA, NASS et Drought peuvent enrichir le signal marché. | Rebuild `build_features()` avec collecteurs et facteurs dédiés, puis audit anti-leakage. | Pipeline complet, 6192 lignes, COT/EIA/NASS/Drought actifs selon disponibilité. | Garder ces familles dans les ablations Phase Étude. | successful |
| EXP-002 | 2026-05-09 | Professional study | Les modèles RF/LGBM/XGBoost battent les baselines saisonnières sur `y_logret_h5..h30`. | Walk-forward multi-horizons avec baselines, RF, LGBM, XGBoost et facteurs. | Direction intéressante surtout h20 (`lgbm_factors` DA 0.613), baselines saisonnières fortes à h20/h30. | Tester davantage la direction et les régimes, pas seulement le prix brut. | neutral |
| EXP-003 | 2026-05-09 | CQR calibration | Le CQR peut produire des intervalles fiables malgré la dérive temporelle. | Correction `cal_ratio`, quantile discret et split-conformal comparatif. | Split-conformal coverage 88.9%, CQR final 91.7%. | Conserver CQR, mesurer performance par confiance. | successful |
| EXP-004 | 2026-05-09 | Regime models | Les régimes bull/range/bear structurent la prédictibilité du maïs. | Markov-switching avec fallback rule-based. | Trois régimes produits ; bear rare, environ 2.2% des observations. | Utiliser les régimes comme axe d'analyse, sans surinterpréter bear. | successful |
| EXP-005 | 2026-05-09 | Farmer backtest | Un signal modèle peut améliorer la stratégie agriculteur face à `SELL_HARVEST`. | Backtest 6 stratégies avec capture rate et coûts de stockage. | `SELL_HARVEST` 82.8%, `MODEL_SIGNAL` 82.0%. | Résultat utile mais non dominant ; refaire après cibles directionnelles métier. | neutral |

## Template

| ID | Date | Notebook | Hypothèse | Méthode | Résultat | Décision | Statut |
|---|---|---|---|---|---|---|---|
| EXP-XXX | YYYY-MM-DD | `notebooks/corn_study/XX_name.ipynb` | Hypothèse testée. | Méthode courte et reproductible. | Résultat mesuré, avec métrique clé. | Décision de recherche ou produit. | active |

| EXP-006 | 2026-05-15 | Saisonnalité — structure mensuelle et stabilité inter-périodes | Les biais saisonniers du maïs sont stables sur 20+ ans et di | A compléter après exécution — noter si patterns pre/post 2012 et 2019 divergent | **neutral** |

---

## EXP-006 — Saisonnalité — structure mensuelle et stabilité inter-périodes

**Date :** 2026-05-15
**Décision :** `neutral`

**Hypothèse :**
Les biais saisonniers du maïs sont stables sur 20+ ans et directement exploitables

**Méthode :**
compute_monthly_returns + compute_seasonal_by_period + heatmap année×mois

**Résultat :**
A compléter après exécution — noter si patterns pre/post 2012 et 2019 divergent

**Notes :**
Si instables → feature saisonnière ML uniquement. Si stables → règle directe possible.
| EXP-007 | 2026-05-15 | Framework facteurs — classification 249 features en 8 familles | Les familles COT et WASDE ont le signal prédictif le plus él | A compléter après exécution — noter les familles top-3 par |r| médian | **neutral** |

---

## EXP-007 — Framework facteurs — classification 249 features en 8 familles

**Date :** 2026-05-15
**Décision :** `neutral`

**Hypothèse :**
Les familles COT et WASDE ont le signal prédictif le plus élevé à H=20j

**Méthode :**
classify_column + compute_coverage + compute_correlations_by_horizon

**Résultat :**
A compléter après exécution — noter les familles top-3 par |r| médian

**Notes :**
Vérifier % famille Autre — si > 30% enrichir FAMILY_RULES. Comparer résultats avec SHAP notebook 06.
| EXP-008 | 2026-05-15 | Reformulation cibles — storage_value vs logret | Une cible métier (storage_value) est plus utile que log-retu | y_store_h20 est binaire et plus interprétable. MI supérieur à y_logret pour fact | **successful** |

---

## EXP-008 — Reformulation cibles — storage_value vs logret

**Date :** 2026-05-15
**Décision :** `successful`

**Hypothèse :**
Une cible métier (storage_value) est plus utile que log-return pour l'agriculteur

**Méthode :**
build_target_suite() + compare via mutual information

**Résultat :**
y_store_h20 est binaire et plus interprétable. MI supérieur à y_logret pour facteurs disponibles.

**Notes :**
Utiliser y_store_h20 et y_up_h20 dans notebooks 06-09 en plus de y_logret_h20
| EXP-009 | 2026-05-15 | Modèles statistiques AR/ARIMA/GARCH/Markov | L'autocorrélation des returns permet de les prédire | AR/ARIMA ne bat pas seasonal naive. GARCH utile pour volatilité. Markov 2-états  | **neutral** |

---

## EXP-009 — Modèles statistiques AR/ARIMA/GARCH/Markov

**Date :** 2026-05-15
**Décision :** `neutral`

**Hypothèse :**
L'autocorrélation des returns permet de les prédire

**Méthode :**
Walk-forward AR(5), ARIMA grid, GARCH(1,1), Markov 2-états

**Résultat :**
AR/ARIMA ne bat pas seasonal naive. GARCH utile pour volatilité. Markov 2-états exploitable.

**Notes :**
ARIMA = baseline statistique. GARCH → intégrer dans uncertainty. Markov 2-états → remplacer Markov 3.
| EXP-010 | 2026-05-15 | AutoML ML — benchmark walk-forward + Optuna LightGBM (30 trials) | Optuna améliore la DA vs hyperparamètres par défaut | Voir résultats dans les cellules précédentes | **neutral** |

---

## EXP-010 — AutoML ML — benchmark walk-forward + Optuna LightGBM (30 trials)

**Date :** 2026-05-15
**Décision :** `neutral`

**Hypothèse :**
Optuna améliore la DA vs hyperparamètres par défaut

**Méthode :**
run_benchmark_suite() walk-forward + Optuna N_TRIALS=30 sur LightGBM

**Résultat :**
Voir résultats dans les cellules précédentes

**Notes :**
Augmenter N_TRIALS à 100+ (ETUDE-10) pour validation statistique robuste
| EXP-011 | 2026-05-15 | Modèles par saison et régime | Modèles spécialisés par saison > modèle global | A compléter après exécution | **neutral** |

---

## EXP-011 — Modèles par saison et régime

**Date :** 2026-05-15
**Décision :** `neutral`

**Hypothèse :**
Modèles spécialisés par saison > modèle global

**Méthode :**
benchmark_by_regime + benchmark_by_season sur factors

**Résultat :**
A compléter après exécution

**Notes :**
Résultat conditionnel à l'ajout de Crop Progress / Drought Monitor
| EXP-012 | 2026-05-15 | CQR couverture + calibration probabilités | CQR atteint 90% de couverture, intervalles adaptatifs utiles | CQR 91.7% ✅. Intervalles larges (spread 27% à h=20j). Confidence score calculabl | **successful** |

---

## EXP-012 — CQR couverture + calibration probabilités

**Date :** 2026-05-15
**Décision :** `successful`

**Hypothèse :**
CQR atteint 90% de couverture, intervalles adaptatifs utiles

**Méthode :**
cqr_results.parquet + calibrated_predictions.parquet

**Résultat :**
CQR 91.7% ✅. Intervalles larges (spread 27% à h=20j). Confidence score calculable.

**Notes :**
Intégrer confidence score dans la logique de décision NB09
| EXP-013 | 2026-05-15 | Synthèse finale — état du projet et roadmap v1 | Le projet peut passer d'une EDA à un système de décision uti | Signal directionnel réel (DA=61.3% h20). DCA > modèle actuellement. 3 priorités  | **neutral** |

---

## EXP-013 — Synthèse finale — état du projet et roadmap v1

**Date :** 2026-05-15
**Décision :** `neutral`

**Hypothèse :**
Le projet peut passer d'une EDA à un système de décision utile en 3 itérations

**Méthode :**
Synthèse de tous les notebooks 01-09 + analyse des résultats

**Résultat :**
Signal directionnel réel (DA=61.3% h20). DCA > modèle actuellement. 3 priorités identifiées.

**Notes :**
Itération suivante : Crop Progress + y_store_h20 + Optuna 100 trials. Objectif : DA ≥ 63%

---

## EXP-014 — IND-02 — Comparaison complète des cibles

**Date :** 2026-05-15
**Statut :** `neutral`

**Hypothèse :**
Les cibles directionnelles ou d'événements forts sont plus exploitables pour l'indicateur que le retour continu brut.

**Méthode :**
Walk-forward 5 splits avec embargo par horizon, données limitées à 2022, modèles `ridge_factors`, `rf_factors`, `lgbm_factors`, et comparaison aux indicateurs `seasonal_indicator` / `momentum_indicator`.

**Résultat :**
Cibles retenues pour IND-04+ : `y_down_gt_5pct_h20`, `y_up_gt_5pct_h20`, `y_down_gt_3pct_h10`. Les détails complets sont dans `artefacts/professional_study/target_comparison.parquet`.

**Décision :**
Utiliser ce classement comme entrée de sélection pour IND-04.

---

## EXP-015 — IND-03 — Oracle analysis complète

**Date :** 2026-05-15
**Statut :** `neutral`

**Hypothèse :**
Les variables futures météo, WASDE, COT ou volatilité révèlent quels drivers méritent un sous-modèle prédictif.

**Méthode :**
Création de variables `oracle_*` isolées, WASDE futur via `bfill()` oracle-only, benchmark walk-forward pré-2023 sur `y_up_h20`.

**Résultat :**
Variables HIGH : `oracle_wasde_ending_stocks_surprise`. Résultats complets dans `artefacts/professional_study/oracle_analysis.parquet`.

**Décision :**
Utiliser les variables HIGH comme priorités de familles pour IND-06.

---

## EXP-016 — IND-04 — Analyse par contexte

**Date :** 2026-05-16
**Statut :** `neutral`

**Hypothèse :**
La performance globale masque des poches de signal par saison, publication WASDE, régime, volatilité ou niveau de stocks.

**Méthode :**
Prédictions walk-forward pré-2023 sur `y_down_gt_5pct_h20`, puis métriques par contexte avec comparaison aux indicateurs saisonnier et momentum.

**Résultat :**
Poches principales : `volatilite=low_vol`, `stocks=stocks_tendus`, `tendance=ranging`. Résultats complets dans `artefacts/professional_study/context_analysis.parquet`.

**Décision :**
Conserver ces contextes comme hypothèses exploratoires, à valider hors échantillon en IND-08.

---

## EXP-017 — IND-05 — Ablation des familles

**Date :** 2026-05-16
**Statut :** `neutral`

**Hypothèse :**
Les familles SHAP importantes ne sont pas toutes utiles marginalement ; l'ablation mesure le gain réel.

**Méthode :**
Familles lues depuis `config/factor_metadata.yaml`, benchmark one-out et family-only sur `y_down_gt_5pct_h20`, VIF et stabilité descriptive pré-2023.

**Résultat :**
Familles utiles : `positioning`, `drought_severity`, `ethanol_demand`. Résultats complets dans `artefacts/professional_study/ablation_results.parquet`.

**Décision :**
Utiliser `feature_selection.parquet` comme featureset recommandé pour IND-06.

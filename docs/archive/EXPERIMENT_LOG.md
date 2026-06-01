# Journal des expériences

## Principe

Chaque modification significative du système doit être documentée ici avec :
- L'hypothèse testée
- Ce qui a changé
- Les données utilisées
- Les résultats mesurés
- L'interprétation
- La décision prise

Ce journal est le fil conducteur du projet. Sans lui, on ne sait plus pourquoi on a fait tel choix.

---

## Format d'une expérience

```markdown
### EXP-XXX — [Titre court]

**Date :** YYYY-MM-DD
**Statut :** EN COURS | TERMINÉ | ANNULÉ
**Horizon(s) concerné(s) :** J+5 / J+10 / J+20 / J+30 / Tous

**Hypothèse :**
[Pourquoi on pense que ce changement va améliorer quelque chose]

**Changement apporté :**
[Précisément ce qui a été modifié : fichier, paramètre, source de données]

**Données utilisées :**
[Période, sources, nombre de lignes]

**Résultats avant :**
| Horizon | Modèle | RMSE | DA | R² |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

**Résultats après :**
| Horizon | Modèle | RMSE | DA | R² |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

**Interprétation :**
[Ce qu'on apprend de ces résultats]

**Décision :**
[Garder / Rejeter / Tester autre chose]

**Suite :**
[Prochaine expérience envisagée]
```

---

## EXP-001 — Palier 1 : Intégration FRED + QuickStats + Production dans features

**Date :** 2026-04 (session précédente)
**Statut :** TERMINÉ
**Horizon(s) :** Tous

**Hypothèse :**
Ajouter les données macro (FRED), les données de production NASS et les parts de production par état devrait enrichir les features et améliorer la prédiction sur les horizons longs (J+20, J+30).

**Changement apporté :**
- `src/mais/features/__init__.py` : ajout sections 6 (FRED), 7 (QuickStats), 8 (Production shares)
- `src/mais/features/factors.py` : ajout familles `production_fundamentals` (4 recettes) et `macro_dollar_rates` (2 recettes)

**Résultats :**
- Ridge sur production_fundamentals : Δ RMSE = -0.00391 (se dégrade légèrement)
- HGB sur production_fundamentals : Δ RMSE ≈ 0.000 (neutre)
- Explication : colinéarité forte avec WASDE (les deux contiennent yield, stocks, production)

**Interprétation :**
Production_fundamentals est redondant avec WASDE sur Ridge. Neutre sur HGB. La colinéarité est documentée et non cachée dans le rapport.

**Décision :** Garder (neutre sur HGB, futur bénéfice sur LightGBM via interactions)

---

## EXP-002 — Palier 2 : Collecteur CFTC COT

**Date :** 2026-04 (session précédente)
**Statut :** TERMINÉ
**Horizon(s) :** J+10, J+20

**Hypothèse :**
Le positionnement spéculatif COT (managed money net) devrait améliorer la DA sur J+10/J+20, car les fonds amplifient ou anticipent les tendances.

**Changement apporté :**
- `src/mais/collect/cftc_cot_collector.py` : collecteur complet (FIRST_YEAR=2009, code maïs 002602)
- `src/mais/features/__init__.py` : section 9 COT
- `src/mais/features/factors.py` : 3 nouvelles recettes COT (`factor_cot_speculative_pressure`, `factor_cot_commercial_hedge`, `factor_cot_open_interest_momentum`)

**Données obtenues :** 695 lignes, 2013-01-08 → 2026

**Résultats :** Pas encore mesurés (rebuild pas encore lancé post-palier)

**Décision :** En attente de rebuild

---

## EXP-003 — Palier 2b : EIA éthanol (proxy corn/oil)

**Date :** 2026-04 (session précédente)
**Statut :** TERMINÉ (partiel)
**Horizon(s) :** J+10, J+20

**Hypothèse :**
La demande éthanol (principal débouché industriel du maïs aux US : 35-40% de la production) devrait améliorer la prédiction sur J+10/J+20.

**Changement apporté :**
- `src/mais/collect/eia_ethanol_collector.py` : collecteur V2 EIA (échoue sans clé API)
- `src/mais/features/__init__.py` : proxy `ethanol_proxy_crush_margin = oil_price / corn_price` si EIA absent

**Problème rencontré :**
L'API EIA V2 avec DEMO_KEY retourne des données gasoline (WGFRPUS2 = gasoline, pas éthanol). L'éthanol nécessite une vraie clé API.

**Décision :** Proxy actif en attendant la clé API. Documenter dans le rapport.

---

## EXP-004 — Palier 3 : XGBoost + LightGBM dans benchmarks

**Date :** 2026-05 (session courante)
**Statut :** TERMINÉ
**Horizon(s) :** Tous

**Hypothèse :**
LightGBM et XGBoost devraient surpasser HGB et RF sur les facteurs synthétiques grâce à leurs regularisations plus flexibles et leurs interactions.

**Changement apporté :**
- `src/mais/study/professional.py` : `_model_specs()` étendu avec `lgbm_factors` et `xgb_factors`
- Imports optionnels via `try/except ImportError`

**Résultats :** Pas encore mesurés (rebuild pas encore lancé)

---

## EXP-005 — Palier 4 : SHAP réel via TreeExplainer

**Date :** 2026-05 (session courante)
**Statut :** TERMINÉ
**Horizon(s) :** Tous

**Hypothèse :**
Les coefficients Ridge ne mesurent pas l'importance réelle des facteurs. SHAP via TreeExplainer sur LightGBM donne les contributions réelles et capturent les non-linéarités.

**Changement apporté :**
- `src/mais/study/professional.py` : `_compute_shap_importance()` avec `shap.TreeExplainer`
- Priorité : LightGBM → XGBoost → abandon

**Résultats :** Pas encore mesurés

**Décision :** En attente de rebuild. La table d'implémentation passe de ❌ à ✅ uniquement après vérification que `shap_importance.parquet` est non vide.

---

## EXP-006 — Palier 5 : CQR (Conformalized Quantile Regression)

**Date :** 2026-05 (session courante)
**Statut :** TERMINÉ
**Horizon(s) :** Tous

**Hypothèse :**
Le split-conformal symétrique surestime les intervalles dans un sens et les sous-estime dans l'autre (asymétrie des mouvements de prix). CQR avec deux quantile regressors produit des intervalles asymétriques mieux calibrés.

**Changement apporté :**
- `src/mais/meta/cqr.py` : nouveau module complet
  - `CQRModel` : fit deux quantile LightGBM, calibre correction _e sur set de calibration
  - `walk_forward_cqr()` : évaluation walk-forward
- `src/mais/study/professional.py` :
  - `CQR_RESULTS_PARQUET` constant
  - `_build_cqr_results()` : appelle `walk_forward_cqr` pour chaque horizon
  - Câblé dans `build_professional_study()`

**Théorie :**
```
Score conformité : max(q_lo - y, y - q_hi)
Niveau quantile ajusté : (1-alpha) × (1 + 1/n_cal)
Correction : E = quantile(scores, q_level)
Garantie : P(y ∈ [q_lo-E, q_hi+E]) ≥ 1 - alpha
```

**Résultats :** Pas encore mesurés (rebuild requis)

---

## EXP-007 — Palier 6 : Markov-switching 3 états

**Date :** 2026-05 (session courante)
**Statut :** TERMINÉ
**Horizon(s) :** Tous (régime utilisé dans décision et métamodèle)

**Hypothèse :**
Les règles déterministes (score > 0.45 → bull) sont arbitraires et instables. Un modèle Markov-switching apprend les régimes statistiquement depuis les données.

**Changement apporté :**
- `src/mais/study/professional.py` : `_build_regimes()` refactorisé
  - Fit `MarkovRegression(k_regimes=3, switching_variance=True, trend='c')`
  - Identification des régimes par moyenne pondérée des returns
  - Fallback rule-based si convergence échoue ou < 500 observations

**Propriétés attendues du modèle :**
- Régime bull : return moyen journalier positif, variance faible
- Régime range : return moyen ≈ 0, variance modérée
- Régime bear : return moyen négatif, variance élevée ou faible

**Résultats :** Pas encore mesurés

---

## Expériences planifiées

| ID | Hypothèse | Priorité | Statut |
|---|---|---|---|
| EXP-008 | Rebuild complet post-paliers 1-6 | Critique | À lancer |
| EXP-009 | Ajouter Crop Progress dans features | Haute | À planifier |
| EXP-010 | Ajouter Drought Monitor dans features | Haute | À planifier |
| EXP-011 | Optuna sur LightGBM (vs hyperparams fixes) | Haute | À planifier |
| EXP-012 | Test modèle par saison (été vs hiver) | Moyenne | À planifier |
| EXP-013 | Métamodèle avec features de contexte régime | Moyenne | À planifier |
| EXP-014 | Backtest agriculteur complet | Haute | À planifier |
| EXP-015 | Obtenir clé EIA_API_KEY et intégrer éthanol réel | Haute | Externe |

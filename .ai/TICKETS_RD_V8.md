# TICKETS V8 — PROGRAMME R&D MAIS CBOT + EURONEXT

**Date** : 2026-05-30.
**Référence** : `docs/RECHERCHE_MAIS_REFLEXION_PRO_V8.md`, `docs/ROADMAP_EXPERIENCES_MAIS_V8.md`, `docs/DATA_SOURCES_MAIS_CBOT_EURONEXT_V8.md`.
**Règle d'or V8** : aucune expérience scientifique ne tourne tant que Phase A (infra méthodo) n'est pas DONE. Aucun artefact V0–V7 n'est supprimé.

---

## Index global

| Ticket | Phase | Statut | Niveau | Dépendances | Sujet |
|---|---|---|---|---|---|
| V8-INFRA-HOLDOUT | A | READY | complexe | — | Verrouillage physique du holdout 2024 |
| V8-INFRA-REGISTRY | A | READY | moyen | — | Unification registre V6+V7 → registry_unified |
| V8-INFRA-LEAKAGE | A | READY | moyen | V8-INFRA-HOLDOUT | Suite tests anti-leakage V8 étendue |
| V8-MT-BH-GLOBAL | A | BLOCKED | complexe | V8-INFRA-REGISTRY | Bilan FDR global par famille |
| V8-CALIBRATION-PLATT-ISO | A | READY | moyen | — | Comparaison Platt vs Isotonic |
| V8-FRAGILE-FLAGS-AUDIT | A | READY | simple | — | Marquer FRAGILE tous les résultats V0–V7 à n<100 ou AUC≥0.9 |
| V8-RULE-TRAIN-ONLY-AUDIT | A | READY | moyen | — | Audit seuils top20/top40 des V6/V7 strictement train-only |
| V8-RED-TEAM-PREMIUM | A | BLOCKED | critique | V8-FRAGILE-FLAGS-AUDIT | Red team formelle des pics V6/V7 FRAGILE |
| V8-META-REVALIDATION | B | BLOCKED | critique | V8-INFRA-HOLDOUT, V8-INFRA-REGISTRY, V8-MT-BH-GLOBAL | Revalidation V6 meta sous protocole V7 strict |
| V8-CROSS-TARGET-V3 | B | BLOCKED | critique | V8-META-REVALIDATION | Cross-target stacking corrigé (sur les bonnes cibles) |
| V8-CBOT-LAB-PLUS | C | BLOCKED | complexe | V8-META-REVALIDATION | Extension cibles CBOT (triple-barrier, conditionnels) |
| V8-EMA-PREMIUM-LAB-PLUS | C | BLOCKED | complexe | V8-META-REVALIDATION | Extension cibles EMA premium et basis |
| V8-EXPERTS-OOF | D | BLOCKED | complexe | V8-CROSS-TARGET-V3 | Bibliothèque d'experts OOF stricts (15+ targets) |
| V8-META-FEATURES-V3 | D | BLOCKED | moyen | V8-EXPERTS-OOF | Meta-features économiques avancées |
| V8-BASIS-REGIME-V3 | E | BLOCKED | complexe | V8-CROSS-TARGET-V3 | KMeans + GMM + HMM + Markov Switching sur basis |
| V8-SEASONAL-V3 | E | BLOCKED | complexe | V8-RULE-TRAIN-ONLY-AUDIT | Modèles experts par saison train-only stricts |
| V8-ROLL-FILTERS-V3 | E | BLOCKED | moyen | V8-EXPERTS-OOF | Filtres roll-aware DTE + OI + expected_gap |
| V8-DQ-V3 | E | BLOCKED | moyen | — | Data quality score complet |
| V8-FAIR-VALUE-V3 | E | BLOCKED | moyen | — | Fair value descriptif (audit V7-32) |
| V8-CROSS-MARKET-V3 | F | BLOCKED | complexe | V8-EXPERTS-OOF | Cross-market CBOT↔EMA systématique |
| V8-CAUSALITY-V3 | F | BLOCKED | complexe | V8-INFRA-REGISTRY | Granger BH + PCMCI (tigramite) + IV + RDD |
| V8-DISTRIB-V3 | G | BLOCKED | moyen | V8-EMA-PREMIUM-LAB-PLUS | CQR sur spread relatif, expected shortfall |
| V8-EVENT-STUDY-V3 | G | BLOCKED | moyen | — | Event study étendu, ajout MARS/FAM/CONAB |
| V8-PCORRECT-V3 | G | BLOCKED | complexe | V8-CALIBRATION-PLATT-ISO, V8-CROSS-TARGET-V3 | P(correct) Platt + features avancées |
| V8-BACKTEST-V3 | G | BLOCKED | critique | V8-PCORRECT-V3, V8-ROLL-FILTERS-V3 | Backtest stress 1/2/3/5/8 €/t + rolling 12m |
| V8-EMBARGO-ROBUSTNESS | A | READY | moyen | — | Sensibilité embargo {0,5,20,40,60,90,180j} |
| V8-HYPER-AUDIT | A | READY | simple | V8-INFRA-REGISTRY | Audit hyper-params : train-only ou OOF leak? |
| V8-INDICATOR-DESIGN-V2 | H | BLOCKED | moyen | V8-BACKTEST-V3 | Architecture indicateur, sans coder |
| V8-BOT-PAPER-DESIGN | H | BLOCKED | moyen | V8-INDICATOR-DESIGN-V2 | Design bot paper-trading research-only |
| V8-DECISION-UPDATE | H | BLOCKED | simple | V8-BACKTEST-V3 | Mise à jour `docs/DECISION_RECHERCHE_MAIS_V8.md` |

Total : 30 tickets V8.

---

## V8-INFRA-HOLDOUT — Verrouillage holdout 2024

**Niveau** : complexe.
**Phase** : A.
**Statut** : READY.

### Contexte
Aucun fichier `holdout_lock.json` n'existe physiquement sur le disque. Les artefacts V7 affirment `holdout_used: false` mais c'est purement déclaratif. Avant tout pas vers indicateur, le holdout 2024 doit être verrouillé physiquement.

### Objectif
Créer un mécanisme physique de verrouillage + assertion runtime.

### Fichiers à créer
- `src/mais/registry/holdout_lock.py` (lock + check + assert)
- `artefacts/v8/holdout_lock.json`
- `tests/test_v8_holdout_lock.py`

### Fichiers à lire
- `src/mais/registry/experiment_registry.py`
- `src/mais/paths.py`

### Fichiers interdits
- `data/` (ne pas lire)
- `notebooks/`

### Implémentation
```python
# src/mais/registry/holdout_lock.py
HOLDOUT_RANGE = ("2024-01-01", "2024-12-31")
HOLDOUT_LOCK_PATH = ARTEFACTS_DIR / "v8" / "holdout_lock.json"

def write_lock(dataset_path: Path) -> dict:
    """Calcule sha256 du dataset, écrit le lock, retourne le contenu."""
    ...

def assert_no_holdout(df: pd.DataFrame) -> None:
    """Vérifie qu'aucune date du DataFrame n'est dans HOLDOUT_RANGE.
    Raise HoldoutLeakageError sinon."""
    ...
```

### Critères de succès
- `holdout_lock.json` créé avec hash dataset + range + signature.
- `assert_no_holdout` appelé dans tous les modules V8.
- Tests unitaires : un test valide qui passe, un test invalide qui raise.
- Ruff PASS.

### Verdict
- DONE si artefact + tests verts.

---

## V8-INFRA-REGISTRY — Registre unifié V6+V7

**Niveau** : moyen.
**Phase** : A.
**Statut** : READY.

### Objectif
Fusionner `artefacts/experiments/experiment_registry_v6.csv` et `artefacts/registry/experiments.jsonl` en `artefacts/registry/experiments_unified.jsonl`, dédupliquer par `experiment_id`, conserver le `dataset_version`.

### Livrables
- `src/mais/registry/merge_v6_v7.py`
- `artefacts/registry/experiments_unified.jsonl`
- `tests/test_v8_registry_merge.py`
- `docs/V8_REGISTRY_MERGE.md` (compte rendu)

### Critère
- Pas de doublon `(experiment_id, dataset_version)`.
- Toutes les entrées V6 et V7 présentes.
- Champs alignés.

---

## V8-INFRA-LEAKAGE — Suite anti-leakage V8 étendue

**Niveau** : moyen.
**Phase** : A.
**Statut** : READY.
**Dépendance** : V8-INFRA-HOLDOUT.

### Objectif
Étendre `tests/test_v7_leakage.py` :
- Vérif `shift(1)` sur toutes les colonnes fundamentales.
- Vérif z-scores expanding sur train uniquement.
- Vérif holdout 2024 jamais touché.
- Vérif que les meta-features `pred_*_oof` ont une cohérence temporelle (test : `pred_at_t(t)` n'utilise pas `target(t+H)`).

### Livrables
- `tests/test_v8_anti_leakage.py`
- `docs/V8_ANTI_LEAKAGE_TESTS.md`

---

## V8-MT-BH-GLOBAL — Bilan FDR global par famille

**Niveau** : complexe.
**Phase** : A.
**Statut** : BLOCKED par V8-INFRA-REGISTRY.

### Objectif
Calculer p-values manquantes du registre, appliquer Benjamini-Hochberg par famille (CBOT, EMA premium, basis_extreme, seasonal, cross-market, distributional, backtest).

### Méthode
- AUC p-values via DeLong (Hanley & McNeil 1983).
- DA / Balanced Accuracy / Top20 via bootstrap 5000.
- BH par famille à α = 0.05, α = 0.10 (stricte/standard).
- `q_BH` ajouté à chaque entrée registry.

### Livrables
- `src/mais/research/multiple_testing_v8.py`
- `artefacts/v8/mt_bh_global.json`
- `docs/V8_MULTIPLE_TESTING.md` (table résultats par famille).

---

## V8-CALIBRATION-PLATT-ISO — Comparaison Platt vs Isotonic

**Niveau** : moyen.
**Phase** : A.
**Statut** : READY.

### Objectif
Comparer Platt scaling et Isotonic regression sur les meilleurs modèles V7 :
- premium H40 classic + meta
- premium H90 classic + meta
- CBOT direction H20/H60
- CBOT drawdown H20

### Métriques
- ECE par décile
- Brier score
- Reliability diagram
- Cox calibration test

### Livrables
- `src/mais/meta/calibration_v8.py`
- `artefacts/v8/calibration_platt_iso.json`

---

## V8-FRAGILE-FLAGS-AUDIT — Marquage FRAGILE systématique

**Niveau** : simple.
**Phase** : A.
**Statut** : READY.

### Objectif
Scanner tous les artefacts V0–V7 et ajouter un flag `fragile_review_required` = true si :
- n_oof < 100
- AUC > 0.90 avec n_oof < 200
- DA > 0.90 avec n_oof < 200
- top20 > 0.90 avec n_oof < 100

### Livrables
- `src/mais/research/fragile_flags_audit.py`
- `artefacts/v8/fragile_flags_audit.json`
- Mise à jour de tous les artefacts concernés (champ ajouté, pas supprimé).

---

## V8-RULE-TRAIN-ONLY-AUDIT — Audit seuils train-only

**Niveau** : moyen.
**Phase** : A.
**Statut** : READY.

### Objectif
Vérifier formellement que les seuils top20/top40 des V6/V7 (notamment V6 seasonal_expert AUC 0.98 n=68) sont **strictement train-only**.

### Méthode
- Re-exécuter V6 seasonal_expert avec seuils calibrés walk-forward expansif.
- Comparer AUC train-only vs original.
- Si delta > 5 points → résultat marqué `THRESHOLD_INSAMPLE_LEAKAGE`.

### Livrables
- `artefacts/v8/rule_train_only_audit.json`

---

## V8-RED-TEAM-PREMIUM — Red team formelle

**Niveau** : critique.
**Phase** : A.
**Statut** : BLOCKED par V8-FRAGILE-FLAGS-AUDIT.

### Objectif
Pour chaque résultat marqué FRAGILE ou SUSPECT par §4–§6 de la réflexion V8, appliquer :
- Permutation des labels (1000 perms, distribution AUC nulle)
- Shuffle dates 7j
- Perturbation seuils ±10%
- Holdout temporel synthétique (mask 6 mois aléatoires, 100 répétitions)

### Verdict
- `RED_TEAM_PASS` : AUC empirique > p95 distribution nulle.
- `RED_TEAM_FAIL` : sinon. Le résultat est alors marqué comme **non utilisable** dans toute conclusion future.

### Livrables
- `src/mais/research/red_team_v8.py`
- `artefacts/v8/red_team_premium.json`
- `docs/V8_RED_TEAM_REPORT.md`

---

## V8-META-REVALIDATION — Revalidation V6 meta sous V7 strict

**Niveau** : critique.
**Phase** : B.
**Statut** : BLOCKED par V8-INFRA-HOLDOUT + V8-INFRA-REGISTRY + V8-MT-BH-GLOBAL.

### Détail
Voir `docs/RECHERCHE_MAIS_REFLEXION_PRO_V8.md §13`.

### Fichiers à créer
- `src/mais/meta/meta_revalidation_v8.py`
- `artefacts/v8/meta_revalidation.json`
- `docs/V8_META_REVALIDATION.md`
- `tests/test_v8_meta_revalidation.py`

### Fichiers à lire
- `src/mais/research/meta_model_premium_v6.py` (source originale V6)
- `src/mais/meta/nested_stacking.py` (V7 nested protocole)
- `artefacts/v6/meta_model_premium_v6.json` (résultats V6 référence)

### Cibles
- `y_rel_outperform_h40`
- `y_rel_outperform_h90`
- `y_rel_outperform_when_basis_extreme_h40` (FRAGILE flag attendu)
- `y_rel_outperform_when_basis_extreme_h90` (FRAGILE flag attendu)

### Build de features step
- Construire explicitement les cibles `y_rel_outperform_*` dans le dataset avant de lancer le module (fix de la limite V7-03).

### Combinaisons × Protocoles : 8 × 8 = 64 expériences.

### Verdict global
Selon §13 :
- ROBUST / USEFUL_BUT_OVERSTATED / FRAGILE / OVERFIT_OR_LEAKAGE / NO_GO.

---

## V8-CROSS-TARGET-V3 — Cross-target stacking propre

**Niveau** : critique.
**Phase** : B.
**Statut** : BLOCKED par V8-META-REVALIDATION.

### Différence avec V7-03
- Construction garantie de `y_rel_outperform_h40/h90` dans le dataset (pas de fallback).
- 15+ base learners au lieu de 4.
- Meta-features économiques (cf roadmap §C).
- Comparaison directe `règle économique vs ML`.

### Livrables
- `src/mais/meta/cross_target_v3.py`
- `artefacts/v8/cross_target_stacking_v3.json`
- `docs/V8_CROSS_TARGET_STACKING_V3.md`

---

## V8-CBOT-LAB-PLUS — CBOT Target Lab étendu

**Niveau** : complexe.
**Phase** : C.
**Statut** : BLOCKED par V8-META-REVALIDATION.

### Cibles nouvelles
Voir roadmap §A.

### Livrables
- `src/mais/research/cbot_target_lab_v8.py`
- `artefacts/v8/cbot_target_lab_plus.json`

---

## V8-EMA-PREMIUM-LAB-PLUS — EMA Premium Lab étendu

**Niveau** : complexe.
**Phase** : C.
**Statut** : BLOCKED par V8-META-REVALIDATION.

### Cibles nouvelles
Voir roadmap §B.

### Livrables
- `src/mais/research/ema_premium_lab_v8.py`
- `artefacts/v8/ema_premium_target_lab_plus.json`

---

## V8-EXPERTS-OOF — Bibliothèque d'experts OOF

**Niveau** : complexe.
**Phase** : D.
**Statut** : BLOCKED par V8-CROSS-TARGET-V3.

### Objectif
Construire **un module unique** qui :
- Charge le dataset (avec assert no holdout).
- Génère 15+ séries OOF (cf roadmap §C experts niveau 0).
- Sauvegarde dans `data/processed/experts_oof_v8.parquet`.
- Enregistre chaque expert dans le registry.

### Livrables
- `src/mais/research/experts_oof_v8.py`
- `data/processed/experts_oof_v8.parquet`
- `artefacts/v8/experts_oof_summary.json`

---

## V8-META-FEATURES-V3 — Meta-features économiques

**Niveau** : moyen.
**Phase** : D.
**Statut** : BLOCKED par V8-EXPERTS-OOF.

### Livrables
- `src/mais/features/meta_features_v8.py`
- `data/processed/meta_features_v8.parquet`

---

## V8-BASIS-REGIME-V3

**Niveau** : complexe.
**Phase** : E.
**Statut** : BLOCKED par V8-CROSS-TARGET-V3.

### Méthodes
KMeans (k=4–7) + GMM (k=4–6) + HMM (3–4 états) + Markov Switching.

### Livrables
- `src/mais/research/basis_regimes_v8.py`
- `artefacts/v8/basis_regimes_v3.json`

---

## V8-SEASONAL-V3

**Niveau** : complexe.
**Phase** : E.
**Statut** : BLOCKED par V8-RULE-TRAIN-ONLY-AUDIT.

### Saisons
jan-mar, apr-jun, jul-aug, sep-nov, dec.

### Livrables
- `src/mais/research/seasonal_experts_v8.py`
- `artefacts/v8/seasonal_experts_v3.json`

---

## V8-ROLL-FILTERS-V3

**Niveau** : moyen.
**Phase** : E.
**Statut** : BLOCKED par V8-EXPERTS-OOF.

### Livrables
- `src/mais/features/roll_aware_v8.py`
- `artefacts/v8/roll_aware_premium_v3.json`

---

## V8-DQ-V3

**Niveau** : moyen.
**Phase** : E.
**Statut** : READY.

### Livrables
- `src/mais/features/data_quality_v8.py`
- `artefacts/v8/data_quality_v3.json`

---

## V8-FAIR-VALUE-V3

**Niveau** : moyen.
**Phase** : E.
**Statut** : READY.

### Objectif
Audit du V7-32 NO_GO : conserver comme **descriptif** dans rapport, pas comme prédicteur.

### Livrables
- `src/mais/research/fair_value_v8.py`
- `artefacts/v8/fair_value_v3.json`

---

## V8-CROSS-MARKET-V3

**Niveau** : complexe.
**Phase** : F.
**Statut** : BLOCKED par V8-EXPERTS-OOF.

### Livrables
- `src/mais/research/cross_market_v8.py`
- `artefacts/v8/cross_market_v3.json`

---

## V8-CAUSALITY-V3

**Niveau** : complexe.
**Phase** : F.
**Statut** : BLOCKED par V8-INFRA-REGISTRY.

### À installer (optionnel mais préféré)
- `tigramite` pour PCMCI (sinon fallback Granger bivariate).

### Livrables
- `src/mais/research/causality_v8.py`
- `artefacts/v8/causality_v3.json`
- `docs/V8_CAUSALITY_GRAPH.md`

---

## V8-DISTRIB-V3

**Niveau** : moyen.
**Phase** : G.
**Statut** : BLOCKED par V8-EMA-PREMIUM-LAB-PLUS.

### Différence V7-35
- Cible : spread relatif EMA/CBOT (pas EMA brut).
- CQR sur calibration set séparé.

### Livrables
- `src/mais/research/distributional_v8.py`
- `artefacts/v8/distributional_v3.json`

---

## V8-EVENT-STUDY-V3

**Niveau** : moyen.
**Phase** : G.
**Statut** : READY.

### Livrables
- `src/mais/research/event_study_v8.py`
- `artefacts/v8/event_study_v3.json`

---

## V8-PCORRECT-V3

**Niveau** : complexe.
**Phase** : G.
**Statut** : BLOCKED par V8-CALIBRATION-PLATT-ISO + V8-CROSS-TARGET-V3.

### Livrables
- `src/mais/meta/p_correct_v8.py`
- `artefacts/v8/p_correct_v3.json`

---

## V8-BACKTEST-V3

**Niveau** : critique.
**Phase** : G.
**Statut** : BLOCKED par V8-PCORRECT-V3 + V8-ROLL-FILTERS-V3.

### Stress test obligatoire
Coûts 1/2/3/5/8 €/t × slippage 1/2 €/t × leave-one-year-out × rolling 12m.

### Verdict toujours `RESEARCH_ONLY_NOT_TRADING`.

### Livrables
- `src/mais/research/backtests_v8.py`
- `artefacts/v8/backtests_v3.json`
- `docs/V8_BACKTESTS_V3.md`

---

## V8-EMBARGO-ROBUSTNESS

**Niveau** : moyen.
**Phase** : A.
**Statut** : READY.

### Objectif
Sensibilité embargo {0, 5, 20, 40, 60, 90, 180 jours} sur premium H40/H90.

### Livrables
- `artefacts/v8/embargo_robustness.json`

---

## V8-HYPER-AUDIT

**Niveau** : simple.
**Phase** : A.
**Statut** : BLOCKED par V8-INFRA-REGISTRY.

### Objectif
Auditer comment les hyper-params V6/V7 ont été choisis : sur train ? sur OOF ? leakage potentiel ?

### Livrables
- `artefacts/v8/hyper_audit.json`

---

## V8-INDICATOR-DESIGN-V2

**Niveau** : moyen.
**Phase** : H.
**Statut** : BLOCKED par V8-BACKTEST-V3.

### Objectif
Architecture indicateur hybride (cf roadmap §16 réflexion V8). **Pas de code**, juste design + interfaces.

### Livrables
- `docs/V8_INDICATOR_DESIGN_V2.md`

---

## V8-BOT-PAPER-DESIGN

**Niveau** : moyen.
**Phase** : H.
**Statut** : BLOCKED par V8-INDICATOR-DESIGN-V2.

### Objectif
Design d'un bot paper-trading research-only : journal de signaux, simulateur avec coûts, monitoring, alerts, dashboard. **Pas de code**.

### Livrables
- `docs/V8_BOT_PAPER_DESIGN.md`

---

## V8-DECISION-UPDATE

**Niveau** : simple.
**Phase** : H.
**Statut** : BLOCKED par V8-BACKTEST-V3.

### Objectif
Mettre à jour `docs/DECISION_RECHERCHE_MAIS_V8.md` avec les conclusions finales.

---

## RÈGLES DE TRAVAIL V8

1. **Aucun ticket V8 ne tourne tant que Phase A n'est pas DONE.**
2. Toute expérience produit : code (`src/mais/...`), artefact JSON (`artefacts/v8/...`), entry registry, test unitaire, mise à jour doc (si nouveau résultat important).
3. Tout résultat `AUC ≥ 0.85 avec n < 200` est marqué `FRAGILE_REVIEW_REQUIRED` et passe par V8-RED-TEAM.
4. Backtests jamais affichés comme tradables. Toujours `RESEARCH_ONLY_NOT_TRADING`.
5. Notebook agent interdit (règle projet).
6. Aucun artefact V0–V7 n'est supprimé. V8 augmente, ne remplace pas.
7. Imports optionnels (`tigramite`, `shap`, `lightgbm`, `xgboost`) dans try/except.
8. Ruff PASS, pytest PASS exigés pour chaque ticket DONE.
9. Toute prédiction utilisée comme feature DOIT être OOF strict (assertion runtime).
10. Holdout 2024 jamais accédé sans appel explicite à `unlock_holdout_2024(human_signature=...)` (à définir).

---

## Sortie attendue de V8

Trois scénarios possibles :

### Scénario 1 — META_PREMIUM_ROBUST
Le meta-model V6 survit aux protocoles stricts V7 → l'étude passe en `RESEARCH_COMPLETE_INDICATOR_DESIGN_READY`. V8-INDICATOR-DESIGN-V2 et V8-BOT-PAPER-DESIGN livrés. Pas de bot réel sans 6 mois paper.

### Scénario 2 — USEFUL_BUT_OVERSTATED / FRAGILE
AUC réelle entre 0.70 et 0.85, gain modeste. → indicateur **hybride règle + meta avec poids modeste**, abstention forte. Pas de bot avant V9.

### Scénario 3 — OVERFIT_OR_LEAKAGE / NO_GO
Tout le travail V6 est invalidé en strict. → on revient à V5 + corrections V8 (basis rule + season + roll + DQ + Pcorrect) sans meta-model lourd. Pas d'indicateur prêt.

---

*Document V8 — programme tickets — 2026-05-30.*

# Tickets — Etude Mais

## Statuts autorisés

- `READY` — prêt à être pris (toutes les dépendances sont DONE)
- `IN_PROGRESS` — en cours
- `NEEDS_REVIEW` — terminé, en attente de review
- `DONE` — validé après review
- `BLOCKED` — bloqué par une dépendance externe (clé API, donnée manquante)
- `DEFERRED_PHASE1` — reporté à Phase 1, après Phase 0 complète
- `DEFERRED_PHASE4` — reporté à Phase 4 (AutoML)
- `DEFERRED_PHASE5` — reporté à Phase 5 (pipeline quotidien)
- `REJECTED` — refusé

## Règle de prise de ticket

Un agent prend seulement un ticket `READY` dont toutes les dépendances sont `DONE`.
Le ticket doit finir en `NEEDS_REVIEW`. Seule une review peut le passer en `DONE`.

## Convention des chemins

Ne jamais inventer un chemin. Toujours utiliser les chemins réels définis dans `src/mais/paths.py` :

| Fichier | Chemin réel |
|---|---|
| features | `data/processed/features.parquet` |
| targets | `data/processed/targets.parquet` |
| factors | `data/processed/factors.parquet` |
| model_benchmarks | `artefacts/professional_study/model_benchmarks.parquet` |
| model_predictions | `artefacts/professional_study/model_predictions.parquet` |
| shap_importance | `artefacts/professional_study/shap_importance.parquet` |
| cqr_results | `artefacts/professional_study/cqr_results.parquet` |
| regime_timeseries | `artefacts/professional_study/regime_timeseries.parquet` |
| decision_snapshot | `artefacts/professional_study/decision_snapshot.json` |
| anti-leakage audit | `data/metadata/anti_leakage_audit.parquet` |

## Règle sur les fichiers data/ et artefacts/

**Interdit** de modifier manuellement `data/` et `artefacts/`.
**Autorisé** de les régénérer uniquement via les commandes officielles :
- `make features` → régénère `data/processed/features.parquet`
- `make study` → régénère tous les artefacts de `artefacts/professional_study/`
- `make audit` → régénère `data/metadata/anti_leakage_audit.parquet`
- `make collect` → régénère `data/interim/*.parquet`

## Agents recommandés

| Agent | Rôle |
|---|---|
| `Claude Code` | Tickets complexes/critiques, planification, review |
| `Code Review Graph` | Cartographie des fichiers liés (tickets moyens/complexes/critiques) |
| `Caveman` | Résumé court, mini-review, update `STATE.md` |

## Modèle de ticket

### TICKET-XXX — Titre

- Statut : `READY`
- Difficulté : `simple | moyen | complexe | critique`
- Agent recommandé : `Claude Code | Caveman`
- Dépendances : aucune ou `TICKET-XXX`

**Objectif :**

**Fichiers à modifier :**

**Fichiers à lire :**

**Fichiers interdits (modification manuelle) :**

**Critères de réussite :**

**Vérifications à lancer :**

**Risques :**

---

## Ordre strict d'exécution

```
Phase 0 (obligatoire avant tout) :
  TICKET-R01 → review → TICKET-R02 → review → TICKET-R03 → review

Phase 1 (après Phase 0 complète) :
  TICKET-D01, TICKET-D02, TICKET-D04 (parallélisables)
  TICKET-M01, TICKET-M02, TICKET-M03 (après Phase 0)

Phase 4 : TICKET-P01 → TICKET-P02 → TICKET-P03
Phase 5 : TICKET-Q01
```

Ne jamais sauter une Phase. Ne jamais prendre un ticket DEFERRED_PHASE1 avant que tous les tickets R0x soient DONE.

---

## Tickets actifs — Phase 0

---

### TICKET-R01 — Rebuild features.parquet avec données COT

- **Statut :** `NEEDS_REVIEW`
- **Difficulté :** `simple`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** aucune (COT câblé dans `build_features()`, `data/interim/cftc_cot.parquet` doit exister)

**Objectif :** Relancer `make features` pour intégrer les colonnes COT dans `data/processed/features.parquet`. Vérifier la présence de `cot_mm_net` et l'absence d'erreur anti-leakage.

**Fichiers à modifier :** aucun (déjà câblé)

**Fichiers à lire :** `src/mais/features/__init__.py`, `src/mais/collect/cftc_cot_collector.py`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `data/processed/features.parquet` régénéré sans erreur
- `cot_mm_net` présent dans les colonnes
- `make audit` passe sans erreur de leakage sur les colonnes COT

**Vérifications à lancer :**
```bash
make features
make audit
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/features.parquet')
print('cot_mm_net present:', 'cot_mm_net' in df.columns)
print('Shape:', df.shape)
"
```

**Risques :** Si `data/interim/cftc_cot.parquet` n'existe pas, lancer `make collect` d'abord. `make features` écrase l'ancien features.parquet — pas de rollback automatique.

**Résultat ticket (2026-05-09) :**
- `make features` PASS — `features.parquet` régénéré en `(6192, 306)`.
- `cot_mm_net` présent, 56 colonnes `cot_*`, 3152 valeurs non nulles sur `cot_mm_net`.
- `make audit` PASS — `future_dep=0`, `perfect_fit=0`, `naming=0`.
- Ticket prêt pour review, non passé en `DONE` conformément à la règle.

---

### TICKET-R02 — Rebuild study complet post-paliers 1–6

- **Statut :** `READY`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R01` DONE

**Objectif :** Lancer `make study` et vérifier que tous les artefacts des paliers 1–6 sont produits, non vides et cohérents. Mesurer les vrais résultats pour la première fois.

**Fichiers à modifier :** aucun (si tout fonctionne — corrections de bugs uniquement si nécessaire)

**Fichiers à lire :** `src/mais/study/professional.py`, `src/mais/meta/cqr.py`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `artefacts/professional_study/shap_importance.parquet` non vide (≥ 1 ligne)
- `artefacts/professional_study/cqr_results.parquet` couverture empirique ≥ 88%
- `artefacts/professional_study/regime_timeseries.parquet` contient les 3 labels (bull/range/bear)
- `artefacts/professional_study/model_benchmarks.parquet` non vide
- Rapport `docs/PROFESSIONAL_STUDY_REPORT.md` généré sans exception

**Vérifications à lancer :**
```bash
make study
python -c "
import pandas as pd
cqr = pd.read_parquet('artefacts/professional_study/cqr_results.parquet')
print('CQR coverage:', round(cqr['covered'].mean(), 3), '(objectif >=0.88)')
reg = pd.read_parquet('artefacts/professional_study/regime_timeseries.parquet')
print('Regimes distincts:', sorted(reg['regime'].unique()))
shap = pd.read_parquet('artefacts/professional_study/shap_importance.parquet')
print('SHAP rows:', len(shap))
bm = pd.read_parquet('artefacts/professional_study/model_benchmarks.parquet')
print('Models evaluated:', list(bm['model'].unique()) if 'model' in bm.columns else bm.shape)
"
```

**Risques :** MarkovRegression peut échouer si < 500 obs ou non-convergence → fallback rule-based actif, vérifier les logs. LightGBM/XGBoost optionnels — ne pas bloquer si absents.

---

### TICKET-R03 — Mettre à jour table d'implémentation dans le rapport

- **Statut :** `READY`
- **Difficulté :** `simple`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Corriger la table ✅/❌/⚠️ dans `_write_report()` pour qu'elle reflète exactement les vrais résultats mesurés après TICKET-R02. Aucun ✅ non mérité.

**Fichiers à modifier :** `src/mais/study/professional.py` (section `impl_status` dans `_write_report()`)

**Fichiers à lire :** `docs/PROFESSIONAL_STUDY_REPORT.md` (rapport généré par TICKET-R02)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- Chaque ✅ dans le rapport correspond à un artefact non vide vérifié
- Les fonctionnalités non encore testées sont ❌ ou ⚠️
- COT : distinguer ✅ collecte / ⚠️ features / ⚠️ impact mesuré
- Rapport re-généré avec la table corrigée

**Vérifications à lancer :**
```bash
grep -A 40 "impl_status\|État réel" docs/PROFESSIONAL_STUDY_REPORT.md | head -50
make study
```

**Risques :** aucun.

---

## Tickets actifs — Phase 1 (DEFERRED_PHASE1)

*Débloqués uniquement après que TICKET-R01, R02, R03 sont tous DONE.*

---

### TICKET-D01 — Intégrer Crop Progress dans features

- **Statut :** `DEFERRED_PHASE1`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Collecter le Crop Progress NASS hebdomadaire, câbler dans `build_features()`, créer le facteur `factor_crop_condition_pressure`.

**Fichiers à modifier :**
- `src/mais/collect/nass_quickstats_collector.py`
- `src/mais/features/__init__.py`
- `src/mais/features/factors.py`

**Fichiers à lire :** `src/mais/features/factors.py`, `.ai/CODEX.md` (famille weather_belt_stress)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `condition_gd_ex_pct` présent dans `data/processed/features.parquet`
- `factor_crop_condition_pressure` présent dans `data/processed/factors.parquet`
- Anti-leakage passé (`shift(1)` sur données hebdo, NaN hors-saison acceptés)

**Risques :** Données NASS disponibles seulement mai–oct — NaN hors-saison attendus, ne pas forwardfiller au-delà de 7 jours.

---

### TICKET-D02 — Intégrer Drought Monitor dans features

- **Statut :** `DEFERRED_PHASE1`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Câbler `drought_monitor_collector.py` dans `build_features()`, créer le facteur `factor_drought_severity`.

**Fichiers à modifier :**
- `src/mais/features/__init__.py`
- `src/mais/features/factors.py`

**Fichiers à lire :** `src/mais/collect/drought_monitor_collector.py`, `.ai/CODEX.md`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `drought_composite` présent dans `data/processed/features.parquet`
- `factor_drought_severity` présent dans `data/processed/factors.parquet`
- Anti-leakage passé (forward-fill hebdo → journalier avec `shift(1)`)

**Risques :** Alignement hebdo → journalier critique — forward-fill max 7 jours puis NaN.

---

### TICKET-D03 — EIA éthanol avec vraie clé API

- **Statut :** `BLOCKED`
- **Difficulté :** `simple`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** clé `EIA_API_KEY` réelle (eia.gov/opendata)

**Objectif :** Corriger les Series IDs EIA dans `config/sources.yaml`, tester avec `EIA_API_KEY` réelle, désactiver le proxy corn/oil.

**Fichiers à modifier :**
- `config/sources.yaml`
- `src/mais/collect/eia_ethanol_collector.py`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `ethanol_production_kbd` dans `data/processed/features.parquet` avec vraies données EIA
- Proxy corn/oil désactivé dans le code

**Risques :** Bloqué sans clé API — ne pas débloquer sans la clé.

---

### TICKET-D04 — Intégrer FAS Export Sales dans features

- **Statut :** `DEFERRED_PHASE1`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Compléter `fas_export_sales_collector.py`, câbler dans `build_features()`, créer le facteur `factor_export_demand_surprise`.

**Fichiers à modifier :**
- `src/mais/collect/fas_export_sales_collector.py`
- `src/mais/features/__init__.py`
- `src/mais/features/factors.py`

**Fichiers à lire :** `src/mais/features/factors.py`, `.ai/CODEX.md` (famille wasde_supply_demand)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `export_sales_mt` dans `data/processed/features.parquet`
- `factor_export_demand_surprise` calculé (z-score de la déviation vs moyenne historique)
- Anti-leakage passé (`shift(1)` sur les données hebdo publiées le jeudi)

**Risques :** Publication FAS le jeudi → `shift(1)` obligatoire pour éviter le leakage de la semaine courante.

---

### TICKET-M01 — Câbler Optuna dans l'étude maïs

- **Statut :** `DEFERRED_PHASE1`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Intégrer `optimize/runner.py` dans `build_professional_study()` pour optimiser LightGBM via Optuna sur le walk-forward.

**Fichiers à modifier :**
- `src/mais/study/professional.py`
- `src/mais/optimize/runner.py`

**Fichiers à lire :** `src/mais/optimize/runner.py`, `src/mais/study/professional.py`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- LightGBM optimisé évalué honnêtement vs défauts — amélioration mesurée, même si nulle
- Flag `optimize=False` par défaut dans `build_professional_study()` pour ne pas bloquer le build normal
- Résultats Optuna loggés dans `artefacts/professional_study/`

**Risques :** Optuna rallonge le build — flag désactivé par défaut obligatoire.

---

### TICKET-M02 — Backtest agriculteur complet

- **Statut :** `DEFERRED_PHASE1`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Compléter `decision/backtest.py` avec les 6 stratégies, capture rate, coûts de stockage. Mesurer honnêtement — même si MODEL_SIGNAL ne bat pas SELL_HARVEST, le résultat est scientifiquement valide.

**Fichiers à modifier :** `src/mais/decision/backtest.py`

**Fichiers à lire :** `src/mais/decision/backtest.py`, `docs/00_PROJET_COMPLET_MAIS.md` (section 11)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `FARMER_BACKTEST_REPORT.md` généré avec capture rate mesuré sur 10+ ans
- 6 stratégies évaluées : SELL_HARVEST, STORE_3M, STORE_6M, MODEL_SIGNAL, CQR_OPTIMAL, BENCHMARK_AVG
- Métrique principale : `price_obtained / annual_max_price` documentée honnêtement
- Hypothèses de coût de stockage explicites dans le rapport

**Risques :** Ne pas fixer comme critère que le modèle batte la baseline — mesurer et documenter le résultat réel.

---

### TICKET-M03 — Ajouter baselines seasonal naive et momentum

- **Statut :** `DEFERRED_PHASE1`
- **Difficulté :** `simple`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Ajouter `baseline_historical_mean` et `baseline_seasonal_naive` dans `_model_specs()` de `professional.py`.

**Fichiers à modifier :** `src/mais/study/professional.py`

**Fichiers à lire :** `src/mais/study/professional.py` (fonction `_model_specs()`)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- Les 2 baselines apparaissent dans `artefacts/professional_study/model_benchmarks.parquet`
- Seasonal naive = prix moyen du même mois sur les 5 années précédentes (expanding window)
- Momentum = retour rolling 20j, anti-leakage avec `shift(1)`

**Risques :** aucun.

---

## Tickets actifs — Phase 4 (DEFERRED_PLATFORM)

*Débloqués uniquement après Phase 0 + Phase 1 complètes.*

---

### TICKET-P01 — Profiler CSV générique

- **Statut :** `DEFERRED_PHASE4`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** Phase 0 et 1 complètes

**Objectif :** Créer `src/mais/platform/profiler.py` — détection automatique du type de problème parmi les 6 types AutoML (régression, classification binaire, classification multi-classe, série temporelle univariée, série temporelle multivariée, ranking).

---

### TICKET-P02 — Preprocessing générique

- **Statut :** `DEFERRED_PHASE4`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-P01` DONE

**Objectif :** Créer `src/mais/platform/preprocessing.py` — pipeline configurable (lags si temporel, encodage si catégoriel, imputation, scaling).

---

### TICKET-P03 — Rapport AutoML générique

- **Statut :** `DEFERRED_PHASE4`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-P01` DONE, `TICKET-P02` DONE

**Objectif :** Créer `src/mais/platform/reporting.py` — rapport Markdown automatique avec benchmark, SHAP, limites identifiées.

---

## Tickets actifs — Phase 5 (DEFERRED_PIPELINE)

---

### TICKET-Q01 — Compléter ops/daily.py

- **Statut :** `DEFERRED_PHASE5`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** Phase 0–3 complètes

**Objectif :** Collecte incrémentale quotidienne + rapport quotidien + validation des prédictions passées.

**Fichiers à modifier :** `src/mais/ops/daily.py`

---

## Tickets terminés

*(Aucun pour l'instant)*

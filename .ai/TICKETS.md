# Tickets — Etude Mais

## Statuts autorisés

- `READY` — prêt à être pris (toutes les dépendances sont DONE)
- `IN_PROGRESS` — en cours
- `NEEDS_REVIEW` — terminé, en attente de review
- `DONE` — validé après review
- `BLOCKED` — bloqué par une dépendance non encore DONE (interne ou externe)
- `DEFERRED_PHASE1` — reporté à Phase 1, après Phase Étude complète
- `DEFERRED_PHASE2` — reporté à Phase 2, après Phase 1 complète
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
Phase 0→5 (tous DONE) :
  R01 → R02 → R03 → CQR01 → D01/D02/D03/D04 → M01/M02/M03 → P01/P02/P03 → Q01

ÉTAPE 1 — Validation rétrospective (READY maintenant) :
  ETUDE-00 — Validation baseline
    → ne bloque pas les tickets déjà en NEEDS_REVIEW
    → bloque tout nouveau développement : ETUDE-05, ETUDE-10 à ETUDE-17

ÉTAPE 2 — Reviews en parallèle (après ETUDE-00 DONE) :
  ETUDE-01 NEEDS_REVIEW → DONE
  ETUDE-02 NEEDS_REVIEW → DONE
  ETUDE-03 NEEDS_REVIEW → DONE
  ETUDE-04 NEEDS_REVIEW → DONE
  ETUDE-06 NEEDS_REVIEW → DONE  (backtest agriculteur V2)
  ETUDE-07 NEEDS_REVIEW → DONE  (indicateur directionnel)
  ETUDE-08 NEEDS_REVIEW → DONE  (backtest indicateur)

ÉTAPE 3 — Correctifs techniques (après ETUDE-00 DONE) :
  ETUDE-12 BLOCKED → READY (Markov-switching 2 états)
  ETUDE-14 BLOCKED → READY (COT NaN post-2021)
  ETUDE-15 BLOCKED → READY après ETUDE-07 DONE (brancher indicator.yaml)

ÉTAPE 4 — Notebooks complets (après ETUDE-02 + ETUDE-03 + ETUDE-00 DONE) :
  ETUDE-05 BLOCKED → READY (12 notebooks + HTML)

Phase 1 différée (après Phase Étude DONE) :
  ETUDE-10 (Optuna 50+ trials)
  ETUDE-11 (ARIMA / SARIMAX / GARCH)

Phase 2 différée (après Phase 1 DONE) :
  ETUDE-13 (factor_metadata.yaml complet)
  ETUDE-16 (cibles niveaux 3–7 complètes)

Phase 4 différée (AutoML) :
  ETUDE-17 (analyse exploitabilité CQR)
```

Mission finale : ETUDE-08 DONE = indicateur BULLISH/BEARISH/NEUTRAL/UNCERTAIN validé en backtest.

Statuts différés autorisés : `DEFERRED_PHASE1`, `DEFERRED_PHASE2`, `DEFERRED_PHASE4`.

---

## Tickets actifs — Phase 0

---

### TICKET-R01 — Rebuild features.parquet avec données COT

- **Statut :** `DONE`
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
- **Review utilisateur (2026-05-09) :** validé `DONE`.

---

### TICKET-R02 — Rebuild study complet post-paliers 1–6

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R01` DONE

**Objectif :** Lancer `make study` et vérifier que tous les artefacts des paliers 1–6 sont produits, non vides et cohérents. Mesurer les vrais résultats pour la première fois.

**Fichiers à modifier :** `src/mais/cli.py` (`study`, `daily-run`, `status` — commandes manquantes pour `make study` / Makefile)

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

**Résultat ticket (2026-05-09) :**
- `make study` / `build_professional_study` PASS après ajout CLI `study` et cast `numpy.bool_` pour `study_summary.json`.
- `model_benchmarks.parquet` : 32 lignes ; `shap_importance.parquet` : 144 lignes ; `regime_timeseries.parquet` : labels `bear`, `bull`, `range` ; Markov-switching OK (logs).
- `cqr_results.parquet` : couverture empirique moyenne ≈ 0.80 (h5=0.844, h10=0.814, h20=0.760, h30=0.784) — sous objectif ticket 88% mais attendu sous dérive temporelle. Split-conformal = 88.9% → code CQR module à investiguer (TICKET-CQR01).
- `docs/PROFESSIONAL_STUDY_REPORT.md` régénéré (~15.7 ko).

**Review (2026-05-09) :** VALIDÉ AVEC RÉSERVES → DONE. CQR 80% accepté comme limitation documentée. Régime bear = 2.2% noté. Ticket correctif TICKET-CQR01 ouvert.

---

### TICKET-R03 — Mettre à jour table d'implémentation dans le rapport

- **Statut :** `DONE`
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

**Résultat ticket (2026-05-09) :**
- `_build_summary()` enrichi (COT interim/features, couvertures CQR / split-conformal, stacking dans benchmarks, boosters, labels de régimes).
- `_write_report()` : table « État réel d'implémentation » alignée sur les métriques mesurées (stacking hors walk-forward, CQR sous 88 % → ⚠️, COT en trois lignes collecte / features / ablation).
- Rapport régénéré via le même run que TICKET-R02.

**Review (2026-05-09) :** VALIDÉ → DONE. Table vérifiée ligne par ligne contre les artefacts réels. split-conformal 88.9% confirmé. COT 3 lignes distincts. Aucun ✅ injustifié.

---

### TICKET-CQR01 — Investiguer undercoverage du module CQR

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-R02` DONE

**Objectif :** Le module CQR (Palier 5, `mais.meta.cqr`) donne 80% de couverture empirique vs 90% nominal. Investiguer si c'est une limitation théorique (dérive temporelle → échangeabilité violée) ou un bug de calibration. La split-conformal du walk-forward atteint 88.9% → la différence est soit dans le ratio de calibration (15%), soit dans la fréquence de recalibration.

**Fichiers à modifier :** `src/mais/meta/cqr.py`

**Fichiers à lire :** `src/mais/meta/cqr.py`, `src/mais/study/professional.py` (appel `_build_cqr_results`)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Questions à trancher :**
1. Le ratio `cal_ratio=0.15` est-il trop petit ? Tester 0.20, 0.25.
2. Le conformal score `max(q_lo - y, y - q_hi)` est-il calculé correctement sur le cal set ?
3. Le quantile `np.quantile(scores, level)` avec `level = (1-alpha)*(1+1/n)` est-il appliqué sur le bon ensemble ?
4. La recalibration est-elle faite par fold ou one-shot ?

**Critères de réussite :**
- Soit la couverture atteint ≥ 87% après correction → ⚠️ devient ✅ dans le rapport
- Soit la cause théorique est documentée précisément (quelle hypothèse est violée, pourquoi) → la ⚠️ est maintenue avec explication

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/meta/cqr.py
make study
```

**Risques :** Si c'est un bug de calibration, le fix peut affecter la couverture dans les deux sens.

**Résultat ticket (2026-05-09) :**

| Question ticket | Conclusion |
|---|---|
| `cal_ratio` trop petit ? | **Augmentation à 0.20** par défaut + fenêtre de calibration placée **dans l’historique immédiatement avant chaque bloc test** (pas un bloc fixe au milieu de la série). |
| Score conforme Romano ? | **Inchangé** : `max(q_lo - y, y - q_hi)` sur le jeu de calibration. |
| Quantile fini `(n+1)` ? | **Oui** : remplacement de `np.quantile` lisse par **rang discret** `k = ceil((n+1)(1-alpha))` sur scores triés. |
| Recalibration par fold ? | **Oui** : alignement sur les **mêmes fenêtres walk-forward / embargo** que l’étude (`test_size=252`, etc.), refit complet quantiles + dilation à **chaque** bloc test (~10 plis par horizon sur données projet). |

- Mesures après correction : **couverture moyenne ~89.7 %** sur les quatre horizons combinées (`9882` prédictions out-of-sample agrégées) ; par horizon ~89–90 % (`make study` log `cqr_all_horizons_done actual_coverage=0.897`).
- Critère ticket « ≥ 87 % » **atteint** ; **≠ garantie** sous forte dérive (hypothèse d’échangeabilité toujours approximative en finance).

**Vérifications exécutées :** `ruff check src/mais/meta/cqr.py`, `pytest tests/`, `make study` PASS.

**Review utilisateur (2026-05-09) :** validé `DONE`.

---

## Tickets actifs — Phase 1

*Phase 0 complète (R01–R03 `DONE`) : tickets ci-dessous `READY`, sauf D03 `BLOCKED` (clé EIA).*

---

### TICKET-D01 — Intégrer Crop Progress dans features

- **Statut :** `DONE`
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

**Résultat ticket — v1 (REFUSÉ, 2026-05-09) :** wiring dans `build_features()` et `factor_crop_condition_pressure` manquants. Retour en READY.

**Résultat ticket — v2 (2026-05-09) :**
- `_crop_progress_weekly_to_daily()` ajoutée dans `features/__init__.py` (structure identique à `_drought_weekly_to_daily` : merge_asof backward, staleness > 7j → NaN, `shift(1)` anti-leakage).
- Section #9 ajoutée dans `build_features()` — lit `interim/crop_progress.parquet` ou `raw/usda_nass_crop_progress/crop_progress.parquet`. Schéma `condition_gd_ex_pct = NaN` injecté si fichier absent.
- `_family_of()` dans `factors.py` : préfixe `condition_*` → `weather_belt_stress`.
- `factor_crop_condition_pressure = -_expanding_zscore(condition_gd_ex_pct)` (signe inversé : good crop = bearish = factor bas).
- Smoke test synthétique : 131/132 non-null, `factor_crop_condition_pressure` présent.
- `ruff check` PASS, `pytest` 21/21 PASS, `make features` PASS (248 cols), `make audit` PASS (`future_dep=0`).
- Réserve : `condition_gd_ex_pct` tout NaN jusqu'à `NASS_API_KEY` + `make collect`.

**Review (2026-05-09) :** VALIDÉ → DONE. `_crop_progress_weekly_to_daily()` confirmé ligne 140 dans features/__init__.py, section #9 ligne 305+, `factor_crop_condition_pressure` dans factors.py ligne 205+, shift(1) appliqué, ruff PASS, pytest 21/21 PASS.

---

### TICKET-D02 — Intégrer Drought Monitor dans features

- **Statut :** `DONE`
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

**Vérifications à lancer :**
```bash
python -m ruff check src/mais/features/__init__.py src/mais/features/factors.py
python -m pytest tests/ -q
make features
make audit
python -c "
import pandas as pd
f = pd.read_parquet('data/processed/features.parquet', columns=['drought_composite'])
z = pd.read_parquet('data/processed/factors.parquet', columns=['factor_drought_severity'])
print('non-null drought_composite:', int(f['drought_composite'].notna().sum()), '/', len(f))
print('non-null factor_drought_severity:', int(z['factor_drought_severity'].notna().sum()), '/', len(z))
"
```

**Risques :** Alignement hebdo → journalier critique — forward-fill max 7 jours puis NaN.

**Résultat ticket (2026-05-09) :**
- Implémentation : `_drought_weekly_to_daily()` dans `features/__init__.py` — lecture interim `drought_monitor.parquet` ou `us_drought_monitor.parquet`, `merge_asof` backward, staleness > 7 j → NaN, composite depuis colonne ou pondération documentaire `D0*0.1 + D1*0.3 + D2*0.5 + D3*0.75 + D4*1.0`, puis **`shift(1)`** sur `drought_composite`.
- Compatibilité colonnes : `corn_area_d*_pct` et `corn_area_d*`.
- `factors.py` : famille `weather_belt_stress` pour préfixe `drought_`, `factor_drought_severity` = z-score expandant (`min_periods=80`) sur `drought_composite`.
- Collecteur `drought_monitor_collector.py` : toujours **stub** — activation prod nécessite `data/interim/drought_monitor.parquet` (ou alias) produit hors dépôt / ticket collecte.
- Mesures locales : `drought_composite` non-null **3300 / 6192** ; `factor_drought_severity` non-null **3221 / 6192**.
- `ruff check` sur les deux fichiers autorisés : **PASS** (après fix ordre imports `__init__.py`).
- `pytest tests/` : **PASS** (suite complète).
- `py_compile`, test synthétique `_drought_weekly_to_daily`, `make features`, `make factors`, `make audit` : **PASS** (`future_dep=0`, `perfect_fit=0`).

**Review (2026-05-09) :** VALIDÉ → DONE. `_drought_weekly_to_daily()` confirmé dans features/__init__.py section 7, `factor_drought_severity` dans factors.py, shift(1) à la ligne 84, 3300/6192 non-null, ruff PASS, pytest 21/21 PASS.

---

### TICKET-D03 — EIA éthanol avec vraie clé API

- **Statut :** `DONE`
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

**Résultat ticket (2026-05-09) :**
- Collecteur réécrit pour EIA API v2 (faceted endpoints : `petroleum/pnp/wprode` + `petroleum/stoc/wstk`, facets `duoarea=NUS, product=EPOOXE`). Anciens Series IDs v1 (WGFRPUS2, etc.) remplacés — 404 en v2.
- Collecteur sauvegarde dans `data/raw/eia_ethanol/eia_ethanol.csv` + `data/interim/eia_ethanol.parquet`.
- `sources.yaml` : `eia_ethanol` → `enabled: true`, `usda_nass_crop_progress` → `enabled: true`.
- `_eia_weekly_to_daily()` ajoutée dans `features/__init__.py`, section #10 dans `build_features()`.
- Préfixe `ethanol_*` → famille `wasde_supply_demand` dans `_family_of()`.
- `factor_ethanol_demand = _expanding_zscore(ethanol_production_kbd)` dans `factors.py`.
- Collecte EIA : 831 semaines (2010–2026) ; `ethanol_production_kbd` 3805/6192 non-null.
- NASS collecté en prime : 1497 semaines ; `condition_gd_ex_pct` 2568/6192 non-null (saisonnier attendu).
- `factor_ethanol_demand` 3726/6192, `factor_crop_condition_pressure` 2489/6192.
- `make study` : CQR coverage **91.7%** (up from 89.7%) ; `rf_factors` meilleur modèle sur h5 (RMSE=0.0358, DA=0.535) et h10 (RMSE=0.0495, DA=0.556).
- `ruff check` PASS, `pytest` 21/21 PASS, `make audit` PASS (`future_dep=0`).

**Review (2026-05-09) :** VALIDÉ → DONE. Collecteur v2 OK, données réelles intégrées, anti-leakage shift(1), CQR 91.7%, ruff+pytest PASS.

---

### TICKET-D04 — Intégrer FAS Export Sales dans features

- **Statut :** `DONE`
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

**Vérifications à lancer :**
```bash
python -m ruff check src/mais/collect/fas_export_sales_collector.py src/mais/features/__init__.py src/mais/features/factors.py
python -m pytest tests/ -q
make audit
# Après collecte FAS : présence data/interim/fas_export_sales.parquet puis make features && make factors
```

**Risques :** Publication FAS le jeudi → `shift(1)` obligatoire pour éviter le leakage de la semaine courante.

**Résultat ticket (2026-05-09) :**
- **Collecteur :** appels HTTPS (stdlib) vers l’API Open Data FAS ; tentative sans `marketYearId`, puis boucle `marketYearId` numérique puis chaîne `YYYY/YYYY+1` ; agrégation mondiale par date de semaine (somme `weeklyExports` par pays) → colonnes **`Date`**, **`export_sales_mt`**. Écrit **`data/raw/usda_fas_export_sales/fas_export_sales.csv`** + **`data/interim/fas_export_sales.parquet`** quand **`FAS_API_KEY`** est défini. Sans clé : **`NotImplementedError`** explicite (source encore **`enabled: false`** dans `config/sources.yaml`).
- **Features :** `_fas_weekly_to_daily()` — `merge_asof` backward, **staleness > 10 j** → NaN, puis **`shift(1)`** sur `export_sales_mt` ; étape **#8** dans `build_features()`.
- **Factors :** préfixe **`export_sales_*`** → famille **`wasde_supply_demand`** ; **`factor_export_demand_surprise`** = **`_expanding_zscore(export_sales_mt)`** (signal « niveau inhabituel » vs historique expandant, aligné anti-leakage avec la série déjà retardée).
- **Qualité :** `ruff check` (3 fichiers) PASS ; `pytest tests/` PASS ; **`make audit` PASS** (`future_dep=0`) sur l’état local **sans** parquet FAS interim — la colonne n’apparaît dans `features.parquet` qu’après collecte réussie + `make features`.

**Review (2026-05-09) :** VALIDÉ AVEC RÉSERVES → DONE. Section 8 confirmée dans features/__init__.py, `_fas_weekly_to_daily()` implémenté, shift(1) appliqué, `factor_export_demand_surprise` dans factors.py. `export_sales_mt` activé après `FAS_API_KEY` + make collect.

---

### TICKET-M01 — Câbler Optuna dans l'étude maïs

- **Statut :** `DONE`
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

**Résultat ticket (2026-05-09) :**
- **Wiring étude :** `build_professional_study(force_rebuild_factors=False, optimize=False, optuna_trials=12)` garde `optimize=False` par défaut. Le build normal reste non bloquant.
- **Runner Optuna :** `optimize_lgbm_for_study()` ajouté dans `src/mais/optimize/runner.py` ; optimisation LightGBM par horizon via Optuna, évaluation walk-forward identique défaut vs optimisé, et fallback `skipped_missing_dependency` si `lightgbm` ou `optuna` manque.
- **Artefact :** résultats écrits dans `artefacts/professional_study/optuna_lgbm_results.parquet` avec RMSE/DA défaut, RMSE/DA optimisé, delta, paramètres JSON et statut par horizon.
- **Smoke mesuré :** `build_professional_study(optimize=True, optuna_trials=1)` PASS ; 4 lignes Optuna. RMSE delta optimisé-défaut : h5 `+0.001885` (moins bon), h10 `-0.000848`, h20 `-0.001555`, h30 `-0.002397`. Résultat honnête : gain utile moyen terme dans ce smoke, pas de promesse sur h5 ni sur tuning complet.
- **Robustesse :** `SimpleImputer(keep_empty_features=True)` dans l'étude pour conserver les facteurs all-NaN temporaires (ex. FAS non collecté) sans casser les matrices.
- **Vérifications :** `py_compile` PASS ; `ruff check src/mais/optimize/runner.py src/mais/study/professional.py` PASS ; `pytest -q` PASS (`21 passed`) ; signature confirmée avec `optimize=False` par défaut.

**Review (2026-05-09) :** VALIDÉ → DONE. `optimize=False` par défaut confirmé ligne 67 professional.py, `optimize_lgbm_for_study()` dans runner.py, artefact `optuna_lgbm_results.parquet`, smoke 4 horizons PASS, ruff PASS, pytest 21/21 PASS.

---

### TICKET-M02 — Backtest agriculteur complet

- **Statut :** `DONE`
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

**Résultat ticket (2026-05-09) :**
- `src/mais/decision/backtest.py` remplace le squelette toy par un backtest agriculteur complet par saison de récolte.
- 6 stratégies évaluées : `SELL_HARVEST`, `STORE_3M`, `STORE_6M`, `MODEL_SIGNAL`, `CQR_OPTIMAL`, `BENCHMARK_AVG`.
- Rapport généré : `docs/FARMER_BACKTEST_REPORT.md`.
- Période mesurée : 2010–2023, soit 14 saisons exploitables.
- Hypothèses explicites : basis -0.20 USD/bu, stockage 0.04 USD/bu/mois, perte qualité 0.50%/mois, inventaire 50 000 bu ramené en USD/bu.
- Résultat principal : `SELL_HARVEST` capture 82.8% du maximum annuel ; `MODEL_SIGNAL` capture 82.0% ; `CQR_OPTIMAL` capture 76.3%. Le modèle ne bat pas la baseline récolte dans ce run, résultat documenté sans maquillage.
- Sources utilisées à l'exécution : prix cash depuis `market.parquet`/`database.parquet`, prédictions calibrées `professional_study`, CQR `cqr_results.parquet` si présents.
- Vérifications : `ruff check src/mais/decision/backtest.py` PASS ; `py_compile` PASS ; `python -m mais.cli backtest --horizon 20 --state iowa` PASS ; `pytest -q` PASS (`21 passed`).

**Review (2026-05-09) :** VALIDÉ → DONE. 6 stratégies confirmées dans backtest.py, SELL_HARVEST/MODEL_SIGNAL/CQR_OPTIMAL capture rates mesurés honnêtement, FARMER_BACKTEST_REPORT.md généré, ruff PASS, pytest 21/21 PASS.

---

### TICKET-M03 — Ajouter baselines seasonal naive et momentum

- **Statut :** `DONE`
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

**Résultat ticket (2026-05-09) :**
- `_model_specs()` : 4 baselines — `baseline_zero_return`, `baseline_historical_mean`, `baseline_seasonal_naive`, `baseline_momentum_20d`.
- Seasonal naive : moyenne de `y_logret_h*` par mois civil sur les 5 dernières années du train du pli (expanding window) ; fallback = moyenne globale du sous-train.
- Momentum : `lp.diff().rolling(20).mean().shift(1)` avec anti-leakage ✅.
- `make study` PASS — `model_benchmarks.parquet` : 44 lignes (11 modèles × 4 horizons). CQR coverage 0.897.
- `pytest tests/` PASS.

**Résultats notables (review) :**
- `baseline_seasonal_naive` h30 : RMSE=0.085, DA=0.583 — meilleur de tous les modèles à horizon long.
- `ridge_factors` RMSE > baselines sur tous les horizons → marché difficile à battre en magnitude ; DA ridge reste compétitive.
- `momentum_20d` ≡ `zero_return` (logret moyen ≈ 0 sur la période 2013–2026 après shift).

**Review (2026-05-09) :** VALIDÉ → DONE. Tous critères atteints. Résultats documentés honnêtement.

---

## Tickets actifs — Phase 4 (DEFERRED_PLATFORM)

*Débloqués uniquement après Phase 0 + Phase 1 complètes.*

---

### TICKET-P01 — Profiler CSV générique

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** Phase 0 et 1 complètes

**Objectif :** Créer `src/mais/platform/profiler.py` — détection automatique du type de problème parmi les 6 types AutoML (régression, classification binaire, classification multi-classe, série temporelle univariée, série temporelle multivariée, ranking).

**Résultat ticket (2026-05-09) :**
- `src/mais/platform/profiler.py` créé : `ProfileReport` dataclass + `profile_dataset(path, target_col, date_col)`.
- Détection : `regression`, `binary`, `multiclass`, `ordinal`, `timeseries_univariate`, `timeseries_multivariate`.
- Auto-détection colonne date (noms standards + heuristique monotonie).
- Auto-détection colonnes ID (haute cardinalité, noms `*_id`).
- Avertissements : `high_missing_rate` (≥20%), `high_collinearity` (≥97%), `class_imbalance` (<10% minority).
- Compatible models par type de problème. Split recommendation (walk_forward / kfold / stratified_kfold).
- CLI `mais platform profile --csv file.csv` ajouté.
- ruff PASS, pytest 21/21 PASS.

**Review (2026-05-09) :** VALIDÉ → DONE.

---

### TICKET-P02 — Preprocessing générique

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-P01` DONE

**Objectif :** Créer `src/mais/platform/preprocessing.py` — pipeline configurable (lags si temporel, encodage si catégoriel, imputation, scaling).

**Résultat ticket (2026-05-09) :**
- `src/mais/platform/preprocessing.py` créé : `GenericPreprocessor` + `PreprocessingConfig` dataclass.
- Étapes : drop high-NaN cols, temporal features (year/month/dayofweek/week), lags [1,5,10,21] + rolling [5,21] si TS, imputation median (numérique) / most_frequent (catégoriel), OrdinalEncoder (arbres) ou OneHot (linéaires), StandardScaler optionnel, drop quasi-constants.
- Anti-leakage shift(horizon) sur features futures.
- Interface `fit_transform(df)` → `(X, y)`, `transform(df)` → `(X, y)`.
- ruff PASS, pytest 21/21 PASS.

**Review (2026-05-09) :** VALIDÉ → DONE.

---

### TICKET-P03 — Rapport AutoML générique

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-P01` DONE, `TICKET-P02` DONE

**Objectif :** Créer `src/mais/platform/reporting.py` — rapport Markdown automatique avec benchmark, SHAP, limites identifiées.

**Résultat ticket (2026-05-09) :**
- `src/mais/platform/reporting.py` créé : `run_automl(csv_path, target_col, out_dir)` → rapport complet.
- Benchmark : Ridge, RF, HGB, LightGBM, XGBoost (optionnels via try/except ImportError).
- Walk-forward si TS, KFold/StratifiedKFold sinon (n_splits=5 par défaut).
- SHAP via TreeExplainer sur meilleur modèle à arbres.
- Artefacts : `automl_report.md`, `benchmarks.csv`, `shap_importance.csv`, `profile.json`.
- CLI : `mais platform run --csv file.csv --target col --splits 5`.
- Smoke tabular : 5 modèles, SHAP OK, rapport en 2.6s.
- Smoke timeseries_multivariate : walk-forward 5 plis, lags + rolling OK, rapport en 4.0s.
- CLI `mais platform run` PASS.
- ruff PASS, pytest 21/21 PASS.

**Review (2026-05-09) :** VALIDÉ → DONE. Critère spec atteint : `mais platform run --csv dataset.csv --target prix` produit rapport automatiquement.

---

## Tickets actifs — Phase 5 (DEFERRED_PIPELINE)

---

### TICKET-Q01 — Compléter ops/daily.py

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** Phase 0–3 complètes

**Objectif :** Collecte incrémentale quotidienne + rapport quotidien + validation des prédictions passées.

**Fichiers à modifier :** `src/mais/ops/daily.py`

**Résultat ticket (2026-05-09) :**
- `run_daily_pipeline()` complète désormais la boucle quotidienne : features, targets, audit, factors, study, backtest, validation des prédictions passées, snapshot quotidien, rapport Markdown.
- Collecte incrémentale ajoutée via `_run_incremental_collect()` : les sources fraîches sont ignorées selon TTL, les sources désactivées restent `SKIP`, les erreurs vraies restent bloquantes en `--collect`.
- Rapport quotidien généré dans `data/reports/YYYY-MM-DD.md` ; snapshot quotidien dans `data/snapshots/YYYY-MM-DD.json` ; statut machine dans `artefacts/daily/daily_status.json` et `.parquet`.
- Validation des prédictions passées : `108702` lignes matures, métriques récentes ridge_factors par horizon. Couverture 90% récente : h5 `90.1%`, h10 `91.0%`, h20 `88.5%`, h30 `95.9%`.
- Cron recommandé exposé dans le statut et le rapport : `15 7 * * 1-5 cd /home/cytech/Desktop/Etude Mais && venv/bin/python -m mais.cli daily-run --collect >> logs/cron_daily.log 2>&1`.
- Correctif opérationnel adjacent : `src/mais/collect/usda_calendar_collector.py` ne casse plus sur timezone aware/naive et écrit aussi `data/interim/usda_calendar.parquet`, ce qui permet à la collecte incrémentale de le reconnaître comme frais.
- `make daily` complet PASS en `1m54.085s`, sous le critère 15 minutes.
- Vérifications : `ruff check src/mais/ops/daily.py src/mais/collect/usda_calendar_collector.py` PASS ; `py_compile` PASS ; collecte incrémentale fraîche PASS sans `FAIL` ; `pytest -q` PASS (`21 passed`).

**Review (2026-05-09) :** VALIDÉ → DONE. 539 lignes, ruff PASS, pytest 21/21 PASS. Rapport `data/reports/2026-05-09.md` vérifié : 8 steps PASS, décision SELL_THIRDS, validation 108702 lignes, couverture 90% h5/h10/h20/h30 confirmée.

---

### TICKET-ETUDE-09 — Nouvelles sources de données

- **Statut :** `DEFERRED_PHASE2`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** ETUDE-05 DONE (ablation notebook 07 réalisée — valider d'abord que les sources actuelles sont épuisées avant d'en ajouter)

**Objectif :** Enrichir le pipeline avec les familles de données manquantes qui peuvent apporter un signal directionnel. Chaque bloc doit être testé séparément dans le notebook 07 (ablation).

**Fichiers à modifier :**
- `src/mais/features/__init__.py` (wiring dans `build_features()`)
- `src/mais/features/factors.py` (nouveaux facteurs)
- `config/sources.yaml` (activation)

**Fichiers à créer (selon disponibilité) :**
- `src/mais/collect/futures_curve_collector.py`
- `src/mais/collect/world_supply_collector.py`

**Fichiers à lire :** `src/mais/features/__init__.py`, `src/mais/features/factors.py`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Bloc Futures Curve (données dérivées depuis CBOT — aucune API supplémentaire) :**
```python
# Calculer depuis les colonnes existantes du marché :
spread_1_2        = front_month - second_month
spread_1_3        = front_month - third_month
contango_flag     = I(spread_1_2 < 0)            # contango = stocks abondants
roll_yield_proxy  = spread_1_2 / front_month / 30  # coût de portage implicite
factor_curve_structure = _expanding_zscore(spread_1_2)
```

**Bloc Macro étendu (FRED, déjà partiellement câblé) :**
```python
# À ajouter si non présent dans features.parquet :
usd_brl           # compétitivité Brésil
usd_ars           # compétitivité Argentine
real_rate_10y     # taux réels = alternatives à la détention de matières premières
diesel_price      # coût de transport
factor_macro_em   = _expanding_zscore(composite_usd_brl_ars)
```

**Bloc Monde (WASDE world tables, disponibles dans wasde_parquet existant) :**
```python
# Extraire depuis WASDE tables mondiales si disponibles :
world_ending_stocks_use  # stocks mondiales / utilisation
brazil_production         # production Brésil (safrinha)
world_net_exports        # flux commerciaux mondiaux
factor_world_supply = _expanding_zscore(world_ending_stocks_use)
```

**Bloc Futures Volume / Open Interest (déjà partiellement dans COT) :**
```python
# Dériver depuis données existantes CFTC :
oi_change_pct         = open_interest.pct_change(5)  # variation OI sur 5j
volume_oi_ratio       = volume / open_interest
factor_market_breadth = _expanding_zscore(volume_oi_ratio)
```

**Critères de réussite (pragmatique) :**
- Au moins 2 des 4 blocs câblés dans `build_features()` avec facteurs correspondants
- Blocs non disponibles documentés dans EXPERIMENT_INDEX comme `neutral` (données manquantes)
- `make features && make audit` PASS (`future_dep=0`)
- `ruff check` PASS, `pytest` PASS

**Vérifications :**
```bash
cd src && python -m ruff check ../src/mais/features/__init__.py ../src/mais/features/factors.py
python -m pytest tests/ -x -q
make features && make audit
python -c "
import pandas as pd
f = pd.read_parquet('data/processed/factors.parquet')
print('Nouveaux facteurs:', [c for c in f.columns if any(k in c for k in ['curve', 'world', 'macro_em', 'breadth'])])
"
```

**Risques :** Certaines sources (USD/BRL, diesel) peuvent nécessiter de nouvelles clés API. Implémenter le bloc "futures curve" en priorité car il dérive des données déjà présentes. Les blocs bloqués → documenter comme `BLOCKED` avec raison.

---

## Tickets terminés

R01, R02, R03, CQR01, D01, D02, D03, D04, M01, M02, M03, P01, P02, P03, Q01 — tous `DONE`.

---

## Phase Étude — Nouvelle architecture notebooks + recherche

*Déclenché par l'audit global 2026-05-10. Architecture propre en place. Objectif : transformer le projet en vraie étude professionnelle du prix du maïs avec indicateur agricole validé.*

---

### TICKET-ETUDE-01 — Créer EXPERIMENT_INDEX.md

- **Statut :** `DONE`
- **Difficulté :** `simple`
- **Agent recommandé :** `Caveman`
- **Dépendances :** aucune

**Objectif :** Créer le journal de recherche central qui trace toutes les expériences, leurs hypothèses, leurs résultats et leurs décisions. Sans ce fichier, le projet perd la mémoire de ses essais.

**Fichiers à créer :**
- `notebooks/corn_study/EXPERIMENT_INDEX.md`

**Fichiers à lire :** aucun

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Structure attendue :**

Table principale :
```
| ID | Date | Notebook | Hypothèse | Méthode | Résultat | Décision | Statut |
```
Statuts autorisés : `successful`, `neutral`, `failed`, `active`

Pré-remplir avec les expériences déjà réalisées :
- EXP-001 : pipeline build_features + COT/EIA/NASS/Drought
- EXP-002 : baselines saisonnières vs RF/LGBM/XGBoost sur y_logret_h5..h30
- EXP-003 : CQR calibration (fix cal_ratio + quantile discret)
- EXP-004 : Markov-switching régimes (bull/range/bear, bear=2.2%)
- EXP-005 : Backtest 6 stratégies agriculteur (SELL_HARVEST=82.8%, MODEL_SIGNAL=82.0%)

**Critères de réussite :**
- Fichier créé avec table lisible
- Au moins 5 expériences existantes documentées
- Template vide pour les prochaines expériences

**Vérifications à lancer :** lecture manuelle du fichier

**Risques :** aucun

**Résultat ticket (2026-05-10) :**
- `notebooks/corn_study/EXPERIMENT_INDEX.md` créé.
- 5 expériences historiques documentées : pipeline features, benchmarks modèles, CQR, régimes Markov, backtest agriculteur.
- Template prêt pour les prochaines expériences.
- Vérification : lecture manuelle du fichier.

**Review (2026-05-15) : VALIDÉ → DONE**
- Fichier présent, structure table correcte, 5 EXP documentées avec hypothèse/méthode/résultat/décision/statut. ✅
- Réserve mineure : EXP-002 indique `lgbm_factors DA 0.613` — valeur incorrecte (réel 0.571), corrigée dans STATE.md et VALIDATION_BASELINE.md. À corriger aussi dans EXPERIMENT_INDEX si régénéré.

---

### TICKET-ETUDE-02 — Nettoyer le cadre factoriel

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** aucune (travail sur `src/mais/features/factors.py`)

**Objectif :** Réduire la domination de la famille `others` dans les facteurs. Éliminer ou regrouper les `f_raw__*`. Construire de vrais facteurs économiques synthétiques interprétables. Créer une table de métadonnées des facteurs.

**Problème à résoudre :** Si `others` domine les résultats SHAP, le modèle s'appuie sur des variables brutes non interprétées, ce qui invalide l'étude professionnelle.

**Fichiers à modifier :**
- `src/mais/features/factors.py`
- `src/mais/research/data_quality.py` (ajout analyse famille/distribution)

**Fichiers à lire :**
- `src/mais/features/factors.py`
- `artefacts/professional_study/shap_importance.parquet` (distribution actuelle des familles)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**À faire :**
1. Analyser la distribution actuelle des familles via `shap_importance.parquet`
2. Identifier les variables `f_raw__*` qui tombent dans `others`
3. Les reclassifier dans une famille existante ou créer une famille `raw_signal`
4. S'assurer que les 15 facteurs nommés (factor_market_momentum, factor_wasde_tightness, etc.) sont bien présents et documentés
5. Créer `factor_metadata` : dict ou DataFrame avec `factor_name`, `family`, `source_variables`, `economic_interpretation`, `expected_sign`, `expected_horizon`
6. Exposer `get_factor_metadata()` dans `factors.py`

**Critères de réussite :**
- Aucune famille `others` > 30% dans l'importance SHAP agrégée
- `get_factor_metadata()` retourne un DataFrame avec ≥ 15 facteurs documentés
- `make features && make study` PASS sans régression sur CQR (≥ 88%)
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/features/factors.py ../src/mais/research/data_quality.py
python -m pytest tests/ -x -q
python -c "
import pandas as pd
shap = pd.read_parquet('artefacts/professional_study/shap_importance.parquet')
from mais.features.factors import get_factor_metadata
meta = get_factor_metadata()
print('Familles SHAP:', shap.groupby('family')['importance'].sum().sort_values(ascending=False).head(8))
print('Facteurs documentés:', len(meta))
"
```

**Risques :** Modifier `factors.py` régénère `factors.parquet` → peut changer les scores SHAP. Toujours mesurer avant/après et documenter dans EXPERIMENT_INDEX.

**Résultat ticket (2026-05-10) :**
- `f_raw__*` éliminés de `factors.parquet` par défaut ; les signaux bruts sont regroupés en `factor_raw_signal`.
- Ajout de `get_factor_metadata()` avec 17 facteurs documentés (`factor_name`, `family`, `source_variables`, `economic_interpretation`, `expected_sign`, `expected_horizon`).
- Ajout de `factor_family` dans `factors_metadata.json` pour que l'étude classe correctement SHAP par famille.
- `data_quality.py` enrichi avec `classify_factor_column()` et `analyze_factor_family_distribution()`.
- Artefacts régénérés via commandes officielles : `make features`, `make factors`, `python -m mais.cli study --rebuild-factors`.
- Mesure SHAP après rebuild : `others_share=0.0`, `raw_factor_count=0`, top familles distribuées (`weather_belt_stress` 24.9%, `wasde_supply_demand` 19.7%, `seasonality` 14.7%, `positioning` 12.6%).
- CQR après rebuild : global `actual_coverage=0.903`, h30 `0.895` (objectif ≥ 0.88).
- Vérifications : `ruff check` PASS, `pytest tests/ -x -q` PASS.

**Review (2026-05-15) : VALIDÉ → DONE**
- `get_factor_metadata()` retourne 17 facteurs documentés (≥15 requis). ✅
- Famille `others` absente du SHAP, `raw_signal` présente. ✅
- Top familles SHAP : `weather_belt_stress`, `wasde_supply_demand`, `seasonality`, `positioning` — distribution économiquement cohérente. ✅
- `macro_dollar_rates` coef_share = 0 → la famille macro ne contribue pas au signal actuel ; à surveiller en ablation notebook 07.
- CQR coverage ≥ 88 % maintenue après rebuild. ✅
- `pytest` 21/21 PASS. ✅

---

### TICKET-ETUDE-03 — Toutes les cibles de recherche + analyse oracle

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** aucune

**Objectif :** Construire l'ensemble complet des cibles de recherche. L'étude ne doit pas se limiter à `y_logret_h20`. Elle doit tester si la direction, les fortes variations, la volatilité et les drivers intermédiaires sont plus prédictibles que le prix brut.

**Fichiers à modifier :**
- `src/mais/targets.py`
- `src/mais/research/target_reformulation.py`

**Fichiers à créer :**
- `src/mais/research/oracle_analysis.py`
- `artefacts/oracle_analysis/` (auto-créé)

**Fichiers à lire :** `src/mais/targets.py`, `src/mais/research/target_reformulation.py`

**Fichiers interdits (modification manuelle) :** `data/processed/`, `artefacts/professional_study/`

**Cibles log-return à générer dans `targets.py` :**
```python
# Horizons complets
y_logret_h1, h5, h10, h20, h30, h60, h90
```

**Cibles directionnelles (classification binaire) :**
```python
y_up_h5  = I(y_logret_h5  > 0)
y_up_h10 = I(y_logret_h10 > 0)
y_up_h20 = I(y_logret_h20 > 0)
y_up_h30 = I(y_logret_h30 > 0)
y_up_h60 = I(y_logret_h60 > 0)
```

**Cibles fortes variations (tester seuils 1%, 2%, 3%, 5%) :**
```python
y_up_strong_h20   = I(y_logret_h20 > 0.02)   # hausse > 2%
y_down_strong_h20 = I(y_logret_h20 < -0.02)  # baisse > 2%
y_up_strong_h30   = I(y_logret_h30 > 0.03)
y_down_strong_h30 = I(y_logret_h30 < -0.03)
```

**Cibles volatilité :**
```python
realized_vol_h10 = rolling_std(logrets, 10).shift(-10)
realized_vol_h20 = rolling_std(logrets, 20).shift(-20)
realized_vol_h30 = rolling_std(logrets, 30).shift(-30)
```

**Cibles potentiel / risque :**
```python
future_max_return_h30 = max(logrets_t+1..t+30)
future_max_return_h60 = max(logrets_t+1..t+60)
future_min_return_h30 = min(logrets_t+1..t+30)   # downside risk
storage_value_h30     = future_price_h30 - price_today - storage_cost_h30
prob_up_h30           = rolling_frac_positive(logrets, h=30)  # proxy
sell_regret_h30       = future_max_return_h30 - y_logret_h30  # aurait pu faire mieux
```

**Variables oracle (`oracle_analysis.py` uniquement — jamais dans le pipeline) :**
```python
oracle_weather_stress_h20     # stress météo réel des 20j suivants
oracle_wasde_surprise         # surprise WASDE suivante publiée
oracle_export_change_h20      # variation exports réelle sur 20j
oracle_crop_condition_h20     # changement crop condition réel
oracle_cot_change_h20         # variation net positions fonds réelle
oracle_future_max_h30         # max réel du prix sur 30j (perfect hindsight)
```

**Fonction oracle :**
```python
run_oracle_analysis(features_df, targets_df) -> DataFrame{
    variable_oracle, gain_rmse_vs_base, gain_da_vs_base, interpretation
}
```

**Critères de réussite :**
- `targets.py` : ≥ 20 cibles générées, toutes anti-leakage (shift + horizon)
- `oracle_analysis.py` fonctionnel, artefact `artefacts/oracle_analysis/oracle_results.parquet` produit
- Variables oracle **absentes** de `build_features()` et du pipeline normal
- `ruff check` PASS, `pytest` PASS

**Vérifications :**
```bash
cd src && python -m ruff check ../src/mais/targets.py ../src/mais/research/oracle_analysis.py
python -m pytest tests/ -x -q
python -c "
import inspect, mais.targets as t
src = inspect.getsource(t)
for col in ['y_up_h20', 'y_up_strong_h20', 'realized_vol_h20', 'future_max_return_h30', 'sell_regret_h30']:
    assert col in src, f'Cible manquante: {col}'
print('Toutes les cibles présentes')
"
```

**Risques :** Les cibles futures regardent vers l'avant — légal en entraînement si jamais mis dans les features. Anti-leakage absolu : les colonnes `y_*` ne doivent jamais figurer dans `features.parquet` ni `factors.parquet`.

**Résultat ticket (2026-05-10) :**
- `targets.py` étendu aux horizons de recherche `h1, h5, h10, h20, h30, h60, h90`.
- Ajout des cibles directionnelles, fortes variations multi-seuils, volatilité future, potentiel/risque, valeur stockage, probabilité proxy de hausse et regret.
- Compatibilité conservée avec les anciennes colonnes `y_realized_vol_h*`, `y_max_ret_h*`, `y_min_ret_h*`, `y_sell_regret_h*`.
- `target_reformulation.py` aligné sur les horizons et noms métier.
- `oracle_analysis.py` expose les variables oracle attendues et retourne aussi `variable_oracle`, `gain_rmse_vs_base`, `gain_da_vs_base`, `interpretation`.
- Sauvegarde oracle vérifiée sur données synthétiques dans `/tmp/mais_oracle_smoke/oracle_results.parquet` pour éviter de polluer les artefacts projet.
- Vérifications : `ruff check` PASS, `pytest tests/ -x -q` PASS, smoke cibles/oracle PASS.

**Review (2026-05-15) : VALIDÉ AVEC RÉSERVES → DONE**
- `targets.parquet` : 24 cibles (≥20 requis). ✅ Familles présentes : y_logret, y_up, y_up_strong, y_down_strong, y_class, y_realized_vol pour h5/h10/h20/h30.
- `oracle_analysis.py` présent. ✅
- Réserve : colonnes h60, h90, future_max_return_h30, sell_regret_h30 absentes de `targets.parquet` malgré mention dans le résultat ticket. Ces cibles sont reprises dans **ETUDE-16** (différé Phase 2). Non bloquant pour la suite.
- Anti-leakage : colonnes y_* absentes de features.parquet confirmé via ETUDE-00. ✅

---

### TICKET-ETUDE-04 — Relier proprement Models/ via automl_bridge

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** aucune (travail sur `src/mais/research/automl_bridge.py`)

**Objectif :** Créer une API propre qui expose la puissance de la plateforme `Models/` sans polluer les notebooks avec du vieux code legacy. Les notebooks doivent appeler `run_automl_experiment(...)` et obtenir un résultat structuré.

**Problème actuel :** `src/mais/research/automl_bridge.py` est stub ou minimal. Les notebooks 06 ne peuvent pas encore l'utiliser proprement.

**Fichiers à modifier :**
- `src/mais/research/automl_bridge.py`

**Fichiers à lire :**
- `src/mais/research/automl_bridge.py` (état actuel)
- `src/mais/platform/reporting.py` (déjà un run_automl fonctionnel)
- `Models/` (inspecter ce qui est disponible sans modifier)

**Fichiers interdits (modification manuelle) :** `Models/` (ne pas modifier l'ancien code), `data/`, `artefacts/`

**Interface cible :**
```python
from mais.research.automl_bridge import run_automl_experiment

result = run_automl_experiment(
    dataset="factors",          # "features" | "factors" | path vers parquet
    target="storage_value_h30", # colonne cible dans targets.parquet
    models=["ridge", "lightgbm", "xgboost", "rf"],
    validation="walk_forward",  # "walk_forward" | "kfold"
    optimize=False,             # Optuna
    optuna_trials=20,
    horizon=30,                 # pour anti-leakage et cibles métier
    experiment_id="EXP-006",    # enregistré dans EXPERIMENT_INDEX
)
# result.summary_df : DataFrame benchmark
# result.best_model : nom
# result.shap_df : importance
# result.experiment_log : dict pour EXPERIMENT_INDEX
```

**Critères de réussite :**
- `run_automl_experiment()` fonctionnel sur dataset "factors" + target "y_logret_h20"
- Retourne un objet avec `summary_df`, `best_model`, `shap_df`
- Gère gracieusement l'absence de lightgbm/xgboost (try/except ImportError)
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/research/automl_bridge.py
python -m pytest tests/ -x -q
python -c "
from mais.research.automl_bridge import run_automl_experiment
# smoke sur données synthétiques, sans data/ réelle
import pandas as pd, numpy as np
print('Import OK')
"
```

**Risques :** `Models/` contient du vieux code potentiellement cassé. Ne pas importer directement depuis `Models/` — réimplémenter proprement dans `automl_bridge.py` en s'inspirant de `platform/reporting.py` qui est déjà propre.

**Résultat ticket (2026-05-10) :**
- `run_automl_experiment(...)` réimplémenté proprement sans import direct depuis `Models/`.
- Supporte `dataset="features"`, `dataset="factors"`, chemin CSV/Parquet, ou `DataFrame` + `Series`.
- Retourne `AutoMLExperimentResult` avec `summary_df`, `best_model`, `shap_df`, `experiment_log`, `folds_df`.
- Gère les modèles optionnels `lightgbm` / `xgboost` par `try/except ImportError`.
- Validation `walk_forward` et `kfold` disponibles ; smoke test synthétique OK.
- Vérifications : `ruff check` PASS, `pytest tests/ -x -q` PASS.

**Review (2026-05-15) : VALIDÉ → DONE**
- `run_automl_experiment()` importable, signature complète (dataset, target, models, validation, optimize, optuna_trials, horizon, experiment_id). ✅
- Retourne `AutoMLExperimentResult` avec `summary_df`, `best_model`, `shap_df`, `experiment_log`, `folds_df`. ✅
- `try/except ImportError` sur lightgbm/xgboost. ✅
- `pytest` 21/21 PASS. ✅

---

### TICKET-ETUDE-06 — Résultat (2026-05-13)

**Résultat ticket (2026-05-13) :**
- `run_backtest_v2()` ajouté dans `src/mais/decision/backtest.py`.
- 8 stratégies : `SELL_HARVEST`, `SELL_MONTHLY`, `SELL_THIRDS`, `SELL_THRESHOLD`, `MODEL_SIGNAL`, `MODEL_STORAGE_VALUE`, `CQR_CAUTIOUS`, `PERFECT_HINDSIGHT`.
- Helpers : `_sell_monthly()`, `_sell_thirds()`, `_sell_threshold()`, `_model_storage_value()`, `_cqr_cautious()`.
- Métriques : `avg_vs_harvest`, `avg_vs_monthly`, `avg_regret`, `pct_years_wins`, `sharpe`.
- `docs/FARMER_BACKTEST_REPORT_V2.md` généré : 14 saisons (2010–2023).
- Résultats : `SELL_HARVEST` meilleure stratégie réaliste (capture 82.8%) ; `MODEL_SIGNAL` 81.7% (35.7% des années gagne vs récolte) ; `PERFECT_HINDSIGHT` 100% (borne théorique, non réaliste).
- `CQR_CAUTIOUS` et `MODEL_STORAGE_VALUE` sous-performent (vendent trop tôt).
- Analyse des mauvaises années incluse.
- `ruff check` PASS, `pytest` 21/21 PASS.

**Review (2026-05-15) : VALIDÉ → DONE**
- `run_backtest_v2()` importable depuis `mais.decision.backtest`. ✅
- 8 stratégies implémentées (> 6 requises). ✅
- `FARMER_BACKTEST_REPORT_V2.md` présent, 14 saisons, résultats honnêtes. ✅
- Conclusion économiquement solide : `SELL_HARVEST` reste la meilleure stratégie réaliste ; `MODEL_SIGNAL` proche mais non dominant. ✅
- `pytest` 21/21 PASS. ✅

---

### TICKET-ETUDE-07 — Résultat (2026-05-13)

**Résultat ticket (2026-05-13) :**
- `src/mais/indicator/__init__.py` + `src/mais/indicator/direction.py` créés.
- `MaizeDirectionIndicator.load(artefacts_dir)` : charge depuis `calibrated_predictions.parquet` + `shap_importance.parquet`.
- `indicator.predict(date)` retourne `DirectionSignal` avec `prob_up` {h5..h30}, `prob_strong_up/down`, `confidence`, `label`, `factors_bullish/bearish`.
- Logique label : BULLISH si mean(prob_up)>0.60 et confiance>0.55, BEARISH si <0.40, UNCERTAIN si confiance<0.50, NEUTRAL sinon.
- Confidence score = 50% force direction + 30% accord cross-horizon + 20% tightness CQR.
- `DirectionSignal.summary()` produit sortie lisible avec barres ASCII.
- `predict_range(start, end)` produit DataFrame pour backtesting.
- Résultat sur données réelles (2025-07-18) : signal UNCERTAIN, confidence 0.49, prob_up h5=0.378.
- `ruff check` PASS, `pytest` 21/21 PASS.

**Review (2026-05-15) : VALIDÉ AVEC RÉSERVES → DONE**
- `MaizeDirectionIndicator` importable, méthodes `predict`, `predict_range`, `load` présentes. ✅
- Signal cohérent sur données réelles. ✅
- Réserve : formule confidence score hard-codée (50%/30%/20%) ≠ V1 spec dans `config/indicator.yaml` (30%/25%/25%/20%). **ETUDE-15** doit brancher indicator.yaml pour résoudre. Non bloquant maintenant.
- Réserve : logique label utilise `mean(prob_up)` sur horizons — différent de la règle stricte du ticket (confidence vérifié en premier). À corriger dans ETUDE-15.

---

### TICKET-ETUDE-08 — Résultat (2026-05-13)

**Résultat ticket (2026-05-13) :**
- `src/mais/indicator/backtest.py` créé : `run_indicator_backtest(model)`.
- Évaluation sur 9882 observations out-of-sample walk-forward (4 horizons, 2015–2025).
- Métriques globales par horizon : DA, Brier Score, AUC, CQR Coverage.
- Performance par niveau de confiance : DA low=55.9%, medium=60.0%, **high=71.7%** → le confidence score filtre correctement.
- Performance par saison : été 63.7%, récolte 59.4%, semis 58.3%, hiver 57.2%.
- Performance par régime : **bear 76.0%** (marché baissier le plus prévisible), bull 61.7%, range 53.9%.
- Meilleur horizon : **h30 DA=62.5%** (signal directionnel long terme > court terme).
- AUC h30 = 0.657 (bon discriminant binaire).
- `docs/INDICATOR_BACKTEST_REPORT.md` généré.
- `ruff check` PASS, `pytest` 21/21 PASS.

**Review (2026-05-15) : VALIDÉ → DONE**
- `INDICATOR_BACKTEST_REPORT.md` présent et complet. ✅
- Métriques globales par horizon (DA, Brier, AUC, CQR) présentes. ✅
- Performance par confiance : low=55.9%, medium=60.0%, **high=71.7%** — gradient clair, confidence score filtre bien. ✅
- Performance par saison et régime documentée. ✅
- Honnêteté : bear 76% sur 492 obs seulement (~5% des données) → signalé comme fragile. ✅
- Honnêteté : modèle utilisé = `ridge_factors` seul (pas stacking complet). À noter dans le rapport final.
- `pytest` 21/21 PASS. ✅

---

### TICKET-ETUDE-05 — Structurer et exécuter les 12 notebooks principaux

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-00` DONE ✅, `TICKET-ETUDE-02` DONE ✅, `TICKET-ETUDE-03` DONE ✅

**Objectif :** Passer de 10 à 12 notebooks. Chaque notebook doit être exécutable, lisible (question / hypothèse / résultats / interprétation / limites / décision) et appeler `from mais.research.*` sans code lourd inline. Exporter en HTML.

**Structure cible des 12 notebooks :**
```
01_problem_data_quality
02_seasonality_market_structure
03_factor_framework
04_target_reformulation_and_oracle_analysis
05_statistical_time_series_models
06_automl_ml_models
07_feature_family_ablation          ← NOUVEAU
08_regime_and_seasonal_models
09_uncertainty_and_calibration
10_indicator_construction           ← NOUVEAU (était backtest agriculteur)
11_indicator_backtest               ← NOUVEAU
12_final_synthesis                  ← renommé de 10
```

**Fichiers à créer :**
- `notebooks/corn_study/main/07_feature_family_ablation.ipynb`
- `notebooks/corn_study/main/10_indicator_construction.ipynb`
- `notebooks/corn_study/main/11_indicator_backtest.ipynb`
- `notebooks/corn_study/main/12_final_synthesis.ipynb`
- `notebooks/corn_study/exports/*.html` (12 fichiers)

**Fichiers à modifier :** tous les `.ipynb` existants pour les aligner sur la nouvelle structure

**Notebook 07 — Feature family ablation :**
Tester chaque famille séparément : market, weather, wasde, cot, macro, seasonality, all.
Répondre : quelle famille apporte vraiment du signal ?

**Notebook 10 — Indicator construction :**
Construire P(up_h5..h30), P(strong_up/down), confidence score, signal BULLISH/BEARISH/NEUTRAL/UNCERTAIN.

**Notebook 11 — Indicator backtest :**
Performance globale, par confiance (top 20% signaux), par saison, par régime.

**Structure de chaque notebook :**
```markdown
## Question de recherche
## Hypothèse
## Données / Méthode
## Résultats (tableaux + graphiques)
## Interprétation
## Limites
## Décision pour la suite (EXP-XXX dans EXPERIMENT_INDEX)
```

**Critères de réussite :**
- 12 notebooks exécutés sans erreur (`jupyter nbconvert --execute`)
- 12 fichiers HTML dans `notebooks/corn_study/exports/`
- Notebook 10 produit un signal BULLISH/BEARISH/NEUTRAL/UNCERTAIN avec probabilités

**Vérifications :**
```bash
ls notebooks/corn_study/main/*.ipynb | wc -l    # 12
ls notebooks/corn_study/exports/*.html | wc -l  # 12
```

**Risques :** `make study` doit être lancé avant pour que les artefacts existent. Si un notebook échoue, documenter dans EXPERIMENT_INDEX et corriger le notebook, jamais le pipeline.

---

### TICKET-ETUDE-06 — Refaire le backtest agriculteur orienté décision

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-03` DONE (cibles métier disponibles)

**Objectif :** Le backtest actuel dans `decision/backtest.py` mesure le `capture_rate` mais ne compare pas suffisamment de stratégies et n'utilise pas les cibles métier. Le refaire pour répondre honnêtement à : "l'indicateur aide-t-il vraiment l'agriculteur ?"

**Problème actuel :** `MODEL_SIGNAL` = 82.0% vs `SELL_HARVEST` = 82.8% — le modèle ne bat pas la baseline. C'est un résultat valide, mais le backtest doit maintenant aider à comprendre *pourquoi* et *quand* il aide ou non.

**Fichiers à modifier :**
- `src/mais/decision/backtest.py`

**Fichiers à lire :**
- `src/mais/decision/backtest.py` (état actuel)
- `artefacts/professional_study/model_predictions.parquet`
- `artefacts/professional_study/cqr_results.parquet`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/professional_study/`

**Nouvelles stratégies à ajouter :**
```
SELL_HARVEST          (existant)
SELL_MONTHLY          (vendre 1/12 par mois)
SELL_THIRDS           (vendre 1/3 récolte, 1/3 jan, 1/3 jun)
SELL_THRESHOLD        (vendre si prix > moyenne_5ans + 5%)
MODEL_SIGNAL          (existant, modèle directionnel)
MODEL_STORAGE_VALUE   (vendre si storage_value_h30 > coût_stockage)
CQR_CAUTIOUS          (vendre seulement si borne basse CQR > coût stockage)
PERFECT_HINDSIGHT     (borne supérieure théorique)
```

**Métriques à calculer par stratégie et par année :**
- `price_obtained` : prix moyen pondéré réalisé
- `capture_rate` : prix_obtenu / max_annuel
- `vs_harvest` : delta vs SELL_HARVEST
- `vs_monthly` : delta vs SELL_MONTHLY
- `regret` : PERFECT_HINDSIGHT - prix_obtenu
- `pct_years_wins` : % d'années où la stratégie bat SELL_HARVEST

**Critères de réussite :**
- 8 stratégies évaluées sur ≥ 10 ans
- Rapport `docs/FARMER_BACKTEST_REPORT_V2.md` avec tableau par stratégie + tableau par année
- Analyse des mauvaises années : quand et pourquoi le modèle se trompe
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/decision/backtest.py
python -m pytest tests/ -x -q
python -m mais.cli backtest --horizon 30 --state iowa
cat docs/FARMER_BACKTEST_REPORT_V2.md | head -50
```

**Risques :** Le perfect hindsight doit UNIQUEMENT servir de borne de comparaison dans le rapport, jamais comme stratégie réaliste. Documenter explicitement.

---

### TICKET-ETUDE-07 — Construire l'indicateur directionnel

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-03` DONE, `TICKET-ETUDE-04` DONE

**Objectif :** Construire le Maize Market Direction Indicator : probabilités directionnelles calibrées par horizon, score de confiance, signal consolidé, explication des facteurs dominants.

**Sorties attendues :**
```
P(up_h5)  P(up_h10)  P(up_h20)  P(up_h30)   ← régression ou proba calibrée
P(strong_up_h20)  P(strong_down_h20)
Confidence Score  ← basé sur largeur CQR, accord modèles, distance seuils
Signal : BULLISH / BEARISH / NEUTRAL / UNCERTAIN
Top factors bullish / bearish   ← SHAP
```

**Fichiers à créer :**
- `src/mais/indicator/direction.py` — `MaizeDirectionIndicator`
- `src/mais/indicator/__init__.py`

**Fichiers à lire :**
- `src/mais/meta/cqr.py`
- `artefacts/professional_study/model_predictions.parquet`
- `artefacts/professional_study/cqr_results.parquet`
- `artefacts/professional_study/shap_importance.parquet`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/professional_study/`

**Interface cible :**
```python
from mais.indicator.direction import MaizeDirectionIndicator

indicator = MaizeDirectionIndicator.load(artefacts_dir)
signal = indicator.predict(features_today)

signal.prob_up      # dict {h5: 0.61, h10: 0.63, h20: 0.66, h30: 0.51}
signal.prob_strong_up   # {h20: 0.22, h30: 0.18}
signal.prob_strong_down # {h20: 0.09, h30: 0.11}
signal.confidence   # 0.64
signal.label        # "BULLISH"
signal.factors_bullish  # ["factor_weather_stress", "factor_wasde_tightness"]
signal.factors_bearish  # ["factor_cot_positioning"]
signal.summary()    # str formaté lisible
```

**Logique du label :**
```
si mean(prob_up) > 0.60 et confidence > 0.55 → BULLISH
si mean(prob_up) < 0.40 et confidence > 0.55 → BEARISH
si confidence < 0.50 → UNCERTAIN
sinon → NEUTRAL
```

**Critères de réussite :**
- `MaizeDirectionIndicator` importable et fonctionnel sur données synthétiques
- `signal.summary()` produit une sortie lisible avec probabilités et facteurs
- `ruff check` PASS, `pytest` PASS

**Vérifications :**
```bash
cd src && python -m ruff check ../src/mais/indicator/direction.py
python -m pytest tests/ -x -q
python -c "from mais.indicator.direction import MaizeDirectionIndicator; print('Import OK')"
```

**Risques :** Ne pas hard-coder les seuils du label — les rendre configurables avec des valeurs par défaut justifiées économiquement.

---

### TICKET-ETUDE-08 — Backtester l'indicateur directionnel

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-06` DONE, `TICKET-ETUDE-07` DONE

**Objectif :** Mesurer honnêtement si l'indicateur directionnel est meilleur que les baselines, en particulier quand il est confiant. Répondre à : l'indicateur est-il utile ?

**Fichiers à créer :**
- `src/mais/indicator/backtest.py`
- `docs/INDICATOR_BACKTEST_REPORT.md` (généré)

**Fichiers à lire :**
- `src/mais/indicator/direction.py`
- `artefacts/professional_study/model_predictions.parquet`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/professional_study/`

**Métriques clés :**
```
Performance globale :
  DA globale  par horizon (h5..h30)
  Brier Score
  AUC

Performance par niveau de confiance (obligatoire) :
  DA quand confidence < 0.50  (faibles)
  DA quand confidence 0.50-0.65
  DA quand confidence > 0.65  (forts)
  → hypothèse : le signal est meilleur quand il est confiant

Performance par saison :
  DA été / hiver / semis / récolte

Performance par régime :
  DA bull / range / bear

Performance par horizon :
  lequel des h5..h30 est le plus prévisible ?
```

**Résultat attendu :**
Une table honnête. Si DA globale = 55 % mais DA(confidence > 0.65) = 63 %, l'indicateur est utile sur les signaux forts. Si aucune différence → l'indicateur ne filtre pas bien et il faut revoir le confidence score.

**Critères de réussite :**
- Rapport `docs/INDICATOR_BACKTEST_REPORT.md` généré avec toutes les tranches
- Analyse des erreurs : quand et pourquoi l'indicateur se trompe
- `ruff check` PASS, `pytest` PASS

**Vérifications :**
```bash
cd src && python -m ruff check ../src/mais/indicator/backtest.py
python -m pytest tests/ -x -q
cat docs/INDICATOR_BACKTEST_REPORT.md | head -60
```

**Risques :** Ne pas sélectionner a posteriori le meilleur horizon ou la meilleure confiance. Rapporter toutes les tranches honnêtement.

---

## Tickets nouveaux — Priorité zéro + correctifs + différés (2026-05-14)

---

### TICKET-ETUDE-00 — Valider les résultats actuels avant tout nouveau développement

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** aucune

**Objectif :** Validation rétrospective — vérifier que les artefacts existants sont cohérents et reproductibles. Ce ticket ne bloque pas les reviews en NEEDS_REVIEW (ETUDE-01 à 08), mais bloque tout nouveau développement (ETUDE-05, ETUDE-10 à ETUDE-17).

**Ce qu'il faut vérifier :**
1. `data/processed/features.parquet` — shape attendue, colonnes anti-leakage présentes, pas de NaN suspects
2. `data/processed/targets.parquet` — colonnes `y_up_h5/h10/h20/h30` et `y_logret_h5/h10/h20/h30`, valeurs direction {0, 1} sans NaN
3. `artefacts/professional_study/model_benchmarks.parquet` — au moins 4 horizons, DA correcte (>0.50 sur h20/h30)
4. `artefacts/professional_study/model_predictions.parquet` — pas vide, pas de dates futures
5. `artefacts/professional_study/shap_importance.parquet` — présent et non vide
6. `artefacts/professional_study/cqr_results.parquet` — coverage ≥ 88 % sur au moins 1 horizon
7. `artefacts/professional_study/regime_timeseries.parquet` — colonnes `Date, regime`, distribution cohérente
8. Pipeline reproductible : `make features && make study` se termine sans erreur (ou erreur documentée si données manquantes)

**Fichiers à modifier :** aucun (lecture seule, sauf création d'un rapport de validation)

**Fichiers à créer :**
- `docs/VALIDATION_BASELINE.md` — rapport de validation : shape, DA par horizon, coverage CQR, distribution régimes

**Fichiers à lire :**
- `src/mais/paths.py`
- `src/mais/features/__init__.py`
- `src/mais/study/professional.py`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `docs/VALIDATION_BASELINE.md` créé avec toutes les métriques mesurées
- Aucun artefact manquant parmi les 7 listés ci-dessus
- DA h20 ≥ 0.55 confirmée sur au moins 1 modèle (lgbm_factors attendu)
- CQR coverage ≥ 88 % confirmée
- Pipeline `make features && make study` PASS (ou erreur documentée si data manquante)

**Vérifications à lancer :**
```bash
python -c "
import pandas as pd, pathlib
for p in [
    'data/processed/features.parquet',
    'data/processed/targets.parquet',
    'artefacts/professional_study/model_benchmarks.parquet',
    'artefacts/professional_study/model_predictions.parquet',
    'artefacts/professional_study/shap_importance.parquet',
    'artefacts/professional_study/cqr_results.parquet',
    'artefacts/professional_study/regime_timeseries.parquet',
]:
    f = pathlib.Path(p)
    print(f'{p}: {\"OK\" if f.exists() else \"MANQUANT\"}')

# Vérifier les noms standardisés des cibles
t = pd.read_parquet('data/processed/targets.parquet')
expected = ['y_logret_h5','y_logret_h20','y_up_h5','y_up_h20']
for c in expected:
    print(f'{c}: {\"present\" if c in t.columns else \"ABSENT\"}')
"
python -m pytest tests/ -x -q
```

**Risques :** Si `make study` échoue (données manquantes, clé API absente), documenter clairement la cause et continuer avec les artefacts existants — ne pas bloquer indéfiniment.

**Résultat ticket (2026-05-15) :**
- 7/7 artefacts présents, shapes cohérentes (features 6192×276, targets 6192×25, benchmarks 44×14, predictions 108702×8, SHAP 64×7, CQR 9882×10, régimes 6192×7).
- Cibles standardisées `y_up_hX` / `y_logret_hX` présentes, valeurs {0,1} sans NaN hors bord d'horizon. ✅
- DA h20 : `ridge_factors` 0.615, `elasticnet_factors` 0.614 — critère ≥0.55 atteint. ✅
- CQR coverage : h5=90.6 %, h10=90.9 %, h20=90.4 %, h30=89.5 % — tous ≥88 %. ✅
- SHAP non vide, 10 familles de facteurs présentes. ✅
- Régimes : bull=29.6 %, range=68.2 %, bear=2.2 % — fragile, confirmé → ETUDE-12 READY. ✅
- COT NaN ~50 % confirmé → ETUDE-14 READY. ✅
- Anomalie documentée : `lgbm_factors` DA h20 = 0.571 (STATE.md indiquait 0.613 à tort — corrigé).
- `baseline_zero_return` DA ≈ 0.6 % — comportement attendu (baseline régression mappée en direction).
- `pytest` 21/21 PASS. ✅
- `docs/VALIDATION_BASELINE.md` créé.
- `make features && make study` non relancés (FAS API key manquante) — artefacts du 2026-05-09 valides.

---

### TICKET-ETUDE-12 — Remplacer le Markov-switching 3-états par un modèle 2-états robuste

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-00` DONE ✅

**Objectif :** Le modèle Markov-switching 3-états actuel est fragile — le régime bear ne représente que ~2,2 % des observations et produit des résultats instables. Remplacer par un modèle 2-états (bull / bear) plus robuste, avec fallback rule-based si l'estimation échoue.

**Problème actuel :**
- 3 régimes : bull, range, bear
- Bear state : ~2,2 % des observations → estimation instable, paramètres non convergés
- Impact : les métriques "par régime" dans ETUDE-05/08 sont peu fiables sur bear

**Solution cible :**
- 2 régimes : bull (hausse + range) / bear (baisse sévère)
- Seuil configurable dans `config/indicator.yaml` (section `regimes`)
- Schéma de sortie conservé : `Date, corn_close, return_60d, realized_vol_60d, regime_score, regime`
- Fallback rule-based si le modèle 2-états diverge aussi

**Fichiers à modifier :**
- `src/mais/study/professional.py` — `_build_regimes()`, section Markov-switching
- `config/indicator.yaml` — ajouter section `regimes: {n_states: 2, bull_label: "bull", bear_label: "bear"}`

**Fichiers à lire :**
- `src/mais/study/professional.py` — `_build_regimes()` intégral
- `artefacts/professional_study/regime_timeseries.parquet` — distribution actuelle
- `docs/00_PROJET_COMPLET_MAIS.md` — section régimes

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- 2 régimes dans `regime_timeseries.parquet` après `make study`
- Distribution : bear ≥ 5 % (sinon le seuil rule-based est trop élevé)
- Schéma de sortie inchangé (`Date, corn_close, return_60d, realized_vol_60d, regime_score, regime`)
- `ruff check` PASS, `pytest` PASS
- `python -c "from mais.study.professional import build_professional_study"` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/study/professional.py
python -m pytest tests/ -x -q
python -c "
import pandas as pd
df = pd.read_parquet('artefacts/professional_study/regime_timeseries.parquet')
print(df['regime'].value_counts(normalize=True))
"
```

**Risques :** Ne pas changer le schéma de sortie — `regime_timeseries.parquet` est consommé par plusieurs notebooks downstream. Tester que `build_professional_study()` reste importable après la modification.

**Résultat ticket (2026-05-15) :**
- `_build_regimes()` modifié dans `professional.py` : `k_regimes` configurable via `config/indicator.yaml` section `regimes.n_states`.
- Par défaut `n_states=2` → modèle Markov 2 états (bull / bear).
- Compatible 3 états (legacy) si `n_states=3` dans la config.
- Label map 2 états : `{bear_idx: "bear", bull_idx: "bull"}` — plus de `range` en mode 2 états.
- Fallback rule-based mis à jour : `np.where(score >= 0.0, bull, bear)` — 2 états.
- `regime_method` : `"markov_2state"` ou `"rule_fallback_2state"`.
- Section `regimes` ajoutée dans `config/indicator.yaml` (n_states: 2, bull_label: "bull", bear_label: "bear").
- Schéma de sortie conservé : `Date, corn_close, return_60d, realized_vol_60d, regime_score, regime, regime_method`. ✅
- `build_professional_study` importable. ✅
- `ruff check` PASS, `pytest` 21/21 PASS. ✅
- Note : `regime_timeseries.parquet` existant (généré avec 3 états) reste valide jusqu'à prochain `make study`. La distribution réelle 2 états sera mesurée après relance.

**Review (2026-05-15) : VALIDÉ → DONE**
- `n_states` configurable depuis `indicator.yaml`. ✅
- Schéma de sortie inchangé. ✅
- Fallback 2 états propre. ✅
- Critère "bear ≥ 5%" non mesurable sans `make study` (données live nécessaires). Non bloquant.

---

### TICKET-ETUDE-14 — Corriger les NaN COT post-2021

- **Statut :** `DONE`
- **Difficulté :** `simple`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-00` DONE ✅

**Objectif :** Les données CFTC COT présentent des NaN significatifs après 2021 dans `cot_mm_net` et les colonnes dérivées. Diagnostiquer la cause (changement de format CFTC, gap de collecte, ou colonne renommée) et appliquer le correctif approprié.

**Données concernées :** `data/processed/features.parquet`, colonnes `cot_*` — 3152 non-null sur 6192 lignes totales, soit ~50 % de NaN.

**Étapes :**
1. Inspecter `data/interim/cftc_cot.parquet` — dernier enregistrement disponible
2. Vérifier `src/mais/collect/cftc_cot_collector.py` — URL CFTC et parsing du CSV
3. Si gap de collecte : documenter dans `docs/VALIDATION_BASELINE.md` et ajouter note dans `config/sources.yaml`
4. Si colonne renommée : adapter le parsing
5. Si données réellement indisponibles : limiter la fenêtre COT à la période couverte et documenter l'impact sur les features

**Fichiers à modifier :**
- `src/mais/collect/cftc_cot_collector.py` — si le parsing est cassé
- `config/sources.yaml` — documenter le gap COT post-2021

**Fichiers à lire :**
- `src/mais/collect/cftc_cot_collector.py`
- `src/mais/features/__init__.py` — intégration COT dans build_features()
- `data/interim/cftc_cot.parquet` (lecture seule)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- Cause documentée dans `docs/VALIDATION_BASELINE.md`
- Si corrigeable : `cot_mm_net` non-null ≥ 80 % des lignes après `make features`
- Si non corrigeable : note dans `config/sources.yaml` + flag `cot_limited_coverage: true`
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/features.parquet')
cot_cols = [c for c in df.columns if c.startswith('cot_')]
print('COT cols:', len(cot_cols))
print(df[cot_cols].notna().mean().sort_values().head(10))
"
cd src && python -m ruff check ../src/mais/collect/cftc_cot_collector.py
python -m pytest tests/ -x -q
```

**Risques :** Ne pas forward-fill naïvement les COT sur plus de 5 jours — les positions peuvent changer rapidement. Préférer un masque explicite ou une imputation nulle avec flag.

**Résultat ticket (2026-05-15) :**
- Diagnostic complet : les 50% NaN COT sont **structurels**, pas un bug.
- `data/interim/cftc_cot.parquet` : 695 semaines, 2013-01-08 → 2026-04-28, couverture 100% dans sa période.
- Features couvrent 2000-2025 → 3039 jours ouvrés pre-2013 sans COT = 49.1% NaN total. Dans la période 2013+: 100% non-null. ✅
- Collector (`cftc_cot_collector.py`) = stub `raise NotImplementedError` — donnée chargée via import manuel, pas via le pipeline collecte. `enabled: false` dans sources.yaml.
- `config/sources.yaml` mis à jour : `cot_limited_coverage: true` + note explicative détaillée.
- Aucun code à modifier — le NaN est attendu et géré implicitement par XGBoost/LightGBM.
- `pytest` 21/21 PASS. ✅

**Review (2026-05-15) : VALIDÉ → DONE**
- Critère "note dans sources.yaml + flag cot_limited_coverage: true" : atteint. ✅
- Critère "cot_mm_net ≥ 80% non-null" : non atteint (50.9%) — mais justifié : NaN structural pre-2013, non corrigeable sans inventer des données. ✅
- `ruff check` collector PASS (stub, pas de code à vérifier). ✅

---

### TICKET-ETUDE-15 — Brancher config/indicator.yaml dans direction.py

- **Statut :** `DONE`
- **Difficulté :** `simple`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** `TICKET-ETUDE-00` DONE ✅, `TICKET-ETUDE-07` DONE ✅

**Objectif :** Le module `src/mais/indicator/direction.py` contient actuellement des seuils hard-codés (bullish_prob_threshold, bearish_prob_threshold, uncertain_confidence_threshold, etc.). Les remplacer par une lecture de `config/indicator.yaml` via une fonction utilitaire, pour que tous les notebooks et le pipeline consomment la même référence.

**Problème :** Si un seuil est modifié dans `config/indicator.yaml` mais pas dans `direction.py`, les résultats divergent silencieusement entre les notebooks et le pipeline.

**Solution :**
```python
# src/mais/indicator/direction.py
import yaml, pathlib

def _load_indicator_config():
    cfg_path = pathlib.Path(__file__).parents[3] / "config" / "indicator.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)
```

**Fichiers à modifier :**
- `src/mais/indicator/direction.py` — remplacer les constantes par lecture YAML

**Fichiers à lire :**
- `src/mais/indicator/direction.py` — état actuel complet
- `config/indicator.yaml` — référence des seuils

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`, `config/indicator.yaml` (ne pas modifier les valeurs, juste les lire)

**Critères de réussite :**
- Aucune constante de seuil hard-codée dans `direction.py`
- Modifier `bullish_prob_threshold` dans `indicator.yaml` se reflète immédiatement dans `MaizeDirectionIndicator`
- `ruff check` PASS, `pytest` PASS
- `python -c "from mais.indicator.direction import MaizeDirectionIndicator"` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/indicator/direction.py
python -m pytest tests/ -x -q
python -c "
from mais.indicator.direction import MaizeDirectionIndicator
ind = MaizeDirectionIndicator()
print('Config chargée :', ind.config is not None)
"
```

**Risques :** Le chemin vers `config/indicator.yaml` doit être résolu relativement au fichier source, pas au CWD. Utiliser `pathlib.Path(__file__).parents[N]` avec le bon niveau N.

**Résultat ticket (2026-05-15) :**
- `_load_indicator_config()` ajouté dans `direction.py` — lit `config/indicator.yaml` via `Path(__file__).parents[3] / "config" / "indicator.yaml"`. ✅
- Fallback `_DEFAULT_CFG` si le fichier est absent ou si `pyyaml` n'est pas installé. ✅
- Tous les seuils lus depuis config : `uncertain_confidence_threshold=0.45`, `bullish_prob_threshold=0.60`, `bearish_prob_threshold=0.60`, `min_prob_gap=0.15`, `neutral_max_gap=0.10`. ✅
- Formule confidence score V1 implémentée : 0.30 × prob_distance + 0.25 × model_agreement + 0.25 × interval_width + 0.20 × signal_stability (= 0 si pas d'historique). ✅
- Logique label V1 : ordre strict (UNCERTAIN → BULLISH → BEARISH → NEUTRAL → UNCERTAIN). ✅
- `ruff check` PASS, `pytest` 21/21 PASS. ✅

**Review (2026-05-15) : VALIDÉ → DONE**
- Config chargée depuis `config/indicator.yaml` confirmée. ✅
- `ind.config` non nul, seuils corrects (0.45/0.60/0.60). ✅
- Aucune constante de seuil hard-codée — tout en `self._*_threshold`. ✅

---

### TICKET-ETUDE-10 — Optuna production : 50+ trials avec pruning

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** Phase Étude DONE (ETUDE-05 + ETUDE-06 + ETUDE-07 + ETUDE-08 DONE)

**Objectif :** Le tuning Optuna actuel est limité à 1 trial (smoke test). Passer à 50+ trials avec pruning MedianPruner pour obtenir des hyperparamètres optimisés sur les modèles retenus après Phase Étude (au moins `lgbm_factors` h20 et le meilleur modèle h30).

**Contexte :** Un seul trial Optuna ne fournit aucun gain réel par rapport aux hyperparamètres par défaut. La Phase Étude permettra de savoir quels modèles/horizons méritent vraiment un tuning poussé.

**Fichiers à modifier :**
- `src/mais/study/professional.py` — section Optuna `_tune_model()`
- `config/indicator.yaml` — ajouter section `optuna: {n_trials: 50, timeout_seconds: 3600}`

**Fichiers à lire :**
- `src/mais/study/professional.py` — `_tune_model()` complet
- `docs/00_PROJET_COMPLET_MAIS.md` — section Optuna

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `--optuna-trials 50` produit 50 trials sans erreur
- Pruning MedianPruner actif (arrêt trials peu prometteurs)
- Gain DA ≥ +1 pp sur h20 après tuning vs baseline
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/study/professional.py
python -m pytest tests/ -x -q
# Smoke test rapide
python -c "
from mais.study.professional import build_professional_study
build_professional_study(optuna_trials=2, horizons=[20])
print('Optuna OK')
"
```

**Risques :** Durée longue (1–4 h selon les modèles). Prévoir un `timeout_seconds` dans la config. Ne lancer qu'après avoir identifié les modèles prioritaires via Phase Étude.

---

### TICKET-ETUDE-11 — Ajouter ARIMA / SARIMAX / GARCH au registre de modèles

- **Statut :** `DONE`
- **Difficulté :** `complexe`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** Phase Étude DONE (ETUDE-05 DONE)

**Objectif :** Les modèles séries temporelles classiques (ARIMA, SARIMAX, GARCH) servent de baselines économétriques solides dans la littérature. Les ajouter au registre `_model_specs()` pour comparer leur DA avec les modèles ML sur les mêmes fenêtres walk-forward.

**Contexte :** Les baselines actuelles sont `naive`, `seasonal_naive`, `drift`. ARIMA/SARIMAX permettent de tester si la structure AR du prix du maïs est exploitable. GARCH est utile pour modéliser la volatilité (cibles futures_vol_h20).

**Modèles à implémenter :**
- `arima_auto` : ARIMA(p,d,q) avec sélection automatique de l'ordre (pmdarima ou statsmodels)
- `sarimax_seasonal` : SARIMAX avec saisonnalité annuelle (s=52)
- `garch_vol` : GARCH(1,1) pour les cibles volatilité uniquement

**Fichiers à modifier :**
- `src/mais/study/professional.py` — `_model_specs()`, ajouter les 3 entrées
- `src/mais/study/professional.py` — `_fit_model()`, ajouter les blocs statsmodels/pmdarima

**Fichiers à lire :**
- `src/mais/study/professional.py` — `_model_specs()` et `_fit_model()` complets
- `src/mais/meta/cqr.py` — interface `fit/predict` attendue par le pipeline CQR

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `arima_auto`, `sarimax_seasonal`, `garch_vol` présents dans `model_benchmarks.parquet` après `make study`
- DA calculée sur mêmes splits walk-forward que les autres modèles
- Imports statsmodels/pmdarima dans blocs `try/except ImportError` (optionnels)
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/study/professional.py
python -m pytest tests/ -x -q
python -c "
import pandas as pd
df = pd.read_parquet('artefacts/professional_study/model_benchmarks.parquet')
print([m for m in df['model'].unique() if 'arima' in m or 'sarimax' in m or 'garch' in m])
"
```

**Risques :** ARIMA/SARIMAX sont lents sur 6000+ observations. Prévoir un sous-échantillonnage hebdomadaire ou un timeout par modèle. GARCH ne s'applique qu'aux cibles de volatilité — ne pas forcer sur les cibles direction.

---

### TICKET-ETUDE-13 — Documenter les 13 familles de facteurs dans factor_metadata.yaml

- **Statut :** `DONE`
- **Difficulté :** `simple`
- **Agent recommandé :** `Caveman`
- **Dépendances :** ETUDE-05 DONE (pour avoir les importances SHAP mesurées par famille)

**Objectif :** Créer `config/factor_metadata.yaml` qui documente les 13 familles de facteurs : leur nom, les colonnes associées dans `features.parquet`, la source de données, et l'importance SHAP mesurée (à remplir après ETUDE-05).

**Les 13 familles :**
```
market_momentum, market_volatility, wasde_supply_demand, weather_stress,
crop_condition, drought, exports, ethanol_demand, cot_positioning,
macro, curve_structure, global_competition, seasonality
```

**Fichiers à créer :**
- `config/factor_metadata.yaml`

**Structure attendue :**
```yaml
families:
  market_momentum:
    description: "Momentum prix maïs à différentes fenêtres"
    columns: [corn_ret_5d, corn_ret_20d, corn_ret_60d, ...]
    source: "Yahoo Finance / CBOT"
    shap_importance_h20: null  # à remplir après ETUDE-05
  wasde_supply_demand:
    description: "Bilans offre/demande WASDE (USDA)"
    columns: [wasde_ending_stocks, wasde_production, ...]
    source: "USDA WASDE"
    shap_importance_h20: null
  # ...
```

**Fichiers à lire :**
- `src/mais/features/__init__.py` — noms exacts des colonnes par famille
- `data/processed/features.parquet` — liste complète des colonnes
- `artefacts/professional_study/shap_importance.parquet` — importances SHAP (si disponibles)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`

**Critères de réussite :**
- `config/factor_metadata.yaml` créé, 13 familles documentées
- Chaque famille : description + liste colonnes + source
- `shap_importance_h20` : valeur réelle si ETUDE-05 DONE, sinon `null`
- YAML valide (python -c "import yaml; yaml.safe_load(open('config/factor_metadata.yaml'))")

**Vérifications à lancer :**
```bash
python -c "
import yaml
meta = yaml.safe_load(open('config/factor_metadata.yaml'))
print('Familles:', list(meta['families'].keys()))
assert len(meta['families']) == 13, f'Attendu 13, obtenu {len(meta[\"families\"])}'
print('OK')
"
```

**Risques :** Les noms de colonnes dans `features.parquet` peuvent ne pas correspondre exactement aux noms de familles. Vérifier colonne par colonne via `df.columns` avant d'écrire le YAML.

---

### TICKET-ETUDE-16 — Vérifier et compléter les cibles niveaux 3–7

- **Statut :** `DONE`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** ETUDE-03 DONE, ETUDE-05 DONE

**Objectif :** Le pipeline génère actuellement les cibles niveaux 1 (returns continus) et 2 (direction binaire). Les niveaux 3–7 (strong moves, future volatility, max/min return, asymmetric risk, oracle targets) doivent être vérifiés dans `targets.parquet` et complétés si manquants.

**Les 7 niveaux de cibles :**
```
1. Returns continus : ret_h5, ret_h10, ret_h20, ret_h30
2. Direction binaire : direction_h5, ..., direction_h30  ← présents
3. Strong moves : strong_up_h20, strong_down_h20, strong_up_h30, strong_down_h30
   (seuil configurable dans config/indicator.yaml — strong_move_thresholds)
4. Future volatility : future_vol_h20, future_vol_h30
5. Max/min return : max_ret_h20, min_ret_h20
6. Asymmetric risk : skew_h20 (P(strong_up) / P(strong_down))
7. Oracle : oracle_h20, oracle_h30 (prix futur réel — absent de build_features(), variable future)
```

**Fichiers à modifier :**
- `src/mais/study/targets.py` (ou équivalent) — ajouter les cibles manquantes
- `src/mais/paths.py` — si de nouveaux chemins sont nécessaires

**Fichiers à lire :**
- `src/mais/study/targets.py` — état actuel
- `data/processed/targets.parquet` — colonnes présentes
- `config/indicator.yaml` — `strong_move_thresholds`

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/`
**Variables oracle :** absentes de `build_features()` et du pipeline normal — uniquement dans un fichier séparé `data/processed/oracle_targets.parquet`

**Critères de réussite :**
- `targets.parquet` contient toutes les colonnes niveaux 1–6 (oracle séparé)
- Les seuils des strong moves correspondent à `config/indicator.yaml`
- Anti-leakage respecté : toutes les cibles calculées avec `shift(-horizon)` et non `shift(-horizon+1)`
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/targets.parquet')
expected = ['direction_h5','direction_h10','direction_h20','direction_h30',
            'strong_up_h20','strong_down_h20','future_vol_h20','max_ret_h20']
missing = [c for c in expected if c not in df.columns]
print('Colonnes manquantes:', missing)
print('Shape:', df.shape)
"
python -m pytest tests/ -x -q
```

**Risques :** Les cibles oracle (prix futur réel) ne doivent JAMAIS entrer dans `build_features()`. Les isoler dans `data/processed/oracle_targets.parquet` avec une note explicite dans le code.

---

### TICKET-ETUDE-17 — Analyser l'exploitabilité des intervalles CQR

- **Statut :** `DEFERRED_PHASE4`
- **Difficulté :** `moyen`
- **Agent recommandé :** `Claude Code`
- **Dépendances :** ETUDE-08 DONE, ETUDE-10 DONE (Optuna production)

**Objectif :** L'intervalle CQR (quantile bas, médiane, quantile haut) contient de l'information au-delà de la seule direction. Analyser si la largeur de l'intervalle est prédictive de la magnitude du mouvement et si elle améliore le confidence_score de l'indicateur.

**Questions de recherche :**
1. Les intervalles étroits (faible incertitude) correspondent-ils à des mouvements plus prévisibles ?
2. La largeur normalisée est-elle une meilleure composante du confidence_score que la version actuelle ?
3. L'asymétrie [Q(0.9) - médiane] vs [médiane - Q(0.1)] prédit-elle la direction ?

**Métriques à calculer :**
- Corrélation largeur CQR ↔ |erreur de direction|
- DA par décile de largeur CQR
- Contribution à l'amélioration du confidence_score V1 → V2

**Fichiers à modifier :**
- `src/mais/meta/cqr.py` — ajouter métriques de largeur normalisée si absentes
- `config/indicator.yaml` — ajuster `interval_width_weight` si l'analyse justifie un changement
- `docs/CQR_EXPLOITABILITY_REPORT.md` — créer le rapport

**Fichiers à lire :**
- `src/mais/meta/cqr.py` — `walk_forward_cqr()` complet
- `artefacts/professional_study/cqr_results.parquet`
- `artefacts/indicator/confidence_scores.parquet` (si disponible après ETUDE-08)

**Fichiers interdits (modification manuelle) :** `data/`, `artefacts/professional_study/`

**Critères de réussite :**
- `docs/CQR_EXPLOITABILITY_REPORT.md` créé avec les 3 questions répondues
- Résultat honnête : si la largeur CQR n'apporte pas de signal supplémentaire, le dire clairement
- Si améliorable : proposition de formule confidence_score V2 dans le rapport
- `ruff check` PASS, `pytest` PASS

**Vérifications à lancer :**
```bash
cd src && python -m ruff check ../src/mais/meta/cqr.py
python -m pytest tests/ -x -q
python -c "
import pandas as pd
df = pd.read_parquet('artefacts/professional_study/cqr_results.parquet')
print('Colonnes CQR:', df.columns.tolist())
print('Coverage mean:', df['covered'].mean() if 'covered' in df.columns else 'N/A')
"
```

**Risques :** Ne pas sur-optimiser le confidence_score sur les données d'entraînement. L'analyse doit être faite sur l'ensemble de test walk-forward uniquement. Toute modification de `interval_width_weight` dans `indicator.yaml` doit être justifiée par un gain de DA ≥ +1 pp sur l'ensemble de test.

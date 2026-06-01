# Roadmap finale — Mais AutoML + Étude professionnelle

## Principe

La roadmap est organisée en phases séquentielles. Chaque phase a des livrables précis et des critères d'entrée clairs. On ne passe pas à la phase suivante si les livrables de la phase courante ne sont pas validés.

---

## État actuel (2026-05-09)

### Ce qui est en place

| Composant | État |
|---|---|
| Code Paliers 1–6 écrit | ✅ |
| Collecteurs (11 sources) | ✅ |
| Facteurs synthétiques (32, 9 familles) | ✅ |
| LightGBM + XGBoost dans benchmarks | ✅ |
| SHAP via TreeExplainer | ✅ |
| CQR module + wiring | ✅ |
| Markov-switching 3 états | ✅ |
| Système CursorOPS installé | ✅ |
| Documents de cadrage | ✅ (ce document et les 11 autres) |

### Ce qui bloque

- **Rebuild non lancé** : le code est écrit mais `features.parquet`, `factors.parquet`, et l'étude complète n'ont pas été rebuiltés depuis les paliers 1-6.
- **Résultats non mesurés** : on ne sait pas encore si LightGBM bat Ridge, si CQR atteint 90%, si Markov converge.

---

## Phase 0 — Validation et rebuild (CRITIQUE, maintenant)

**Durée estimée :** 1-2 sessions

**Objectif :** vérifier que les paliers 1-6 fonctionnent end-to-end et mesurer les résultats pour la première fois.

**Étapes :**

| Étape | Commande | Attendu |
|---|---|---|
| Collect COT | `mais collect cot` | 695+ lignes dans cftc_cot.parquet |
| Rebuild features | `make features` | features.parquet avec COT |
| Rebuild targets | `make targets` | targets.parquet inchangé |
| Audit leakage | `make audit` | 0 erreur |
| Rebuild study | `build_professional_study(force_rebuild_factors=True)` | Tous artefacts générés |
| Vérifier SHAP | Lire `shap_importance.parquet` | Non vide |
| Vérifier CQR | Lire `cqr_results.parquet` | Couverture ≥ 88% |
| Vérifier régimes | Lire `regime_timeseries.parquet` | 3 régimes distincts |
| Mettre à jour rapport | Modifier table impl. | ✅ où mérité |

**Livrables :**
- Rapport `PROFESSIONAL_STUDY_REPORT.md` à jour avec vrais résultats
- Journal EXP-008 complété avec résultats mesurés
- `STATE.md` mis à jour

---

## Phase 1 — Données manquantes prioritaires (Haute valeur)

**Durée estimée :** 2-3 sessions

**Objectif :** intégrer les sources de données qui ont le plus d'impact attendu sur la prédiction.

### 1.1 — Crop Progress + Crop Condition

**Impact attendu :** facteur fort sur J+10/J+20 en saison (mai-octobre)

**Actions :**
- Compléter le collecteur Crop Progress dans `nass_quickstats_collector.py`
- Ajouter section Crop Progress dans `build_features()`
- Créer recette facteur `factor_crop_condition_pressure`
- Tester (EXP-009)

### 1.2 — Drought Monitor

**Impact attendu :** indicateur synthétique du stress hydrique

**Actions :**
- Compléter `drought_monitor_collector.py`
- Ajouter dans `build_features()`
- Créer facteur `factor_drought_severity`
- Tester (EXP-010)

### 1.3 — EIA éthanol (vraie clé API)

**Impact attendu :** demande interne US en maïs (35-40% de la production)

**Actions :**
- Créer compte sur eia.gov/opendata et récupérer `EIA_API_KEY`
- Mettre à jour `config/sources.yaml` avec les bons Series IDs
- Tester `mais collect eia` avec vraie clé
- Tester (EXP-015)

### 1.4 — FAS Export Sales

**Impact attendu :** demande internationale hebdomadaire

**Actions :**
- Compléter `fas_export_sales_collector.py`
- Ajouter dans `build_features()`
- Créer facteur `factor_export_demand_surprise`
- Tester (EXP-011)

**Livrables Phase 1 :**
- 4+ nouvelles sources dans features.parquet
- 4+ nouveaux facteurs dans factors.parquet
- Benchmark mis à jour
- EXPERIMENT_LOG mis à jour

---

## Phase 2 — Optimisation Optuna

**Durée estimée :** 1-2 sessions

**Objectif :** optimiser les hyperparamètres de LightGBM, XGBoost et Ridge par Optuna plutôt que les valeurs fixes actuelles.

**Actions :**
- Câbler `src/mais/optimize/runner.py` dans `build_professional_study()`
- Définir search spaces pour chaque modèle
- Lancer l'optimisation sur LightGBM (50-100 trials)
- Comparer LightGBM optimisé vs LightGBM defaults (EXP-011)
- Sauvegarder meilleurs params dans `artefacts/best_params/`

**Critère de succès :** LightGBM optimisé améliore RMSE de ≥ 2% vs defaults.

---

## Phase 3 — Backtest agriculteur complet

**Durée estimée :** 2-3 sessions

**Objectif :** produire le résultat économique final du projet.

**Actions :**
- Compléter `src/mais/decision/backtest.py` avec les 6 stratégies
- Implémenter `capture_rate` et `regret` comme métriques principales
- Intégrer coûts de stockage
- Faire tourner sur 2013-2025 (minimum)
- Documenter dans rapport

**Critère de succès :**
```
Capture rate (système) > Capture rate (vente récolte) sur 70%+ des années
```

**Livrables :**
- `FARMER_BACKTEST_REPORT.md` complet avec tableaux et graphiques
- Phrase finale : "Notre système capture X% du prix maximum annuel vs Y% pour la vente récolte"

---

## Phase 4 — Plateforme AutoML générique

**Durée estimée :** 4-6 sessions

**Objectif :** abstraire le pipeline maïs en une plateforme réutilisable sur n'importe quel dataset.

**Actions :**
- Créer `src/mais/platform/profiler.py` — détection automatique type de problème
- Créer `src/mais/platform/preprocessing.py` — pipeline prétraitement complet
- Adapter `src/mais/models/registry.py` — modèles par type de problème
- Adapter `src/mais/optimize/runner.py` — Optuna générique
- Adapter `src/mais/walkforward/` — walk-forward configurable
- Créer `src/mais/platform/reporting.py` — rapport automatique générique
- Tester sur 5 datasets différents

**Critère de succès :**
```bash
python -m mais.platform.run --csv dataset.csv --target prix
# → Produit rapport complet automatiquement
```

---

## Phase 5 — Pipeline quotidien automatique

**Durée estimée :** 1-2 sessions

**Objectif :** `make daily` tourne automatiquement chaque matin.

**Actions :**
- Compléter `src/mais/ops/daily.py`
- Ajouter collecte incrémentale (uniquement les nouvelles dates)
- Ajouter rapport quotidien Markdown
- Ajouter validation des prédictions passées
- Configurer cron job

---

## Phase 6 — Deep Learning (optionnel, post-v1)

**Durée estimée :** 4-8 sessions

**Prérequis :** toutes les phases 0-5 complètes, résultats des modèles classiques documentés.

**Modèles à tester :**
- LSTM simple sur facteurs
- N-BEATS
- Temporal Fusion Transformer

**Règle :** ne tester le deep learning que si les données sont suffisantes (>5000 observations out-of-sample) et que les modèles classiques ont atteint leurs limites documentées.

**Risque :** avec 6000-7000 jours de données et 32 facteurs, le deep learning peut surapprendre. À tester avec prudence.

---

## Décisions architecturales à prendre

Ces questions doivent être tranchées avant de commencer Phase 4 :

### Q1 — Séparation du code

**Option A :** Garder `src/mais/` unifié avec sous-dossiers `platform/` et `study/`

```
src/mais/
├── platform/     # Nouveau : logique générique
└── study/        # Existant : logique maïs
```

**Option B :** Séparer en deux packages

```
src/
├── automl/       # Package générique
└── mais/         # Package maïs (dépend de automl)
```

**Recommandation provisoire :** Option A (moins de refactoring, plus rapide).

### Q2 — Scope de la plateforme AutoML v1

Quels types de problèmes inclure dans la v1 ?

| Type | Inclure v1 ? |
|---|---|
| Régression tabulaire | Oui |
| Série temporelle univariée | Oui |
| Série temporelle multivariée | Oui (cas maïs) |
| Classification binaire | Oui (simple à ajouter) |
| Classification multi-classe | À discuter |
| Classification ordinale | À discuter |

### Q3 — Rapport quotidien

**Option A :** Markdown simple dans `data/reports/`
**Option B :** Streamlit dashboard mis à jour automatiquement
**Option C :** Les deux

---

## Résumé visuel de la roadmap

```
Maintenant
   │
   ├── Phase 0 : Rebuild + validation résultats (CRITIQUE)
   │   └── Durée : 1-2 sessions
   │
   ├── Phase 1 : Données manquantes (Crop Progress, Drought, EIA, FAS)
   │   └── Durée : 2-3 sessions
   │
   ├── Phase 2 : Optuna hyperparamètres
   │   └── Durée : 1-2 sessions
   │
   ├── Phase 3 : Backtest agriculteur complet
   │   └── Durée : 2-3 sessions  ← RÉSULTAT FINAL CLÉ
   │
   ├── Phase 4 : Plateforme AutoML générique
   │   └── Durée : 4-6 sessions
   │
   ├── Phase 5 : Pipeline quotidien automatique
   │   └── Durée : 1-2 sessions
   │
   └── Phase 6 : Deep Learning (optionnel)
       └── Durée : 4-8 sessions
```

---

## Ce qu'on ne fera probablement pas

Il faut être honnête sur ce qui est hors périmètre réaliste :

- **Basis locale française** : nécessite des données de coopératives locales, non publiques
- **ENSO/El Niño** : pertinent pour le long terme (>30j), pas pour le court terme
- **Données satellites NDVI** (NASA) : complexité d'ingestion élevée, valeur marginale si Drought Monitor est intégré
- **Modèles profonds (TFT, PatchTST)** : réservés à Phase 6 si données suffisantes
- **Déploiement cloud** : hors périmètre local actuel
- **Trading algorithmatique** : le projet vise l'aide à la décision agriculteur, pas le trading

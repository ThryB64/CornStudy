# Rapport d'audit du projet historique

Ce document est la version persistée de l'audit livré dans le plan
`audit_refonte_mais_*.plan.md`.

## 1. Bugs bloquants détectés et corrigés

### Bug A : cible cassée
- Fichier : [Models/config.yaml](../Models/config.yaml) ligne 12
- Symptôme : `target_col: is_last_lightning_cloud_ground` (copier-coller d'un autre projet)
- Conséquence : tous les résultats antérieurs reposent sur une mauvaise cible
- Fix v2 : [config/models.yaml](../config/models.yaml) déclare `primary_targets`, `classification_targets`, `binary_targets` comme listes explicites de cibles construites par `mais targets`

### Bug B : colonnes "fantômes" 5.98, 175.1, ...
- Fichier coupable : [script/corrige/complete_fred_data.py](../script/corrige/complete_fred_data.py) ligne 164 - écrit le CSV avec `header=False`
- Fichier victime : [script/corrige/database.py](../script/corrige/database.py) - relit avec `pd.read_csv(path)` qui prend la première ligne comme entête
- Conséquence : 10 colonnes du `database.csv` ont des noms de type `5.98`, `175.1`, `0.6321...`
- Fix v2 : `src/mais/clean/legacy_migration.py::_read_macro_fred_with_correct_header()` réattache les bons noms (extraits de `TARGET_ORDER` de l'ancien script)

### Bug C : doublons de colonnes `corn_*_1d.1`
- Cause : `indicateurs_completed.csv` et `historique_marche_mais_completed.csv` partagent ~25 colonnes ; `database.py` ligne 80 utilise `merge(... suffixes=("", "_dup"))` mais le suffixe pandas par défaut crée `.1`
- Fix v2 : `src/mais/utils/io.py::dedupe_columns()` supprime systématiquement les colonnes `.1` et préfixe les sources non-anchor (`macro_fred_*`, `wasde_*`, etc.) au lieu de laisser pandas trancher

### Bug D : stacking non implémenté
- Fichier : [Models/models/stacking_reg.py](../Models/models/stacking_reg.py) ligne 64 - `raise NotImplementedError`
- Conséquence : la "meta-database" promise dans la doc n'a jamais existé
- Fix v2 : `src/mais/meta/stacking.py` implémente une vraie meta-database (concat des prédictions OOF) + un méta-modèle (Ridge / Lasso / LGBM) walk-forward

### Bug E : couverture météo incohérente
- 6 fichiers `csv/meteo_etats/meteo_*.csv` font 214 KB vs ~650 KB pour les autres
- Conséquence : les anomalies z-score sont calculées sur des historiques de longueurs différentes
- Fix v2 : `src/mais/features/weather_belt.py` calcule **un** anom-z par variable au niveau du belt (pondéré par production) et garde seulement le top 5 d'états individuellement

## 2. Problèmes structurels identifiés

| Problème | Localisation | Solution v2 |
|---|---|---|
| `app.py` 4608 lignes | [Models/app.py](../Models/app.py) | Cassé en 4 pages dans [src/mais/ui/app.py](../src/mais/ui/app.py) |
| `optimize.py` 3286 lignes | [Models/optimize.py](../Models/optimize.py) | Cassé en `profiler.py`, `runner.py`, `feature_select.py`, `optuna_loop.py` |
| `pretraitement.py` 1841 lignes | [Models/pretraitement.py](../Models/pretraitement.py) | Cassé par responsabilité dans `src/mais/clean/` et `src/mais/leakage/` |
| 4 scripts shell qui se chevauchent | `*.sh` | Remplacés par un [Makefile](../Makefile) unifié |
| CSV partout | `csv/` | Parquet pour `data/interim/` et `data/processed/` (compat CSV via CLI) |
| Pas de `requirements.txt` figé | racine | `pyproject.toml` avec extras `[collect, ml, dl, ui, dev, api]` |
| Mélange français/anglais | partout | Code en anglais, doc en français |
| Aucun test | aucun | `tests/unit/test_leakage.py`, `test_targets.py`, `test_legacy_migration.py` |
| `venv/` au repo | racine | `.gitignore` |

## 3. Problèmes méthodologiques

| Problème | Solution v2 |
|---|---|
| Anti-leakage déclaratif jamais vérifié | `src/mais/leakage/audit.py` avec 5 checks automatiques |
| Météo non pondérée par production | `src/mais/features/weather_belt.py` (poids dans `config/sources.yaml`) |
| Pas de notion de fréquence | `lag_days` déclaré pour chaque source/feature dans les YAML |
| `merge_asof tolerance=3D` indistinct | flags `_is_stale_d` à venir Phase 1 |
| `yearly_rolling` trop espacé | `WalkForwardSplitter(step_days=21)` par défaut |
| Cible mal définie | `src/mais/targets.py` construit explicitement `y_logret_h{5,10,20,30}` |
| Métriques trading-only | `config/models.yaml::metrics.agronomic` ajoute `decision_pnl_vs_baseline` |
| Pas d'incertitude | `src/mais/meta/conformal.py` + adapters quantile (xgboost_quantile, ngboost) |

## 4. Variables manquantes critiques (au-delà de tes propositions)

Au-delà de tes 10 catégories, j'ai identifié dans `config/sources.yaml` et
`config/features.yaml` :

- DTN/Pro Farmer Crop Tour (août)
- Bolsa de Cereales Rosario condition reports hebdo Argentine (BCR)
- Freight rates Mississippi-NOLA (USDA AMS)
- NOLA export inspections (USDA FGIS hebdo)
- Renewable Fuel Standard (RVO) EPA
- Sentinel-2/MODIS NDVI corn belt
- Soil moisture SMAP NASA
- ENSO ONI El Niño/La Niña (driver dominant safrinha)
- Calendrier USDA (binaires `is_wasde_day`, `days_to_next_wasde`) [implémenté]
- Volatilité implicite options maïs CME
- Spreads inter-marchés (corn_brazil, corn_ukraine_fob)

## 5. Stratégies de prédiction recommandées

### 5.1 Reformuler la cible

Un agriculteur ne veut pas un return régressé. `src/mais/targets.py` génère :
- `y_logret_h{H}` (régression)
- `y_class_h{H}` (décile ordinale, anti-leakage)
- `y_up_h{H}`, `y_up_strong_h{H}`, `y_down_strong_h{H}` (binaires)
- `y_realized_vol_h{H}` (volatilité réalisée future)

### 5.2 Couche `decision/`

`src/mais/decision/` lit `config/decision.yaml` et applique des règles
priorisées qui combinent :
- probabilité directionnelle calibrée
- intervalles de prédiction (q10, q90)
- régime de marché (Markov-switching à wirer)
- coûts de stockage et basis local
- profil de l'agriculteur (cash-flow, aversion au risque)

### 5.3 Calibration et explicabilité

- Conformal prediction intégré (`src/mais/meta/conformal.py`)
- SHAP local : à wirer dans `src/mais/decision/explain.py` (Phase 3 future)

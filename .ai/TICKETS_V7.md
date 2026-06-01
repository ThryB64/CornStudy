# TICKETS V7 — Étude du cours du maïs CBOT + Euronext
## Programme complet V7 — 50 tickets (V7-00 à V7-40 + tickets infrastructure)

---

## Index des tickets

| ID | Titre | Priorité | Type | Phase | experiment_type | Statut |
|---|---|---|---|---|---|---|
| V7-INFRA-00 | Registre global des expériences | CRITIQUE | critique | 0 | DATA_VALIDATION | DONE |
| V7-DATA-CAL | Calendrier de publication des données | HAUTE | simple | 0 | DATA_VALIDATION | DONE |
| V7-LEAKAGE-00 | Suite de tests anti-leakage global | CRITIQUE | critique | 0 | STATISTICAL_VALIDATION | DONE |
| V7-00 | Audit de cohérence V6 | CRITIQUE | critique | 0 | DATA_VALIDATION | DONE |
| V7-02 | Purged CV avec embargo H40/H90/H120 | CRITIQUE | critique | 0 | STATISTICAL_VALIDATION | DONE |
| V7-29 | Multiple testing et discipline statistique | CRITIQUE | critique | 0 | STATISTICAL_VALIDATION | DONE |
| V7-30 | Red team validation des meilleurs résultats | CRITIQUE | critique | 0 | STATISTICAL_VALIDATION | DONE |
| V7-01A | Inventaire et stratégie données EMA proxy | CRITIQUE | critique | 0 | DATA_VALIDATION | DONE |
| V7-01B | Comparaison proxy vs source officielle EMA | CRITIQUE | critique | 0 | DATA_VALIDATION | WAITING_DATA |
| V7-31 | Benchmark naïf et professionnel | HAUTE | complexe | 1 | PREDICTIVE_OOF | DONE |
| V7-04 | CBOT Target Lab avancé | HAUTE | complexe | 1 | PREDICTIVE_OOF | DONE |
| V7-06 | Modèles saisonniers experts | HAUTE | complexe | 1 | PREDICTIVE_OOF | DONE |
| V7-07 | Roll-aware premium model | HAUTE | complexe | 1 | PREDICTIVE_OOF | DONE |
| V7-08 | Régimes de basis | HAUTE | complexe | 1 | MODEL_VALIDATION | DONE |
| V7-12 | P(correct) et calibration avancée | HAUTE | complexe | 1 | PREDICTIVE_OOF | DONE |
| V7-39 | Indicateur de qualité des données | HAUTE | moyen | 1 | DATA_VALIDATION | DONE |
| V7-09 | Décomposition dynamique EMA | MOYENNE | complexe | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-10 | Event study premium | MOYENNE | complexe | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-11A | Données EU — EC MARS | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-11B | Données EU — FranceAgriMer | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-11C | Données EU — Eurostat COMEXT | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-11D | Données EU — Exports Ukraine | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-11E | Données EU — Météo pondérée UE | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-11F | Données EU — Prix FOB export | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-11G | Données EU — Énergie/TTF/fertilisants | MOYENNE | moyen | 2 | DATA_VALIDATION | WAITING_DATA |
| V7-17 | Relations inter-commodités | MOYENNE | moyen | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-19 | Détection de ruptures structurelles | MOYENNE | moyen | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-25 | Tests des anomalies de marché | MOYENNE | moyen | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-26 | Analyse de mémoire longue et persistance | BASSE | moyen | 2 | DESCRIPTIVE_ECONOMIC | WATCHLIST |
| V7-32 | Fair value model EMA/CBOT | HAUTE | complexe | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-33 | Cartographie des drivers par horizon | HAUTE | complexe | 2 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-03 | Cross-target stacking V2 | HAUTE | critique | 3 | PREDICTIVE_OOF | DONE |
| V7-05 | Cross-market CBOT ↔ EMA | MOYENNE | complexe | 3 | PREDICTIVE_OOF | DONE |
| V7-20 | Modèles espace-état dynamiques (Kalman) | BASSE | complexe | 3 | MODEL_VALIDATION | WATCHLIST |
| V7-27 | Modèles multi-facteurs conditionnels | MOYENNE | critique | 3 | PREDICTIVE_OOF | DONE |
| V7-34 | Modèle de scénario de marché | MOYENNE | complexe | 3 | MODEL_VALIDATION | DONE |
| V7-35 | Distributional forecasting du premium | MOYENNE | complexe | 3 | PREDICTIVE_OOF | DONE |
| V7-37 | Analyse de stabilité des features | HAUTE | complexe | 3 | MODEL_VALIDATION | DONE |
| V7-38 | Étude du model decay | HAUTE | complexe | 3 | MODEL_VALIDATION | DONE |
| V7-16 | Microstructure et liquidité EMA | BASSE | moyen | 4 | MODEL_VALIDATION | DONE |
| V7-22 | Analyse logistique et prix de parité | BASSE | moyen | 4 | DESCRIPTIVE_ECONOMIC | WAITING_DATA |
| V7-23 | Analyse textuelle WASDE et rapports | BASSE | complexe | 4 | PREDICTIVE_OOF | WAITING_DATA |
| V7-24 | Signaux options et volatilité implicite | BASSE | moyen | 4 | PREDICTIVE_OOF | WAITING_DATA |
| V7-14 | Explicabilité et analyse des erreurs | MOYENNE | complexe | 5 | MODEL_VALIDATION | DONE |
| V7-18 | Causalité formelle PCMCI | MOYENNE | complexe | 5 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-21 | Analyse facteur EUR/USD et régimes de change | BASSE | moyen | 5 | PREDICTIVE_OOF | DONE |
| V7-36 | Graphe de causalité économique | MOYENNE | complexe | 5 | DESCRIPTIVE_ECONOMIC | DONE |
| V7-40 | Étude des unknown unknowns | BASSE | moyen | 5 | MODEL_VALIDATION | WATCHLIST |
| V7-13 | Backtests recherche avancés | FINALE | critique | 6 | BACKTEST_RESEARCH | DONE |
| V7-15 | Rapport final V7 | FINALE | complexe | 6 | — | DONE |
| V7-15B | Notebooks narratifs finaux | FINALE | complexe | 6 | — | BLOCKED |
| V7-28 | Architecture finale de l'indicateur | FINALE | critique | 6 | INDICATOR_CANDIDATE | DONE |

---

## Règles communes à tous les tickets

- `shift(1)` obligatoire sur toutes les features fondamentales (anti-leakage)
- z-scores expandants calculés sur train uniquement (aucune fuite du test vers le train)
- Seuils percentiles (top20, top40, confiance) appris sur train uniquement
- Meta-features = prédictions OOF uniquement (`is_oof=True` obligatoire)
- Embargo H jours pour toutes les cibles H ≥ 40 jours
- `seed = 42` dans tous les modèles, reproductibilité garantie
- Chaque expérience auto-enregistrée dans le Registre (V7-INFRA-00)
- Tests leakage `pytest tests/test_leakage_global.py` PASS avant tout commit
- Vérifications standard : `cd src && python -m ruff check ../src/mais/` + `python -m pytest tests/ -x -q`
- Verdict obligatoire : `GO_RESEARCH` / `PROMISING` / `WATCHLIST` / `NO_GO`
- Backtest verdict toujours : `RESEARCH_ONLY_NOT_TRADING`
- **Règle anti-sur-optimisation** : ne jamais optimiser plus de 3 degrés de liberté simultanément sans validation externe indépendante. Si > 3 hyperparamètres libres → réduire le scope ou ajouter un holdout interne dédié.
- Todos les signaux GO_RESEARCH doivent survivre à q_BH < 0.05 (Benjamini-Hochberg sur l'ensemble des tests)

---

## PHASE 0 — Sécurité statistique absolue

**Ordre d'exécution obligatoire** : V7-INFRA-00 → V7-DATA-CAL → V7-LEAKAGE-00 → V7-00 → V7-02 → V7-29 → V7-30 → V7-01A → V7-01B

---

### V7-INFRA-00 — Registre global des expériences

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : aucune (premier ticket à exécuter)
**experiment_type** : DATA_VALIDATION

### Contexte

V7 teste ~50 expériences × plusieurs cibles × plusieurs horizons. Sans traçabilité automatique, on ne sait plus quelle configuration a produit quel résultat, si un résultat a été sélectionné rétrospectivement, ou si deux expériences utilisent exactement les mêmes données. Ce ticket crée le registre central qui auto-enregistre chaque expérience dès sa production et qui est lu par V7-29 pour la correction BH.

### Objectifs mesurables

- Tout appel à `register_experiment()` écrit une ligne dans `artefacts/registry/experiments.jsonl`
- Chaque entrée contient : `experiment_id`, `date`, `git_commit`, `dataset_version`, `features_hash`, `target`, `horizon`, `model`, `cv_protocol`, `embargo_days`, `n_oof`, `auc`, `da`, `p_value`, `q_bh`, `verdict`, `artefact_paths`, `review_status`
- Un test vérifie que le fichier est lisible et non-dupliqué
- Tests : `ruff check src/mais/` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/walkforward/runner.py` | Format de sortie des OOF existants |
| `src/mais/research/final_corn_study_v6.py` | Exemple d'expérience à adapter |
| `.ai/STATE.md` | Liste de ce qui existe déjà |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/registry/__init__.py` | Créer — module registre |
| `src/mais/registry/experiment_registry.py` | Créer — fonction register_experiment() |
| `artefacts/registry/experiments.jsonl` | Créer — base JSONL append-only |
| `tests/test_experiment_registry.py` | Créer — tests du registre |

### Fichiers interdits

`notebooks/`, `data/raw/`, `*.parquet`

### Implémentation

**Étape 1 — Schéma de l'entrée registre**
```python
import hashlib, json, subprocess
from datetime import datetime
from pathlib import Path

REGISTRY_PATH = Path("artefacts/registry/experiments.jsonl")

def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()[:12]
    except Exception:
        return "unknown"

def _features_hash(feature_names: list[str]) -> str:
    s = "|".join(sorted(feature_names))
    return hashlib.sha256(s.encode()).hexdigest()[:12]
```

**Étape 2 — Fonction register_experiment()**
```python
def register_experiment(
    experiment_id: str,
    target: str,
    horizon: int,
    model: str,
    cv_protocol: str,
    embargo_days: int,
    n_oof: int,
    features: list[str],
    metrics: dict,          # {"auc": float, "da": float, ...}
    p_value: float | None,
    verdict: str,
    artefact_paths: list[str],
    dataset_version: str = "proxy_v1",
    review_status: str = "PENDING",
) -> dict:
    entry = {
        "experiment_id": experiment_id,
        "date": datetime.utcnow().isoformat(),
        "git_commit": _git_commit(),
        "dataset_version": dataset_version,
        "features_hash": _features_hash(features),
        "n_features": len(features),
        "target": target,
        "horizon": horizon,
        "model": model,
        "cv_protocol": cv_protocol,
        "embargo_days": embargo_days,
        "n_oof": n_oof,
        **metrics,
        "p_value": p_value,
        "q_bh": None,          # rempli par V7-29
        "verdict": verdict,
        "artefact_paths": artefact_paths,
        "review_status": review_status,
    }
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
```

**Étape 3 — Lecture et déduplication**
```python
def load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    entries = []
    seen_ids = set()
    with open(REGISTRY_PATH) as f:
        for line in f:
            e = json.loads(line)
            if e["experiment_id"] not in seen_ids:
                entries.append(e)
                seen_ids.add(e["experiment_id"])
    return entries
```

**Étape 4 — Test registre**
```python
def test_register_experiment():
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        tmp_path = tmp.name
    import mais.registry.experiment_registry as reg
    reg.REGISTRY_PATH = Path(tmp_path)
    entry = reg.register_experiment(
        experiment_id="TEST-001", target="y_rel_outperform_h90",
        horizon=90, model="lgbm", cv_protocol="purged_kfold",
        embargo_days=90, n_oof=100, features=["f1", "f2"],
        metrics={"auc": 0.65, "da": 0.60}, p_value=0.01,
        verdict="PROMISING", artefact_paths=[]
    )
    assert entry["auc"] == 0.65
    loaded = reg.load_registry()
    assert len(loaded) == 1
    os.unlink(tmp_path)
```

### Livrables obligatoires

- `src/mais/registry/experiment_registry.py` — module complet
- `artefacts/registry/experiments.jsonl` — fichier initialisé (peut être vide)
- `tests/test_experiment_registry.py` — test PASS

### Critères de succès

```
register_experiment() appelle: écriture JSONL OK
load_registry(): lecture sans doublon OK
test_experiment_registry.py: PASS
ruff check: PASS
```

---

### V7-DATA-CAL — Calendrier de publication des données

**Priorité** : HAUTE
**Type** : simple
**Statut** : READY
**Phase** : 0
**Dépendances** : aucune
**experiment_type** : DATA_VALIDATION

### Contexte

Chaque source de données a un délai de publication précis. Ignorer ces délais produit un leakage caché : les features sont construites comme si la donnée était disponible en temps réel alors qu'elle arrive avec 1-4 semaines de retard. Ce ticket documente les lags exacts et les intègre dans le pipeline de features via `shift()` adaptatif.

### Objectifs mesurables

- Tableau exhaustif des délais pour 8 sources (WASDE, COT, EIA, FAS, EC MARS, FranceAgriMer, Eurostat, COMEXT)
- Module Python `publication_calendar.py` retournant le lag officiel par source
- Vérification que les features utilisent `shift(max(1, lag_source))` au minimum
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/__init__.py` | Pipeline features principal |
| `src/mais/features/market.py` | Features COT/EIA existantes |
| `src/mais/features/fas_features.py` | Features FAS existantes |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/data/publication_calendar.py` | Créer — lags officiels par source |
| `docs/DATA_PUBLICATION_CALENDAR.md` | Créer — tableau de référence |
| `tests/test_publication_calendar.py` | Créer — test lags >= 1 |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Étape 1 — Tableau des lags**
```python
# Délais de publication officiels (en jours ouvrés)
PUBLICATION_LAGS = {
    # Source: (lag_min_jours, lag_max_jours, frequence, notes)
    "wasde": (0, 1, "mensuelle", "Publication 12h00 EST, 1er vendredi du mois"),
    "cot": (3, 3, "hebdomadaire", "COT publié chaque vendredi pour la semaine précédente"),
    "eia_weekly": (4, 4, "hebdomadaire", "EIA publié chaque mercredi matin pour sem-1"),
    "fas_grain": (1, 7, "mensuelle", "FAS WASDE attachment, même jour que WASDE"),
    "ec_mars": (14, 21, "mensuelle", "Bulletin MARS publié ~15-20 du mois suivant"),
    "franceagrimer": (7, 30, "mensuelle", "Bilan offrandes/demandes, 4 semaines retard"),
    "eurostat_comext": (30, 60, "mensuelle", "T-2 mois minimum"),
    "comext_trade": (45, 75, "mensuelle", "Données commerce T-2 à T-3 mois"),
    "ukraine_exports": (7, 14, "hebdomadaire", "Données douanières ukrainiennes, 1-2 sem"),
    "fob_prices": (1, 3, "quotidien", "Prix FOB Rouen/Ukraine cotés J-1 ou J"),
    "ttf_gas": (1, 1, "quotidien", "Cotation TTF J-1"),
    "ets_carbon": (1, 1, "quotidien", "EUA price J-1"),
}

def get_lag(source: str) -> int:
    """Retourne le lag conservateur (max) pour une source."""
    if source not in PUBLICATION_LAGS:
        raise KeyError(f"Source inconnue: {source}")
    _, lag_max, _, _ = PUBLICATION_LAGS[source]
    return lag_max
```

**Étape 2 — Vérification des shifts dans le pipeline**
```python
def verify_feature_lags(df_features: pd.DataFrame, source_col_map: dict) -> dict:
    """Vérifie que chaque colonne a bien été shiftée >= lag officiel."""
    violations = {}
    for col, source in source_col_map.items():
        lag = get_lag(source)
        # Vérification par corrélation avec version non-shiftée
        # Si corr(col, col.shift(-lag)) > 0.95 → leak probable
        if col in df_features.columns:
            corr = df_features[col].corr(df_features[col].shift(-lag))
            if abs(corr) > 0.95:
                violations[col] = {"source": source, "required_lag": lag, "corr": corr}
    return violations
```

**Étape 3 — Documentation markdown**
```markdown
# Calendrier de publication des données

| Source | Fréquence | Délai min | Délai max | Shift obligatoire | Notes |
|---|---|---|---|---|---|
| WASDE | Mensuelle | 0j | 1j | shift(1) | 12h00 EST 1er ven. du mois |
| COT | Hebdomadaire | 3j | 3j | shift(3) | Pub. vendredi pour sem. préc. |
| EIA Weekly | Hebdomadaire | 4j | 4j | shift(4) | Pub. mercredi |
| EC MARS | Mensuelle | 14j | 21j | shift(21) | Bulletin ~15-20 mois suivant |
| FranceAgriMer | Mensuelle | 7j | 30j | shift(30) | Bilan céréales |
| Eurostat COMEXT | Mensuelle | 30j | 75j | shift(75) | T-2 à T-3 mois |
| Ukraine exports | Hebdomadaire | 7j | 14j | shift(14) | Données douanières |
```

### Livrables obligatoires

- `src/mais/data/publication_calendar.py` — dictionnaire PUBLICATION_LAGS + get_lag()
- `docs/DATA_PUBLICATION_CALENDAR.md` — tableau de référence
- `tests/test_publication_calendar.py` — test que tous les lags >= 1

### Critères de succès

```
get_lag("wasde") >= 1 : OK
get_lag("ec_mars") >= 14 : OK
verify_feature_lags() sans violation sur le pipeline existant : OK
test_publication_calendar.py : PASS
```

---

### V7-LEAKAGE-00 — Suite de tests anti-leakage global

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : V7-INFRA-00
**experiment_type** : STATISTICAL_VALIDATION

### Contexte

Le leakage est la cause la plus fréquente de résultats illusoirement élevés en ML financier. Ce ticket crée une suite de 8 tests automatiques qui vérifient les invariants anti-leakage les plus critiques. Ces tests doivent passer sur TOUTE expérience V7 avant qu'un verdict GO_RESEARCH puisse être émis.

### Objectifs mesurables

- 8 tests de leakage implémentés dans `tests/test_leakage_global.py`
- `pytest tests/test_leakage_global.py` PASS sur les features V6 existantes
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/__init__.py` | Pipeline features, chercher les shifts |
| `src/mais/walkforward/splits.py` | Protocole CV, vérifier embargo |
| `src/mais/meta/stacking.py` | Meta-features OOF, vérifier is_oof |
| `src/mais/targets.py` | Construction des cibles, pas de shift(-H) |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `tests/test_leakage_global.py` | Créer — 8 tests anti-leakage |

### Fichiers interdits

`notebooks/`, `data/raw/`, `artefacts/`

### Implémentation

**8 tests à implémenter**

```python
# tests/test_leakage_global.py
import pytest
import pandas as pd
import numpy as np

def test_no_target_column_in_X(X, y):
    """Aucune colonne cible ne doit apparaître dans X."""
    target_cols = [c for c in X.columns if c.startswith(("y_", "return_", "future_"))]
    assert len(target_cols) == 0, f"Target columns in X: {target_cols}"

def test_no_future_return_in_X(X):
    """Aucune feature de type return_Xd non-shiftée."""
    suspicious = [c for c in X.columns if "return" in c.lower() and "_shift" not in c.lower()]
    # Tolérer si la feature est elle-même un ratio ou une différence passée
    # Interdire si c'est un return futur (ne peut être vérifié qu'à la revue manuelle)
    # Auto-test: corrélation de la colonne avec elle-même décalée de -H doit être < 0.5
    for col in suspicious:
        if hasattr(X[col], 'autocorr'):
            fwd_corr = X[col].corr(X[col].shift(-60))
            assert fwd_corr < 0.8, f"{col} semble corrélé avec sa valeur future ({fwd_corr:.2f})"

def test_no_negative_shift_in_features(feature_pipeline_source: str):
    """Aucun shift(-H) dans le code source du pipeline features."""
    import re
    with open(feature_pipeline_source) as f:
        code = f.read()
    negative_shifts = re.findall(r'shift\(-\d+\)', code)
    assert len(negative_shifts) == 0, f"Negative shifts found: {negative_shifts}"

def test_no_insamle_meta_features(meta_predictions: pd.DataFrame):
    """Toutes les prédictions meta doivent avoir is_oof=True."""
    assert "is_oof" in meta_predictions.columns, "Colonne is_oof manquante"
    non_oof = meta_predictions[~meta_predictions["is_oof"]]
    assert len(non_oof) == 0, f"{len(non_oof)} prédictions non-OOF détectées"

def test_oof_respect_embargo(oof_df: pd.DataFrame, embargo_days: int):
    """Chaque prédiction OOF : train_end < test_date - embargo."""
    violations = oof_df[oof_df["test_date"] - oof_df["train_end"] < pd.Timedelta(days=embargo_days)]
    assert len(violations) == 0, f"{len(violations)} violations d'embargo détectées"

def test_zscores_fit_on_train_only(scaler, X_train, X_test):
    """Le scaler z-score doit être fitted sur train uniquement."""
    from sklearn.preprocessing import StandardScaler
    assert hasattr(scaler, 'mean_'), "Scaler non fitted"
    # Vérifier que mean_ est proche de X_train.mean()
    for i, col in enumerate(X_train.columns):
        assert abs(scaler.mean_[i] - X_train[col].mean()) < 1e-6, \
            f"Scaler mean pour {col} != train mean"

def test_top20_threshold_train_only(thresholds: dict):
    """Les seuils percentile top20/top40 doivent être appris sur train."""
    assert "computed_on" in thresholds, "Source des seuils non documentée"
    assert thresholds["computed_on"] == "train_only", \
        f"Seuils appris sur: {thresholds['computed_on']}"

def test_test_rows_after_train_end(splits: list[dict]):
    """Pour chaque fold: toutes les dates test > train_end + embargo."""
    for fold in splits:
        train_end = fold["train_end"]
        embargo = fold["embargo_days"]
        test_dates = fold["test_dates"]
        violations = [d for d in test_dates if d <= train_end + pd.Timedelta(days=embargo)]
        assert len(violations) == 0, \
            f"Fold {fold['fold_id']}: {len(violations)} dates test dans la zone embargo"
```

### Livrables obligatoires

- `tests/test_leakage_global.py` — 8 tests complets
- `pytest tests/test_leakage_global.py` : PASS sur données V6

### Critères de succès

```
8 tests présents et documentés : OK
Aucun test SKIP (les fixtures doivent être implémentées) : OK
pytest tests/test_leakage_global.py PASS : OK
```

---

### V7-00 — Audit de cohérence V6

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : V7-INFRA-00
**experiment_type** : DATA_VALIDATION

### Contexte

Les résultats V6 montrent des AUC très élevés (meta-model H90 = 0.937, basis_extreme_h90 = 1.000, seasonal_expert = 0.982). Avant toute conclusion, il faut vérifier que ces résultats ne sont pas issus d'un leakage, d'un artefact de période ou d'une erreur de configuration. Ce ticket est la porte d'entrée obligatoire de V7 : tout résultat non-COHERENT bloque les tickets Phase 1 correspondants.

### Objectifs mesurables

- Audit complet des 11 expériences V6 avec verdict par expérience
- Chaque expérience classée : `COHERENT` / `FRAGILE` / `SUSPECT` / `INVALID`
- Tests leakage V7-LEAKAGE-00 appliqués aux données V6
- Rapport structuré `artefacts/v7/v6_consistency_audit.json`
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/final_corn_study_v6.py` | Code V6, vérifier leakage |
| `src/mais/research/target_labs_v6.py` | Cibles V6, logique OOF |
| `src/mais/meta/stacking.py` | Meta-features V6, vérifier OOF strict |
| `src/mais/research/roll_season_backtest_v6.py` | Backtest V6 |
| `src/mais/walkforward/splits.py` | Protocole CV, vérifier embargo |
| `artefacts/ema_study/` | Artefacts JSON V6 existants |
| `docs/FINAL_CORN_STUDY_V6.md` | Résultats officiels V6 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/v6_coherence_audit.py` | Créer — script d'audit complet |
| `artefacts/v7/v6_consistency_audit.json` | Créer — résultats audit |
| `docs/V6_CONSISTENCY_AUDIT.md` | Créer — rapport lisible |
| `tests/test_v6_coherence_audit.py` | Créer — test validation |

### Fichiers interdits

`data/raw/`, `notebooks/`, `*.parquet` hors lecture

### Implémentation

**Étape 1 — Vérifier périodes et chevauchements**
```python
# Pour chaque expérience V6 dans l'artefact JSON :
# Lire les dates de début/fin train et test
# Vérifier qu'il n'y a aucun chevauchement train/test
# Vérifier que l'embargo est bien de H jours pour cibles H40/H90
def check_no_overlap(train_dates, test_dates):
    overlap = set(train_dates) & set(test_dates)
    return len(overlap) == 0
```

**Étape 2 — Vérifier OOF strict des meta-features**
```python
# Pour V6-02 (cross-target stacking) :
# Vérifier que chaque prédiction OOF est issue d'un fold
# où la date n'était pas dans le train
# Si is_oof=False détecté → marquer INVALID
def check_oof_strict(oof_predictions: pd.DataFrame) -> bool:
    if "is_oof" not in oof_predictions.columns:
        return False
    return oof_predictions["is_oof"].all()
```

**Étape 3 — Vérifier les seuils train-only**
```python
# Pour V6-04 (seasonal policies) :
# Vérifier que les percentiles de confiance sont calculés sur train uniquement
# Détecter : seuil calculé sur ensemble train+test → marquer SUSPECT
```

**Étape 4 — Vérifier les n OOF**
```python
n_oof_map = {
    "meta_model_h90": 503,          # OK (> 100)
    "basis_extreme_h90": 29,         # FRAGILE (n < 30)
    "seasonal_expert": None,         # À vérifier
}
for exp_id, n in n_oof_map.items():
    if n is not None and n < 30:
        verdicts[exp_id] = "FRAGILE"
    elif n is not None and n < 50:
        verdicts[exp_id] = "COHERENT_LOW_N"
```

**Étape 5 — Expliquer le delta AUC V5→V6**
```python
# AUC V5 = 0.770, AUC V6 = 0.937
# Causes légitimes : meta-features OOF, meilleure cible, plus de données
# Causes suspectes : changement de période, biais de sélection
# Documenter explicitement la cause
delta_analysis = {
    "auc_v5": 0.770, "auc_v6": 0.937, "delta": 0.167,
    "attributed_to": ["meta_features_oof", "cross_target_stacking"],
    "period_change": False,
    "verdict": "COHERENT"
}
```

**Étape 6 — Produire le rapport**
```python
audit_result = {
    "experiments": {
        "meta_model_h90": {
            "verdict": "COHERENT", "n_oof": 503,
            "issues": [], "oof_strict": True
        },
        "basis_extreme_h90": {
            "verdict": "FRAGILE", "n_oof": 29,
            "issues": ["n=29 too low, high variance AUC"], "oof_strict": True
        },
    },
    "global_verdict": "COHERENT_WITH_CAVEATS",
    "blockers": [],
    "warnings": ["basis_extreme_h90 n=29 requires replication on larger sample"]
}
```

### Livrables obligatoires

- `artefacts/v7/v6_consistency_audit.json` — résultats structurés
- `docs/V6_CONSISTENCY_AUDIT.md` — rapport complet
- `tests/test_v6_coherence_audit.py` — test de non-régression
- Enregistrement dans le Registre via `register_experiment("V7-00", ...)`

### Critères de succès

```
COHERENT : aucun leakage, n OOF conformes, embargo vérifié → Phase 1 débloquée
COHERENT_WITH_CAVEATS : n faibles mais pas de leakage → Phase 1 avec notes
SUSPECT : seuils ou OOF potentiellement contaminés → Phase 1 bloquée jusqu'à correction
INVALID : leakage avéré → résultats V6 rétrogradés EXPLORATORY_ONLY, V7 repart de zéro
```

---

### V7-02 — Purged CV avec embargo H40/H90/H120

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : V7-00
**experiment_type** : STATISTICAL_VALIDATION

### Contexte

Avec H90, deux observations consécutives partagent 89 jours de labels chevauchants. Un modèle peut exploiter cette corrélation indirectement via le protocole CV classique. Ce ticket compare 9 protocoles CV différents sur les cibles principales et définit le protocole officiel V7.

### Objectifs mesurables

- 9 protocoles CV comparés : classic, embargo_H, embargo_2H, non_overlap, block_bootstrap, leave_one_year, leave_one_crop_year, leave_one_crisis, purged_kfold
- Delta AUC (classic vs purged) quantifié pour H40, H90, H120
- Protocole officiel V7 sélectionné et documenté
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/walkforward/splits.py` | Protocole CV actuel |
| `src/mais/walkforward/runner.py` | Runner OOF actuel |
| `src/mais/research/final_corn_study_v6.py` | Cibles V6 à reproduire |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/walkforward/purged_cv.py` | Créer — 9 protocoles CV |
| `artefacts/v7/purged_cv_embargo_study.json` | Créer — comparaison |
| `docs/PURGED_CV_EMBARGO.md` | Créer — rapport |
| `tests/test_purged_cv.py` | Créer — test protocoles |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Étape 1 — Implémenter les 9 protocoles**
```python
class PurgedCVProtocol:
    """9 protocoles CV avec embargo configurable."""

    @staticmethod
    def classic(dates, n_splits=5):
        """Walk-forward classique sans embargo."""
        return TimeSeriesSplit(n_splits=n_splits).split(np.arange(len(dates)))

    @staticmethod
    def embargo_h(dates, embargo_days, n_splits=5):
        """Walk-forward + embargo H jours."""
        for train_idx, test_idx in TimeSeriesSplit(n_splits).split(dates):
            cutoff = dates[train_idx[-1]] + pd.Timedelta(days=embargo_days)
            test_idx_purged = [i for i in test_idx if dates[i] > cutoff]
            yield train_idx, np.array(test_idx_purged)

    @staticmethod
    def embargo_2h(dates, horizon_days, n_splits=5):
        return PurgedCVProtocol.embargo_h(dates, 2 * horizon_days, n_splits)

    @staticmethod
    def non_overlap(dates, horizon_days):
        """Garder 1 obs par fenêtre de H jours (stride = H)."""
        idx = np.arange(0, len(dates), horizon_days)
        return TimeSeriesSplit(n_splits=5).split(idx)

    @staticmethod
    def leave_one_year(dates):
        """Validation croisée par année."""
        for year in dates.year.unique()[1:]:  # skip first year (pas assez de train)
            test_mask = dates.year == year
            train_mask = dates < dates[test_mask].min() - pd.Timedelta(days=7)
            yield np.where(train_mask)[0], np.where(test_mask)[0]

    @staticmethod
    def leave_one_crop_year(dates):
        """Validation par crop year (sept-août)."""
        def crop_year(d): return d.year if d.month >= 9 else d.year - 1
        crop_years = [crop_year(d) for d in dates]
        for cy in sorted(set(crop_years))[1:]:
            test_mask = np.array([c == cy for c in crop_years])
            train_mask = np.array([c < cy for c in crop_years])
            yield np.where(train_mask)[0], np.where(test_mask)[0]

    @staticmethod
    def leave_one_crisis(dates):
        """Retirer une crise : 2012, 2020, 2022."""
        crisis_periods = [
            (pd.Timestamp("2012-01-01"), pd.Timestamp("2012-12-31")),
            (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31")),
            (pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31")),
        ]
        for start, end in crisis_periods:
            test_mask = (dates >= start) & (dates <= end)
            train_mask = dates < start
            yield np.where(train_mask)[0], np.where(test_mask)[0]
```

**Étape 2 — Comparer les AUC sur 5 cibles**
```python
TARGETS = [
    "y_rel_outperform_h40", "y_rel_outperform_h90",
    "y_cbot_up_h60", "y_basis_up_h40", "y_rel_outperform_when_basis_extreme_h90"
]
PROTOCOLS = ["classic", "embargo_H", "embargo_2H", "non_overlap",
             "block_bootstrap", "leave_one_year", "leave_one_crop_year",
             "leave_one_crisis", "purged_kfold"]

results = {}
for target in TARGETS:
    for proto in PROTOCOLS:
        auc = run_oof_with_protocol(X, y[target], proto)
        results[(target, proto)] = auc

# Delta optimisme
for target in TARGETS:
    delta = results[(target, "classic")] - results[(target, "purged_kfold")]
    print(f"{target}: delta_AUC classic-purged = {delta:.3f}")
```

**Étape 3 — Sélectionner le protocole officiel V7**
```python
# Critère : protocole avec le moins d'optimisme + couverture suffisante (n_test > 50)
# Si delta classic-purged > 0.05 → walk-forward classique biaisé, utiliser purged_kfold
# Si delta < 0.05 → embargo_H est suffisant
OFFICIAL_V7_PROTOCOL = "purged_kfold_with_embargo_H"  # à confirmer après résultats
```

### Livrables obligatoires

- `src/mais/walkforward/purged_cv.py` — 9 protocoles implémentés
- `artefacts/v7/purged_cv_embargo_study.json` — comparaison complète
- `docs/PURGED_CV_EMBARGO.md` — protocole officiel V7 documenté
- `tests/test_purged_cv.py` — test protocoles

### Critères de succès

```
9 protocoles fonctionnels : OK
Delta AUC classic-purged documenté pour chaque cible+horizon : OK
Protocole officiel V7 défini et justifié : OK
```

---

### V7-29 — Multiple testing et discipline statistique

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : V7-00, V7-INFRA-00
**experiment_type** : STATISTICAL_VALIDATION

### Contexte

V7 teste ~50 expériences × plusieurs cibles × horizons × modèles. Sans correction pour tests multiples, certains résultats positifs sont dus au hasard pur (FDR incontrôlé). La correction Benjamini-Hochberg (FDR) est obligatoire. Ce ticket définit le protocole de contrôle statistique global, gèle le holdout 2024, et établit les règles post-hoc pour les verdicts V7.

### Objectifs mesurables

- Registre global de toutes les comparaisons V7 alimenté par V7-INFRA-00
- Correction BH appliquée dynamiquement sur toutes les p-values
- Holdout 2024 gelé avec verrou JSON
- Signal `GO_RESEARCH` uniquement si q_BH < 0.05
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/registry/experiment_registry.py` | Registre V7-INFRA-00 |
| `src/mais/walkforward/runner.py` | Structure des résultats OOF |
| `docs/FINAL_CORN_STUDY_V6.md` | Résultats V6 à corriger BH |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/multiple_testing.py` | Créer — correction BH + holdout |
| `artefacts/v7/multiple_testing_report.json` | Créer — résultats correction BH |
| `artefacts/v7/holdout_lock.json` | Créer — verrou holdout 2024 |
| `docs/MULTIPLE_TESTING_CONTROL.md` | Créer — rapport FDR |
| `tests/test_multiple_testing.py` | Créer — test BH correction |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Étape 1 — Calculer les p-values bootstrap**
```python
def bootstrap_auc_pvalue(y_true, y_scores, n_bootstrap=5000, seed=42):
    """P-value H0: AUC = 0.5 par permutation bootstrap."""
    rng = np.random.default_rng(seed)
    obs_auc = roc_auc_score(y_true, y_scores)
    null_aucs = [
        roc_auc_score(y_true, rng.permutation(y_scores))
        for _ in range(n_bootstrap)
    ]
    return np.mean(np.array(null_aucs) >= obs_auc)
```

**Étape 2 — Appliquer Benjamini-Hochberg**
```python
from statsmodels.stats.multitest import multipletests
from mais.registry.experiment_registry import load_registry

def apply_bh_correction(alpha=0.05):
    entries = load_registry()
    entries_with_pval = [e for e in entries if e["p_value"] is not None]
    pvalues = [e["p_value"] for e in entries_with_pval]
    reject, q_corrected, _, _ = multipletests(pvalues, alpha=alpha, method="fdr_bh")
    for i, e in enumerate(entries_with_pval):
        e["q_bh"] = float(q_corrected[i])
        e["survives_fdr"] = bool(reject[i])
        e["verdict_adjusted"] = "GO_RESEARCH" if reject[i] else "EXPLORATORY_ONLY"
    return entries_with_pval
```

**Étape 3 — Geler le holdout 2024**
```python
holdout_config = {
    "start": "2024-01-01",
    "end": "2024-12-31",
    "used": False,
    "used_by": None,
    "authorized_ticket": "V7-28",
    "note": "NE PAS TOUCHER avant la phase 6 finale (V7-28)"
}
with open("artefacts/v7/holdout_lock.json", "w") as f:
    json.dump(holdout_config, f, indent=2)
```

**Étape 4 — Règles post-hoc**
```python
# Interdire la sélection du modèle final sur le set d'exploration
# Tout résultat EXPLORATORY_ONLY ne peut pas entrer dans V7-28
# Tout résultat GO_RESEARCH doit être reproductible avec seed=42
```

### Livrables obligatoires

- `src/mais/research/multiple_testing.py` — correction BH complète
- `artefacts/v7/holdout_lock.json` — verrou holdout 2024 (`used=False`)
- `artefacts/v7/multiple_testing_report.json` — registre avec q_BH
- `docs/MULTIPLE_TESTING_CONTROL.md` — rapport FDR

### Critères de succès

```
BH appliqué sur tous les tests V7 : OK (via registre INFRA-00)
Holdout gelé : holdout_lock.json présent, used=False : OK
Signal GO valide uniquement si q_BH < 0.05 : OK
```

---

### V7-30 — Red team validation des meilleurs résultats

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : V7-00, V7-02
**experiment_type** : STATISTICAL_VALIDATION

### Contexte

Les résultats V6 très élevés (AUC 0.937, AUC 1.000, AUC 0.982) doivent être attaqués systématiquement avant d'être acceptés. Ce ticket implémente 11 tests de stress pour chaque résultat supérieur à AUC 0.85. Le but est de classer chaque résultat : ROBUST, PROMISING_BUT_FRAGILE, LIKELY_SELECTION_BIAS ou LEAKAGE_SUSPECTED.

### Objectifs mesurables

- 11 tests appliqués à chaque résultat V6 avec AUC > 0.85
- Verdict structuré par résultat
- AUC stable (delta < 0.10) sur ≥ 8/11 tests → ROBUST
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/final_corn_study_v6.py` | Reproduire les expériences V6 |
| `src/mais/meta/stacking.py` | Meta-model V6 |
| `src/mais/walkforward/splits.py` | Protocole CV |
| `artefacts/v7/v6_consistency_audit.json` | Résultats V7-00 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/red_team_validation.py` | Créer — 11 tests stress |
| `artefacts/v7/red_team_validation.json` | Créer — résultats |
| `docs/RED_TEAM_VALIDATION.md` | Créer — rapport |
| `tests/test_red_team.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**11 tests de stress**
```python
# Test 1 : Shuffle labels temporel
# Si AUC reste élevé après shuffle → leakage
def test1_shuffle_labels(X, y, model, cv):
    y_shuffled = np.random.default_rng(42).permutation(y.values)
    return {"auc": run_oof(X, y_shuffled, model, cv), "leakage": None}

# Test 2 : Permutation meta-features décalée 1 an
def test2_permute_meta_features(X, y, meta_cols, model, cv):
    X_p = X.copy()
    X_p[meta_cols] = X_p[meta_cols].shift(252)
    return run_oof(X_p.dropna(), y.loc[X_p.dropna().index], model, cv)

# Test 3 : Décalage OOF dans le futur (leakage artificiel)
def test3_shift_oof_future(X, y, oof_col, H, model, cv):
    X_l = X.copy()
    X_l[oof_col] = X_l[oof_col].shift(-H)
    return run_oof(X_l.dropna(), y.loc[X_l.dropna().index], model, cv)

# Test 4 : Embargo 2H
# Test 5 : Non-overlap strict (stride = H)
# Test 6 : Exclure 2020 et 2022
# Test 7 : Retirer les 10 meilleures observations OOF
# Test 8 : Modèle sans features basis
# Test 9 : Modèle sans indicateurs saisonniers
# Test 10 : Évaluation uniquement 2021-2023
# Test 11 : Évaluation sur période EMA officielle (si disponible)

def compute_red_team_verdict(test_results: list[dict], baseline_auc: float) -> str:
    n_stable = sum(1 for r in test_results if abs(r["auc"] - baseline_auc) < 0.10)
    leakage_detected = test_results[0].get("auc", 0.5) > 0.60  # Test 1
    if leakage_detected:
        return "LEAKAGE_SUSPECTED"
    if n_stable >= 8:
        return "ROBUST"
    elif n_stable >= 5:
        return "PROMISING_BUT_FRAGILE"
    return "LIKELY_SELECTION_BIAS"
```

### Livrables obligatoires

- `src/mais/research/red_team_validation.py` — 11 tests implémentés
- `artefacts/v7/red_team_validation.json` — verdicts par résultat V6
- `docs/RED_TEAM_VALIDATION.md` — rapport

### Critères de succès

```
ROBUST : delta < 0.10 sur >= 8/11 tests → signal conservé GO_RESEARCH
PROMISING_BUT_FRAGILE : 5-7 tests stables → WATCHLIST uniquement
LIKELY_SELECTION_BIAS : < 5 tests stables → EXPLORATORY_ONLY
LEAKAGE_SUSPECTED : Test 1 positif → résultat invalidé
```

---

### V7-01A — Inventaire et stratégie données EMA proxy

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : READY
**Phase** : 0
**Dépendances** : V7-00
**experiment_type** : DATA_VALIDATION

### Contexte

L'étude EMA utilise des données proxy construites via Euronext et des sources alternatives. Avant toute expérience quantitative, il faut dresser un inventaire précis de ce qui existe, évaluer la qualité/couverture, et documenter les limites de validité. Ce ticket est faisable immédiatement avec les données existantes. V7-01B (comparaison officielle) attend les données officielles Euronext.

### Objectifs mesurables

- Inventaire complet : sources, couverture temporelle, fréquence, qualité, gaps
- Score de qualité par source [0-1] documenté
- Recommandation stratégique : quel proxy utiliser pour quelle expérience
- Rapport `artefacts/v7/ema_proxy_inventory.json`
- Tests : `ruff check` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/euronext.py` | Données EMA existantes |
| `src/mais/features/euronext_continuous.py` | Série continue EMA |
| `src/mais/features/euronext_curve.py` | Courbe terme EMA |
| `src/mais/features/ema_features.py` | Features EMA calculées |
| `src/mais/features/ema_targets.py` | Cibles EMA définies |
| `src/mais/paths.py` | Chemins vers les données |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/data/ema_proxy_inventory.py` | Créer — inventaire et qualité |
| `artefacts/v7/ema_proxy_inventory.json` | Créer — résultats |
| `docs/EMA_PROXY_INVENTORY.md` | Créer — rapport stratégique |

### Fichiers interdits

`notebooks/`, `data/raw/` sauf lecture

### Implémentation

**Étape 1 — Lister toutes les sources EMA**
```python
ema_sources = {
    "euronext_front_month": {
        "file": "data/processed/ema_front.parquet",
        "freq": "daily", "start": None, "end": None
    },
    "euronext_continuous": {
        "file": "data/processed/ema_continuous.parquet",
        "freq": "daily", "start": None, "end": None
    },
    # ...
}
```

**Étape 2 — Évaluer la qualité**
```python
def score_data_source(df: pd.DataFrame) -> dict:
    n_days = len(df)
    n_gaps = df.index.to_series().diff().dt.days.gt(3).sum()
    gap_ratio = n_gaps / n_days
    coverage_years = (df.index[-1] - df.index[0]).days / 365
    quality_score = max(0, 1 - gap_ratio * 5) * min(1, coverage_years / 10)
    return {
        "n_days": n_days, "n_gaps": int(n_gaps),
        "gap_ratio": float(gap_ratio),
        "coverage_years": float(coverage_years),
        "quality_score": float(quality_score),
        "status": "OK" if quality_score > 0.7 else "PARTIAL" if quality_score > 0.4 else "POOR"
    }
```

**Étape 3 — Recommandations stratégiques**
```python
strategy = {
    "primary_target_source": "euronext_continuous",
    "basis_calculation": "ema_front - cbot_converted_eur",
    "validity_period": "2010-2023",
    "known_caveats": [
        "EMA proxy may differ from official Euronext prices",
        "Pre-2010 data quality uncertain",
        "Roll methodology impacts basis calculation"
    ],
    "recommendation": "USE_FOR_RESEARCH_ONLY"
}
```

### Livrables obligatoires

- `artefacts/v7/ema_proxy_inventory.json` — inventaire complet
- `docs/EMA_PROXY_INVENTORY.md` — rapport avec recommandations

### Critères de succès

```
Toutes les sources EMA documentées : OK
Score qualité par source calculé : OK
Recommandation stratégique claire : OK
Caveat proxy documenté : OK
```

---

### V7-01B — Comparaison proxy vs source officielle EMA

**Priorité** : CRITIQUE
**Type** : critique
**Statut** : WAITING_DATA
**Phase** : 0
**Dépendances** : V7-01A + données officielles Euronext
**experiment_type** : DATA_VALIDATION

### Contexte

Ce ticket compare les données proxy EMA utilisées dans V6 avec la source officielle Euronext (données licenciées). Il ne peut être exécuté qu'une fois les données officielles obtenues. Jusqu'à ce que cette validation soit faite, tous les résultats EMA restent au statut RESEARCH_PROXY et ne peuvent pas prétendre à une validation sur données réelles.

### Objectifs mesurables

- Corrélation proxy vs officiel > 0.99 sur période commune
- Biais de niveau documenté (MAE, RMSE)
- Si corrélation < 0.95 → révision complète de la stratégie EMA
- Rapport `artefacts/v7/ema_proxy_vs_official.json`

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `artefacts/v7/ema_proxy_inventory.json` | Résultats V7-01A |
| `src/mais/features/euronext.py` | Données proxy actuelles |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/data/ema_official_validator.py` | Créer — comparaison proxy/officiel |
| `artefacts/v7/ema_proxy_vs_official.json` | Créer — résultats |
| `docs/EMA_PROXY_VALIDATION.md` | Créer — rapport |

### Fichiers interdits

`notebooks/`, `data/raw/` sauf lecture données officielles

### Implémentation

**Étape 1 — Charger et aligner les deux séries**
```python
def compare_proxy_vs_official(df_proxy: pd.DataFrame, df_official: pd.DataFrame) -> dict:
    common_idx = df_proxy.index.intersection(df_official.index)
    proxy = df_proxy.loc[common_idx, "close"]
    official = df_official.loc[common_idx, "close"]
    corr = proxy.corr(official)
    mae = (proxy - official).abs().mean()
    rmse = ((proxy - official) ** 2).mean() ** 0.5
    bias = (proxy - official).mean()
    return {
        "n_common_days": len(common_idx),
        "correlation": float(corr),
        "mae": float(mae),
        "rmse": float(rmse),
        "bias": float(bias),
        "verdict": "PROXY_VALID" if corr > 0.99 else "PROXY_PARTIAL" if corr > 0.95 else "PROXY_INVALID"
    }
```

**Étape 2 — Impact sur les résultats V6**
```python
# Si proxy_verdict == PROXY_VALID → V6 résultats conservés
# Si proxy_verdict == PROXY_PARTIAL → V6 marqués PROXY_DEPENDENT
# Si proxy_verdict == PROXY_INVALID → V6 invalidés, recommencer sur officiel
```

### Livrables obligatoires

- `artefacts/v7/ema_proxy_vs_official.json` — résultats comparaison
- `docs/EMA_PROXY_VALIDATION.md` — verdict + impact sur V6

### Critères de succès

```
PROXY_VALID : corr > 0.99 → V6 conservés
PROXY_PARTIAL : 0.95 < corr < 0.99 → V6 marqués PROXY_DEPENDENT
PROXY_INVALID : corr < 0.95 → V6 invalidés
```

---

## PHASE 1 — Consolidation des signaux prioritaires

---

### V7-31 — Benchmark naïf et professionnel

**Priorité** : HAUTE
**Type** : complexe
**Statut** : READY
**Phase** : 1
**Dépendances** : V7-00
**experiment_type** : PREDICTIVE_OOF

### Contexte

Sans benchmark solide, on ne sait pas si AUC=0.60 est bon ou médiocre. Ce ticket définit les baselines naïves (random, persistence, naive seasonal) et professionnelles (momentum, trend-following, consensus WASDE) pour chaque cible V7. Tout signal V7 est évalué en delta AUC vs ces benchmarks.

### Objectifs mesurables

- 5 benchmarks naïfs + 3 benchmarks professionnels pour chaque cible principale
- AUC baseline documentée par cible+horizon
- Delta AUC (signal - baseline) documenté pour chaque résultat V7
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/ema_smart_baselines.py` | Baselines EMA existantes V6 |
| `src/mais/walkforward/runner.py` | Runner OOF |
| `src/mais/targets.py` | Définition des cibles |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/benchmark_suite.py` | Créer — 8 benchmarks |
| `artefacts/v7/benchmark_suite.json` | Créer — AUC par benchmark/cible |
| `docs/BENCHMARK_SUITE.md` | Créer — rapport |
| `tests/test_benchmark_suite.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Étape 1 — Benchmarks naïfs**
```python
class NaiveBenchmarks:
    @staticmethod
    def random(y_true, seed=42):
        rng = np.random.default_rng(seed)
        return rng.random(len(y_true))

    @staticmethod
    def persistence(y_true):
        """Prédire que la direction H passée se répète."""
        return (y_true.shift(1) > 0).astype(float).fillna(0.5)

    @staticmethod
    def naive_seasonal(y_true, dates):
        """Tendance saisonnière moyenne par mois."""
        seasonal_mean = y_true.groupby(dates.month).transform("mean")
        return (seasonal_mean > seasonal_mean.median()).astype(float)

    @staticmethod
    def always_up(y_true):
        return pd.Series(1.0, index=y_true.index)

    @staticmethod
    def consensus_wasde_direction(wasde_revision):
        """Direction de la révision WASDE comme signal."""
        return (wasde_revision > 0).astype(float)
```

**Étape 2 — Benchmarks professionnels**
```python
class ProfessionalBenchmarks:
    @staticmethod
    def momentum_20d(returns):
        return (returns.rolling(20).mean() > 0).astype(float)

    @staticmethod
    def trend_following_52w(prices):
        return (prices > prices.rolling(252).mean()).astype(float)

    @staticmethod
    def carry_signal(basis):
        return (basis > basis.rolling(60).mean()).astype(float)
```

**Étape 3 — Évaluer sur toutes les cibles**
```python
BENCHMARK_RESULTS = {}
for target in TARGETS:
    for bench_name, bench_fn in ALL_BENCHMARKS.items():
        scores = bench_fn(y[target])
        auc = roc_auc_score(y[target].dropna(), scores.reindex(y[target].dropna().index))
        BENCHMARK_RESULTS[(target, bench_name)] = auc
```

### Livrables obligatoires

- `src/mais/research/benchmark_suite.py` — 8 benchmarks implémentés
- `artefacts/v7/benchmark_suite.json` — AUC par benchmark/cible
- `docs/BENCHMARK_SUITE.md` — tableau de référence V7

### Critères de succès

```
8 benchmarks documentés par cible : OK
AUC baseline la plus forte identifiée par cible : OK
Delta AUC calculable pour chaque futur résultat V7 : OK
```

---

### V7-04 — CBOT Target Lab avancé

**Priorité** : HAUTE
**Type** : complexe
**Statut** : READY
**Phase** : 1
**Dépendances** : V7-00, V7-02
**experiment_type** : PREDICTIVE_OOF

### Contexte

V6 a défini des cibles CBOT simples. V7 étend le target lab avec des cibles plus riches : conditionnelles (CBOT up when EMA premium high), asymétriques (forte hausse > +3%), de risk-adjusted performance, et de timing d'entrée optimal. Ces nouvelles cibles permettent de tester des signaux plus fins pour le trading.

### Objectifs mesurables

- 8 nouvelles cibles CBOT définies et documentées
- Prévalence (% positif) entre 30-70% pour chaque cible
- OOF AUC calculé pour chaque cible avec le modèle best_v6
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/targets.py` | Cibles V6 existantes |
| `src/mais/research/target_labs_v6.py` | Target lab V6 |
| `src/mais/features/ema_targets.py` | Cibles EMA |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/cbot_target_lab_v7.py` | Créer — 8 nouvelles cibles |
| `artefacts/v7/cbot_target_lab.json` | Créer — résultats |
| `docs/CBOT_TARGET_LAB_V7.md` | Créer — rapport |
| `tests/test_cbot_target_lab.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**8 nouvelles cibles CBOT**
```python
def build_cbot_targets_v7(df: pd.DataFrame) -> pd.DataFrame:
    targets = {}

    # T1 : CBOT up conditionnellement (quand premium EMA/CBOT élevé)
    basis_high = df["basis_eur_t"] > df["basis_eur_t"].rolling(252).quantile(0.7)
    targets["y_cbot_up_h60_when_basis_high"] = (
        (df["cbot_close"].pct_change(60).shift(-60) > 0) & basis_high
    ).astype(int)

    # T2 : CBOT strong up (> +3%)
    targets["y_cbot_strong_up_h60"] = (
        df["cbot_close"].pct_change(60).shift(-60) > 0.03
    ).astype(int)

    # T3 : CBOT risk-adjusted (sharpe positif sur H60)
    rolling_vol = df["cbot_close"].pct_change().rolling(60).std() * np.sqrt(252)
    targets["y_cbot_risk_adj_h60"] = (
        df["cbot_close"].pct_change(60).shift(-60) / rolling_vol.shift(-60) > 0.5
    ).astype(int)

    # T4 : Direction inversée (short signal)
    targets["y_cbot_down_h60"] = (
        df["cbot_close"].pct_change(60).shift(-60) < -0.02
    ).astype(int)

    # T5 : CBOT up H120 (horizon long)
    targets["y_cbot_up_h120"] = (
        df["cbot_close"].pct_change(120).shift(-120) > 0
    ).astype(int)

    # T6 : Volatility spike H40 (risk-off signal)
    targets["y_cbot_vol_spike_h40"] = (
        df["cbot_close"].pct_change().rolling(40).std().shift(-40) >
        df["cbot_close"].pct_change().rolling(120).std() * 1.5
    ).astype(int)

    # T7 : Premium compression (EMA sous-performe dans 60j)
    targets["y_ema_underperform_h60"] = (
        df["cbot_close"].pct_change(60).shift(-60) -
        df["ema_close"].pct_change(60).shift(-60) > 0.02
    ).astype(int)

    # T8 : Breakout haussier CBOT (close > max 52w)
    targets["y_cbot_52w_breakout_h20"] = (
        df["cbot_close"] > df["cbot_close"].rolling(252).max()
    ).astype(int)

    return pd.DataFrame(targets)
```

**Vérification prévalences**
```python
for col in targets.columns:
    prev = targets[col].mean()
    assert 0.25 <= prev <= 0.75, f"{col}: prévalence {prev:.2%} hors [25%, 75%]"
```

### Livrables obligatoires

- `src/mais/research/cbot_target_lab_v7.py` — 8 cibles avec prévalences vérifiées
- `artefacts/v7/cbot_target_lab.json` — AUC par cible avec benchmark
- `docs/CBOT_TARGET_LAB_V7.md` — rapport

### Critères de succès

```
8 cibles définies, prévalences [25%-75%] : OK
OOF AUC > baseline naïve pour au moins 5/8 cibles : OK
```

---

### V7-06 — Modèles saisonniers experts

**Priorité** : HAUTE
**Type** : complexe
**Statut** : BLOCKED
**Phase** : 1
**Dépendances** : V7-02, V7-31
**experiment_type** : PREDICTIVE_OOF

### Contexte

V6 a montré que `seasonal_expert / top20_train_only` atteint BA=0.983 et AUC=0.982 sur 103 trades sélectionnés. V7 doit reproduire ce résultat avec le protocole CV officiel (V7-02), étendre les politiques saisonnières, et tester la robustesse crop-year par crop-year. L'expert saisonnier est un candidat fort pour l'indicateur final V7-28.

### Objectifs mesurables

- 6 politiques saisonnières comparées (mensuelle, crop-year, rolling-52w, event-driven, phase-lunaire, combinaison)
- AUC V7 stable vs AUC V6 (delta < 0.05) avec protocole purged CV
- Coverage saisonnière documentée par politique (% des jours couverts)
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/seasonality.py` | Features saisonnières V6 |
| `src/mais/research/roll_season_backtest_v6.py` | Backtest saisonnier V6 |
| `src/mais/walkforward/purged_cv.py` | Protocole CV V7-02 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/seasonal_experts_v7.py` | Créer — 6 politiques |
| `artefacts/v7/seasonal_experts.json` | Créer — comparaison |
| `docs/SEASONAL_EXPERTS_V7.md` | Créer — rapport |
| `tests/test_seasonal_experts.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**6 politiques saisonnières**
```python
class SeasonalPolicy:
    POLICIES = {
        "monthly_classic": monthly_expert,      # V6 : meilleur mois historique
        "crop_year_phase": crop_year_expert,    # Basé sur phase crop (plantation, pollination, harvest)
        "rolling_52w_best": rolling_52w_expert, # 52 semaines glissantes
        "event_driven": event_expert,           # Pré/post WASDE, pré-récolte
        "combined_score": combined_expert,      # Score pondéré de toutes les politiques
        "no_filter": None,                      # Baseline sans filtre saisonnier
    }

def monthly_expert(date: pd.Timestamp) -> bool:
    """Actif uniquement dans les mois historiquement favorables."""
    # Mois favorables EMA premium H90 : à calculer sur train
    # Anti-leakage : les mois favorables sont calculés sur train uniquement
    favorable_months_train = {3, 4, 6, 7, 9}  # à remplacer par calcul train
    return date.month in favorable_months_train

def crop_year_expert(date: pd.Timestamp, phase: str) -> bool:
    """Phase du cycle cultural : PLANTING, GROWING, HARVEST, POST_HARVEST."""
    northern_hemisphere_phases = {
        "PLANTING": (3, 5),    # Mars-Mai
        "GROWING": (6, 8),     # Juin-Août
        "HARVEST": (9, 11),    # Sept-Nov
        "POST_HARVEST": (12, 2) # Déc-Fév
    }
    return phase in ["GROWING", "POST_HARVEST"]  # phases historiquement actives
```

**Backtests saisonniers (RESEARCH ONLY)**
```python
def backtest_seasonal_policy(
    df_signals: pd.DataFrame,
    policy_fn,
    confidence_threshold: float,
    label: str = "research_only"
) -> dict:
    """Backtest recherche : RESEARCH_ONLY_NOT_TRADING."""
    selected = df_signals[
        df_signals.apply(lambda r: policy_fn(r.name), axis=1) &
        (df_signals["confidence"] >= confidence_threshold)
    ]
    if len(selected) == 0:
        return {"trades": 0, "verdict": "NO_SIGNAL"}
    pnl = selected["forward_return_h90"].sum()
    return {
        "label": label,
        "trades": len(selected),
        "coverage": len(selected) / len(df_signals),
        "pnl_eur_t": float(pnl),
        "verdict": "RESEARCH_ONLY_NOT_TRADING"
    }
```

### Livrables obligatoires

- `src/mais/research/seasonal_experts_v7.py` — 6 politiques implémentées
- `artefacts/v7/seasonal_experts.json` — résultats purged CV
- `docs/SEASONAL_EXPERTS_V7.md` — rapport avec verdict

### Critères de succès

```
6 politiques saisonnières fonctionnelles : OK
AUC delta (V6 vs V7-purged) documenté : OK
Politique best_v7 identifiée avec q_BH < 0.05 : GO_RESEARCH
```

---

### V7-07 — Roll-aware premium model

**Priorité** : HAUTE
**Type** : complexe
**Statut** : BLOCKED
**Phase** : 1
**Dépendances** : V7-02, V7-08
**experiment_type** : PREDICTIVE_OOF

### Contexte

Les rolls Euronext créent des distorsions artificielles dans la série premium. Ces distorsions peuvent être confondues avec des signaux économiques. Ce ticket modélise explicitement le roll-risk et intègre un roll-risk score [0,1] dans le pipeline comme feature de veto.

### Objectifs mesurables

- Roll-risk score [0,1] calculé quotidiennement (DTE, historical gap percentile, recent vol)
- AUC premium avec vs sans roll-risk score documenté
- Veto automatique sur les jours à roll-risk > 0.7
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/euronext_curve.py` | Courbe terme EMA, roll dates |
| `src/mais/features/curve_spreads.py` | Spreads calendaires |
| `src/mais/features/euronext_continuous.py` | Construction série continue |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/roll_risk.py` | Créer — roll-risk score |
| `artefacts/v7/roll_aware_premium.json` | Créer — résultats |
| `docs/ROLL_AWARE_PREMIUM.md` | Créer — rapport |
| `tests/test_roll_risk.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Roll-risk score**
```python
def compute_roll_risk_score(
    df: pd.DataFrame,
    dte_col: str = "days_to_expiry",
    gap_col: str = "roll_gap",
) -> pd.Series:
    """Score roll-risk [0,1] : 0=pas de risque, 1=risque maximum."""
    # Composante 1 : Proximité du roll (DTE)
    dte_score = np.clip(1 - df[dte_col] / 30, 0, 1)  # Max score dans les 30 derniers jours

    # Composante 2 : Percentile historique du gap de roll
    gap_percentile = df[gap_col].expanding().rank(pct=True)

    # Composante 3 : Volatilité récente (20j vs 60j)
    vol_20 = df["ema_close"].pct_change().rolling(20).std()
    vol_60 = df["ema_close"].pct_change().rolling(60).std()
    vol_ratio = (vol_20 / vol_60).clip(0, 3) / 3  # normalisé [0,1]

    # Score composite
    roll_risk = 0.4 * dte_score + 0.4 * gap_percentile + 0.2 * vol_ratio
    return roll_risk.rename("roll_risk_score")

def apply_roll_veto(
    signals: pd.DataFrame,
    roll_risk: pd.Series,
    threshold: float = 0.7
) -> pd.DataFrame:
    """Veto automatique sur jours à roll-risk élevé."""
    signals = signals.copy()
    high_roll = roll_risk > threshold
    signals.loc[high_roll, "confidence"] = 0.0
    signals.loc[high_roll, "veto"] = "ROLL_RISK"
    return signals
```

### Livrables obligatoires

- `src/mais/features/roll_risk.py` — roll-risk score + veto
- `artefacts/v7/roll_aware_premium.json` — comparaison AUC avec/sans roll-risk
- `docs/ROLL_AWARE_PREMIUM.md` — rapport

### Critères de succès

```
Roll-risk score [0,1] calculé sans NA après 60j : OK
AUC premium avec veto >= AUC sans veto : OK (plus de signal / bruit)
Contribution roll-risk documentée dans V7-14 (explicabilité) : OK
```

---

### V7-08 — Régimes de basis

**Priorité** : HAUTE
**Type** : complexe
**Statut** : BLOCKED
**Phase** : 1
**Dépendances** : V7-02
**experiment_type** : MODEL_VALIDATION

### Contexte

Le basis EMA/CBOT n'est pas stationnaire. La prime européenne alterne entre des régimes économiques distincts : hausse persistante (récolte européenne mauvaise), compression (convergence CBOT+EMA), distorsion roll, etc. Identifier ces régimes améliore la précision des modèles et permet des filtres conditionnels.

### Objectifs mesurables

- 6 régimes de basis identifiés et nommés (NORMAL, HIGH_STABLE, HIGH_COMPRESSING, HIGH_EXPANDING, LOW_BASIS, ROLL_DISTORTED)
- Schéma de sortie `_build_regimes()` : colonnes `Date, corn_close, return_60d, realized_vol_60d, regime_score, regime`
- Probabilité de transition entre régimes documentée
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/ema_features.py` | Features basis existantes |
| `src/mais/research/ema_return_decomposition.py` | Décomposition V6 |
| `src/mais/walkforward/purged_cv.py` | Protocole CV |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/basis_regimes_v7.py` | Créer — 6 régimes |
| `artefacts/v7/basis_regimes.json` | Créer — résultats |
| `docs/BASIS_REGIMES.md` | Créer — rapport |
| `tests/test_basis_regimes.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Construction des 6 régimes**
```python
def _build_regimes(df: pd.DataFrame) -> pd.DataFrame:
    """Schéma fixe : Date, corn_close, return_60d, realized_vol_60d, regime_score, regime."""
    basis = df["ema_close"] - df["cbot_close_eur"]  # basis EUR/t
    basis_z = (basis - basis.expanding().mean()) / basis.expanding().std()
    basis_trend = basis.rolling(20).mean() - basis.rolling(60).mean()
    roll_risk = df.get("roll_risk_score", pd.Series(0, index=df.index))

    def classify_regime(row):
        z, trend, rr = row["basis_z"], row["basis_trend"], row["roll_risk"]
        if rr > 0.7:
            return "ROLL_DISTORTED"
        elif z > 1.5 and abs(trend) < 0.5:
            return "HIGH_STABLE"
        elif z > 1.0 and trend < -0.5:
            return "HIGH_COMPRESSING"
        elif z > 1.0 and trend > 0.5:
            return "HIGH_EXPANDING"
        elif z < -1.0:
            return "LOW_BASIS"
        return "NORMAL"

    regimes_df = pd.DataFrame({
        "Date": df.index,
        "corn_close": df["ema_close"],
        "return_60d": df["ema_close"].pct_change(60),
        "realized_vol_60d": df["ema_close"].pct_change().rolling(60).std() * np.sqrt(252),
        "basis_z": basis_z,
        "basis_trend": basis_trend,
        "roll_risk": roll_risk,
    }).set_index("Date")

    regimes_df["regime"] = regimes_df.apply(classify_regime, axis=1)
    regimes_df["regime_score"] = basis_z.clip(-3, 3) / 3  # score [-1, 1]

    return regimes_df[["corn_close", "return_60d", "realized_vol_60d", "regime_score", "regime"]]
```

**Test du schéma de sortie**
```python
def test_build_regimes_schema(df):
    result = _build_regimes(df)
    required = ["corn_close", "return_60d", "realized_vol_60d", "regime_score", "regime"]
    assert all(c in result.columns for c in required)
    assert result.index.name == "Date"
    assert set(result["regime"].dropna().unique()).issubset(
        {"NORMAL", "HIGH_STABLE", "HIGH_COMPRESSING", "HIGH_EXPANDING", "LOW_BASIS", "ROLL_DISTORTED"}
    )
```

### Livrables obligatoires

- `src/mais/research/basis_regimes_v7.py` — 6 régimes + schéma fixe
- `artefacts/v7/basis_regimes.json` — fréquence et durée de chaque régime
- `docs/BASIS_REGIMES.md` — rapport avec matrice de transition

### Critères de succès

```
_build_regimes() retourne colonnes exactes requises : OK
6 régimes couvrent 100% des dates (pas de NA) : OK
Durée médiane de chaque régime > 10 jours : OK
```

---

### V7-12 — P(correct) et calibration avancée

**Priorité** : HAUTE
**Type** : complexe
**Statut** : DONE
**Phase** : 1
**Dépendances** : V7-03, V7-06
**experiment_type** : PREDICTIVE_OOF

### Contexte

Un modèle qui prédit 60% de bonne direction mais ne sait pas QUAND il a raison est peu utilisable. Ce ticket entraîne un méta-modèle `P(correct)` qui prédit la probabilité que la prédiction principale soit correcte. Ce signal de confiance est utilisé comme filtre de sélection dans V7-13 et V7-28.

### Objectifs mesurables

- Modèle P(correct) entraîné sur features de contexte (régime, roll_risk, data_quality, consensus)
- Calibration Brier score < 0.25 sur test OOF
- AUC P(correct) > 0.60 sur les erreurs du modèle principal
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/meta/stacking.py` | Meta-model V6, base pour P(correct) |
| `src/mais/meta/conformal.py` | Intervalles de confiance existants |
| `src/mais/research/basis_regimes_v7.py` | Régimes V7-08 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/meta/p_correct.py` | Créer — modèle P(correct) |
| `artefacts/v7/p_correct_model.json` | Créer — résultats calibration |
| `docs/P_CORRECT_MODEL.md` | Créer — rapport |
| `tests/test_p_correct.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Features du modèle P(correct)**
```python
def build_p_correct_features(
    df: pd.DataFrame,
    primary_prediction: pd.Series,
    regimes: pd.DataFrame,
    roll_risk: pd.Series,
    data_quality: pd.Series,
) -> pd.DataFrame:
    feats = pd.DataFrame(index=df.index)
    feats["primary_proba"] = primary_prediction               # confiance du modèle principal
    feats["basis_regime"] = pd.Categorical(regimes["regime"]).codes
    feats["roll_risk"] = roll_risk
    feats["data_quality_score"] = data_quality
    feats["primary_proba_distance"] = (primary_prediction - 0.5).abs()  # distance à 0.5
    feats["vol_ratio_20_60"] = (
        df["ema_close"].pct_change().rolling(20).std() /
        df["ema_close"].pct_change().rolling(60).std()
    )
    return feats

def train_p_correct(X_meta: pd.DataFrame, y_was_correct: pd.Series, cv_splits):
    """Entraîner P(correct) en OOF strict."""
    from sklearn.calibration import CalibratedClassifierCV
    from lightgbm import LGBMClassifier
    clf = CalibratedClassifierCV(LGBMClassifier(n_estimators=100, seed=42), cv=3)
    p_correct_oof = np.zeros(len(y_was_correct))
    for train_idx, test_idx in cv_splits:
        clf.fit(X_meta.iloc[train_idx], y_was_correct.iloc[train_idx])
        p_correct_oof[test_idx] = clf.predict_proba(X_meta.iloc[test_idx])[:, 1]
    return p_correct_oof
```

**Évaluation de la calibration**
```python
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve

brier = brier_score_loss(y_was_correct, p_correct_oof)
fraction_pos, mean_pred = calibration_curve(y_was_correct, p_correct_oof, n_bins=10)
# Brier < 0.25 : OK, < 0.20 : excellent
```

### Livrables obligatoires

- `src/mais/meta/p_correct.py` — modèle P(correct) OOF strict
- `artefacts/v7/p_correct_model.json` — Brier score + AUC
- `docs/P_CORRECT_MODEL.md` — rapport

### Critères de succès

```
Brier score < 0.25 : OK
AUC P(correct) > 0.60 : OK
P(correct) calculé en OOF strict (is_oof=True) : OK
```

---

### V7-39 — Indicateur de qualité des données

**Priorité** : HAUTE
**Type** : moyen
**Statut** : READY
**Phase** : 1
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION

### Contexte

Certains jours, les données disponibles sont incomplètes (EIA manquant, COT retardé, WASDE absent). Un score de qualité [0,1] par date permet d'identifier les jours où les prédictions sont moins fiables et de les filtrer ou pondérer différemment.

### Objectifs mesurables

- Score qualité_data [0,1] calculé pour chaque date du dataset
- 6 composantes documentées avec poids w1-w6
- Corrélation entre score_qualité et erreur de prédiction calculée
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/data/publication_calendar.py` | Lags par source (V7-DATA-CAL) |
| `src/mais/features/__init__.py` | Pipeline features, NA par source |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/data_quality.py` | Créer — score qualité 6 composantes |
| `artefacts/v7/data_quality_scores.json` | Créer — résultats |
| `tests/test_data_quality.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Score qualité 6 composantes**
```python
def compute_data_quality_score(df: pd.DataFrame) -> pd.Series:
    """Score composite [0,1] par date : 6 composantes."""
    w = {"cot": 0.25, "wasde": 0.20, "eia": 0.15,
         "ema_price": 0.20, "cbot_price": 0.15, "basis": 0.05}

    scores = {}
    scores["cot"] = (~df["cot_net_position"].isna()).astype(float)
    scores["wasde"] = (~df["wasde_stocks"].isna()).astype(float)
    scores["eia"] = (~df["eia_ethanol"].isna()).astype(float)
    scores["ema_price"] = (~df["ema_close"].isna()).astype(float)
    scores["cbot_price"] = (~df["cbot_close"].isna()).astype(float)
    scores["basis"] = (~(df["ema_close"] - df["cbot_close_eur"]).isna()).astype(float)

    quality = sum(w[k] * scores[k] for k in w)
    return quality.rename("data_quality_score")
```

### Livrables obligatoires

- `src/mais/features/data_quality.py` — score 6 composantes
- `artefacts/v7/data_quality_scores.json` — statistiques par date
- `tests/test_data_quality.py` — test score dans [0,1]

### Critères de succès

```
Score [0,1] sur toutes les dates : OK
6 composantes documentées : OK
Corrélation score_qualité / erreur modèle calculée : OK
```

---

## PHASE 2 — Exploration de signaux économiques

---

### V7-09 — Décomposition dynamique EMA

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : READY
**Phase** : 2
**Dépendances** : V7-00
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Le prix EMA est influencé par plusieurs forces simultanées : la composante CBOT (marché mondial), le taux EUR/USD, la prime européenne fondamentale, et les distorsions de roll. Ce ticket décompose dynamiquement le mouvement EMA en ces composantes pour quantifier l'importance relative de chaque driver selon les régimes.

### Objectifs mesurables

- Décomposition EMA en 4 composantes : CBOT_component, FX_component, premium_component, roll_component
- Variance expliquée par composante documentée (% total)
- Décomposition stable sur 3 sous-périodes (2010-2014, 2015-2019, 2020-2023)
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/ema_return_decomposition.py` | Décomposition V6 |
| `src/mais/features/ema_features.py` | Features EMA |
| `src/mais/features/factors.py` | Facteurs FX |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/ema_decomposition_v7.py` | Créer — décomposition 4 composantes |
| `artefacts/v7/ema_decomposition.json` | Créer — résultats |
| `docs/EMA_DECOMPOSITION_V7.md` | Créer — rapport |
| `tests/test_ema_decomposition.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Décomposition par régression roulante**
```python
def decompose_ema_returns(df: pd.DataFrame, window: int = 120) -> pd.DataFrame:
    """Décomposition rolling par OLS sur 4 composantes."""
    from sklearn.linear_model import LinearRegression

    ema_ret = df["ema_close"].pct_change()
    cbot_ret_eur = df["cbot_close_eur"].pct_change()
    fx_ret = df["eurusd"].pct_change()
    basis_change = (df["ema_close"] - df["cbot_close_eur"]).diff()
    roll_adj = df.get("roll_adj", pd.Series(0, index=df.index))

    components = pd.DataFrame({
        "cbot_component": np.nan,
        "fx_component": np.nan,
        "premium_component": np.nan,
        "roll_component": np.nan,
        "r2": np.nan,
    }, index=df.index)

    X = pd.DataFrame({
        "cbot": cbot_ret_eur,
        "fx": fx_ret,
        "basis": basis_change,
        "roll": roll_adj,
    }).dropna()

    for i in range(window, len(X)):
        X_w = X.iloc[i-window:i]
        y_w = ema_ret.loc[X_w.index]
        mask = y_w.notna()
        reg = LinearRegression().fit(X_w[mask], y_w[mask])
        components.loc[X.index[i], "cbot_component"] = reg.coef_[0]
        components.loc[X.index[i], "fx_component"] = reg.coef_[1]
        components.loc[X.index[i], "premium_component"] = reg.coef_[2]
        components.loc[X.index[i], "roll_component"] = reg.coef_[3]
        components.loc[X.index[i], "r2"] = reg.score(X_w[mask], y_w[mask])

    return components
```

### Livrables obligatoires

- `src/mais/research/ema_decomposition_v7.py` — décomposition 4 composantes
- `artefacts/v7/ema_decomposition.json` — variance par composante/période
- `docs/EMA_DECOMPOSITION_V7.md` — rapport économique

### Critères de succès

```
4 composantes calculées sans NA après 120j : OK
Variance totale expliquée documentée par période : OK
experiment_type = DESCRIPTIVE_ECONOMIC (pas de verdict GO/NO_GO) : OK
```

---

### V7-10 — Event study premium

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : READY
**Phase** : 2
**Dépendances** : V7-00
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Les publications WASDE, COT, récoltes majeures et crises géopolitiques créent des mouvements aberrants dans le premium EMA/CBOT. Ce ticket mesure l'impact moyen des événements sur le premium (avant/après) sur des fenêtres [-30j, +60j], et identifie les patterns persistants vs transitoires.

### Objectifs mesurables

- 8 types d'événements analysés avec fenêtres [-30j, +60j]
- Abnormal return moyen (vs benchmark) documenté par type d'événement
- Bootstrap p-value pour chaque effet
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/confidence_study.py` | Analyse de confiance V6 |
| `src/mais/features/surprise.py` | Features surprise WASDE |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/event_study_v7.py` | Créer — 8 types événements |
| `artefacts/v7/event_study.json` | Créer — résultats |
| `docs/EVENT_STUDY_V7.md` | Créer — rapport |
| `tests/test_event_study.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**8 types d'événements**
```python
EVENT_TYPES = {
    "wasde_bullish_surprise": "WASDE revision > +1 MT",
    "wasde_bearish_surprise": "WASDE revision < -1 MT",
    "cot_speculative_extreme_long": "Net position speculative > 90th percentile",
    "cot_speculative_extreme_short": "Net position speculative < 10th percentile",
    "european_drought": "NDVI anomalie > -1 std sur zone EU maïs",
    "ukraine_conflict_escalation": "Dates clés 2022",
    "us_harvest_report": "NASS crop progress > 90%",
    "eu_harvest_poor": "MARS yield estimate < historical mean - 1std",
}

def compute_abnormal_return(
    event_dates: pd.DatetimeIndex,
    premium: pd.Series,
    window_before: int = 30,
    window_after: int = 60,
) -> dict:
    """Calcule le retour anormal autour des événements."""
    car_list = []
    for event_date in event_dates:
        pre = premium.loc[event_date - pd.Timedelta(days=window_before):event_date]
        post = premium.loc[event_date:event_date + pd.Timedelta(days=window_after)]
        if len(post) > 5:
            benchmark_return = pre.mean()
            car = post.mean() - benchmark_return
            car_list.append(car)
    return {
        "n_events": len(car_list),
        "mean_car": float(np.mean(car_list)) if car_list else None,
        "p_value_bootstrap": bootstrap_mean_pvalue(car_list)
    }
```

### Livrables obligatoires

- `src/mais/research/event_study_v7.py` — 8 types d'événements
- `artefacts/v7/event_study.json` — CAR par type d'événement
- `docs/EVENT_STUDY_V7.md` — rapport

### Critères de succès

```
8 types d'événements analysés : OK
Bootstrap p-value calculée pour chaque effet : OK
Événements à effet significatif identifiés : OK
```

---

### V7-11A — Données EU — EC MARS

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

Le bulletin MARS de la Commission Européenne publie mensuellement des estimations de rendements par culture et région. Ces estimations arrivent avec 14-21 jours de retard. Ce ticket intègre les données MARS historiques, valide leur qualité et teste si l'écart MARS vs consensus ajoute un signal au premium EMA/CBOT.

### Objectifs mesurables

- Série MARS rendements maïs EU disponible depuis au moins 2005
- Shift officiel = 21 jours (délai conservateur publication)
- Corrélation MARS_surprise vs premium_change documentée
- Verdict : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/data/publication_calendar.py` | Lag officiel EC MARS |
| `src/mais/features/__init__.py` | Pipeline features, point d'intégration |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/eu_mars.py` | Créer — feature MARS surprise |
| `artefacts/v7/eu_data_11a_mars.json` | Créer — verdict DATA |
| `tests/test_eu_mars.py` | Créer |

### Fichiers interdits

`notebooks/`

### Implémentation

```python
def build_mars_features(df_mars: pd.DataFrame, lag_days: int = 21) -> pd.DataFrame:
    """Feature MARS : écart vs consensus historique (shift officiel = 21j)."""
    df_mars = df_mars.copy()
    df_mars.index = pd.to_datetime(df_mars.index)
    # Anti-leakage : shift du lag officiel
    yield_estimate = df_mars["eu_corn_yield_est"].shift(lag_days)
    # Surprise : écart vs moyenne rolling des 3 estimations précédentes
    consensus = yield_estimate.rolling(3).mean()
    mars_surprise = yield_estimate - consensus
    return pd.DataFrame({
        "mars_yield_estimate": yield_estimate,
        "mars_surprise": mars_surprise,
        "mars_surprise_z": (mars_surprise - mars_surprise.expanding().mean()) /
                           mars_surprise.expanding().std()
    })

def test_mars_signal(df_combined: pd.DataFrame) -> dict:
    """Test si mars_surprise_z ajoute du signal au premium."""
    corr = df_combined["mars_surprise_z"].corr(df_combined["premium_return_h90"])
    n = df_combined[["mars_surprise_z", "premium_return_h90"]].dropna().__len__()
    return {
        "correlation": float(corr), "n": n,
        "verdict": "SIGNAL_ADDS_VALUE" if abs(corr) > 0.15 and n >= 50
                   else "NO_SIGNAL" if n >= 50
                   else "DATA_TOO_SPARSE"
    }
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11a_mars.json` — verdict avec métriques
- `src/mais/features/eu_mars.py` si DATA_OK ou DATA_PARTIAL

### Critères de succès

```
Verdict clairement émis parmi : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE
Shift officiel = lag_days respecté : OK
```

---

### V7-11B — Données EU — FranceAgriMer

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

FranceAgriMer publie mensuellement le bilan offres/demandes céréales France. La France étant le premier producteur européen de maïs, ces données impactent directement le premium EMA/CBOT. Délai conservateur : 30 jours.

### Objectifs mesurables

- Bilan cerales maïs France disponible (stock début, production, exportations)
- Shift officiel = 30 jours respecté
- Test corrélation révision de bilan vs premium change
- Verdict DATA émis

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/franceagrimer.py` | Créer si DATA_OK |
| `artefacts/v7/eu_data_11b_franceagrimer.json` | Créer — verdict |

### Implémentation

```python
def build_franceagrimer_features(df_fam: pd.DataFrame, lag_days: int = 30) -> pd.DataFrame:
    """Bilan FranceAgriMer : stock, production, exports avec shift officiel."""
    cols = ["stocks_debut", "production", "exports", "utilisation_interieure"]
    df = df_fam[cols].shift(lag_days)
    df["fam_balance"] = df["production"] - df["exports"] - df["utilisation_interieure"]
    df["fam_balance_revision"] = df["fam_balance"].diff()
    df["fam_balance_revision_z"] = (
        df["fam_balance_revision"] - df["fam_balance_revision"].expanding().mean()
    ) / df["fam_balance_revision"].expanding().std()
    return df
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11b_franceagrimer.json` — verdict DATA
- `src/mais/features/franceagrimer.py` si applicable

---

### V7-11C — Données EU — Eurostat COMEXT

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

Eurostat COMEXT publie les flux commerciaux EU par produit et pays d'origine. Délai très long (30-75 jours). Utile comme signal de pression d'importation EU maïs mais potentiellement trop retardé pour prédire H40.

### Objectifs mesurables

- Imports EU maïs par pays origine disponibles depuis 2010
- Shift officiel = 75 jours respecté
- Signal évalué uniquement sur H90/H120 (H40 trop court vs lag)
- Verdict DATA émis

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/eurostat_comext.py` | Créer si DATA_OK |
| `artefacts/v7/eu_data_11c_comext.json` | Créer — verdict |

### Implémentation

```python
def build_comext_features(df_comext: pd.DataFrame, lag_days: int = 75) -> pd.DataFrame:
    """Flux COMEXT : imports EU maïs par pays, shift 75j."""
    total_imports = df_comext.groupby("date")["quantity_kg"].sum()
    ukraine_share = (
        df_comext[df_comext["country_origin"] == "UA"]
        .groupby("date")["quantity_kg"].sum() / total_imports
    )
    feats = pd.DataFrame({
        "comext_eu_corn_imports": total_imports.shift(lag_days),
        "comext_ukraine_share": ukraine_share.shift(lag_days),
        "comext_imports_yoy": total_imports.pct_change(12).shift(lag_days),
    })
    return feats
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11c_comext.json` — verdict DATA
- Note : si lag 75j → signal uniquement pour H90/H120

---

### V7-11D — Données EU — Exports Ukraine

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

L'Ukraine est le 2e exportateur mondial de maïs. Ses exportations impactent directement la disponibilité et le premium EMA/CBOT. Les données douanières ukrainiennes sont disponibles avec 7-14 jours de délai via des sources officielles (USDA, Ukrstat).

### Objectifs mesurables

- Exports hebdomadaires Ukraine maïs disponibles depuis 2010
- Shift officiel = 14 jours
- Signal Ukraine exports change vs premium documenté
- Verdict DATA émis

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/ukraine_exports.py` | Créer si DATA_OK |
| `artefacts/v7/eu_data_11d_ukraine.json` | Créer — verdict |

### Implémentation

```python
def build_ukraine_export_features(df_ukr: pd.DataFrame, lag_days: int = 14) -> pd.DataFrame:
    """Exports Ukraine maïs : variation hebdomadaire, shift 14j."""
    exports_w = df_ukr["ukraine_corn_exports_kt"].resample("W").sum()
    feats = pd.DataFrame({
        "ukraine_exports_w": exports_w.shift(lag_days // 7),
        "ukraine_exports_4w_sum": exports_w.rolling(4).sum().shift(lag_days // 7),
        "ukraine_exports_yoy_pct": exports_w.pct_change(52).shift(lag_days // 7),
        "ukraine_exports_momentum": (
            exports_w.rolling(4).mean() / exports_w.rolling(26).mean()
        ).shift(lag_days // 7),
    })
    return feats.resample("D").ffill()
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11d_ukraine.json` — verdict DATA avec métriques

---

### V7-11E — Données EU — Météo pondérée UE

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

Les anomalies météo dans les zones de production maïs EU (France, Allemagne, Roumanie, Ukraine) ont un impact direct sur les rendements et le premium EMA. Ce ticket construit un index météo pondéré par surface cultivée.

### Objectifs mesurables

- Index météo pondéré pour 5 pays producteurs (France, DE, RO, PL, UA)
- Variables : température, précipitations, NDVI (si disponible)
- Corrélation avec premium été documentée (juin-août = période critique)
- Verdict DATA émis

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/weather_belt.py` | Données météo existantes |
| `src/mais/features/phenology.py` | Phases phénologiques |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/eu_weather_weighted.py` | Créer — index pondéré |
| `artefacts/v7/eu_data_11e_weather.json` | Créer — verdict |

### Implémentation

```python
EU_CORN_WEIGHTS = {
    "FR": 0.28, "DE": 0.14, "RO": 0.18, "PL": 0.12, "UA": 0.20, "other": 0.08
}

def build_eu_weather_index(df_weather: pd.DataFrame) -> pd.DataFrame:
    """Index météo pondéré EU maïs."""
    weighted_temp = sum(
        EU_CORN_WEIGHTS[country] * df_weather[f"temp_anomaly_{country}"]
        for country in EU_CORN_WEIGHTS if country != "other"
        and f"temp_anomaly_{country}" in df_weather.columns
    )
    weighted_precip = sum(
        EU_CORN_WEIGHTS[country] * df_weather[f"precip_anomaly_{country}"]
        for country in EU_CORN_WEIGHTS if country != "other"
        and f"precip_anomaly_{country}" in df_weather.columns
    )
    # Stress index : temp haute + précip faible en été = stress
    stress_index = weighted_temp - 0.5 * weighted_precip
    return pd.DataFrame({
        "eu_weather_temp_index": weighted_temp,
        "eu_weather_precip_index": weighted_precip,
        "eu_weather_stress": stress_index,
    })
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11e_weather.json` — verdict DATA
- `src/mais/features/eu_weather_weighted.py` si DATA_OK

---

### V7-11F — Données EU — Prix FOB export

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

Les prix FOB Rouen (France), FOB Ukraine (Odessa/Mykolaiv), et FOB Brazil (Paranaguá) sont les références mondiales pour le maïs export. Leur écart vs CBOT reflète les tensions logistiques et la compétitivité EU. Lag : 1-3 jours (cotations quasi-temps-réel).

### Objectifs mesurables

- Prix FOB Rouen, Ukraine, Brazil disponibles (au moins 2015-2023)
- Spread FOB_Rouen - CBOT_EUR calculé quotidiennement
- Corrélation spread FOB vs premium EMA/CBOT documentée
- Verdict DATA émis

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/fob_prices.py` | Créer si DATA_OK |
| `artefacts/v7/eu_data_11f_fob.json` | Créer — verdict |

### Implémentation

```python
def build_fob_features(df_fob: pd.DataFrame, lag_days: int = 2) -> pd.DataFrame:
    """Spreads FOB : Rouen, Ukraine, Brazil vs CBOT_EUR."""
    feats = {}
    for origin in ["rouen", "ukraine", "brazil"]:
        col = f"fob_{origin}_eur_t"
        if col in df_fob.columns:
            fob = df_fob[col].shift(lag_days)
            feats[f"fob_{origin}_vs_cbot"] = fob - df_fob["cbot_close_eur"].shift(lag_days)
            feats[f"fob_{origin}_spread_z"] = (
                feats[f"fob_{origin}_vs_cbot"] -
                feats[f"fob_{origin}_vs_cbot"].expanding().mean()
            ) / feats[f"fob_{origin}_vs_cbot"].expanding().std()
    # Spread inter-origines (arbitrage)
    if "fob_rouen_vs_cbot" in feats and "fob_ukraine_vs_cbot" in feats:
        feats["fob_rouen_ukraine_spread"] = (
            feats["fob_rouen_vs_cbot"] - feats["fob_ukraine_vs_cbot"]
        )
    return pd.DataFrame(feats)
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11f_fob.json` — verdict DATA avec corrélation vs premium

---

### V7-11G — Données EU — Énergie, TTF, fertilisants

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 2
**Dépendances** : V7-DATA-CAL
**experiment_type** : DATA_VALIDATION
**Verdict possible** : DATA_OK / DATA_PARTIAL / DATA_TOO_SPARSE / DATA_BLOCKED / NO_SIGNAL / SIGNAL_ADDS_VALUE

### Contexte

Le coût de production du maïs EU est fortement lié aux prix de l'énergie (gaz TTF) et des fertilisants azotés (DAP, urée). Ces inputs impactent l'offre EU et donc le premium EMA. Le carbone EU (ETS) affecte le coût de production des biocarburants (demande maïs EU).

### Objectifs mesurables

- TTF, EUA, DAP price séries disponibles depuis 2010
- Lag = 1 jour (cotations quotidiennes)
- Corrélation TTF/DAP vs premium change documentée
- Verdict DATA émis

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/energy_fertilizer.py` | Créer si DATA_OK |
| `artefacts/v7/eu_data_11g_energy.json` | Créer — verdict |

### Implémentation

```python
def build_energy_features(df_energy: pd.DataFrame, lag_days: int = 1) -> pd.DataFrame:
    """Features énergie/fertilisants : TTF, EUA, DAP."""
    feats = pd.DataFrame(index=df_energy.index)

    for col in ["ttf_gas_eur_mwh", "eua_carbon_eur_t", "dap_usd_t", "urea_usd_t"]:
        if col in df_energy.columns:
            series = df_energy[col].shift(lag_days)
            feats[f"{col}_ret20"] = series.pct_change(20)
            feats[f"{col}_z60"] = (
                series - series.expanding().mean()
            ) / series.expanding().std()

    # Ratio gaz/maïs : coût production relatif
    if "ttf_gas_eur_mwh" in df_energy.columns and "ema_close" in df_energy.columns:
        feats["ttf_corn_ratio"] = (
            df_energy["ttf_gas_eur_mwh"].shift(lag_days) /
            df_energy["ema_close"].shift(lag_days)
        )

    return feats
```

### Livrables obligatoires

- `artefacts/v7/eu_data_11g_energy.json` — verdict DATA avec métriques

---

### V7-17 — Relations inter-commodités

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : READY
**Phase** : 2
**Dépendances** : V7-00
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Le maïs est en concurrence avec le soja, le blé et l'orge pour l'utilisation des terres et de l'alimentation animale. Le ratio maïs/soja, le spread blé/maïs, et l'indice GSCI agroalimentaire capturent des substitutions fondamentales. Ce ticket quantifie ces relations et teste leur valeur prédictive pour le premium EMA/CBOT.

### Objectifs mesurables

- 6 spreads inter-commodités calculés (corn/soy ratio, wheat/corn spread, corn/ethanol, GSCI corn component, corn/feed barley, corn/oats)
- Corrélation mobile documentée vs premium (fenêtre 90j glissante)
- Test régression OOF : les spreads ajoutent-ils au modèle baseline ?
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/features/market.py` | Features marché existantes |
| `src/mais/features/factors.py` | Facteurs multi-actifs |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/inter_commodity.py` | Créer — 6 spreads |
| `artefacts/v7/inter_commodity.json` | Créer — résultats |
| `docs/INTER_COMMODITY.md` | Créer — rapport |
| `tests/test_inter_commodity.py` | Créer |

### Implémentation

```python
def build_inter_commodity_features(df: pd.DataFrame) -> pd.DataFrame:
    feats = pd.DataFrame(index=df.index)

    # Ratio corn/soy (substitution alimentation animale)
    feats["corn_soy_ratio"] = df["cbot_corn_close"] / df["cbot_soy_close"]
    feats["corn_soy_ratio_z60"] = _expandz(feats["corn_soy_ratio"])

    # Spread wheat/corn (substitution céréales)
    feats["wheat_corn_spread"] = df["cbot_wheat_close"] - df["cbot_corn_close"]
    feats["wheat_corn_spread_z60"] = _expandz(feats["wheat_corn_spread"])

    # Corn vs ethanol economics
    if "ethanol_price_usd" in df.columns:
        feats["corn_ethanol_crush"] = df["ethanol_price_usd"] * 2.75 - df["cbot_corn_close"] / 36

    # GSCI agroalimentaire (positionnement institutionnel)
    if "gsci_agricultural" in df.columns:
        feats["gsci_agri_z60"] = _expandz(df["gsci_agricultural"])

    # Tous les features : shift(1) pour anti-leakage
    return feats.shift(1)

def _expandz(series: pd.Series) -> pd.Series:
    return (series - series.expanding().mean()) / series.expanding().std()
```

### Livrables obligatoires

- `src/mais/features/inter_commodity.py` — 6 spreads avec shift(1)
- `artefacts/v7/inter_commodity.json` — corrélations vs premium
- `docs/INTER_COMMODITY.md` — rapport économique

---

### V7-19 — Détection de ruptures structurelles

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : READY
**Phase** : 2
**Dépendances** : V7-00
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

La relation CBOT/EMA a probablement changé structurellement en 2022 (invasion Ukraine) et peut-être en 2020 (COVID). Ce ticket teste formellement les ruptures structurelles avec les tests Chow, CUSUM, et Bai-Perron, et documente les implications pour la stabilité des modèles.

### Objectifs mesurables

- Tests Chow sur 5 dates candidates (2008 crise, 2012 sécheresse, 2020 COVID, 2022 Ukraine)
- Test CUSUM sur les résidus de régression EMA~CBOT
- Bai-Perron multiple breakpoints (max 3)
- Implications pour la fenêtre d'entraînement documentées
- Tests : `ruff check` PASS

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/structural_breaks.py` | Créer — tests formels |
| `artefacts/v7/structural_breaks.json` | Créer — résultats |
| `docs/STRUCTURAL_BREAKS.md` | Créer — rapport |

### Implémentation

```python
def test_chow_breakpoint(y: pd.Series, X: pd.DataFrame, break_date: str) -> dict:
    """Test Chow de rupture structurelle."""
    try:
        import statsmodels.api as sm
    except ImportError:
        return {"error": "statsmodels_not_installed"}
    idx = pd.Timestamp(break_date)
    mask1 = X.index < idx
    mask2 = X.index >= idx
    if mask1.sum() < 30 or mask2.sum() < 30:
        return {"verdict": "INSUFFICIENT_DATA", "break_date": break_date}
    reg_full = sm.OLS(y, sm.add_constant(X)).fit()
    reg1 = sm.OLS(y[mask1], sm.add_constant(X[mask1])).fit()
    reg2 = sm.OLS(y[mask2], sm.add_constant(X[mask2])).fit()
    rss_full = reg_full.ssr
    rss_parts = reg1.ssr + reg2.ssr
    k = X.shape[1] + 1
    n = len(y)
    f_stat = ((rss_full - rss_parts) / k) / (rss_parts / (n - 2 * k))
    p_value = 1 - scipy.stats.f.cdf(f_stat, k, n - 2 * k)
    return {
        "break_date": break_date, "f_stat": float(f_stat),
        "p_value": float(p_value),
        "verdict": "BREAK_DETECTED" if p_value < 0.05 else "NO_BREAK"
    }
```

### Livrables obligatoires

- `artefacts/v7/structural_breaks.json` — résultats tous tests
- `docs/STRUCTURAL_BREAKS.md` — implications pour l'entraînement

---

### V7-25 — Tests des anomalies de marché

**Priorité** : MOYENNE
**Type** : moyen
**Statut** : READY
**Phase** : 2
**Dépendances** : V7-00, V7-29
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Certaines anomalies de prix sont documentées en théorie financière : effet momentum, mean-reversion, effet jour de la semaine, retournement post-WASDE. Ce ticket teste formellement 8 anomalies sur le premium EMA/CBOT pour documenter si des patterns exploitables persistent après correction BH.

### Objectifs mesurables

- 8 anomalies testées, q_BH calculé pour chacune
- Seules les anomalies avec q_BH < 0.05 sont retenues
- Analyse sub-période pour distinguer persistance vs artifact
- Tests : `ruff check` PASS

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/market_anomalies.py` | Créer — 8 tests anomalies |
| `artefacts/v7/market_anomalies.json` | Créer — résultats BH |
| `docs/MARKET_ANOMALIES.md` | Créer — rapport |

### Implémentation

```python
ANOMALY_TESTS = {
    "momentum_20d": lambda r: (r.rolling(20).mean() > 0).astype(int),
    "momentum_60d": lambda r: (r.rolling(60).mean() > 0).astype(int),
    "mean_reversion_20d": lambda r: (r.rolling(20).mean() < 0).astype(int),
    "post_wasde_drift": lambda r, wasde_dates: ...,  # drift après WASDE
    "harvest_seasonality": lambda r, dates: (dates.month.isin([9,10])).astype(int),
    "new_crop_seasonality": lambda r, dates: (dates.month.isin([3,4])).astype(int),
    "end_of_month": lambda r, dates: (dates.day >= 25).astype(int),
    "cot_reversal": lambda cot: (cot < cot.rolling(52).quantile(0.1)).astype(int),
}
```

### Livrables obligatoires

- `artefacts/v7/market_anomalies.json` — 8 tests avec q_BH

---

### V7-26 — Analyse de mémoire longue et persistance

**Priorité** : BASSE
**Type** : moyen
**Statut** : WATCHLIST
**Phase** : 2
**Dépendances** : V7-00
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Ticket WATCHLIST. La mémoire longue (Hurst, ARFIMA) dans le premium EMA/CBOT peut justifier des horizons plus longs ou invalider les hypothèses de stationnarité. Exécuter uniquement si les tickets Phase 1 montrent une persistance des signaux > H60.

### Objectifs mesurables

- Exposant de Hurst calculé sur premium, basis, CBOT
- Test ADF + KPSS pour stationnarité
- Modèle ARFIMA si H > 0.6

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/long_memory.py` | Créer — Hurst + ARFIMA |
| `artefacts/v7/long_memory.json` | Créer — résultats |

### Implémentation

```python
def hurst_exponent(series: pd.Series, min_lag: int = 10, max_lag: int = 100) -> float:
    """Exposant de Hurst par R/S analysis."""
    lags = range(min_lag, max_lag)
    tau = [series.iloc[:lag].std() for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]  # H > 0.5 = persistance, H < 0.5 = anti-persistance
```

### Livrables obligatoires

- `artefacts/v7/long_memory.json` — Hurst par série

---

### V7-32 — Fair value model EMA/CBOT

**Priorité** : HAUTE
**Type** : complexe
**Statut** : DONE
**Phase** : 2
**Dépendances** : V7-08, V7-09
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Le premium EMA/CBOT a une composante fondamentale (coûts de transport, parité d'importation, stocks EU) et une composante de marché (sentiment, positionnement). Un modèle de "fair value" décompose ces composantes et produit un signal de déviation : quand le premium est très au-dessus du fair value, mean-reversion probable.

### Objectifs mesurables

- Modèle économique linéaire : premium = f(transport_costs, stocks_eu, fx, importation_parity)
- Déviation premium vs fair value calculée quotidiennement
- AUC OOF déviation → premium_return_h90 > 0.55
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/basis_regimes_v7.py` | Régimes V7-08 |
| `src/mais/research/ema_decomposition_v7.py` | Décomposition V7-09 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/fair_value_model.py` | Créer — modèle fair value |
| `artefacts/v7/fair_value_model.json` | Créer — résultats |
| `docs/FAIR_VALUE_MODEL.md` | Créer — rapport |
| `tests/test_fair_value_model.py` | Créer |

### Implémentation

```python
def build_fair_value_model(df: pd.DataFrame, cv_splits) -> dict:
    """Modèle économique linéaire OOF pour fair value premium."""
    premium = df["ema_close"] - df["cbot_close_eur"]

    # Features fondamentales (toutes shiftées)
    X_fundamental = pd.DataFrame({
        "eu_corn_stocks_z": _expandz(df.get("eu_corn_stocks", pd.Series(np.nan, index=df.index))),
        "transport_cost_index": df.get("freight_rate_index", pd.Series(np.nan, index=df.index)).shift(1),
        "eurusd_z60": _expandz(df["eurusd"]),
        "fob_rouen_vs_cbot": df.get("fob_rouen_vs_cbot", pd.Series(np.nan, index=df.index)).shift(1),
    }).dropna()

    # Régression OOF (économique = linéaire, pas d'overfitting)
    from sklearn.linear_model import Ridge
    oof_fair_value = np.full(len(X_fundamental), np.nan)
    for train_idx, test_idx in cv_splits:
        X_tr = X_fundamental.iloc[train_idx]
        y_tr = premium.loc[X_fundamental.index[train_idx]]
        reg = Ridge(alpha=1.0).fit(X_tr.dropna(), y_tr.loc[X_tr.dropna().index])
        oof_fair_value[test_idx] = reg.predict(X_fundamental.iloc[test_idx].fillna(0))

    df_result = pd.DataFrame({
        "premium": premium.loc[X_fundamental.index],
        "fair_value": oof_fair_value,
        "deviation": premium.loc[X_fundamental.index].values - oof_fair_value,
    }, index=X_fundamental.index)

    return df_result
```

### Livrables obligatoires

- `src/mais/research/fair_value_model.py` — modèle OOF strict
- `artefacts/v7/fair_value_model.json` — résultats avec AUC
- `docs/FAIR_VALUE_MODEL.md` — rapport

---

### V7-33 — Cartographie des drivers par horizon

**Priorité** : HAUTE
**Type** : complexe
**Statut** : DONE
**Phase** : 2
**Dépendances** : V7-06, V7-07, V7-08
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Un driver important pour H40 peut être sans effet pour H90. Ce ticket cartographie la contribution de chaque feature par horizon (H20, H40, H60, H90, H120) et par régime de basis, pour guider la construction des modèles en Phase 3.

### Objectifs mesurables

- Feature importance OOF par horizon × régime
- Top 10 drivers documentés pour chaque (horizon, régime)
- Stabilité temporelle (rolling feature importance) calculée
- Tests : `ruff check` PASS

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/driver_cartography.py` | Créer — SHAP par horizon |
| `artefacts/v7/driver_cartography.json` | Créer — résultats |
| `docs/DRIVER_CARTOGRAPHY.md` | Créer — rapport |

### Implémentation

```python
def compute_driver_importance(X, y, horizons, cv_splits) -> dict:
    """SHAP feature importance OOF par horizon."""
    try:
        import shap
    except ImportError:
        return {"error": "shap_not_installed"}
    results = {}
    for H in horizons:
        shap_values_oof = np.zeros((len(X), X.shape[1]))
        for train_idx, test_idx in cv_splits:
            from lightgbm import LGBMClassifier
            clf = LGBMClassifier(n_estimators=200, seed=42)
            clf.fit(X.iloc[train_idx], y[H].iloc[train_idx])
            explainer = shap.TreeExplainer(clf)
            shap_values_oof[test_idx] = explainer.shap_values(X.iloc[test_idx])[1]
        results[H] = {
            "mean_abs_shap": {
                col: float(np.abs(shap_values_oof[:, i]).mean())
                for i, col in enumerate(X.columns)
            }
        }
    return results
```

### Livrables obligatoires

- `artefacts/v7/driver_cartography.json` — SHAP par horizon/régime
- `docs/DRIVER_CARTOGRAPHY.md` — rapport

---

## PHASE 3 — Modèles avancés

---

### V7-03 — Cross-target stacking V2

**Priorité** : HAUTE
**Type** : critique
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-00, V7-02, V7-06, V7-31
**experiment_type** : PREDICTIVE_OOF

### Contexte

V6 a montré qu'empiler les prédictions OOF de plusieurs cibles (H40, H60, H90, CBOT, basis) comme méta-features améliore significativement l'AUC. V7 étend ce stacking avec un protocole **nested walk-forward** rigoureux pour éliminer tout risque de leakage. Le résultat principal de V7 sera ce meta-modèle V2.

**Protocole nested walk-forward (obligatoire)**

Le problème du stacking temporel : si les meta-features OOF des sous-modèles sont générées sur tout le dataset, puis le meta-modèle est entraîné dessus, il y a un leakage car des observations futures ont contribué à la génération des features d'entraînement du meta-modèle.

Solution obligatoire :
- **Outer loop** = boucle de validation année/crop-year
- **Inner loop** = generation des prédictions OOF des experts, UNIQUEMENT dans le outer train
- **Interdiction absolue** : aucune prédiction auxiliaire générée sur une date qui appartient au outer test

### Objectifs mesurables

- Meta-modèle V2 entraîné avec protocole nested walk-forward
- AUC ≥ AUC V6 (0.937) sur protocole purged CV V7-02
- Delta AUC (meta V2 vs meilleur expert seul) > 0.02
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/meta/stacking.py` | Stacking V6, base pour V2 |
| `src/mais/walkforward/purged_cv.py` | Protocole CV V7-02 |
| `src/mais/research/seasonal_experts_v7.py` | Experts saisonniers V7-06 |
| `src/mais/research/benchmark_suite.py` | Benchmarks V7-31 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/meta/nested_stacking.py` | Créer — nested walk-forward stacking |
| `artefacts/v7/cross_target_stacking_v2.json` | Créer — résultats |
| `docs/CROSS_TARGET_STACKING_V2.md` | Créer — rapport |
| `tests/test_nested_stacking.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Étape 1 — Structure du nested walk-forward**
```python
def nested_walk_forward_stacking(
    X: pd.DataFrame,
    y_targets: dict[str, pd.Series],
    outer_cv,
    inner_cv_factory,
    base_learners: dict,
    meta_learner,
    embargo_days: int,
) -> dict:
    """
    Nested walk-forward stacking avec isolation stricte outer/inner.

    Outer loop : validation par crop-year (leave_one_crop_year)
    Inner loop : OOF des base_learners, UNIQUEMENT sur outer_train
    Garantie : aucune date outer_test n'apparaît dans inner_train ou inner_test
    """
    meta_oof = {target: np.full(len(X), np.nan) for target in y_targets}

    for outer_fold_id, (outer_train_idx, outer_test_idx) in enumerate(outer_cv):
        # Isolation stricte : inner ne voit que outer_train
        X_outer_train = X.iloc[outer_train_idx]
        X_outer_test = X.iloc[outer_test_idx]

        # Vérification embargo outer
        outer_train_end = X_outer_train.index[-1]
        outer_test_start = X_outer_test.index[0]
        assert outer_test_start > outer_train_end + pd.Timedelta(days=embargo_days), \
            f"Outer fold {outer_fold_id}: embargo violation"

        # Inner loop : générer OOF des base_learners sur outer_train uniquement
        inner_meta_features = {}
        inner_cv = inner_cv_factory(X_outer_train, embargo_days)

        for learner_name, (learner_fn, target_key) in base_learners.items():
            y_inner = y_targets[target_key].loc[X_outer_train.index]
            inner_oof = np.full(len(X_outer_train), np.nan)

            for inner_train_idx, inner_test_idx in inner_cv:
                # VÉRIFICATION CRITIQUE : inner_test doit rester dans outer_train
                inner_test_dates = X_outer_train.index[inner_test_idx]
                outer_test_dates = X_outer_test.index
                assert len(inner_test_dates.intersection(outer_test_dates)) == 0, \
                    "LEAKAGE DÉTECTÉ : inner_test contient des dates outer_test"

                clf = learner_fn()
                X_in_tr = X_outer_train.iloc[inner_train_idx].dropna()
                y_in_tr = y_inner.iloc[inner_train_idx].loc[X_in_tr.index]
                clf.fit(X_in_tr, y_in_tr)
                inner_oof[inner_test_idx] = clf.predict_proba(
                    X_outer_train.iloc[inner_test_idx]
                )[:, 1]

            inner_meta_features[learner_name] = pd.Series(
                inner_oof, index=X_outer_train.index, name=learner_name
            )
            inner_meta_features[learner_name].attrs["is_oof"] = True

        # Construire X_meta pour outer_train
        X_meta_train = pd.DataFrame(inner_meta_features).dropna()
        y_meta_train = y_targets["y_rel_outperform_h90"].loc[X_meta_train.index]

        # Générer prédictions meta pour outer_test
        # Prédictions base sur outer_test : pas d'OOF possible → entraîner sur tout outer_train
        outer_test_base_preds = {}
        for learner_name, (learner_fn, target_key) in base_learners.items():
            clf_full = learner_fn()
            y_full_tr = y_targets[target_key].loc[X_outer_train.index].dropna()
            X_full_tr = X_outer_train.loc[y_full_tr.index]
            clf_full.fit(X_full_tr, y_full_tr)
            outer_test_base_preds[learner_name] = clf_full.predict_proba(X_outer_test)[:, 1]

        X_meta_test = pd.DataFrame(outer_test_base_preds, index=X_outer_test.index)

        # Entraîner le meta-modèle sur inner OOF
        meta_clf = meta_learner()
        meta_clf.fit(X_meta_train, y_meta_train)

        # Prédire sur outer_test
        y_meta_pred = meta_clf.predict_proba(X_meta_test.fillna(0.5))[:, 1]
        for target in y_targets:
            meta_oof[target][outer_test_idx] = y_meta_pred

    return meta_oof
```

**Étape 2 — Test de non-leakage nested**
```python
def test_nested_stacking_no_leakage():
    """Vérifier que les meta-features OOF ne contiennent pas de leakage."""
    # Test 1 : shuffle labels → AUC ≈ 0.5
    # Test 2 : inner_test_dates ∩ outer_test_dates = ∅ pour tous les folds
    # Test 3 : meta_features.attrs["is_oof"] = True pour toutes les colonnes
    pass
```

**Étape 3 — Évaluer avec protocol purged CV**
```python
result = nested_walk_forward_stacking(
    X=X_features,
    y_targets=targets_dict,
    outer_cv=leave_one_crop_year(X_features.index),
    inner_cv_factory=lambda X_tr, emb: embargo_h(X_tr.index, emb),
    base_learners={
        "seasonal_expert": (lgbm_fn, "y_rel_outperform_h90"),
        "cbot_model": (lgbm_fn, "y_cbot_up_h60"),
        "basis_model": (lgbm_fn, "y_basis_up_h40"),
        "roll_model": (lgbm_fn, "y_rel_outperform_h90"),
    },
    meta_learner=lambda: LogisticRegression(C=1.0),
    embargo_days=90,
)
```

### Livrables obligatoires

- `src/mais/meta/nested_stacking.py` — protocole nested walk-forward complet
- `artefacts/v7/cross_target_stacking_v2.json` — résultats AUC
- `docs/CROSS_TARGET_STACKING_V2.md` — rapport avec documentation du protocole
- `tests/test_nested_stacking.py` — test de non-leakage

### Critères de succès

```
inner_test ∩ outer_test = ∅ pour tous les folds : OK (vérifié par assertion)
meta_features is_oof=True : OK
AUC meta V2 >= AUC V6 (0.937) : GO_RESEARCH
Delta AUC meta - best_single > 0.02 : GO_RESEARCH
```

---

### V7-05 — Cross-market CBOT ↔ EMA

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-04, V7-03
**experiment_type** : PREDICTIVE_OOF

### Contexte

V6 a montré un delta AUC CBOT modeste (0.059) quand on enrichit avec les signaux EMA. Ce ticket approfondit la relation bidirectionnelle : les signaux EMA ajoutent-ils au modèle CBOT, et vice-versa ? Il teste également si le CBOT signal peut servir de meta-feature de contexte pour le premium EMA.

### Objectifs mesurables

- AUC CBOT avec vs sans features EMA documenté
- AUC premium EMA avec vs sans features CBOT documenté
- Verdict : CBOT_ADDS_TO_EMA / EMA_ADDS_TO_CBOT / BIDIRECTIONAL / NONE
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/ema_relative_error_analysis.py` | Analyse d'erreurs V6 |
| `src/mais/meta/nested_stacking.py` | Stacking V7-03 |
| `src/mais/research/cbot_target_lab_v7.py` | Cibles CBOT V7-04 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/cross_market_v7.py` | Créer — test bidirectionnel |
| `artefacts/v7/cross_market_study.json` | Créer — résultats |
| `docs/CROSS_MARKET_STUDY.md` | Créer — rapport |
| `tests/test_cross_market.py` | Créer |

### Implémentation

```python
def run_cross_market_experiment(X_all, y_ema, y_cbot, ema_features, cbot_features, cv):
    """Test bidirectionnel : EMA → CBOT et CBOT → EMA."""
    results = {}

    # Modèle CBOT baseline (sans features EMA)
    auc_cbot_base = run_oof(X_all[cbot_features], y_cbot, lgbm(), cv)

    # Modèle CBOT avec features EMA ajoutées
    auc_cbot_with_ema = run_oof(X_all[cbot_features + ema_features], y_cbot, lgbm(), cv)

    # Modèle EMA baseline (sans features CBOT)
    auc_ema_base = run_oof(X_all[ema_features], y_ema, lgbm(), cv)

    # Modèle EMA avec features CBOT ajoutées
    auc_ema_with_cbot = run_oof(X_all[ema_features + cbot_features], y_ema, lgbm(), cv)

    delta_ema_adds = auc_cbot_with_ema - auc_cbot_base
    delta_cbot_adds = auc_ema_with_cbot - auc_ema_base

    verdict = "NONE"
    if delta_ema_adds > 0.02 and delta_cbot_adds > 0.02:
        verdict = "BIDIRECTIONAL"
    elif delta_ema_adds > 0.02:
        verdict = "EMA_ADDS_TO_CBOT"
    elif delta_cbot_adds > 0.02:
        verdict = "CBOT_ADDS_TO_EMA"

    results = {
        "auc_cbot_base": auc_cbot_base, "auc_cbot_with_ema": auc_cbot_with_ema,
        "delta_ema_adds_to_cbot": delta_ema_adds,
        "auc_ema_base": auc_ema_base, "auc_ema_with_cbot": auc_ema_with_cbot,
        "delta_cbot_adds_to_ema": delta_cbot_adds,
        "verdict": verdict
    }
    return results
```

### Livrables obligatoires

- `src/mais/research/cross_market_v7.py`
- `artefacts/v7/cross_market_study.json`
- `docs/CROSS_MARKET_STUDY.md`

### Critères de succès

```
Test bidirectionnel EMA↔CBOT complet : OK
Delta AUC documenté pour chaque direction : OK
Verdict parmi BIDIRECTIONAL/EMA_ADDS_TO_CBOT/CBOT_ADDS_TO_EMA/NONE : OK
```

---

### V7-20 — Modèles espace-état dynamiques (Kalman)

**Priorité** : BASSE
**Type** : complexe
**Statut** : WATCHLIST
**Phase** : 3
**Dépendances** : V7-03, V7-08
**experiment_type** : MODEL_VALIDATION

### Contexte

Ticket WATCHLIST. Un filtre de Kalman permettrait d'estimer dynamiquement les coefficients de la relation EMA/CBOT, capturant les changements structurels progressifs. Exécuter uniquement si V7-03 montre une instabilité temporelle significative des coefficients du meta-modèle.

### Objectifs mesurables

- Filtre de Kalman sur la relation premium ~ CBOT + basis
- Coefficients time-varying documentés sur 2010-2023
- AUC modèle Kalman vs modèle statique documenté

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/kalman_premium.py` | Créer — filtre Kalman |
| `artefacts/v7/kalman_model.json` | Créer — résultats |

### Implémentation

```python
def kalman_tv_regression(y: pd.Series, X: pd.DataFrame) -> pd.DataFrame:
    """Régression à coefficients time-varying via filtre Kalman."""
    try:
        import statsmodels.api as sm
        from statsmodels.tsa.statespace.kalman_filter import KalmanFilter
    except ImportError:
        return pd.DataFrame()
    # Implémentation via DLM (Dynamic Linear Model)
    # y_t = X_t * beta_t + epsilon_t
    # beta_t = beta_{t-1} + eta_t
    n_params = X.shape[1]
    # ... implémentation DLM
    pass
```

---

### V7-27 — Modèles multi-facteurs conditionnels

**Priorité** : MOYENNE
**Type** : critique
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-06, V7-08
**experiment_type** : PREDICTIVE_OOF

### Contexte

Les drivers du premium changent selon les régimes : en HIGH_STABLE, les stocks EU dominent ; en ROLL_DISTORTED, tout signal fondamental est bruité. Ce ticket entraîne un modèle distinct par régime de basis et compare leur performance vs un modèle global unique.

### Objectifs mesurables

- 6 modèles régime-spécifiques entraînés en OOF
- AUC par régime vs modèle global documenté
- Régimes où le modèle conditionnel améliore significativement l'AUC identifiés
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/basis_regimes_v7.py` | Régimes V7-08 |
| `src/mais/meta/nested_stacking.py` | Framework stacking |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/conditional_models_v7.py` | Créer — 6 modèles conditionnels |
| `artefacts/v7/conditional_models.json` | Créer — résultats |
| `docs/CONDITIONAL_MODELS.md` | Créer — rapport |
| `tests/test_conditional_models.py` | Créer |

### Implémentation

```python
def train_regime_conditional_models(
    X: pd.DataFrame,
    y: pd.Series,
    regimes: pd.Series,
    cv_splits,
) -> dict:
    """Modèle distinct par régime de basis, entraîné en OOF."""
    REGIME_NAMES = ["NORMAL", "HIGH_STABLE", "HIGH_COMPRESSING",
                    "HIGH_EXPANDING", "LOW_BASIS", "ROLL_DISTORTED"]
    results = {}

    for regime in REGIME_NAMES:
        regime_mask = regimes == regime
        X_r = X[regime_mask]
        y_r = y[regime_mask]
        if len(y_r) < 30:
            results[regime] = {"verdict": "TOO_FEW_SAMPLES", "n": len(y_r)}
            continue

        # OOF conditionnel (ne tester que les dates du régime)
        oof_preds = np.full(len(y_r), np.nan)
        for train_idx, test_idx in cv_splits:
            train_mask_r = regime_mask.iloc[train_idx]
            clf = lgbm()
            X_tr_r = X.iloc[train_idx][train_mask_r.values]
            y_tr_r = y.iloc[train_idx][train_mask_r.values]
            if len(y_tr_r) < 10:
                continue
            clf.fit(X_tr_r, y_tr_r)
            test_mask_r = regime_mask.iloc[test_idx]
            if test_mask_r.sum() > 0:
                preds = clf.predict_proba(X.iloc[test_idx][test_mask_r.values])[:, 1]
                oof_preds[regime_mask.iloc[test_idx].values] = preds

        valid_mask = ~np.isnan(oof_preds)
        if valid_mask.sum() > 20:
            auc = roc_auc_score(y_r[valid_mask], oof_preds[valid_mask])
            results[regime] = {"auc": auc, "n": int(valid_mask.sum())}

    return results
```

### Livrables obligatoires

- `src/mais/research/conditional_models_v7.py`
- `artefacts/v7/conditional_models.json`
- `docs/CONDITIONAL_MODELS.md`

---

### V7-34 — Modèle de scénario de marché

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-08, V7-32
**experiment_type** : MODEL_VALIDATION

### Contexte

Ticket de modélisation narrative : étant donné un scénario économique (sécheresse EU, conflit Ukraine, récession demande), quel est l'impact probable sur le premium EMA/CBOT ? Ce ticket construit un framework de scénarios structurés et quantifie chaque scénario via le modèle V7.

### Objectifs mesurables

- 5 scénarios définis avec paramètres économiques
- Impact estimé (distribution premium) par scénario
- Validation backtestée sur crises historiques (2012, 2020, 2022)

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/scenario_model.py` | Créer — 5 scénarios |
| `artefacts/v7/scenario_analysis.json` | Créer — résultats |

### Implémentation

```python
SCENARIOS = {
    "eu_drought": {"mars_yield_z": -2.0, "eu_weather_stress": 2.5, "fob_rouen_premium": 20},
    "ukraine_export_disruption": {"ukraine_exports_yoy_pct": -0.50, "fob_ukraine_premium": -30},
    "demand_recession": {"cot_net_position_z": -2.0, "corn_soy_ratio": 0.20},
    "cbot_bull_market": {"cbot_ret_20d": 0.15, "usd_strength_z": -1.5},
    "basis_normalization": {"basis_z": -1.5, "roll_risk_score": 0.2},
}

def simulate_scenario(model, baseline_X: pd.DataFrame, scenario: dict) -> dict:
    X_scenario = baseline_X.copy()
    for feature, value in scenario.items():
        if feature in X_scenario.columns:
            X_scenario[feature] = value
    proba_base = model.predict_proba(baseline_X)[:, 1].mean()
    proba_scenario = model.predict_proba(X_scenario)[:, 1].mean()
    return {"base": proba_base, "scenario": proba_scenario, "delta": proba_scenario - proba_base}
```

---

### V7-35 — Distributional forecasting du premium

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-03
**experiment_type** : PREDICTIVE_OOF

### Contexte

Un modèle point ne dit pas si le premium va monter de 2 EUR/t ou 20 EUR/t. Ce ticket entraîne un modèle de distribution complète (quantile regression, conformal prediction) qui donne P5, P25, P50, P75, P95 du premium forward.

### Objectifs mesurables

- Intervalles de prédiction calibrés : couverture empirique ≈ couverture nominale (± 5%)
- Bandes PI documentées pour H40, H90
- Coverage test sur set OOF

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/meta/cqr.py` | CQR calibré V6 |
| `src/mais/meta/conformal.py` | Conformal prediction |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/distributional_forecast.py` | Créer — quantile + CQR |
| `artefacts/v7/distributional_forecast.json` | Créer — résultats calibration |
| `tests/test_distributional_forecast.py` | Créer |

### Implémentation

```python
def train_quantile_forecast(X, y, quantiles, cv_splits):
    """Quantile regression OOF avec CQR calibration."""
    from mais.meta.cqr import walk_forward_cqr
    results = {}
    for q in quantiles:
        oof_q = walk_forward_cqr(X, y, quantile=q, cv_splits=cv_splits)
        coverage = np.mean(y.values <= oof_q)
        results[q] = {"predicted_quantile": float(q), "empirical_coverage": float(coverage)}
    return results
```

### Livrables obligatoires

- `src/mais/research/distributional_forecast.py`
- `artefacts/v7/distributional_forecast.json` — calibration par quantile

---

### V7-37 — Analyse de stabilité des features

**Priorité** : HAUTE
**Type** : complexe
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-03
**experiment_type** : MODEL_VALIDATION

### Contexte

Un signal avec une importance feature stable dans le temps est plus fiable qu'un signal qui n'était important que pendant 2 ans. Ce ticket mesure la stabilité temporelle de chaque feature via la variance de son importance SHAP sur des fenêtres glissantes de 2 ans.

### Objectifs mesurables

- Importance SHAP calculée sur fenêtres glissantes 2 ans (stride 6 mois)
- Coefficient de variation de l'importance pour chaque feature
- Top 20 features stables vs top 20 features instables identifiées
- Tests : `ruff check` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/meta/nested_stacking.py` | Modèle V7-03 |
| `src/mais/research/driver_cartography.py` | Cartographie V7-33 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/feature_stability.py` | Créer — stabilité SHAP rolling |
| `artefacts/v7/feature_stability.json` | Créer — résultats |
| `docs/FEATURE_STABILITY.md` | Créer — rapport |

### Implémentation

```python
def compute_rolling_feature_stability(
    X: pd.DataFrame,
    y: pd.Series,
    window_years: int = 2,
    stride_months: int = 6,
) -> pd.DataFrame:
    """Stabilité des features : variance SHAP sur fenêtres glissantes."""
    try:
        import shap
        from lightgbm import LGBMClassifier
    except ImportError:
        return pd.DataFrame()

    window = pd.DateOffset(years=window_years)
    stride = pd.DateOffset(months=stride_months)
    start = X.index[0]
    end = X.index[-1]

    shap_by_window = []
    current = start
    while current + window <= end:
        mask = (X.index >= current) & (X.index < current + window)
        X_w, y_w = X[mask].dropna(), y[mask].dropna()
        if len(y_w) < 50:
            current += stride
            continue
        clf = LGBMClassifier(n_estimators=100, seed=42)
        clf.fit(X_w.loc[y_w.index], y_w)
        explainer = shap.TreeExplainer(clf)
        shap_vals = np.abs(explainer.shap_values(X_w.loc[y_w.index])[1]).mean(axis=0)
        shap_by_window.append({"window_start": current, **dict(zip(X.columns, shap_vals))})
        current += stride

    df_stability = pd.DataFrame(shap_by_window).set_index("window_start")
    stability_metrics = pd.DataFrame({
        "mean_importance": df_stability.mean(),
        "std_importance": df_stability.std(),
        "cv_importance": df_stability.std() / df_stability.mean().clip(1e-6),
    })
    return stability_metrics.sort_values("cv_importance")  # stable = CV faible
```

### Livrables obligatoires

- `src/mais/research/feature_stability.py`
- `artefacts/v7/feature_stability.json` — CV par feature
- `docs/FEATURE_STABILITY.md` — top 20 stables + top 20 instables

---

### V7-38 — Étude du model decay

**Priorité** : HAUTE
**Type** : complexe
**Statut** : DONE
**Phase** : 3
**Dépendances** : V7-03
**experiment_type** : MODEL_VALIDATION

### Contexte

Un modèle entraîné en 2015 peut être performant jusqu'en 2020 puis se dégrader. Ce ticket mesure le decay de performance du meta-modèle V7-03 en fonction du temps écoulé depuis l'entraînement, pour définir la fréquence optimale de re-entraînement.

### Objectifs mesurables

- AUC en fonction de l'âge du modèle (jours depuis train_end) documentée
- Seuil de decay : age à partir duquel AUC descend sous baseline + 0.02
- Recommandation fréquence de re-entraînement documentée

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/model_decay.py` | Créer — analyse decay |
| `artefacts/v7/model_decay.json` | Créer — résultats |
| `docs/MODEL_DECAY.md` | Créer — rapport |

### Implémentation

```python
def analyze_model_decay(
    X: pd.DataFrame,
    y: pd.Series,
    cv_splits,
    model_factory,
) -> pd.DataFrame:
    """AUC en fonction de l'âge du modèle depuis le train_end."""
    decay_results = []
    for train_idx, test_idx in cv_splits:
        train_end = X.index[train_idx[-1]]
        clf = model_factory()
        clf.fit(X.iloc[train_idx], y.iloc[train_idx])
        for i in test_idx:
            age_days = (X.index[i] - train_end).days
            pred = clf.predict_proba(X.iloc[[i]])[:, 1][0]
            decay_results.append({
                "date": X.index[i],
                "age_days": age_days,
                "prediction": pred,
                "true_label": y.iloc[i]
            })

    df = pd.DataFrame(decay_results)
    # AUC par bucket d'âge (0-30j, 30-90j, 90-180j, 180-365j, 365j+)
    df["age_bucket"] = pd.cut(df["age_days"], bins=[0, 30, 90, 180, 365, 9999])
    auc_by_age = df.groupby("age_bucket").apply(
        lambda g: roc_auc_score(g["true_label"], g["prediction"])
        if g["true_label"].nunique() > 1 else np.nan
    )
    return auc_by_age.to_frame("auc_by_model_age")
```

### Livrables obligatoires

- `src/mais/research/model_decay.py`
- `artefacts/v7/model_decay.json` — AUC par âge du modèle
- `docs/MODEL_DECAY.md` — recommandation de fréquence

---

## PHASE 4 — Données supplémentaires

---

### V7-16 — Microstructure et liquidité EMA

**Priorité** : BASSE
**Type** : moyen
**Statut** : DONE
**Phase** : 4
**Dépendances** : V7-01A
**experiment_type** : MODEL_VALIDATION

### Contexte

Le contrat EMA Euronext a une liquidité inférieure au CBOT. Les primes de liquidité (bid-ask spread, volume, open interest) peuvent expliquer une partie du premium et doivent être contrôlées avant toute conclusion sur la prédictibilité. Ce ticket documente les patterns de liquidité EMA.

### Objectifs mesurables

- Séries volume, OI, bid-ask EMA disponibles
- Corrélation liquidité vs spread premium documentée
- Alerte : jours de faible liquidité (volume < P10) identifiés

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/microstructure.py` | Créer — features liquidité |
| `artefacts/v7/microstructure.json` | Créer — résultats |

### Implémentation

```python
def build_microstructure_features(df: pd.DataFrame) -> pd.DataFrame:
    feats = {}
    if "ema_volume" in df.columns:
        feats["ema_volume_z60"] = _expandz(df["ema_volume"])
        feats["ema_low_liquidity"] = (
            df["ema_volume"] < df["ema_volume"].rolling(252).quantile(0.10)
        ).astype(int)
    if "ema_open_interest" in df.columns:
        feats["ema_oi_change_pct"] = df["ema_open_interest"].pct_change(20)
    return pd.DataFrame(feats).shift(1)  # anti-leakage
```

### Livrables obligatoires

- `artefacts/v7/microstructure.json` — patterns de liquidité EMA

---

### V7-22 — Analyse logistique et prix de parité

**Priorité** : BASSE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 4
**Dépendances** : V7-DATA-CAL
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Le premium EMA/CBOT est économiquement borné par le coût de parité d'importation (coût CBOT + fret maritime + coût transport terrestre EU). Quand le premium dépasse ce plafond, une arbitrage import devient rentable. Ce ticket calcule ce plafond théorique et documente les déviations.

### Objectifs mesurables

- Prix de parité import EU calculé quotidiennement (CBOT + fret BDI + handling)
- Déviation EMA vs parité documentée
- Corrélation déviation vs retour futur premium calculée

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/import_parity.py` | Créer — prix parité |
| `artefacts/v7/import_parity.json` | Créer — résultats |

### Implémentation

```python
def compute_import_parity(df: pd.DataFrame) -> pd.Series:
    """Prix de parité import EU = CBOT_EUR + fret + handling."""
    cbot_eur = df["cbot_close"] / df["eurusd"] * 0.0254  # USD/bu → EUR/t
    fret = df.get("bdi_index", pd.Series(25.0, index=df.index)) * 0.5  # proxy EUR/t
    handling = 15.0  # EUR/t fixe
    return (cbot_eur + fret + handling).rename("import_parity_eur_t")
```

---

### V7-23 — Analyse textuelle WASDE et rapports

**Priorité** : BASSE
**Type** : complexe
**Statut** : WAITING_DATA
**Phase** : 4
**Dépendances** : V7-DATA-CAL
**experiment_type** : PREDICTIVE_OOF

### Contexte

Les rapports WASDE contiennent des éléments textuels qualitatifs (commentaires sur les conditions météo, révisions des perspectives d'offre). Le sentiment du texte peut anticiper les révisions quantitatives. Ce ticket teste la valeur d'un sentiment score WASDE NLP pour le premium.

### Objectifs mesurables

- Textes WASDE extraits et structurés pour 2010-2023
- Score sentiment VADER ou FinBERT calculé pour chaque publication
- AUC sentiment → premium_return_h90 documenté

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/wasde_sentiment.py` | Créer — NLP WASDE |
| `artefacts/v7/wasde_sentiment.json` | Créer — résultats |

### Implémentation

```python
def compute_wasde_sentiment(wasde_texts: list[dict]) -> pd.DataFrame:
    """Score sentiment WASDE : VADER ou FinBERT (via try/except)."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        scores = [{"date": w["date"], "sentiment": sia.polarity_scores(w["text"])["compound"]}
                  for w in wasde_texts]
        df = pd.DataFrame(scores).set_index("date")
        df.index = pd.to_datetime(df.index)
        return df.resample("D").ffill().shift(1)  # anti-leakage
    except ImportError:
        return pd.DataFrame()
```

---

### V7-24 — Signaux options et volatilité implicite

**Priorité** : BASSE
**Type** : moyen
**Statut** : WAITING_DATA
**Phase** : 4
**Dépendances** : V7-DATA-CAL
**experiment_type** : PREDICTIVE_OOF

### Contexte

Les options CBOT et EMA encodent les anticipations du marché (IV, skew put/call). La volatilité implicite vs réalisée (variance risk premium) peut indiquer si le marché sur-estime ou sous-estime le risque. Ce ticket teste la valeur prédictive de ces signaux pour le premium.

### Objectifs mesurables

- IV CBOT disponible depuis 2010 (via VOLSURF ou CBOE)
- Variance risk premium = IV - RV calculé quotidiennement
- AUC VRP → premium_return_h90 documenté

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/features/options_signals.py` | Créer — IV + skew |
| `artefacts/v7/options_signals.json` | Créer — résultats |

### Implémentation

```python
def build_options_features(df_options: pd.DataFrame, lag_days: int = 1) -> pd.DataFrame:
    """Features options : IV, skew, VRP."""
    feats = {}
    if "iv_atm_30d" in df_options.columns:
        iv = df_options["iv_atm_30d"].shift(lag_days)
        rv = df_options.get("realized_vol_20d", iv * 0.9).shift(lag_days)
        feats["variance_risk_premium"] = iv ** 2 - rv ** 2
        feats["iv_atm_z60"] = _expandz(iv)
    if "iv_skew_25d" in df_options.columns:
        feats["iv_skew"] = df_options["iv_skew_25d"].shift(lag_days)
    return pd.DataFrame(feats)
```

---

## PHASE 5 — Causalité et interprétabilité

---

### V7-14 — Explicabilité et analyse des erreurs

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : DONE
**Phase** : 5
**Dépendances** : V7-03, V7-06
**experiment_type** : MODEL_VALIDATION

### Contexte

Comprendre POURQUOI le modèle se trompe est aussi important que de mesurer son AUC. Ce ticket analyse systématiquement les erreurs du meta-modèle V7-03 : dans quels régimes, sur quelles features, avec quel niveau de confiance ? L'analyse guide l'amélioration des modèles et renforce la crédibilité du rapport final.

### Objectifs mesurables

- Analyse d'erreurs par régime de basis (V7-08)
- SHAP values des faux positifs vs faux négatifs
- Identification des features les plus associées aux erreurs
- Tests : `ruff check` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/meta/nested_stacking.py` | Meta-modèle V7-03 |
| `src/mais/research/basis_regimes_v7.py` | Régimes V7-08 |
| `src/mais/research/ema_relative_error_analysis.py` | Analyse d'erreurs V6 |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/error_analysis_v7.py` | Créer — analyse systématique |
| `artefacts/v7/error_analysis.json` | Créer — résultats |
| `docs/ERROR_ANALYSIS_V7.md` | Créer — rapport |

### Implémentation

```python
def analyze_model_errors(
    y_true: pd.Series,
    y_pred_proba: pd.Series,
    X: pd.DataFrame,
    regimes: pd.Series,
    threshold: float = 0.5,
) -> dict:
    """Analyse des erreurs : FP, FN par régime et feature."""
    y_pred_class = (y_pred_proba >= threshold).astype(int)
    error_mask = y_true != y_pred_class
    fp_mask = (y_pred_class == 1) & (y_true == 0)
    fn_mask = (y_pred_class == 0) & (y_true == 1)

    errors_by_regime = {}
    for regime in regimes.unique():
        regime_mask = regimes == regime
        errors_in_regime = (error_mask & regime_mask).sum()
        total_in_regime = regime_mask.sum()
        errors_by_regime[regime] = {
            "error_rate": float(errors_in_regime / total_in_regime) if total_in_regime > 0 else None,
            "fp_rate": float((fp_mask & regime_mask).sum() / total_in_regime) if total_in_regime > 0 else None,
            "fn_rate": float((fn_mask & regime_mask).sum() / total_in_regime) if total_in_regime > 0 else None,
        }

    # SHAP analysis des erreurs
    try:
        import shap
        from lightgbm import LGBMClassifier
        clf = LGBMClassifier(n_estimators=100, seed=42)
        is_error = error_mask.astype(int)
        clf.fit(X, is_error)
        explainer = shap.TreeExplainer(clf)
        shap_error = np.abs(explainer.shap_values(X)[1]).mean(axis=0)
        shap_error_importance = dict(zip(X.columns, shap_error))
    except ImportError:
        shap_error_importance = {}

    return {
        "error_rate_global": float(error_mask.mean()),
        "errors_by_regime": errors_by_regime,
        "top_error_features": sorted(shap_error_importance.items(), key=lambda x: -x[1])[:10],
    }
```

### Livrables obligatoires

- `src/mais/research/error_analysis_v7.py`
- `artefacts/v7/error_analysis.json`
- `docs/ERROR_ANALYSIS_V7.md`

---

### V7-18 — Causalité formelle PCMCI

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : DONE
**Phase** : 5
**Dépendances** : V7-00
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Ce ticket applique l'algorithme PCMCI (Peter & Clark Momentary Conditional Independence) pour inférer formellement les relations de causalité temporelle entre les variables clés : CBOT, EMA, basis, COT, WASDE, météo EU. PCMCI est plus rigoureux que la causalité de Granger sur séries multivariées.

### Objectifs mesurables

- Graphe causal PCMCI sur 8 variables × 5 lags
- Liens causaux significatifs identifiés (seuil α = 0.05)
- Rapport sur la direction des causalités CBOT → EMA vs EMA → CBOT
- Tests : `ruff check` PASS

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/pcmci_causality.py` | Créer — causalité PCMCI |
| `artefacts/v7/pcmci_causality.json` | Créer — résultats |
| `docs/PCMCI_CAUSALITY.md` | Créer — rapport |

### Implémentation

```python
def run_pcmci_analysis(
    df: pd.DataFrame,
    variables: list[str],
    max_lag: int = 5,
    alpha: float = 0.05,
) -> dict:
    """Causalité PCMCI : graphe de causalité temporelle."""
    try:
        from tigramite import data_processing as pp
        from tigramite.pcmci import PCMCI
        from tigramite.independence_tests.parcorr import ParCorr
    except ImportError:
        return {"error": "tigramite_not_installed", "install": "pip install tigramite"}

    data_array = df[variables].dropna().values
    dataframe = pp.DataFrame(data_array, var_names=variables)
    pcmci = PCMCI(dataframe=dataframe, cond_ind_test=ParCorr())
    results = pcmci.run_pcmci(tau_max=max_lag, alpha_level=alpha)

    significant_links = {}
    for i, target in enumerate(variables):
        links = []
        for j, source in enumerate(variables):
            for lag in range(1, max_lag + 1):
                pval = results["p_matrix"][i, j, lag]
                if pval < alpha:
                    links.append({"source": source, "lag": lag, "p_value": float(pval)})
        significant_links[target] = links

    return {
        "significant_links": significant_links,
        "n_obs": len(data_array),
        "variables": variables,
        "max_lag": max_lag,
    }
```

### Livrables obligatoires

- `src/mais/research/pcmci_causality.py`
- `artefacts/v7/pcmci_causality.json`
- `docs/PCMCI_CAUSALITY.md`

---

### V7-21 — Analyse facteur EUR/USD et régimes de change

**Priorité** : BASSE
**Type** : moyen
**Statut** : DONE
**Phase** : 5
**Dépendances** : V7-00
**experiment_type** : PREDICTIVE_OOF

### Contexte

Le premium EMA/CBOT est exprimé en EUR/t et le CBOT en USD/bu. Le taux EUR/USD impacte directement la conversion. Ce ticket décompose la part de variation du premium attribuable au FX vs à la dynamique économique réelle, et teste si les régimes de change (EUR fort vs faible) modifient la prédictibilité.

### Objectifs mesurables

- Corrélation EUR/USD avec le premium documentée par régime de change
- Modèle "FX-neutralisé" vs modèle complet comparés
- AUC premium FX-neutralisé documenté

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/fx_analysis.py` | Créer — analyse FX |
| `artefacts/v7/fx_analysis.json` | Créer — résultats |

### Implémentation

```python
def build_fx_neutral_premium(df: pd.DataFrame) -> pd.Series:
    """Premium neutralisé FX : utiliser CBOT en EUR à taux fixe (base 2015)."""
    eurusd_base = df.loc["2015", "eurusd"].mean()  # taux de référence
    cbot_eur_fixed = df["cbot_close"] / eurusd_base / 36.744  # USD/bu → EUR/t à taux fixe
    premium_fx_neutral = df["ema_close"] - cbot_eur_fixed
    return premium_fx_neutral.rename("premium_fx_neutral")

def test_fx_regime_impact(df: pd.DataFrame, premium: pd.Series, cv_splits) -> dict:
    eurusd_z = _expandz(df["eurusd"])
    fx_strong_eur = eurusd_z > 1.0
    fx_weak_eur = eurusd_z < -1.0
    results = {}
    for regime, mask in [("strong_eur", fx_strong_eur), ("weak_eur", fx_weak_eur), ("neutral", ~fx_strong_eur & ~fx_weak_eur)]:
        if mask.sum() > 30:
            corr = df.loc[mask, "eurusd"].corr(premium.loc[mask])
            results[regime] = {"n": int(mask.sum()), "corr_fx_premium": float(corr)}
    return results
```

### Livrables obligatoires

- `src/mais/research/fx_analysis.py`
- `artefacts/v7/fx_analysis.json` — corrélation FX/premium par régime

---

### V7-36 — Graphe de causalité économique

**Priorité** : MOYENNE
**Type** : complexe
**Statut** : DONE
**Phase** : 5
**Dépendances** : V7-18
**experiment_type** : DESCRIPTIVE_ECONOMIC

### Contexte

Ticket WATCHLIST. Ce ticket synthétise les résultats PCMCI (V7-18), Granger (rejeté en OOF, non-applicable), et économétriques pour construire un graphe de causalité complet du système maïs CBOT/EMA. Exécuter uniquement si V7-18 produit des résultats riches et interprétables.

### Objectifs mesurables

- Graphe de causalité avec nœuds et arêtes orientées
- Document stratégique : quels sont les antécédents causaux du premium EMA ?

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/causality_graph.py` | Créer — graphe synthèse |
| `artefacts/v7/causality_graph.json` | Créer — graphe JSON |
| `docs/CAUSALITY_GRAPH.md` | Créer — rapport |

### Implémentation

```python
def build_causality_graph(pcmci_results: dict, econ_priors: dict) -> dict:
    """Synthèse des liens causaux en graphe NetworkX-compatible."""
    nodes = list(set([link["source"] for links in pcmci_results.values() for link in links]
                     + list(pcmci_results.keys())))
    edges = []
    for target, links in pcmci_results.items():
        for link in links:
            edges.append({
                "from": link["source"], "to": target,
                "lag": link["lag"], "p_value": link["p_value"],
                "strength": 1 - link["p_value"]
            })
    return {"nodes": nodes, "edges": edges, "source": "PCMCI"}
```

---

### V7-40 — Étude des unknown unknowns

**Priorité** : BASSE
**Type** : moyen
**Statut** : WATCHLIST
**Phase** : 5
**Dépendances** : V7-03
**experiment_type** : MODEL_VALIDATION

### Contexte

Ticket WATCHLIST. Ce ticket cherche les facteurs de risque NON modélisés qui ont historiquement causé de grandes erreurs de prédiction. Méthode : clustering des résidus d'erreur, recherche de features externes corrélées avec les clusters d'erreurs, documentation des "angles morts" du modèle.

### Objectifs mesurables

- Clusters d'erreurs identifiés par K-means (k=3-5)
- Features externes corrélées avec chaque cluster d'erreurs
- Rapport documentant les angles morts du modèle

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/unknown_unknowns.py` | Créer — clustering erreurs |
| `artefacts/v7/unknown_unknowns.json` | Créer — résultats |

### Implémentation

```python
def find_unknown_unknowns(
    y_true: pd.Series,
    y_pred: pd.Series,
    X: pd.DataFrame,
) -> dict:
    """Clustering des erreurs pour identifier les angles morts."""
    from sklearn.cluster import KMeans
    residuals = y_true - y_pred
    X_error = X.assign(residual=residuals.values).dropna()

    for k in range(3, 6):
        kmeans = KMeans(n_clusters=k, random_state=42)
        X_error[f"cluster_{k}"] = kmeans.fit_predict(X_error)
        for c in range(k):
            mask = X_error[f"cluster_{k}"] == c
            cluster_feats = X_error[mask].mean()
            print(f"Cluster {c} : {cluster_feats.nlargest(5)}")

    return {"n_clusters_tested": [3, 4, 5], "method": "kmeans_residuals"}
```

---

## PHASE 6 — Livrables finaux

---

### V7-13 — Backtests recherche avancés

**Priorité** : FINALE
**Type** : critique
**Statut** : DONE
**Phase** : 6
**Dépendances** : V7-03, V7-06, V7-07, V7-08
**experiment_type** : BACKTEST_RESEARCH

### Contexte

Ce ticket produit les backtests de recherche finaux, en appliquant le signal V7 (meta-modèle + experts saisonniers + roll-veto + qualité_data) sur la période 2010-2023. Ces backtests sont STRICTEMENT de recherche : ils ne constituent pas une preuve de performance trading réelle. Le verdict est toujours RESEARCH_ONLY_NOT_TRADING.

### Objectifs mesurables

- Backtests sur 5 politiques de sélection (top10, top20, top40, seasonal_expert, full)
- Métriques : PnL EUR/t, Profit Factor, Max Drawdown, Sharpe, n_trades
- Holdout 2024 INTERDIT (gelé par V7-29 jusqu'à V7-28)
- Verdict RESEARCH_ONLY_NOT_TRADING obligatoire
- Tests : `ruff check` PASS, `pytest tests/ -x -q` PASS

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/research/roll_season_backtest_v6.py` | Backtest V6 |
| `src/mais/meta/nested_stacking.py` | Meta-modèle V7-03 |
| `src/mais/research/seasonal_experts_v7.py` | Experts V7-06 |
| `src/mais/features/roll_risk.py` | Roll veto V7-07 |
| `artefacts/v7/holdout_lock.json` | Vérifier used=False |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/research/backtests_v7.py` | Créer — backtests recherche |
| `artefacts/v7/backtests_v7.json` | Créer — résultats |
| `docs/BACKTESTS_V7.md` | Créer — rapport |
| `tests/test_backtests_v7.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`, données 2024 (holdout gelé)

### Implémentation

**Étape 1 — Vérifier le holdout gelé**
```python
with open("artefacts/v7/holdout_lock.json") as f:
    holdout = json.load(f)
assert not holdout["used"], "HOLDOUT 2024 DÉJÀ UTILISÉ — backtest impossible"
BACKTEST_END = "2023-12-31"  # Jamais utiliser 2024
```

**Étape 2 — Politique de sélection multi-couche**
```python
def select_trades(
    df_signals: pd.DataFrame,
    confidence_threshold: float,
    seasonal_policy: callable | None,
    roll_veto_threshold: float = 0.7,
    data_quality_threshold: float = 0.6,
) -> pd.DataFrame:
    """Sélection des entrées : confiance + saisonnier + roll_veto + qualité_data."""
    selected = df_signals.copy()

    # Filtre 1 : Confiance du meta-modèle
    selected = selected[selected["meta_proba"] >= confidence_threshold]

    # Filtre 2 : Politique saisonnière (si définie)
    if seasonal_policy is not None:
        mask = selected.index.to_series().apply(seasonal_policy)
        selected = selected[mask]

    # Veto 3 : Roll risk
    selected = selected[selected["roll_risk_score"] <= roll_veto_threshold]

    # Veto 4 : Qualité des données
    selected = selected[selected["data_quality_score"] >= data_quality_threshold]

    return selected
```

**Étape 3 — Calcul des métriques backtestées**
```python
def compute_backtest_metrics(
    selected: pd.DataFrame,
    forward_return_col: str = "forward_return_h90",
) -> dict:
    """Métriques de backtest recherche (RESEARCH_ONLY_NOT_TRADING)."""
    returns = selected[forward_return_col].dropna()
    if len(returns) == 0:
        return {"trades": 0, "verdict": "NO_SIGNAL", "research_only": True}

    pnl = returns.sum()
    winners = (returns > 0).sum()
    win_rate = winners / len(returns)
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns <= 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Drawdown
    cumulative = returns.cumsum()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max)
    max_drawdown = drawdown.min()

    return {
        "trades": len(returns),
        "pnl_eur_t": float(pnl),
        "win_rate": float(win_rate),
        "profit_factor": float(profit_factor),
        "max_drawdown_eur_t": float(max_drawdown),
        "sharpe_approx": float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else None,
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
        "research_only": True,
        "caveat": "Ces résultats sont de recherche uniquement. Ils ne constituent pas une preuve de performance trading réelle."
    }
```

**Étape 4 — Comparer les 5 politiques**
```python
POLICIES = {
    "top10_full": {"confidence": 0.80, "seasonal": None},
    "top20_seasonal": {"confidence": 0.70, "seasonal": monthly_expert},
    "top40_seasonal": {"confidence": 0.60, "seasonal": monthly_expert},
    "seasonal_expert_strict": {"confidence": 0.75, "seasonal": crop_year_expert},
    "full_signal": {"confidence": 0.50, "seasonal": None},
}
backtest_results = {}
for policy_name, params in POLICIES.items():
    selected = select_trades(df_signals, **params)
    backtest_results[policy_name] = compute_backtest_metrics(selected)
```

### Livrables obligatoires

- `src/mais/research/backtests_v7.py` — 5 politiques avec veto complet
- `artefacts/v7/backtests_v7.json` — résultats avec verdict RESEARCH_ONLY
- `docs/BACKTESTS_V7.md` — rapport avec caveat complet
- Holdout still `used=False` après ce ticket

### Critères de succès

```
Verdict = RESEARCH_ONLY_NOT_TRADING sur tous les backtests : OK
Holdout 2024 non utilisé (used=False) : OK
Données 2024 absentes des backtests : OK
5 politiques comparées : OK
```

---

### V7-15 — Rapport final V7

**Priorité** : FINALE
**Type** : complexe
**Statut** : DONE
**Phase** : 6
**Dépendances** : V7-13, V7-28, V7-14, V7-29
**experiment_type** : —

### Contexte

Le rapport final V7 documente l'ensemble du programme de recherche. Il doit respecter le principe cardinal : aucun claim non implémenté. Chaque chiffre du rapport doit être traceable à un artefact JSON. La table "État réel d'implémentation" ✅/❌/⚠️ est maintenue à jour.

### Objectifs mesurables

- Rapport `docs/PROFESSIONAL_STUDY_REPORT_V7.md` complet
- Table "État réel d'implémentation" exhaustive
- Tous les chiffres tracés vers un artefact JSON
- Caveats proxy EMA présents
- Verdict final documenté

### Fichiers à lire

Tous les `artefacts/v7/*.json` et `docs/FINAL_CORN_STUDY_V6.md`

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `docs/PROFESSIONAL_STUDY_REPORT_V7.md` | Créer — rapport final |
| `docs/FINAL_CORN_STUDY_V7.md` | Créer — résumé exécutif V7 |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Structure du rapport

```markdown
# PROFESSIONAL STUDY REPORT V7 — Corn CBOT/EMA

## 1. Executive Summary
## 2. Methodology
### 2.1 Data sources
### 2.2 Anti-leakage protocol (shift(1), OOF, embargo)
### 2.3 CV protocol (purged kfold, embargo H)
### 2.4 Statistical validation (BH correction, red team)
## 3. Main Results
### 3.1 Cross-target meta-model V2
### 3.2 Seasonal expert models
### 3.3 Basis regimes
### 3.4 Fair value model
### 3.5 Cross-market CBOT/EMA
## 4. Research Backtests (RESEARCH ONLY)
## 5. Indicator Architecture (V7-28)
## 6. Implementation Status Table
## 7. Caveats and Limitations
## 8. Recommended Next Research
```

### Livrables obligatoires

- `docs/PROFESSIONAL_STUDY_REPORT_V7.md`
- `docs/FINAL_CORN_STUDY_V7.md`

### Critères de succès

```
Aucun claim non tracé vers un artefact JSON : OK
Table état implémentation complète : OK
Caveats proxy EMA présents : OK
Verdict final documenté : OK
```

---

### V7-15B — Notebooks narratifs finaux

**Priorité** : FINALE
**Type** : complexe
**Statut** : BLOCKED
**Phase** : 6
**Dépendances** : V7-15, V7-13
**experiment_type** : —

### Contexte

Les notebooks narratifs permettent une lecture guidée des résultats V7. Ils sont distincts du rapport technique (V7-15) : ils racontent l'histoire du marché maïs CBOT/EMA avec des visualisations et des narratifs économiques. Ces notebooks sont générés uniquement en fin de projet, quand tous les artefacts JSON sont disponibles.

**Important** : Les notebooks sont en lecture-seule depuis le code Python. Selon les règles CLAUDE.md (`notebooks/` interdit en écriture automatique), ces notebooks sont créés manuellement ou via une commande explicite de l'utilisateur.

### Objectifs mesurables

- 9 notebooks narratifs créés dans `notebooks/`
- Chaque notebook charge des artefacts JSON existants (jamais re-calcule)
- Table des matières documentée

### Fichiers à créer (manuellement)

```
notebooks/
  01_cbot_global_market.ipynb       — CBOT comme moteur mondial
  02_ema_european_premium.ipynb     — EMA et la prime européenne
  03_basis_regimes.ipynb            — Régimes de basis
  04_seasonal_patterns.ipynb        — Patterns saisonniers
  05_meta_model_v2.ipynb            — Cross-target stacking
  06_eu_data_signals.ipynb          — Données européennes
  07_causality_and_drivers.ipynb    — Causalité et drivers
  08_backtests_research.ipynb       — Backtests (RESEARCH ONLY)
  09_final_synthesis.ipynb          — Synthèse finale
```

### Structure type d'un notebook

```python
# 01_cbot_global_market.ipynb — Contenu type
import json, pandas as pd, matplotlib.pyplot as plt

# Charger uniquement les artefacts pré-calculés
with open("../artefacts/v7/cbot_target_lab.json") as f:
    results = json.load(f)

# Visualiser
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
# ... visualisations à partir des artefacts JSON
```

### Livrables obligatoires

- 9 notebooks avec structure documentée
- Chaque notebook : uniquement lecture d'artefacts JSON existants
- Aucun calcul de modèle dans les notebooks (anti-règle AGENTS)

### Critères de succès

```
9 notebooks créés : OK
Aucun calcul de modèle in-notebook : OK
Tous les artefacts JSON référencés existent : OK
```

---

### V7-28 — Architecture finale de l'indicateur

**Priorité** : FINALE
**Type** : critique
**Statut** : DONE
**Phase** : 6
**Dépendances** : V7-13, V7-03, V7-06, V7-07, V7-08, V7-12, V7-39
**experiment_type** : INDICATOR_CANDIDATE

### Contexte

Ce ticket intègre tous les signaux validés en une architecture d'indicateur à 5 couches. C'est le seul ticket autorisé à utiliser le holdout 2024 (une seule utilisation). L'indicateur final est CANDIDATE_ONLY : il ne constitue pas un indicateur de trading validé sans re-validation sur données officielles EMA et sur out-of-sample réel.

**Le holdout 2024 ne peut être utilisé qu'une seule fois dans ce ticket.**

### Objectifs mesurables

- Architecture 5 couches documentée et implémentée
- Évaluation sur holdout 2024 (une seule fois)
- AUC holdout documentée et comparée à l'AUC OOF
- Verdict INDICATOR_CANDIDATE avec toutes les conditions

### Fichiers à lire

| Fichier | Raison |
|---|---|
| `src/mais/meta/nested_stacking.py` | Meta-modèle V7-03 |
| `src/mais/research/seasonal_experts_v7.py` | Experts V7-06 |
| `src/mais/features/roll_risk.py` | Roll veto V7-07 |
| `src/mais/research/basis_regimes_v7.py` | Régimes V7-08 |
| `src/mais/meta/p_correct.py` | P(correct) V7-12 |
| `src/mais/features/data_quality.py` | Score qualité V7-39 |
| `artefacts/v7/holdout_lock.json` | VÉRIFIER used=False AVANT tout |

### Fichiers à créer/modifier

| Fichier | Modification |
|---|---|
| `src/mais/indicator/corn_indicator_v7.py` | Créer — indicateur 5 couches |
| `artefacts/v7/corn_indicator_v7.json` | Créer — résultats holdout |
| `artefacts/v7/holdout_lock.json` | Modifier — used=True après utilisation |
| `docs/CORN_INDICATOR_V7.md` | Créer — documentation indicateur |
| `tests/test_corn_indicator.py` | Créer |

### Fichiers interdits

`notebooks/`, `data/raw/`

### Implémentation

**Architecture 5 couches**
```python
class CornIndicatorV7:
    """Indicateur 5 couches : CANDIDATE_ONLY — non validé pour trading."""

    # Couche 1 : Signal CBOT (contexte marché mondial)
    # Couche 2 : Signal Premium EMA/CBOT (signal principal)
    # Couche 3 : Filtres/Veto (roll_risk, data_quality, régime)
    # Couche 4 : Signal final avec confiance P(correct)
    # Couche 5 : Explicabilité (top 3 features SHAP)

    def __init__(self, meta_model, seasonal_expert, roll_risk_fn, regime_fn, p_correct_fn, quality_fn):
        self.meta_model = meta_model
        self.seasonal_expert = seasonal_expert
        self.roll_risk_fn = roll_risk_fn
        self.regime_fn = regime_fn
        self.p_correct_fn = p_correct_fn
        self.quality_fn = quality_fn

    def predict(self, df: pd.DataFrame, date: pd.Timestamp) -> dict:
        row = df.loc[[date]]

        # Couche 1 : CBOT context
        cbot_signal = self.meta_model.predict_cbot(row)

        # Couche 2 : Premium signal
        premium_signal = self.meta_model.predict_premium(row)

        # Couche 3 : Veto checks
        roll_risk = self.roll_risk_fn(row)["roll_risk_score"].iloc[0]
        data_quality = self.quality_fn(row)["data_quality_score"].iloc[0]
        regime = self.regime_fn(row)["regime"].iloc[0]
        seasonal_ok = self.seasonal_expert(date)

        vetoed = roll_risk > 0.7 or data_quality < 0.6 or not seasonal_ok
        veto_reason = []
        if roll_risk > 0.7: veto_reason.append(f"ROLL_RISK={roll_risk:.2f}")
        if data_quality < 0.6: veto_reason.append(f"DATA_QUALITY={data_quality:.2f}")
        if not seasonal_ok: veto_reason.append("SEASONAL_VETO")

        # Couche 4 : Confiance
        p_correct = self.p_correct_fn(row, premium_signal)

        # Signal final
        final_signal = premium_signal if not vetoed else 0.5
        confidence = p_correct if not vetoed else 0.0

        return {
            "date": date.isoformat(),
            "cbot_context": float(cbot_signal),
            "premium_signal": float(premium_signal),
            "roll_risk": float(roll_risk),
            "data_quality": float(data_quality),
            "regime": regime,
            "seasonal_ok": seasonal_ok,
            "vetoed": vetoed,
            "veto_reasons": veto_reason,
            "confidence_p_correct": float(confidence),
            "final_signal": float(final_signal),
            "indicator_verdict": "SIGNAL" if final_signal > 0.65 and not vetoed else "NO_SIGNAL",
            "caveat": "CANDIDATE_ONLY — non validé pour trading réel",
        }
```

**Utilisation du holdout 2024**
```python
# ÉTAPE CRITIQUE : Vérifier le verrou holdout
with open("artefacts/v7/holdout_lock.json") as f:
    lock = json.load(f)
assert not lock["used"], "HOLDOUT DÉJÀ UTILISÉ — ARRÊT"

# Évaluation sur holdout 2024 (une seule fois)
HOLDOUT_START, HOLDOUT_END = "2024-01-01", "2024-12-31"
df_holdout = df[(df.index >= HOLDOUT_START) & (df.index <= HOLDOUT_END)]
y_holdout = y_true[(y_true.index >= HOLDOUT_START) & (y_true.index <= HOLDOUT_END)]

# Prédictions indicateur sur holdout
holdout_predictions = [indicator.predict(df_holdout, d) for d in df_holdout.index]
holdout_signals = pd.Series(
    [p["final_signal"] for p in holdout_predictions],
    index=df_holdout.index
)
auc_holdout = roc_auc_score(y_holdout, holdout_signals.loc[y_holdout.index])

# MARQUER LE HOLDOUT COMME UTILISÉ
lock["used"] = True
lock["used_by"] = "V7-28"
lock["used_date"] = datetime.utcnow().isoformat()
lock["auc_holdout"] = float(auc_holdout)
with open("artefacts/v7/holdout_lock.json", "w") as f:
    json.dump(lock, f, indent=2)
```

### Livrables obligatoires

- `src/mais/indicator/corn_indicator_v7.py` — architecture 5 couches
- `artefacts/v7/corn_indicator_v7.json` — AUC holdout + verdicts
- `artefacts/v7/holdout_lock.json` — `used=True` après exécution
- `docs/CORN_INDICATOR_V7.md` — documentation complète
- `tests/test_corn_indicator.py`

### Critères de succès

```
Holdout used=False avant exécution : VÉRIFIÉ
Holdout used=True après exécution : OK
AUC holdout documentée : OK
Architecture 5 couches présente : OK
Verdict = INDICATOR_CANDIDATE (pas PRODUCTION_READY) : OK
Caveat proxy EMA présent : OK
```

---

## RÉSUMÉ FINAL

**Statistiques du programme V7**

| Phase | Tickets | READY | BLOCKED | WAITING_DATA | WATCHLIST |
|---|---|---|---|---|---|
| Phase 0 | 9 | 8 | 0 | 1 | 0 |
| Phase 1 | 7 | 3 | 4 | 0 | 0 |
| Phase 2 | 15 | 5 | 2 | 7 | 1 |
| Phase 3 | 8 | 0 | 8 | 0 | 0 |
| Phase 4 | 4 | 1 | 0 | 3 | 0 |
| Phase 5 | 5 | 3 | 1 | 0 | 1 |
| Phase 6 | 4 | 0 | 4 | 0 | 0 |
| **TOTAL** | **52** | **20** | **19** | **11** | **2** |

**Ordre d'exécution Phase 0 (obligatoire)** :
V7-INFRA-00 → V7-DATA-CAL → V7-LEAKAGE-00 → V7-00 → V7-02 → V7-29 → V7-30 → V7-01A → V7-01B

**Tickets débloqués immédiatement après Phase 0** :
V7-31, V7-04, V7-39, V7-09, V7-10, V7-17, V7-19, V7-25, V7-16, V7-18, V7-21

**Goulots d'étranglement critiques** :
- V7-03 (nested stacking) : débloque V7-05, V7-35, V7-37, V7-38, V7-14
- V7-06+V7-07+V7-08 : débloquent V7-12, V7-27, V7-32, V7-33, V7-13
- V7-13 : débloque V7-15, V7-28

**Directive finale** :
Thesis centrale : CBOT = moteur mondial, EMA = prix européen, Basis = prime structurelle.
Signal principal V7 = EMA surperforme ou sous-performe CBOT sur horizon H90.
Aucun résultat ne quitte le statut RESEARCH_ONLY sans validation sur données EMA officielles.


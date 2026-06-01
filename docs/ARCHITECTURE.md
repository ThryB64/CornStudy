# Architecture

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PIPELINE DE DONNÉES                            │
│                                                                         │
│  config/sources.yaml ── collect/ ── data/raw/  ─── clean/ ─── data/     │
│                                                              interim/   │
│                                                                  │      │
│       config/features.yaml ── features/ ─── data/processed/      │      │
│                                              features.parquet ◄──┘      │
│                                              targets.parquet            │
│                                                  │                      │
│                                  ┌───────────────┴────────────────┐     │
│                                  ▼                                ▼     │
│                            leakage/audit                     models/    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     PLATEFORME / INDICATEUR                             │
│                                                                         │
│  config/models.yaml ── walkforward/ ── optimize/ ── PREDICTIONS         │
│                              │                          │               │
│                              ▼                          ▼               │
│                        meta/database ◄─────── meta/stacking             │
│                              │                          │               │
│                              ▼                          ▼               │
│                       meta/conformal ─── decision/rules ── advise()     │
│                                                                         │
│                       config/decision.yaml ─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Couches et responsabilités

### `src/mais/collect/`
Une fonction `download(out_dir, src) -> str` par source. Lit les paramètres
dans `config/sources.yaml`. Échec explicite avec `NotImplementedError`
quand une API key manque (au lieu d'échouer silencieusement).

### `src/mais/clean/`
- `legacy_migration.py` : convertit `csv/corrige/*.csv` en `data/interim/*.parquet` en corrigeant les bugs A et C de l'audit
- (à venir) validations de schéma, détection de drift, harmonisation des fréquences

### `src/mais/features/`
- `market.py` : returns, vols, RSI, MACD, ATR, Bollinger, ratios cross-commo
- `weather_belt.py` : agrégation pondérée par production des 20 états
- `surprise.py` : pour chaque variable fondamentale, ajoute `_surprise_vs_prev`, `_surprise_vs_5y`, `_surprise_vs_trend`
- `seasonality.py` : Fourier + saisons agronomiques

Toutes les features sont SHIFTÉES `+1` jour à la fin (anti-leakage).

### `src/mais/targets.py`
Le SEUL endroit qui regarde le futur. Construit `y_logret_h{H}`, classes
ordinales (deciles expanding-window), binaires up/down strong, vol réalisée.

### `src/mais/leakage/`
5 checks automatiques (cf. `tests/unit/test_leakage.py`) :
1. SHAPE_ALIGNMENT
2. NAMING_CONVENTION (préfixe `y_` réservé aux targets)
3. PERFECT_FIT (corr > 0.97 entre feature et target = suspect)
4. FUTURE_FUNCTION (shifter -1 ne doit pas améliorer la corr)
5. SUSPECT_NAMES (entêtes numériques `5.98`, suffixe `.1`)

Le CLI `mais audit-leakage` exit code != 0 si l'un échoue.

### `src/mais/models/`
- `base.py` : `ModelAdapter` ABC avec interface uniforme
- `registry.py` : enregistre les 50 modèles depuis `config/models.yaml`
- `adapters_basic.py`, `adapters_ml.py` : adapters concrets (incrémental)
- `LegacyShim` : placeholder qui pointe vers le fichier legacy non-porté

### `src/mais/walkforward/`
- `splits.py` : `WalkForwardSplitter` avec embargo horizon-dépendant
- `runner.py` : `walk_forward_run()` qui produit OOF predictions

### `src/mais/optimize/`
- `profiler.py` : auto-détection du type de tâche pour any-CSV-in
- `runner.py` : orchestrateur appelé par `mais train`

### `src/mais/meta/`
- `meta_database.py` : assemble les OOF predictions en table large
- `stacking.py` : meta-modèle Ridge/Lasso/LGBM walk-forward
- `conformal.py` : intervalles 90% par split-conformal rolling

### `src/mais/decision/`
- `rules.py` : moteur de règles évalué sur les sorties du méta-modèle
- `backtest.py` : simulation agronomique vs baselines
- `advise_cli.py` : `mais advise` pour la recommandation du jour

### `src/mais/ui/`
4 pages Streamlit (Conseil, Profilage CSV, Audit, Résultats).
Remplace `Models/app.py` (4608 lignes).

### `src/mais/api/` (future)
Endpoints FastAPI : `/predict`, `/explain`, `/advise`.

## Flow de données complet

```
make data
  ├─ mais collect all          (download dans data/raw/)
  ├─ mais clean                (raw -> data/interim/*.parquet, fix bugs)
  ├─ mais features             (interim -> data/processed/features.parquet)
  ├─ mais targets              (interim -> data/processed/targets.parquet)
  └─ mais audit-leakage        (FAIL si check anti-leakage casse)

make train (--all)
  └─ mais train --all          (-> artefacts/predictions/<target>/<model>.parquet)

make stack
  └─ mais stack                (-> artefacts/meta_database.parquet, meta_predictions.parquet)

make backtest / make ui
  └─ mais backtest / streamlit
```

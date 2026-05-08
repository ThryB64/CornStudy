# Migration ancien → nouveau

L'ancien projet est intentionnellement préservé sous `script/`, `csv/`,
`Models/` pour comparaison et débogage.

## Mapping fichiers

| Ancien (legacy) | Nouveau (v2) |
|---|---|
| `script/collect_yfinance.py` | `src/mais/collect/yfinance_collector.py` |
| `script/meteo_state.py` | `src/mais/collect/openmeteo_collector.py` |
| `script/fred_data.py` | `src/mais/collect/fred_collector.py` |
| `script/wasde_*.py` (5 fichiers) | `src/mais/collect/usda_wasde_collector.py` (à porter) |
| `script/indicateurs_techniques.py` | `src/mais/features/market.py` |
| `script/corrige/*.py` | `src/mais/clean/legacy_migration.py` |
| `script/corrige/database.py` | `src/mais/features/__init__.py::build_features` |
| `script/analyse.py` | `src/mais/leakage/audit.py` + `src/mais/optimize/profiler.py` |
| `script/backtest.py` | `src/mais/decision/backtest.py` |
| `script/train_model.py` | `src/mais/optimize/runner.py` + `src/mais/walkforward/runner.py` |
| `Models/config.yaml` | `config/models.yaml` (cible cassée corrigée) |
| `Models/app.py` (4608 l.) | `src/mais/ui/app.py` (4 pages, ~150 l.) |
| `Models/optimize.py` (3286 l.) | `src/mais/optimize/{runner,profiler,...}.py` |
| `Models/pretraitement.py` (1841 l.) | `src/mais/clean/`, `src/mais/leakage/`, `src/mais/features/` |
| `Models/base/wf_core.py` (866 l.) | `src/mais/walkforward/{splits,runner}.py` |
| `Models/base/io.py` | `src/mais/utils/io.py` |
| `Models/base/metrics.py` | `src/mais/walkforward/runner.py` (+ futures `metrics/` module) |
| `Models/models/<name>.py` | `src/mais/models/adapters_*.py` (adaptateurs ABC, porting incrémental) |
| `Models/models/stacking_reg.py` (NotImplemented) | `src/mais/meta/stacking.py` (vraie implémentation) |
| `install_data.sh` + `complete.sh` + `run.sh` + `analyse.sh` | `Makefile` |
| `csv/corrige/database.csv` | `data/processed/features.parquet` + `data/processed/targets.parquet` |
| `csv/corrige/*_completed.csv` | `data/interim/*.parquet` |
| `Mais Cbot.xlsx` | `config/features.yaml` + `docs/DATA_DICTIONARY.md` (à venir) |

## Procédure de migration

### Étape 1 : installer le nouveau

```bash
cd /home/cytech/Desktop/Etude\ Mais
rm -rf venv  # optionnel : recréer un venv propre
make venv
```

### Étape 2 : convertir les données existantes

```bash
make migrate-legacy
```

Cela crée :
- `data/interim/market.parquet`
- `data/interim/indicateurs.parquet`
- `data/interim/macro_fred.parquet` (avec entêtes corrigées : plus de `5.98`)
- `data/interim/wasde.parquet`
- `data/interim/quickstats.parquet`
- `data/interim/production.parquet`
- `data/interim/meteo.parquet` (toutes les états fusionnés)
- `data/interim/database.parquet` (équivalent du vieux `database.csv`, sans bugs)

### Étape 3 : tester

```bash
make install-dev
make test            # doit passer les tests anti-leakage
```

### Étape 4 : construire features + targets v2

```bash
make features
make targets
make audit           # le seul qui peut FAIL si une feature a leak
```

### Étape 5 : train

```bash
make install-ml
make train           # par défaut: model=ridge, target=y_logret_h20
make stack           # construit la meta-database et le stacking
```

### Étape 6 : conseil

```bash
make ui              # dashboard Streamlit
# ou
mais advise --horizon 20 --state iowa
```

## Fichiers legacy à supprimer (quand prêt)

- `analyse.sh`, `complete.sh`, `install_data.sh`, `run.sh` → remplacés par `Makefile`
- `csv/corrige/database.csv` (déjà ignoré dans `.gitignore`)
- `Models/config.yaml` (cible cassée) → remplacé par `config/models.yaml`
- `Mais Cbot.xlsx` (Excel non-machine-readable) → remplacé par les YAML de `config/`

À garder pour référence pendant ~1 mois :
- `Models/models/*.py` (50 implémentations, à porter incrémentalement)
- `Models/base/*.py` (logique walk-forward de référence)
- `script/wasde_*.py` (parser PDF qui fonctionne, à porter dans `usda_wasde_collector.py`)

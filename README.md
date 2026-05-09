# Etude Mais — v2

Comprendre, expliquer et prédire le prix du maïs CBOT pour fournir aux agriculteurs un indicateur de décision (vendre / stocker / attendre) à J+5, J+10, J+20, J+30.

## Vision en deux sous-projets

1. **Pipeline de données** (`src/mais/collect`, `clean`, `features`, `targets`) — collecte ~30 sources publiques, nettoie, harmonise les fréquences (daily/weekly/monthly), construit `data/processed/features.parquet` + `data/processed/targets.parquet` avec audit anti-leakage automatique.
2. **Plateforme de modèles + indicateur agriculteur** (`src/mais/models`, `walkforward`, `optimize`, `meta`, `decision`, `ui`) — orchestre 50+ modèles (baseline, classique, ML, DL), construit une vraie meta-database et un méta-modèle (stacking), et la couche `decision/` qui transforme les prédictions probabilistes en règles "vendre/stocker/attendre" backtestées de façon agronomique.

## Choix par défaut (modifiables)

- **Code en anglais**, doc en français.
- **Parquet** en interne pour `data/interim/` et `data/processed/`. Export CSV facultatif via la CLI.
- **Makefile** comme orchestrateur (zéro dépendance, lisible). Snakemake/Prefect possibles plus tard si besoin de DAG complexe.
- Le **vieux code reste intact** dans `csv/`, `script/`, `Models/`, `data/wasde_raw/` pour ne rien casser pendant la migration. Le nouveau code vit dans `src/mais/`, `tests/`, `data/{raw,interim,processed}/`, `pipelines/`, `config/`.

## Démarrage rapide

```bash
# 1. installer
make venv

# 2. (optionnel) migrer les données existantes du vieux projet vers data/interim/*.parquet
make migrate-legacy

# 3. construire le dataset complet
make data         # collect -> clean -> features -> targets -> audit anti-leakage

# 4. entraîner et empiler
make install-ml
make train
make stack

# 5. dashboard agriculteur
make install-ui
make ui
```

## Exploitation quotidienne

La commande de production quotidienne est :

```bash
make daily
make status
```

Elle reconstruit les features, targets, audit anti-fuite, facteurs, étude
professionnelle et backtest agriculteur. Sur un serveur avec clés API officielles :

```bash
venv/bin/python -m mais.cli daily-run --collect
```

## Application d'étude professionnelle

La commande principale pour reconstruire l'étude complète issue de `Etude.md` est :

```bash
make study
```

Elle génère :

- `docs/PROFESSIONAL_STUDY_REPORT.md`
- `docs/FARMER_BACKTEST_REPORT.md`
- `artefacts/professional_study/model_benchmarks.parquet`
- `artefacts/professional_study/model_predictions.parquet`
- `artefacts/professional_study/calibrated_predictions.parquet`
- `artefacts/professional_study/factor_importance.parquet`
- `artefacts/professional_study/family_importance.parquet`
- `artefacts/professional_study/regime_timeseries.parquet`
- `artefacts/professional_study/decision_snapshot.json`

L'application Streamlit complète se lance avec :

```bash
make ui
```

Pages incluses : synthèse exécutive, marché/régimes, facteurs économiques,
benchmark modèles, décision agriculteur cash-price, sources/qualité, monitoring
quotidien et rapports.

## Arborescence

```
mais/
  src/mais/                # package installable (pip install -e .)
    cli.py                 # CLI Typer : `mais collect all`, `mais train`, ...
    collect/               # 1 module = 1 source de données
    clean/                 # validations + dédup + harmonisation des fréquences
    features/              # market, weather_belt, fundamentals, surprise, cot, ethanol, world
    targets.py             # construction explicite y_h{5,10,20,30} + classes ordinales
    leakage/               # tests automatiques anti-fuite
    models/                # adaptateurs unifiés des 50 modèles
    walkforward/           # walk-forward extrait de wf_core.py
    optimize/              # extrait d'optimize.py, sous-modules <800 lignes
    meta/                  # vraie meta-database + stacking + blending
    decision/              # couche conseil agriculteur
    api/                   # FastAPI
    ui/                    # Streamlit
  data/
    raw/                   # téléchargements bruts (immuables)
    interim/               # nettoyage intermédiaire (parquet)
    processed/             # features.parquet + targets.parquet
    metadata/              # data_dictionary, anti-leakage audit
  tests/
  config/                  # sources.yaml, features.yaml, models.yaml, decision.yaml
  pipelines/               # plus tard : Snakefile éventuel
  notebooks/
  pyproject.toml
  Makefile
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - vue d'ensemble technique
- [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) - catalogue de toutes les variables (généré automatiquement)
- [docs/ANTI_LEAKAGE.md](docs/ANTI_LEAKAGE.md) - règles d'anti-fuite et tests
- [docs/AGRO_INDICATOR.md](docs/AGRO_INDICATOR.md) - règles de décision agriculteur
- [docs/MIGRATION.md](docs/MIGRATION.md) - mapping ancien -> nouveau
- [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md) - rapport critique du projet historique
- [docs/OPERATIONS.md](docs/OPERATIONS.md) - exploitation quotidienne et cron
- [docs/PROFESSIONAL_STUDY_REPORT.md](docs/PROFESSIONAL_STUDY_REPORT.md) - rapport d'étude généré
- [docs/FACTOR_ANALYSIS_REPORT.md](docs/FACTOR_ANALYSIS_REPORT.md) - analyse factorielle
- [docs/FARMER_BACKTEST_REPORT.md](docs/FARMER_BACKTEST_REPORT.md) - simulation revenu agriculteur

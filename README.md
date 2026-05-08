# CornStudy — Étude professionnelle du maïs CBOT

Comprendre, expliquer et prédire le prix du maïs CBOT pour fournir aux agriculteurs un indicateur de décision (vendre / stocker / attendre) à J+5, J+10, J+20, J+30.

## Vision

1. **Pipeline de données** (`src/mais/collect`, `clean`, `features`, `targets`) — collecte ~30 sources publiques, nettoie, harmonise les fréquences (daily/weekly/monthly), construit `data/processed/features.parquet` + `data/processed/targets.parquet` avec audit anti-leakage automatique.
2. **Facteurs économiques** (`src/mais/features/factors.py`) — réduit les features brutes en facteurs interprétables : WASDE, météo Corn Belt, momentum, volatilité, cross-commodities et saisonnalité.
3. **Étude professionnelle** (`src/mais/study`) — benchmark walk-forward, calibration, intervalles, régimes de marché, importance des facteurs et décision cash-price.
4. **Application Streamlit** (`src/mais/ui/app.py`) — console interactive : synthèse, régimes, facteurs, modèles, décision agriculteur, sources et rapports.

## Organisation du dépôt

- **Code en anglais**, doc en français.
- **Parquet** en interne pour `data/interim/` et `data/processed/`. Export CSV facultatif via la CLI.
- **Makefile** comme orchestrateur (zéro dépendance, lisible). Snakemake/Prefect possibles plus tard si besoin de DAG complexe.
- Les données lourdes, artefacts et environnements locaux ne sont pas versionnés. Les dossiers `data/` et `artefacts/` restent présents avec `.gitkeep` et README dédiés.
- L'ancien projet local est documenté dans `legacy/v1/`, mais le dépôt actif reste centré sur la V2 propre.

## Démarrage rapide

```bash
# 1. installer
make venv
make install-dev

# 2. (optionnel) migrer des CSV legacy locaux vers data/interim/*.parquet
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

## Application d'étude professionnelle

La commande principale pour reconstruire l'étude complète issue de `Etude.md` est :

```bash
make study
```

Elle génère :

- `docs/PROFESSIONAL_STUDY_REPORT.md`
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
benchmark modèles, décision agriculteur cash-price, sources/qualité et rapports.

## Commandes utiles

```bash
make test
make features
make targets
make audit
make factor-analysis
make study
make ui
```

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
  data/                    # dossiers vides en Git ; fichiers générés localement
    raw/                   # téléchargements bruts (immuables)
    interim/               # nettoyage intermédiaire (parquet)
    processed/             # features.parquet + targets.parquet
    metadata/              # data_dictionary, anti-leakage audit
  artefacts/               # sorties modèles/étude générées localement
  docs/
    PROFESSIONAL_STUDY_REPORT.md
    FACTOR_ANALYSIS_REPORT.md
  tests/
  config/                  # sources.yaml, features.yaml, models.yaml, decision.yaml
  pipelines/               # plus tard : Snakefile éventuel
  notebooks/
  legacy/v1/               # notes sur l'ancien projet local non versionné
  pyproject.toml
  Makefile
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - vue d'ensemble technique
- [docs/ANTI_LEAKAGE.md](docs/ANTI_LEAKAGE.md) - règles d'anti-fuite et tests
- [docs/AGRO_INDICATOR.md](docs/AGRO_INDICATOR.md) - règles de décision agriculteur
- [docs/MIGRATION.md](docs/MIGRATION.md) - mapping ancien -> nouveau
- [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md) - rapport critique du projet historique
- [docs/PROFESSIONAL_STUDY_REPORT.md](docs/PROFESSIONAL_STUDY_REPORT.md) - rapport d'étude généré

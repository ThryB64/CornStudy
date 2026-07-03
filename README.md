# Etude Mais — Étude statistique CBOT & Euronext EMA

Étude statistique et économique complète du cours du maïs CBOT et Euronext EMA.  
**Ce n'est pas un indicateur opérationnel agriculteur.** C'est une étude scientifique honnête.

**Phrase directrice :** CBOT explique la tendance mondiale. EMA révèle la prime européenne via le basis. L'étude Euronext consiste à expliquer le basis, la transmission CBOT→EMA, les périodes de découplage, et le résidu européen spécifique.

## Rapport de démarche (présentation école)

`docs/RAPPORT_ETUDE_COMPLETE.md` retrace toute la démarche **question → test → analyse →
nouvelle question**, avec l'inventaire complet des **310 tests/expériences** et leurs visuels :
- `artefacts/rapport_etude/arbre_etude.html` + `docs/ARBRE_ETUDE.md` — **arbre de cheminement**
  (❓question → 📋ce qu'on cherche → 📄fichiers → 🔎analyse → question suivante) où **les 310
  fichiers sont tous tracés** (🟢 gardé / 🔴 abandonné / 🟠 bloqué / 🔧 outil / 🔵 exploration ;
  clic sur un fichier = détail complet) ;
- `artefacts/rapport_etude/tests_performants.html` — graphe des tests aux bons résultats ;
- `artefacts/rapport_etude/inventaire_tests.csv` — 1 ligne par test (régénérer : `make study-report`).

## Résultat final de l'étude CBOT

L'étude (étapes 1-7, vue d'ensemble : **`docs/FINAL_STUDY_OVERVIEW.md`** ; clôture :
`docs/FINAL_CBOT_STUDY_CLOSURE.md`) conclut honnêtement :

- **La prédiction pure du prix n'est pas validée** avec les données publiques gratuites : la
  **random walk reste imbattable en RMSE** (aucun modèle ne la bat, étape 6).
- Le **livrable final est un score de vente / direction / risque H40-H90** (`cbot_sale_score_v1`),
  pas une prévision de prix.
- Le score utilise **Crop Condition** (H90), **WASDE stocks-to-use** (H40), **saisonnalité**,
  **volatilité HAR/EGARCH** et **régimes de marché** (pour doser la confiance).
- **C'est un outil d'aide à la décision, pas un bot de trading autonome** (jamais de short, de
  levier ni de rachat). Sorties : `SELL_PARTIAL` / `WAIT` / `WATCH` / `RISK_HIGH` / `NO_SIGNAL`.
- **Statut : FRAGILE.** Sur le holdout 2024+ (jamais utilisé avant), le score bat la random walk
  (DA 0.686, AUC 0.816) et est économiquement cohérent, **mais ne bat pas une simple
  saisonnalité** sur cette fenêtre courte (~1,5 an). À reconfirmer en forward avant usage.

```bash
python -m mais.cli sale-score --holdout   # score + validation holdout + backtest
python -m mais.cli sale-score --latest    # dernier signal seulement
make sale-score
```

Rapports : `docs/FINAL_CBOT_SALE_SCORE_STUDY.md`, `..._PROTOCOL.md`, `..._LIMITS.md`,
`..._USER_GUIDE.md`, `..._TECHNICAL_SUMMARY.md`, `docs/FINAL_HOLDOUT_2024_VALIDATION.md`,
`docs/FINAL_FARMER_DECISION_BACKTEST.md`. Artefacts : `artefacts/final_cbot_sale_score/`.

## Indicateur Euronext de vente / risque

Le score de vente CBOT est **visualisé sur l'historique de prix Euronext (EMA, €/t)** via un
dashboard HTML interactif (aucune image générée).

- **Objectif** : voir, sur l'historique Euronext, ce que l'indicateur aurait dit (SELL_PARTIAL /
  WAIT / WATCH / RISK_HIGH / NO_SIGNAL), le niveau de risque, et si le prix a ensuite confirmé.
- **Commande** : `python -m mais.cli euronext-indicator` (ou `make euronext-indicator`).
- **Fichiers générés** (`artefacts/final_euronext_indicator/`) :
  `euronext_indicator_dashboard.html` (Plotly interactif, JS inline, autonome),
  `euronext_indicator_history.csv`, `euronext_indicator_latest.json`,
  `euronext_indicator_metrics.csv`, `euronext_backtest_*.csv`, `feature_dictionary.csv`.
- **Résultat honnête** : les recommandations **séparent les retours futurs dans le bon sens**
  (SELL_PARTIAL → baisse moyenne, WAIT → hausse), mais la discrimination **hors échantillon est
  faible** et le prix Euronext disponible est à **~97 % un proxy** (cf.
  `docs/EURONEXT_DATA_AUDIT.md`). **Verdict : RESEARCH_ONLY** — outil de visualisation, pas un
  conseil de vente opérationnel, pas un bot.
- **Limites** : score issu du CBOT (basis / EUR/USD non intégrés), données proxy, validation
  forward nécessaire. Rapports : `docs/FINAL_EURONEXT_INDICATOR_REPORT.md`,
  `docs/FINAL_EURONEXT_INDICATOR_BACKTEST.md`, `docs/EURONEXT_INDICATOR_USER_GUIDE.md`.

## Données nécessaires pour aller plus loin

Les sources publiques gratuites sont explorées. Pour progresser (voir
`external_research/docs/step6_missing_data_recommendations.md`) :

- **Consensus analystes pré-WASDE** (vraie surprise) — payant.
- **Options maïs : volatilité implicite, skew, open interest** — partiel/payant.
- **Courbe futures par contrat** (CBOT par maturité) — payant pour l'historique.
- **Basis / cash bids historiques** — DTN / USDA AMS / FranceAgriMer.
- **Archive de prévisions météo forward** (seule voie météo prédictive) — Open-Meteo, gratuit.
- **Export flows** (USDA FAS) — gratuit. **Satellite / NDVI** (MODIS/Sentinel) — gratuit.
- **EUR/USD quotidien** (FRED) — gratuit, débloque basis / VECM / mean-reversion.

## Architecture

1. **Pipeline de données** (`src/mais/collect`, `features`, `targets`) — collecte ~30 sources publiques, construit `data/processed/features.parquet` + `data/processed/targets.parquet` avec audit anti-leakage strict.
2. **Modules d'étude EMA** (`src/mais/research/ema_*.py`) — cointegration, décomposition retour, étude résidu, basis formel, benchmarks directionnels, event study, volatilité.
3. **Collecteurs EU** (`src/mais/collect/ec_mars.py`, `openmeteo_eu.py`, etc.) — données fondamentales européennes pour expliquer le résidu EMA.

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

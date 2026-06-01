# Notebooks Euronext — Pivot Euronext Matif (EMA)

Ces notebooks adaptent l'étude CBOT vers la cible Euronext EMA (EUR/tonne).
**Les notebooks CBOT originaux ne sont pas supprimés** — voir `main/`.

## Ordre d'exécution recommandé

```
01_ema_data_collection.ipynb     ← COMMENCER ICI (EXP-EU-00)
        ↓
00_benchmark_pivot_ema.ipynb     ← Valider le pivot (EXP-EU-00B)
        ↓
05_statistical_models_ema.ipynb  ← Modèles statistiques sur EMA
        ↓
10_module_a_dashboard.ipynb      ← Indicateur de contexte marché
```

## Notebooks disponibles

| Notebook | Ticket | Description |
|---|---|---|
| `00_benchmark_pivot_ema.ipynb` | EXP-EU-00B | **Commencer ici** — valide que le pivot Euronext vaut le coup |
| `01_ema_data_collection.ipynb` | EXP-EU-00 | Collecte et validation prix EMA + EUR/USD + corrélation CBOT |
| `05_statistical_models_ema.ipynb` | Sprint 1 | Ridge/Logistic sur cible EMA vs CBOT |
| `10_module_a_dashboard.ipynb` | EXP-MOD-A | Prototype Module A — 12 signaux contexte marché |

## Pré-requis données

Pour lancer les notebooks, il faut d'abord collecter les données EMA :

```bash
# Option 1: via le collecteur (si yfinance supporte EMA=F)
cd "Desktop/Etude Mais"
venv/bin/python -m mais.cli collect euronext_ema
venv/bin/python -m mais.cli collect eu_cross_assets

# Option 2: téléchargement manuel (recommandé)
# 1. Aller sur https://www.euronext.com
# 2. Products > Derivatives > Agricultural > Corn (Maïs Rendu Rouen)
# 3. Historical Data > Download (format CSV)
# 4. Sauvegarder dans: data/raw/euronext_ema/ema_manual.csv
#    Colonnes: Date, Open, High, Low, Close, Volume
```

## Architecture pivot Euronext

```
Features (X)                           Cible (y)
─────────────────────────────          ──────────────────────
CBOT existantes (conservées)    →      Euronext EMA (EUR/tonne)
+ Données EU (EC MARS, Agreste)        • direction: y_up_h40_ema
+ Cross-market (basis, EUR/USD)        • retour: y_logret_h40_ema
+ Données mondiales (DCE, CONAB)       • prix absolu: y_price_ema_60d
```

## Différences avec notebooks CBOT (main/)

| | CBOT (main/) | Euronext (ici) |
|---|---|---|
| Cible | `y_up_h40` (CBOT USD/bu) | `y_up_h40_ema` (EMA EUR/t) |
| Features | CBOT seules | CBOT + EU + cross-market |
| Pertinence | Recherche | Application agricole FR/EU |
| Modules | Étude statistique | Dashboard A + Règles B + Prédiction C |

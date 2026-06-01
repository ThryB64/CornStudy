# DATA-WORLD-01 — Enrichissement WASDE EU + Ukraine

## Source

Fichiers texte WASDE existants dans `data/wasde_raw/` — section "World Corn Supply and Use".
Parsés ligne par ligne avec regex pour extraire EU et Ukraine.

## Couverture

| Série | Début | Fin | Lignes valides |
|---|---|---|---|
| EU production (Mt) | 2016-10-11 | 2026-05 | 3 513 |
| EU exports (Mt) | 2016-10-11 | 2026-05 | 3 513 |
| EU ending stocks (Mt) | 2016-10-11 | 2026-05 | 3 513 |
| Ukraine production (Mt) | 2007-10-10 | 2026-05 | 7 319 |
| Ukraine exports (Mt) | 2007-10-10 | 2026-05 | 7 319 |
| EU stock/use ratio | 2016-10-11 | 2026-05 | 3 513 |

## Features créées

| Feature | Description | Anti-leakage |
|---|---|---|
| `wasde_eu_production_mt_lag1` | Production maïs EU (Mt) | shift(1) + ffill |
| `wasde_eu_exports_mt_lag1` | Exports maïs EU (Mt) | shift(1) + ffill |
| `wasde_eu_ending_stocks_mt_lag1` | Stocks fin EU (Mt) | shift(1) + ffill |
| `wasde_ukraine_production_mt_lag1` | Production Ukraine (Mt) | shift(1) + ffill |
| `wasde_ukraine_exports_mt_lag1` | Exports Ukraine (Mt) | shift(1) + ffill |
| `wasde_eu_stock_use_ratio_lag1` | Stocks/consommation EU (approx 80 Mt) | shift(1) + ffill |

## Anti-leakage

Publication WASDE : **~10e du mois** → shift(1) journalier.

## Limites

- EU dans WASDE = historique court (parsing fiable depuis ~2016)
- Ukraine data disponible depuis 2007 (meilleure couverture)
- `eu_stock_use_ratio` basé sur consommation EU approximée à 80 Mt (hors variation)
- Pas de ratio EU/monde (stocks monde non parsés depuis les TXT)

## Fichiers

- `data/raw/wasde_world/wasde_world_raw.parquet`
- `data/raw/wasde_world/wasde_world_features.parquet`
- `artefacts/ema_study/wasde_world_audit.json`

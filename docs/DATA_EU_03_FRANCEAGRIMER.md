# DATA-EU-03 — Collecteur FranceAgriMer / Agreste

## Source

**Eurostat apro_cpsh1** — Production maïs grain par pays (France, Roumanie, Hongrie).
API alternative à FranceAgriMer (bilans mensuels PDF sur data.gouv.fr, non structurés).

## Couverture

| Série | Début | Fin | Lignes valides |
|---|---|---|---|
| France production (kt) | 2000-11-16 | 2026-05 | 9 321 |
| Roumanie production (kt) | 2000-11-16 | 2026-05 | 9 321 |
| Hongrie production (kt) | 2000-11-16 | 2026-05 | 9 321 |
| FR+RO+HU total (kt) | 2000-11-16 | 2026-05 | 9 321 |

## Features créées

| Feature | Description | Anti-leakage |
|---|---|---|
| `fr_mais_production_kt_lag1` | Production France maïs (kt) | shift(1) + ffill |
| `ro_mais_production_kt_lag1` | Production Roumanie maïs (kt) | shift(1) + ffill |
| `hu_mais_production_kt_lag1` | Production Hongrie maïs (kt) | shift(1) + ffill |
| `fr_mais_prod_anomaly_lag1` | Anomalie production FR vs moyenne expandante | shift(1) + ffill |
| `fr_mais_prod_yoy_pct_lag1` | Variation YoY% FR | shift(1) + ffill |
| `fr_ro_hu_mais_total_kt_lag1` | Total FR+RO+HU (représente ~60% EU) | shift(1) + ffill |

## Limites

- FranceAgriMer bilans mensuels (collecte mensuelle, stocks) non disponibles via API
- Données Eurostat annuelles uniquement
- Agreste (estimations de récolte hebdomadaires) : pas d'API publique structurée

## Fichiers

- `data/raw/franceagrimer/franceagrimer_raw.parquet`
- `data/raw/franceagrimer/franceagrimer_monthly.parquet`
- `artefacts/ema_study/franceagrimer_audit.json`

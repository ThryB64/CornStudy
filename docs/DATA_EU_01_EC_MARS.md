# DATA-EU-01 — Collecteur EC MARS (Eurostat)

## Source

**Eurostat apro_cpsh1** — Production céréales EU standard humidity.
Code maïs grain : **C1500** (Grain maize and corn-cob-mix).
Accès via SDMX 2.1 REST API — gratuit, sans authentification.

Note : Les bulletins MARS mensuels (JRC Agri4cast) sont des PDFs non parsés automatiquement.

## Couverture

| Série | Début | Fin | Lignes valides |
|---|---|---|---|
| Production EU27 (kt) | 2010-11-16 | 2026-05 | 5 669 |
| Anomalie production | 2013-11-16 | 2026-05 | 4 938 |
| YoY% production | 2011-11-16 | 2026-05 | 5 304 |

## Features créées

| Feature | Description | Anti-leakage |
|---|---|---|
| `ec_mars_production_eu_kt_lag1` | Production EU27 maïs (kt) | shift(1) + ffill |
| `ec_mars_prod_anomaly_eu_lag1` | Anomalie vs moyenne expandante | shift(1) + ffill |
| `ec_mars_prod_yoy_pct_lag1` | Variation YoY% | shift(1) + ffill |

## Anti-leakage

Publication Eurostat : environ **15 novembre** de l'année de récolte N.
Feature forward-filled à partir de cette date + shift(1) journalier.

## Limites

- Données annuelles uniquement (pas de mise à jour mensuelle comme les bulletins MARS)
- Bulletins MARS mensuels (PDF) : crop monitoring mid-season non disponible via API
- Couverture EU27 uniquement (pas par pays en détail)

## Fichiers

- `data/raw/ec_mars/ec_mars_eurostat_raw.parquet`
- `data/raw/ec_mars/ec_mars_monthly.parquet`
- `artefacts/ema_study/ec_mars_audit.json`

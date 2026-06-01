# DATA-EU-04 — Collecteur ETS CO₂ et TTF enrichi

## Source

- **TTF=F** (Dutch TTF natural gas futures) via yfinance — disponible depuis 2017-10-23
- **CO2.L** (ICE EUA CO₂ allowance futures) via yfinance — disponible depuis 2021-10-18

## Couverture

| Série | Début | Fin | Lignes |
|---|---|---|---|
| TTF gaz (€/MWh) | 2017-10-23 | 2026-05-22 | 2 159 |
| ETS CO₂ (€/t) | 2021-10-18 | 2026-05-22 | 1 159 |

## Features créées

| Feature | Description | Anti-leakage |
|---|---|---|
| `ttf_eur_mwh` | Prix TTF brut | — |
| `ttf_return_1d` | Rendement quotidien TTF | shift(1) |
| `ttf_zscore_52w` | Z-score expandant TTF | shift(1) + expanding min 52j |
| `ets_co2_eur_t` | Prix EUA CO₂ brut | — |
| `ets_co2_return_1d` | Rendement quotidien CO₂ | shift(1) |
| `ets_co2_zscore_52w` | Z-score expandant CO₂ | shift(1) + expanding min 52j |

## Limites

- TTF non disponible avant 2017 via yfinance (couverture partielle par rapport à la période EMA 2006-2026)
- CO₂ ETS uniquement depuis 2021 — insuffisant pour la période principale d'étude
- Alternative pour historique plus long : EEX Historical Data (payant) ou EU ETS Registry CSV (gratuit, annuel uniquement)

## Fichiers

- `data/raw/eu_carbon/eu_carbon_features.parquet`
- `data/raw/eu_carbon/ttf_eur_mwh.parquet`
- `data/raw/eu_carbon/ets_co2_eur_t.parquet`
- `artefacts/ema_study/eu_carbon_audit.json`

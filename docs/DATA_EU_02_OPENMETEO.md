# DATA-EU-02 — Collecteur Open-Meteo Europe

## Source

**Open-Meteo Historical Archive API** — gratuit, sans clé.
URL : `https://archive-api.open-meteo.com/v1/archive`

## Zones maïs EU

| Zone | Coordonnées | Poids |
|---|---|---|
| France SO (Landes/Gers) | 44.0°N, 0.5°E | 25% |
| France CO (Beauce/Brie) | 46.5°N, 2.0°E | 10% |
| Italie Nord (Plaine du Pô) | 45.0°N, 11.0°E | 20% |
| Roumanie (Bucarest) | 44.5°N, 26.0°E | 20% |
| Hongrie (Budapest) | 47.0°N, 19.0°E | 15% |
| Ukraine Ouest (Kiev) | 49.0°N, 27.0°E | 10% |

## Couverture

| Série | Début | Fin | Lignes valides |
|---|---|---|---|
| GDD cumulé EU | 2010-01-02 | 2026-05 | 5 987 |
| Anomalie GDD | 2010-01-02 | 2026-05 | 5 257 |
| Jours stress thermique 4S | 2010-01-02 | 2026-05 | 5 974 |
| Déficit précipitations 30j | 2010-01-02 | 2026-05 | 5 808 |

## Features créées

| Feature | Description | Anti-leakage |
|---|---|---|
| `eu_gdd_cumul` | GDD maïs cumulé depuis 1 mai (base 10°C) | shift(1) |
| `eu_gdd_anomaly` | Anomalie GDD vs moyenne 10 ans | shift(1) |
| `eu_heat_stress_days_4w` | Jours >32°C sur 4 semaines | shift(1) |
| `eu_precip_deficit_30d` | Déficit pluie 30j vs normale | shift(1) |

## Calcul GDD

```
GDD_daily = clip((Tmax + Tmin) / 2, base=10°C, max=30°C) - 10
GDD_cumul = sum(GDD_daily depuis 1 mai)
```

## Fichiers

- `data/raw/openmeteo_eu/zone_*.parquet` (par zone)
- `data/raw/openmeteo_eu/openmeteo_eu_daily.parquet`
- `artefacts/ema_study/openmeteo_eu_audit.json`

# Backtest agriculteur

- Horizon: J+20
- État/profil: `iowa`
- Période: `2015-08-27` -> `2025-06-26`
- Basis: -0.20 USD/bu
- Coût stockage: 0.04 USD/bu/mois

## Résumé stratégies

| Stratégie | Revenu net moyen USD/bu | Sharpe annuel | Années > harvest | Max drawdown | N années |
|---|---:|---:|---:|---:|---:|
| `sell_dca_monthly` | 4.302 | 3.87 | 70.0% | 0.000 | 10 |
| `model_adviser` | 4.164 | 3.99 | 50.0% | 0.000 | 10 |
| `sell_at_harvest_100` | 4.156 | 4.00 | 0.0% | 0.000 | 10 |

## Résultats annuels

| season | model_adviser | sell_at_harvest_100 | sell_dca_monthly |
|---:|---:|---:|---:|
| 2015 | 3.562 | 3.555 | 3.571 |
| 2016 | 3.334 | 3.340 | 3.405 |
| 2017 | 3.293 | 3.305 | 3.329 |
| 2018 | 3.571 | 3.583 | 3.618 |
| 2019 | 3.714 | 3.732 | 3.380 |
| 2020 | 3.859 | 3.837 | 5.085 |
| 2021 | 5.123 | 5.058 | 6.077 |
| 2022 | 6.620 | 6.635 | 6.235 |
| 2023 | 4.708 | 4.700 | 4.221 |
| 2024 | 3.856 | 3.812 | 4.099 |

Lecture: ce backtest simule un boisseau normalisé disponible après récolte. Le modèle vend une fraction du stock selon les règles agriculteur, paie le stockage sur l'inventaire restant, puis liquide tout reliquat avant la saison suivante.
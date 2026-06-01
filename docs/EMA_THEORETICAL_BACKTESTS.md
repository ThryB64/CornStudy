# EMA THEORETICAL BACKTESTS

> Backtests exploratoires. Ce n'est pas un système de trading ni une validation production.

## Verdict

- Statut : THEORETICAL_ONLY_NOT_PRODUCTION
- Meilleure stratégie : basis_extreme_mean_reversion H60
- PnL moyen meilleur cas : 10.20 EUR/t
- Hit rate meilleur cas : 0.714
- Verdict production : NO_PRODUCTION_BACKTEST

## Résultats

| Stratégie | H | n | Hit rate | PnL total | PnL moyen | Worst year | Max DD |
|---|---:|---:|---:|---:|---:|---|---:|
| ema_direct_momentum | 40 | 74 | 0.541 | 59.25 | 0.80 | 2022 | -160.50 |
| relative_basis_z_rule | 40 | 74 | 0.568 | 239.74 | 3.24 | 2012 | -46.62 |
| basis_extreme_mean_reversion | 40 | 10 | 0.400 | 30.07 | 3.01 | 2013 | -20.96 |
| ema_direct_momentum | 60 | 49 | 0.510 | 3.00 | 0.06 | 2022 | -201.50 |
| relative_basis_z_rule | 60 | 49 | 0.653 | 69.38 | 1.42 | 2022 | -68.64 |
| basis_extreme_mean_reversion | 60 | 7 | 0.714 | 71.40 | 10.20 | 2011 | -4.31 |

Limites : source EMA proxy, frictions simplifiées, pas de liquidité réelle, pas de bid-ask historique, pas de sizing, pas de levier.
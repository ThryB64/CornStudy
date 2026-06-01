# EMA RELATIVE BACKTEST V3

> Backtest de recherche H90 avec seuils train-only et contraintes d'execution proxy.

## Verdict

- Statut : RESEARCH_ONLY_NOT_TRADING
- Production : NO_PRODUCTION_BACKTEST
- Signaux candidats avant non-overlap : 48
- Meilleur slippage/leg : 1.0 EUR/t
- Meilleurs trades : 9
- Meilleur hit rate : 0.667
- PnL moyen meilleur cas : 11.04 EUR/t
- PnL moyen high cost : 3.04 EUR/t
- Lecture : V3 remains positive under the highest proxy slippage, but sample size and proxy execution keep it research-only.

## Resultats

| Slippage/leg | n | Hit rate | PnL total | PnL moyen | PF | Sortino | Avg win | Avg loss | Max DD | Pos years |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 9 | 0.667 | 99.40 | 11.04 | 4.861 | 2.617 | 20.86 | -8.58 | -23.14 | 0.667 |
| 2.0 | 9 | 0.556 | 81.40 | 9.04 | 3.440 | 2.408 | 22.95 | -8.34 | -25.14 | 0.556 |
| 3.0 | 9 | 0.556 | 63.40 | 7.04 | 2.533 | 1.875 | 20.95 | -10.34 | -27.14 | 0.556 |
| 5.0 | 9 | 0.556 | 27.40 | 3.04 | 1.478 | 0.810 | 16.95 | -14.34 | -33.88 | 0.556 |

## Limites

- Source EMA proxy.
- Roll cost et slippage restent proxies.
- Pas de bid-ask reel, marge, change, taille ou execution carnet.
- Recherche seulement.
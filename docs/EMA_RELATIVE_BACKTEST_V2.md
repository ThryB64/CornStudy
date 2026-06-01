# EMA RELATIVE BACKTEST V2

> Backtest de recherche avec entrees weekly, non-overlap strict et stress de couts.

## Verdict

- Statut : RESEARCH_ONLY_NOT_TRADING
- Verdict production : NO_PRODUCTION_BACKTEST
- Meilleure strategie : `h90_combined_top40_weekly`
- Cout meilleur cas : 1.0 EUR/t par leg
- Trades : 21
- Hit rate : 0.810
- PnL moyen : 12.50 EUR/t
- Lecture : Best strategy stays positive even under high simplified costs, but proxy data prevents production use.

## Resultats

| Strategie | H | Cout/leg | n | Hit rate | PnL total | PnL moyen | PF | Max DD | Pos years |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| h40_top20_confidence_weekly | 40 | 1.0 | 20 | 0.650 | 111.82 | 5.59 | 2.545 | -29.12 | 0.875 |
| h40_basis_extreme_weekly | 40 | 1.0 | 27 | 0.667 | 130.50 | 4.83 | 2.307 | -32.69 | 0.769 |
| h90_combined_top40_weekly | 90 | 1.0 | 21 | 0.810 | 262.58 | 12.50 | 10.358 | -16.30 | 0.923 |
| premium_medium_high_no_roll_weekly | 40 | 1.0 | 29 | 0.586 | 34.49 | 1.19 | 1.348 | -31.88 | 0.714 |
| h40_top20_confidence_weekly | 40 | 2.0 | 20 | 0.500 | 71.82 | 3.59 | 1.794 | -31.12 | 0.750 |
| h40_basis_extreme_weekly | 40 | 2.0 | 27 | 0.630 | 76.50 | 2.83 | 1.641 | -34.69 | 0.769 |
| h90_combined_top40_weekly | 90 | 2.0 | 21 | 0.714 | 220.58 | 10.50 | 7.087 | -18.30 | 0.923 |
| premium_medium_high_no_roll_weekly | 40 | 2.0 | 29 | 0.552 | -23.51 | -0.81 | 0.811 | -51.00 | 0.643 |
| h40_top20_confidence_weekly | 40 | 3.0 | 20 | 0.400 | 31.82 | 1.59 | 1.283 | -44.51 | 0.625 |
| h40_basis_extreme_weekly | 40 | 3.0 | 27 | 0.519 | 22.50 | 0.83 | 1.156 | -38.50 | 0.692 |
| h90_combined_top40_weekly | 90 | 3.0 | 21 | 0.714 | 178.58 | 8.50 | 4.702 | -20.30 | 0.846 |
| premium_medium_high_no_roll_weekly | 40 | 3.0 | 29 | 0.448 | -81.51 | -2.81 | 0.470 | -100.63 | 0.429 |
| h40_top20_confidence_weekly | 40 | 5.0 | 20 | 0.250 | -48.18 | -2.41 | 0.705 | -92.51 | 0.250 |
| h40_basis_extreme_weekly | 40 | 5.0 | 27 | 0.370 | -85.50 | -3.17 | 0.579 | -94.46 | 0.385 |
| h90_combined_top40_weekly | 90 | 5.0 | 21 | 0.571 | 94.58 | 4.50 | 2.217 | -35.70 | 0.462 |
| premium_medium_high_no_roll_weekly | 40 | 5.0 | 29 | 0.276 | -197.51 | -6.81 | 0.143 | -204.63 | 0.143 |

## Limites

- Source EMA exploratoire/proxy.
- Pas de bid-ask historique ni de profondeur de carnet.
- Pas de modele de marge, change, roll execution reel ou sizing.
- Resultat recherche seulement.
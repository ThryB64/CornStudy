# EMA RELATIVE BACKTEST

> Backtest de recherche du spread relatif EMA/CBOT H40. Ce n'est pas un système de trading.

## Verdict

- Statut : RESEARCH_ONLY_NOT_TRADING
- Verdict production : NO_PRODUCTION_BACKTEST
- Meilleure stratégie : model_top20_confidence
- Trades meilleure stratégie : 25
- Hit rate meilleur cas : 0.760
- PnL moyen meilleur cas : 11.77 EUR/t
- Lecture : Relative signal survives simple costs in this exploratory protocol, but proxy data prevents production use.

## Protocole

- Horizon : H40 jours.
- Coût : 2.00 EUR/t par trade spread.
- Position : long EMA / short CBOT si EMA doit surperformer, inverse sinon.
- Exécution : proxy settlement-to-settlement, sans bid-ask ni liquidité historique.

## Résultats

| Stratégie | n | Hit rate | PnL total | PnL moyen | Profit factor | Max DD | Worst year | Turnover/an |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| model_all | 59 | 0.593 | 178.65 | 3.03 | 1.947 | -65.51 | 2019 | 4.7 |
| model_top20_confidence | 25 | 0.760 | 294.13 | 11.77 | 6.902 | -15.24 | 2020 | 2.2 |
| model_top40_confidence | 39 | 0.641 | 292.16 | 7.49 | 3.094 | -35.12 | 2020 | 3.1 |
| model_basis_extreme_filter | 31 | 0.613 | 218.75 | 7.06 | 3.037 | -32.67 | 2013 | 2.7 |
| model_top20_basis_extreme | 18 | 0.667 | 196.03 | 10.89 | 5.899 | -17.09 | 2020 | 1.6 |
| model_no_roll_risk | 38 | 0.500 | -36.29 | -0.96 | 0.817 | -100.26 | 2023 | 3.1 |
| basis_zscore_rule | 59 | 0.559 | 30.71 | 0.52 | 1.116 | -61.17 | 2019 | 4.7 |

## Limites

- Source EMA exploratoire/proxy.
- Coûts simplifiés ; pas de bid-ask historique, pas de profondeur de carnet, pas de slippage dynamique.
- Non-overlap approximatif sur jours de cotation, pas une simulation d'exécution réelle.
- Résultat utilisable pour prioriser la recherche, pas pour conclure à une stratégie tradable.
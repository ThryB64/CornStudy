# FINAL CORN STUDY CBOT EMA V5

> Synthese recherche : CBOT moteur mondial, Euronext EMA prime europeenne, basis comme driver central.

## Conclusion

- CBOT : `GLOBAL_MAIZE_DRIVER`
- EMA direction absolue : `NO_GO_AS_MAIN_TARGET`
- EMA/CBOT H40 : `PRIMARY_RESEARCH_SIGNAL`
- EMA/CBOT H90 : `PROMISING_RESEARCH_SIGNAL`
- Basis : `CENTRAL_ECONOMIC_DRIVER`
- Production : `NO_PRODUCTION_BACKTEST`

La conclusion ne change pas de cap : le signal exploitable cote Euronext n'est pas le prix brut EMA, mais la prime relative EMA/CBOT.

## Signaux principaux

| Signal | DA | AUC | Balanced acc | Top20 | Statut |
|---|---:|---:|---:|---:|---|
| relative H40 | 0.640 | 0.708 | 0.642 | 0.771 | PRIMARY_PRUDENT_HORIZON |
| relative H90 | 0.690 | 0.770 | N/A | 0.887 | PROMISING_NOT_FINAL |

## V5 nouvelles cibles

- Cibles testees : 24
- Cibles prometteuses : 9
- Meilleure cible : `y_rel_outperform_when_basis_extreme_h90`
- AUC : 0.881
- Balanced accuracy : 0.728
- Top20 DA : 0.912

Lecture : les meilleures nouvelles cibles sont des cibles conditionnelles de prime/basis, pas EMA brut.

## V5 croisements de donnees

- Meilleur overall : `y_rel_outperform_when_basis_extreme_h90` / `all_cross`
- AUC overall : 0.906
- Meilleur delta AUC vs base : 0.028
- Lecture : Cross-data interactions add meaningful OOF value for at least one premium target.

## V5 modele hierarchique

- Meilleur modele diagnostic : `cbot_only` H40
- AUC : 0.559
- Balanced accuracy : 0.545
- Lecture : The global CBOT component dominates absolute EMA direction in this diagnostic.

## Backtest recherche

- Statut : `RESEARCH_ONLY_NOT_TRADING`
- Production : `NO_PRODUCTION_BACKTEST`
- Signaux candidats : 48
- Meilleur PnL moyen : 11.044 EUR/t
- High-cost PnL moyen : 3.044 EUR/t

## Limites

- EMA absolute direction as main target
- EMA absolute price CQR as final result
- EMA volatility regime as primary target
- rare EU residual shock classification
- production trading claims on proxy EMA data

## Prochaine recherche

- European Premium Indicator V3 with V5 target/cross-data evidence
- season-specific premium models with train-only thresholds
- real EC MARS monthly parser and FranceAgriMer monthly balance data
- COMEXT import/export and Ukraine corridor/export features
- official/authorized Euronext EMA historical settlement validation
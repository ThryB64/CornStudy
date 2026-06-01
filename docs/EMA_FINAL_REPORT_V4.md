# EMA FINAL REPORT V4

> Rapport V4 : conclusion scientifique stabilisee et roadmap de validation stricte.

**Source EMA :** exploratoire_barchart_proxy  
**Verdict data :** NO_RELIABLE_PERIOD_ML  
**Verdict production :** NO_PRODUCTION_BACKTEST  
**Equation :** `EMA = CBOT + EUR/USD + basis europeen + residu EU`

## Conclusion V4

- EMA brut reste `NO_GO` comme cible principale.
- EMA relatif au CBOT devient le coeur de l'etude.
- H40 est l'horizon principal prudent.
- H90 est prometteur mais doit passer un stress test strict.
- Le basis est le driver economique central.
- Les backtests restent recherche uniquement.

## H40 Principal

- DA daily : 64.0%
- AUC daily : 0.708
- Balanced accuracy : 64.2%
- Top20 DA : 77.1%
- Weekly AUC : 0.728

## H90 Candidat

- DA daily : 69.0%
- AUC daily : 0.770
- Top20 DA : 88.7%
- Weekly AUC : 0.766
- Statut : PROMISING_NOT_FINAL

## Basis

- Top feature H40 : `ema_cbot_basis`
- Top feature H90 : `ema_cbot_basis`
- Interpretation : Le basis reste le driver le plus robuste de la performance relative EMA/CBOT.

## Saisonnalite

- H40 meilleure saison : `sep_nov_eu_harvest` AUC 0.868
- H90 meilleure saison : `sep_nov_eu_harvest` AUC 0.916

## Premium Indicator

- H40 best strategy : `ml_with_basis_extreme_filter`
- H90 best strategy : `combined_top40_confidence`
- Accuracy medium/high : 71.8%
- Coverage medium/high : 57.7%

## Backtest V2

- Statut : RESEARCH_ONLY_NOT_TRADING
- Production : NO_PRODUCTION_BACKTEST
- H90 cost 1 EUR/t/leg : 21 trades, PnL moyen 12.50 EUR/t
- H90 cost 5 EUR/t/leg : 21 trades, PnL moyen 4.50 EUR/t

## NO_GO

- EMA direction absolue
- volatilite EMA comme cible principale
- stockage EMA
- CQR prix absolu EMA
- prediction des chocs residuels rares

## Roadmap V4

- EMA-H90-01 stress test strict H90
- EMA-ERR-02 error archaeology H40/H90
- EMA-SEASON-02 seasonal premium regime study
- EMA-BT-03 relative spread backtest V3 execution-aware
- EU-DATA future tickets for MARS, FranceAgriMer, COMEXT, Ukraine, weather, TTF/EURUSD
- Notebook 06_relative_ema_cbot remains blocked until notebooks/ rule is lifted
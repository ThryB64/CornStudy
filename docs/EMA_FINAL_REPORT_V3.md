# EMA FINAL REPORT V3

> Pivot scientifique final : ne plus forcer EMA brut, et centrer l'etude sur la prime europeenne EMA/CBOT.

**Source EMA :** exploratoire_barchart_proxy  
**Verdict data :** NO_RELIABLE_PERIOD_ML  
**Equation directrice :** `EMA = CBOT + EUR/USD + basis europeen + residu EU`

## Verdict

- Ancienne question : Can we predict absolute EMA up/down? -> REJECTED_AS_MAIN_TARGET
- Nouvelle question : When is EMA expensive or cheap relative to CBOT, and can that premium correct? -> GO_RESEARCH_EXPLORATORY

## Resultat Principal

- Cible : `relative_ema_outperformance_h40`
- DA daily : 64.0%
- AUC daily : 0.708
- Balanced accuracy : 64.2%
- Top20 DA : 77.1%
- Weekly AUC : 0.728
- Lecture : EMA direction brute reste faible ; la prime relative EMA/CBOT porte le signal.

## H90

- Statut : PROMISING_BUT_NEEDS_STRESS_TEST
- DA daily : 69.0%
- AUC daily : 0.770
- Top20 DA : 88.7%
- Conclusion : H90 est prometteur, mais il reste candidat tant que les stress tests non-overlap/roll/crise/couts ne sont pas faits.

## Basis

- Statut : CENTRAL_DRIVER
- Meilleure baseline simple : `basis_z_rule`
- Balanced accuracy baseline : 64.4%
- Balanced accuracy modele : 64.2%
- Lecture : Le signal relatif existe, mais une regle simple de basis z-score capture deja beaucoup du signal.

## Abstention

- Meilleur filtre : `basis_extreme_only`
- Coverage : 23.1%
- DA : 76.8%
- Balanced accuracy : 76.1%

## Backtest Relatif

- Statut : RESEARCH_ONLY_NOT_TRADING
- Verdict production : NO_PRODUCTION_BACKTEST
- Strategie top20 : 25 trades, hit rate 76.0%, PnL moyen 11.77 EUR/t
- Lecture : Relative signal survives simple costs in this exploratory protocol, but proxy data prevents production use.

## NO_GO Maintenus

- `EMA direction absolue` : NO_GO — Direction brute H40 proche du hasard ; cible trop composite.
- `Volatilite EMA` : NO_GO — AUC proche de 0.51 ; a utiliser comme filtre de risque, pas cible principale.
- `Stockage EMA` : NO_GO — Module stockage non robuste et hors scope actuel.
- `CQR prix absolu EMA` : NO_GO — Intervalles prix absolus sous-calibres ; returns H20 seulement interessant globalement.

## Conclusion Officielle

- CBOT reste le moteur mondial du marche du mais.
- EMA brut ne doit plus etre la cible principale.
- Le resultat principal EMA est la performance relative EMA/CBOT.
- Le basis EMA/CBOT est la variable economique centrale de la prime europeenne.
- Le backtest relatif est prometteur mais strictement recherche, sans claim production.

## Suite

- EMA-NEXT-03 relative feature importance H40/H90
- EMA-NEXT-04 seasonal relative EMA/CBOT study
- EMA-PREM-01 ML vs basis z-score vs combined premium signal
- EMA-PREM-02 European Premium Indicator V2
- EMA-BT-01 realistic relative spread backtest V2
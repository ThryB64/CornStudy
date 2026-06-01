# EMA FINAL SYNTHESIS V3

> Synthese finale de recherche. Source EMA historique exploratoire/proxy ; aucun claim production ou trading reel.

## Verdict Central

L'etude Euronext ne doit plus chercher a forcer la prediction directe du prix EMA brut.

La conclusion scientifique V3 est :

- CBOT reste le moteur mondial du marche du mais.
- EMA est fortement lie au CBOT, mais sa direction brute est trop composite et bruitée.
- Le signal Euronext principal se trouve dans la performance relative EMA/CBOT.
- Le basis EMA/CBOT est le driver economique central de cette prime europeenne.
- Les backtests relatifs sont prometteurs, mais restent recherche uniquement.

Equation directrice :

```text
EMA = CBOT + EUR/USD + basis europeen + residu EU
```

## Resultats Validés En Recherche

### CBOT

Le CBOT reste la partie la plus mature :

- Horizon robuste principal : J+60.
- Signal directionnel modeste mais reel.
- Role dans l'etude EMA : moteur mondial et variable explicative centrale.

### EMA Absolu

La direction brute EMA reste `NO_GO` :

- H40 DA proche de 52%.
- AUC proche de 53%.
- Rolls, liquidite, basis, change et chocs EU diluent le signal.

Conclusion : EMA brut ne doit pas etre la cible principale.

### EMA Relatif Au CBOT

Resultat principal :

- `relative_ema_outperformance_h40`
- DA daily : 64.0%
- AUC daily : 0.708
- balanced accuracy : 64.2%
- top20 DA : 77.1%
- weekly AUC : 0.728

H90 est tres prometteur mais pas encore final :

- DA daily : 69.0%
- AUC daily : 0.770
- top20 DA : 88.7%
- besoin de stress tests : non-overlap strict, roll sensitivity, leave-one-crisis-out, couts de portage.

## Basis Et Prime Europeenne

Le basis est le coeur economique de l'etude.

Feature importance V3 :

- H40 top feature : `ema_cbot_basis`
- H90 top feature : `ema_cbot_basis`
- Permutation H40 du basis : AUC 0.708 -> 0.430
- Permutation H90 du basis : AUC 0.770 -> 0.452
- Ablation famille basis : AUC retombe vers 0.51

Conclusion :

Le signal relatif EMA/CBOT existe, mais il est massivement porte par la structure du basis.

## Saisonnalite

La prime relative n'est pas uniforme toute l'annee.

H40 :

- meilleure saison : recolte Europe septembre-novembre
- AUC : 0.868
- DA : 80.8%
- ete stress rendement : AUC 0.865, DA 81.2%
- saison fragile : avril-juin, AUC 0.503

H90 :

- recolte Europe AUC : 0.916
- DA : 84.2%

Conclusion :

La saison doit devenir un filtre de confiance de l'indicateur premium.

## Indicateur European Premium V2

L'indicateur produit une lecture relative :

- `EU_PREMIUM_BULLISH` : EMA devrait surperformer CBOT.
- `EU_PREMIUM_BEARISH` : EMA devrait sous-performer CBOT.
- `NEUTRAL` : pas de signal relatif fort.
- `UNCERTAIN` : abstention.

Il ne signifie jamais "EMA monte" ou "EMA baisse" en absolu.

Historique indicateur :

- 2358 signaux.
- accuracy tous signaux : 63.9%.
- coverage medium/high : 57.7%.
- accuracy medium/high : 71.8%.

Snapshot recent exploitable :

- date : 2025-03-07
- signal : `NEUTRAL`
- confidence : `low`
- premium score : 0.410
- basis : 48.32 EUR/t
- z-score : 0.127

## Backtests Relatifs

Backtest V1 :

- meilleur signal : `model_top20_confidence`
- 25 trades
- hit rate : 76.0%
- PnL moyen net : 11.77 EUR/t
- statut : `RESEARCH_ONLY_NOT_TRADING`

Backtest V2 :

- protocole weekly vendredi, non-overlap strict.
- stress couts : 1, 2, 3, 5 EUR/t par leg.
- meilleure strategie : `h90_combined_top40_weekly`
- 21 trades.

A 1 EUR/t par leg :

- hit rate : 80.95%
- PnL moyen : 12.50 EUR/t
- PnL total : 262.58 EUR/t
- profit factor : 10.36

A 5 EUR/t par leg :

- hit rate : 57.14%
- PnL moyen : 4.50 EUR/t
- PnL total : 94.58 EUR/t
- profit factor : 2.22
- positive year share : 46.2%

Conclusion :

Le signal relatif selectif survit a des couts simplifiés eleves, mais le backtest reste trop exploratoire pour conclure a une strategie tradable.

## NO_GO Maintenus

Les resultats suivants ne doivent pas etre vendus comme signaux :

- EMA direction absolue.
- volatilite EMA.
- stockage EMA.
- CQR prix absolu EMA.
- prediction de chocs residuels rares.

Ces modules restent utiles comme contexte, filtres ou diagnostic, mais pas comme cible principale.

## Limites Non Negociables

- Source EMA historique proxy/exploratoire.
- Verdict data : `NO_RELIABLE_PERIOD_ML`.
- Courbe Euronext partielle.
- Pas de bid-ask historique.
- Pas de profondeur de carnet.
- Pas de vraie simulation de roll execution.
- Pas de sizing, marge, change ou risque operationnel.
- Pas de claim production.

## Conclusion Finale

L'etude n'est pas faible.

Elle a montre que la mauvaise question etait :

```text
EMA va-t-il monter ?
```

La bonne question est :

```text
EMA est-il cher ou bon marche par rapport au CBOT,
et cette prime europeenne va-t-elle se corriger ou persister ?
```

La suite professionnelle consiste donc a renforcer :

- la source EMA officielle,
- les donnees europeennes,
- l'indicateur European Premium,
- les stress tests H90,
- les backtests relatifs avec execution realiste.

Le coeur de l'etude V3 est maintenant clair :

```text
Comprendre et predire la prime europeenne EMA/CBOT.
```

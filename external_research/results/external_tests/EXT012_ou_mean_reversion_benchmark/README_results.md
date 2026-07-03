# EXT012 — OU mean-reversion benchmark

**Verdict : DATA_BLOCKED.** Non lancé (aucun test artificiel).

## Pourquoi bloqué
Le processus d'Ornstein-Uhlenbeck est pertinent pour une série **stationnaire à retour à
la moyenne** : chez nous, c'est le **basis** (demi-vie ~17-47 j, V10/V138) ou un **spread
de courbe**. Or :
- **EXT013 (basis) = DATA_BLOCKED** : pas d'EUR/USD quotidien historique ni de spot UE
  quotidien → le basis €/t homogène n'est pas reconstructible en externe.
- **EXT005 (courbe) = DATA_BLOCKED** : pas de contrats CBOT par maturité ; courbe EMA
  accumulée ~2 semaines seulement → pas de spread exploitable.

Calibrer un OU sur le **prix CBOT** lui-même n'a pas de sens (le prix n'est pas
stationnaire) et reviendrait à fabriquer un signal sur une donnée inadaptée.

## Données nécessaires pour rouvrir
1. EUR/USD quotidien historique (FRED DEXUSEU / ECB SDW) → basis €/t reconstructible.
2. Idéalement un spot physique UE quotidien/hebdo (FranceAgriMer, Bologne).
3. Ou des contrats CBOT par maturité → spreads de courbe stationnaires.

## Pourquoi ne pas simuler un basis absent
Fabriquer un basis à partir d'hypothèses (taux de change moyen, proxy de spot) introduirait
des artefacts et un risque de fuite (choix calés sur l'échantillon). Le programme externe
est une démarche de preuve : on documente le blocage, on ne simule pas une donnée manquante.

À rouvrir après acquisition de l'EUR/USD quotidien (préalable commun avec EXT013/EXT025-basis).

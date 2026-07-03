---
id: PAPER015
source_type: paper
title: Measuring Price Discovery between Nearby and Deferred Contracts
priority: very_high
status: analyzed_2026-06-12
note: Hu, Mallory, Serra, Garcia (2020). Doublon découvert à fusionner (même papier, slug long).
---
# Price discovery nearby vs deferred (Hu, Mallory, Serra, Garcia 2020)

## 1. Référence

Hu, Z., Mallory, M., Serra, T., Garcia, P. (2020). Measuring price discovery between nearby and deferred contracts in storable and nonstorable commodity futures markets. (Agricultural Economics / J. Futures Markets — à confirmer.)

## 2. Sujet

Où se forme le prix le long de la courbe : le nearby domine-t-il la découverte de prix, et est-ce différent pour les commodities stockables (corn) vs non stockables (bétail) ?

## 3. Données

Contrats nearby et différés corn (stockable) et bétail/non-stockables, haute fréquence ou quotidien, mesures de part informationnelle (Hasbrouck IS / Gonzalo-Granger).

## 4. Méthode

Cointégration entre contrats de maturités différentes + décomposition de la part de découverte de prix par maturité.

## 5. Résultats importants

- Pour les STOCKABLES (corn) : nearby et différés sont liés par le stockage, la découverte de prix est largement partagée mais le **nearby porte généralement la part dominante** ; les chocs se transmettent le long de la courbe.
- Pour les non-stockables : les contrats sont plus segmentés (chaque maturité price son propre équilibre offre/demande).

## 6. Apport pour notre étude

- Justifie l'usage du NEARBY CBOT comme référence de notre basis (ce que nous faisons), MAIS indique que le spread nearby-deferred contient l'info de stockage — exactement la dimension courbe que V125 (NARROWING) capture qualitativement et que EXT005 doit quantifier.
- **Feature** : part du mouvement initiée par le déféré (quand le déféré bouge avant le nearby = info sur la nouvelle récolte) — version simplifiée quotidienne : corrélation roulante des retours nearby vs déféré et leur lead-lag.

## 7. Hypothèses testables

- H1 (EXT005) : le spread nearby−déféré CBOT (z expandant, normalisé par le full carry) prédit-il le retour du nearby H20-H60 ? (Théorie du stockage : spread serré = stocks serrés = backwardation = signal haussier nearby.)
- H2 : le lead-lag nearby/déféré change-t-il en saison de récolte (old crop/new crop) → variable de régime pour EXT017 ?

## 8. Risques et limites

Mesures de découverte de prix exigent de la haute fréquence (nous : quotidien → proxys grossiers) ; le papier établit la structure, pas un signal de trading ; nos données contrats CBOT doivent être propres (dépend EXT006).

## 9. EXT associées

EXT005 (principal), EXT034, EXT006, EXT017.

## 10. Conclusion

**Priorité très haute** — fonde théoriquement EXT005 ; à lire avec PriceAnalysis ch. 9 (full carry).

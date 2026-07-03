---
id: what-do-we-know-about-the-accuracy-and-impact-of-usda-reports-relevant-to-the-corn-market
source_type: paper
title: What Do We Know About the Accuracy and Impact of USDA Reports Relevant to the Corn Market?
priority: high
status: analyzed_2026-06-12
---
# What Do We Know About the Accuracy and Impact of USDA Reports (Corn)?

## 1. Référence

Isengildina-Massa, O., Irwin, S.H., Sanders, D.R., Good, D.L. (2022). Rapport pour la National Corn Growers Association. (Score discovery 0.89.)

## 2. Sujet

Synthèse de plusieurs décennies de recherche : quels rapports USDA sont précis, lesquels bougent le marché du maïs, et comment leur impact a évolué.

## 3. Données

Revue de littérature + évaluations empiriques : WASDE, NASS Crop Production, Grain Stocks, Prospective Plantings, Acreage, Crop Progress, Export Sales.

## 4. Méthode

Méta-revue : précision des prévisions (biais, erreurs), impact de marché (études d'événement), hiérarchisation par famille de rapport.

## 5. Résultats importants

- Hiérarchie d'impact typique sur le corn : **Grain Stocks (janvier surtout) et Acreage/Prospective Plantings > WASDE/Crop Production d'été-automne > rapports d'hiver** ; Crop Progress hebdo = impact plus faible mais récurrent.
- Les rapports restent market-moving malgré l'information privée ; certains biais saisonniers de prévision USDA documentés.

## 6. Apport pour notre étude

- **Filtre d'effort** : exactement l'objet de EXT032 — ne pas construire de features pour les familles de rapports sans impact ; commencer par Grain Stocks + WASDE août-nov + Prospective Plantings (mars) / Acreage (juin).
- **Calendrier enrichi** : notre veto WASDE V9 ignore Grain Stocks et Acreage — les jours à forte vol ne sont pas que les WASDE.

## 7. Hypothèses testables

- H1 : classer NOS épisodes de compression V129/V143 par famille de rapport déclencheur élargie (Grain Stocks/Acreage ajoutés) — l'UNKNOWN de 10 % diminue-t-il ?
- H2 : la vol réalisée CBOT des jours Grain Stocks de janvier > jours WASDE moyens (réplication rapide qui valide l'élargissement du calendrier).

## 8. Risques et limites

Rapport commandité (NCGA) — orientation politique possible sur la valeur de l'USDA ; synthèse US-centrée ; rien sur la prime EMA.

## 9. EXT associées

EXT032 (principal), EXT007, EXT026.

## 10. Conclusion

**Priorité haute** — c'est le filtre qui rend le bloc événements économe : à lire avant de coder EXT007.

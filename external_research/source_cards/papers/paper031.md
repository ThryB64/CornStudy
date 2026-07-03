---
id: PAPER031
source_type: paper
title: Analysis of Agricultural Commodities Prices with New Bayesian Model Combination Schemes
priority: high
status: analyzed_2026-06-12
note: Drachal (Energies/Sustainability, ~2019-2021) — lignée DMA/BMA sur commodities. À confirmer.
---
# Combinaisons bayésiennes DMA/BMA pour prix agricoles (Drachal)

## 1. Référence

Drachal, K. (~2019-2021). Combinaisons bayésiennes (Dynamic Model Averaging / Bayesian Model Averaging) appliquées aux prix de commodities agricoles.

## 2. Sujet

Quand on a beaucoup de prédicteurs candidats et de l'instabilité de régime, la combinaison dynamique de petits modèles (poids réestimés séquentiellement) bat-elle un grand modèle unique et les baselines naïves ?

## 3. Données

Prix mensuels de commodities agricoles (corn inclus), nombreux prédicteurs macro/marché, plusieurs décennies.

## 4. Méthode

DMA : à chaque date, des poids de probabilité sur 2^K combinaisons de prédicteurs sont mis à jour séquentiellement (filtre avec facteur d'oubli) — par construction quasi anti-fuite (séquentiel pur). Comparaison à ARIMA, naïf, TVP.

## 5. Résultats importants

- DMA est compétitif mais les gains vs naïf restent MODESTES sur les agricoles ; l'intérêt principal est l'« inclusion probability » des variables au cours du temps : QUELS prédicteurs comptent QUAND.
- Les variables importantes changent selon les régimes (énergie post-2006, FX en crise...) — confirmation indépendante que les relations macro sont instables.

## 6. Apport pour notre étude

- L'inclusion probability séquentielle est un OUTIL DE DIAGNOSTIC : appliquée à nos familles de features (basis_z, saison, courbe, météo), elle dirait quand chaque famille est informative — utile pour V124 (santé du signal) sans rien changer au modèle.
- Cohérent avec V11 : un grand modèle unique perd contre des petits modèles bien choisis.

## 7. Hypothèses testables

- H1 (EXT014) : DMA sur direction CBOT H20 avec nos prédicteurs OOF existants : bat-il (a) le RW, (b) notre logistique 2 vars ? Verdict honnête attendu : difficile, mais l'inclusion probability vaut le test à elle seule.
- H2 : DMA sur le basis_change H40 : la probabilité d'inclusion de la famille « saison » monte-t-elle en avril-juin (cohérence avec nos découvertes V9/V11) ?

## 8. Risques et limites

Mensuel vs notre quotidien (adapter le facteur d'oubli) ; 2^K explose vite (limiter aux familles, pas aux features) ; le gain de prévision pure sera probablement marginal — vendre l'EXT comme diagnostic, pas comme nouveau modèle.

## 9. EXT associées

EXT014 (principal), EXT017 (régimes via poids), EXT015.

## 10. Conclusion

**Priorité haute** (bloc 3) : valeur diagnostique > valeur prédictive ; à lancer après les blocs fondamentaux.

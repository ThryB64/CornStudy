---
id: REPO003
source_type: repository
title: mindymallory/PriceAnalysis
priority: very_high
status: analyzed_2026-06-12
---
# mindymallory/PriceAnalysis

## 1. Identification

- URL : https://github.com/mindymallory/PriceAnalysis — propriétaire : Mindy Mallory (Purdue, ag economics)
- Licence : **absente** → idées et méthodes réutilisables, copie de contenu interdite
- État local : clone sparse partiel (checkout complet échoué) ; 12 qmd sur 22+ chapitres ; livre Quarto daté 2023-12-21
- Langage : Quarto/R (livre de cours, pas une librairie)
- Fichiers importants : `09-PricesSpaceTime.qmd` (courbe forward, full carry, calendar spreads, basis), `10-FundamentalAnalysisand.qmd` (balance sheet), `13-ForecastingUseof.qmd` (usage du maïs), `15-EndingStocksand.qmd` (stocks→prix), `17-EthanolMarketsand.qmd` (éthanol/DDG/crush/cross-hedge), `22-IntroductiontoCommodityTS.qmd` (nearby, roll, EMH), `references.bib`, xlsx d'exercices

## 2. Objectif

Manuel complet d'analyse fondamentale des prix agricoles : stockage, courbe forward, basis, balance sheet USDA, éthanol, hedging, séries temporelles. Cadre conceptuel de référence pour notre étude basis/prime.

## 3. Données utilisées

USDA WASDE/balance sheet (illustratif), futures CBOT, prix éthanol/DDG/gaz, xlsx d'exercices (corn food-alcohol-ind use). Pas de pipeline de données réel.

## 4. Cible prédite

Aucune (pédagogique). Ch. 15 : relation stocks-to-use → prix moyen de campagne ; ch. 13 : forecast des catégories d'usage.

## 5. Horizons

Campagne de commercialisation (mensuel→annuel) ; calendar spreads intra-campagne.

## 6. Modèles

Régressions simples (stocks/use vs prix), comptabilité balance sheet, ratio de hedge variance-minimale (cross-hedge DDG↔corn futures). Pas de ML.

## 7. Méthode d'évaluation

Aucune évaluation OOF — manuel. Risque réel pour nous : prendre les relations in-sample (stocks→prix) comme prédictives sans test.

## 8. Risques de fuite

Le piège que le livre permet d'identifier : la balance sheet est révisée — utiliser les valeurs WASDE du mois de publication, pas les valeurs révisées (anti_leak_rules n°4). Ch. 22 : construire le nearby proprement AVANT toute analyse, sinon artefacts de roll dans tous les résultats.

## 9. Réutilisable

- **Idée économique** : full carry financier = borne du contango ; basis = transport+stockage+prime locale ; crush éthanol = marge de demande ; stocks-to-use → prix (relation convexe).
- **Méthode** : hedge variance-minimale ; lecture bullish/bearish des calendar spreads ; règle de roll volume takeover (ch. 22).
- **Métrique** : prix d'équilibre par stocks-to-use comme baseline économique simple.

## 10. Faible / inutilisable

Pas de code exécutable, pas de données propres, US-centré (notre basis EMA est une prime LOCALE — V16 — transposer avec prudence), chapitres options absents du clone.

## 11. Hypothèses testables

- H1 : le stocks-to-use US (WASDE, daté publication réelle) en niveau et en surprise vs mois précédent améliore la direction CBOT H20-H90 vs baseline prix seul.
- H2 : la distance du spread nearby-deferred CBOT au full carry financier (taux + coût stockage estimé ex ante) prédit le resserrement de la courbe à H20-H60.
- H3 : le crush éthanol (ethanol + DDG − corn − gaz, lags de publication EIA/USDA respectés) améliore le flag ADVERSE H20-H90.

## 12. EXT associées

EXT004 (crush), EXT005 (courbe/carry), EXT006 (roll), EXT013 (basis), EXT024 (balance sheet), EXT025 (discipline baseline).

## 13. Conclusion

**À utiliser immédiatement comme cadre** (pas comme code) : grammaire économique de nos EXT fondamentaux. Lecture ch. 9→15→17→22 en premier.

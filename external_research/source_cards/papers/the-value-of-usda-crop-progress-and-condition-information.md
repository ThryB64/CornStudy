---
id: the-value-of-usda-crop-progress-and-condition-information
source_type: paper
title: The Value of USDA Crop Progress and Condition Information
priority: very_high
status: analyzed_2026-06-12
---
# The Value of USDA Crop Progress and Condition Information (Lehecka 2014)

## 1. Référence

Lehecka, G.V. (2014). Journal of Agricultural and Resource Economics 39(1). (Score discovery 0.92 — la meilleure source du bloc crop progress.)

## 2. Sujet

Les rapports hebdomadaires NASS Crop Progress & Condition (publiés le lundi ~16h ET pendant la saison) contiennent-ils de l'information valorisée par les futures corn/soy ?

## 3. Données

Notations hebdomadaires good/excellent (et progression des semis/récolte) par État et national ; retours des futures corn/soy autour du lundi de publication ; saison de croissance, multi-années.

## 4. Méthode

Étude d'événement hebdomadaire : surprise = variation des notations vs attente (modèle naïf : pas de changement, ou tendance climatologique) ; réaction des prix mardi à l'ouverture/clôture.

## 5. Résultats importants

- Le marché RÉAGIT significativement aux surprises de condition, surtout **juillet-août** (pollinisation = sensibilité rendement maximale).
- La réaction est asymétrique : détériorations inattendues > améliorations.
- L'information est rapidement incorporée (le mardi) — pas de drift exploitable long.

## 6. Apport pour notre étude

- **Feature** : surprise hebdo de condition = Δ(good+excellent) − attente saisonnière train-only, par État pondéré production, datée du lundi soir (disponible mardi chez nous). Publique, gratuite, hebdomadaire — la meilleure donnée de saison de croissance non encore exploitée par notre étude.
- **Anti-fuite** : climatologie d'attente estimée en expandant ; timing lundi 16h ET → utilisable à J+1.
- Complète V45 : la météo réalisée est pricée par anticipation ; la condition NOTÉE est l'agrégateur officiel de cette anticipation.

## 7. Hypothèses testables

- H1 : surprise de condition corn (z expandant, asymétrique) → direction CBOT H5-H20 en juillet-août vs baseline RW (cœur de EXT027).
- H2 : détérioration cumulée sur 3 semaines = proxy de « stress d'été » → la prime EMA devient moins compressible (réplication interne de V45-stress avec une donnée datée proprement).

## 8. Risques et limites

Réaction concentrée le mardi (peu de drift) → l'edge directionnel H5+ peut être nul ; saisonnier (mai-octobre seulement) ; US-centré ; notre test doit éviter le sur-apprentissage sur ~20 semaines/an.

## 9. EXT associées

EXT027 (principal), EXT019 (qu'il raffine — fusion recommandée), EXT020, EXT001.

## 10. Conclusion

**Priorité très haute** — la source la plus actionnable du bloc météo/saison : donnée publique datée, mécanisme prouvé, feature claire.

---
id: PAPER003
source_type: paper
title: The Impact of Public Information on Commodity Market Performance
priority: very_high
status: analyzed_2026-06-12
note: PDF non disponible localement — analyse fondée sur la littérature publiée ; chiffres à vérifier sur le texte original avant citation.
---
# The Impact of Public Information on Commodity Market Performance

## 1. Référence

Rapport institutionnel USDA ERS (auteurs Arnade/Hoffman et coll., ~2015-2018 — référence exacte à confirmer). Sujet : réponse des corn futures aux prévisions de production de maïs USDA.

## 2. Sujet

L'information publique USDA (prévisions de production NASS/WASDE) a-t-elle encore de la valeur de marché : les futures réagissent-ils aux surprises, et l'information privée (analystes) a-t-elle érodé ce rôle ?

## 3. Données

Corn futures CBOT quotidiens, prévisions de production USDA (août-novembre), attentes d'analystes pré-rapport (enquêtes Reuters/Bloomberg) pour mesurer la surprise. Période multi-décennies.

## 4. Méthode

Étude d'événement : réaction des prix au jour de rapport en fonction de la surprise (publication − attente médiane des analystes), régressions de la variation de prix sur la surprise normalisée.

## 5. Résultats importants

- Les futures réagissent significativement aux surprises de production ; la réaction est proportionnelle à la taille de la surprise.
- L'information USDA garde de la valeur malgré la concurrence privée (satellite, scouts) — le marché ne price pas tout à l'avance.
- La réaction est concentrée le jour du rapport (efficience semi-forte rapide).

## 6. Apport pour notre étude

- **Features** : la surprise (vs attentes) est LA variable, pas la valeur publiée seule. Sans enquêtes d'analystes historiques, proxy possible : surprise = publication M − publication M-1 (EXT008).
- **Protocole** : fenêtres event-day [J, J+1] vs fenêtres de fond — sépare l'effet annonce du drift.
- **Anti-fuite** : tout est daté à la publication réelle (calendrier USDA connu à l'avance).

## 7. Hypothèses testables

- H1 : |surprise| de production (proxy M−M-1, z expandant) le jour du rapport → amplitude du retour CBOT [J, J+5] supérieure aux jours sans rapport (étalonnage de EXT007).
- H2 : le SIGNE de la surprise prédit le signe du retour [J, J+1] (baseline directionnelle event-day).

## 8. Risques et limites

Pré-période électronique partiellement ; effet intraday (minutes) non capturable avec nos données quotidiennes — nous mesurons l'effet J→J+1 seulement ; attentes d'analystes historiques difficiles à sourcer (d'où le proxy).

## 9. EXT associées

EXT007 (principal), EXT008, EXT032.

## 10. Conclusion

**Priorité très haute** — fonde la conception event-day de EXT007 et la définition de surprise de EXT008.

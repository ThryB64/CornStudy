---
id: PATENT007
source_type: patent
title: US9087312B1 - Drying, weather, moisture and storage costs
priority: medium_high
status: analyzed_2026-06-12 (analyse sur métadonnées — texte complet à récupérer via Google Patents si l'idée passe en EXT)
---
# US9087312B1 — Séchage, humidité, météo et coûts de stockage

## 1. Référence

Brevet US9087312B1. Modélisation des coûts de séchage/humidité/stockage des grains en fonction de la météo.

## 2. Sujet / idée économique

Le coût réel de stockage du maïs n'est pas constant : il dépend de l'humidité de récolte (coût de séchage, gaz propane/naturel) et des conditions météo de conservation. Or le coût de stockage est LE paramètre de la théorie du stockage (full carry, contango maximal, V13/V30).

## 3. Idée de feature

Coût de carry VARIABLE dans le temps : full carry = taux d'intérêt + stockage(t) où stockage(t) dépend de (a) prix de l'énergie de séchage, (b) humidité de la récolte de l'année (publiée par USDA/universités d'État à la récolte). Notre full carry actuel (si EXT005 le construit avec un coût fixe) serait mal calibré les années de récolte humide.

## 4. Idée de modèle / évaluation

Aucun modèle — paramétrage économique. Évaluation indirecte : la distance au full carry CORRIGÉ du coût variable explique-t-elle mieux les spreads que le full carry naïf (EXT005) ?

## 5. Limites

Brevet = revendications système, peu de données ; l'effet est probablement de second ordre au quotidien ; séries d'humidité de récolte à sourcer (qualité incertaine).

## 6. Risque de fuite

Faible si les coûts énergie/humidité sont datés correctement (énergie quotidienne OK ; humidité = donnée de récolte annuelle, disponible à partir de novembre).

## 7. EXT associées

EXT005 (raffinement du full carry), EXT031.

## 8. Conclusion

**Garder pour plus tard** : enrichissement de EXT005 en phase 2 de l'expérience, pas un EXT autonome. Priorité moyenne-haute conceptuelle, basse opérationnelle.

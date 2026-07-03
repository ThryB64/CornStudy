---
id: PAPER008
source_type: paper
title: The Weather Risk Premium in New-Crop Corn Futures Prices
priority: very_high
status: analyzed_2026-06-12
note: Article farmdoc daily (Janzen, ~2023) — accessible en ligne, à relire avant chiffrage.
---
# The Weather Risk Premium in New-Crop Corn Futures Prices (Janzen)

## 1. Référence

Janzen, J. (~2023). farmdoc daily, University of Illinois. Article de vulgarisation académique, complément actualisé de PAPER007.

## 2. Sujet

Quantification simple et actuelle de la prime de risque météo dans le décembre corn : de combien le contrat new-crop baisse-t-il en moyenne entre le printemps et la récolte, et que cela implique-t-il pour la commercialisation ?

## 3. Données

Contrats décembre corn, trajectoires saisonnières moyennes sur les dernières décennies, distinction années à choc.

## 4. Méthode

Statistiques descriptives saisonnières (prix moyen par mois du contrat décembre, fréquence des années où le pic de printemps > prix de récolte).

## 5. Résultats importants

- La majorité des années, le prix de printemps du décembre dépasse le prix de récolte (prime qui se dissipe) ; l'ampleur moyenne est de l'ordre de quelques pour cent (chiffre exact à vérifier sur l'article).
- Implication producteur : vendre tôt capture la prime en moyenne — mais s'expose aux années de spike.

## 6. Apport pour notre étude

- Version simple et reproductible de EXT018 : la stat descriptive de Janzen est notre test de validation avant tout modèle.
- Donne le cadre « assurance » à notre machine d'état (PRIME_JUSTIFIED vs EXCESSIVE) côté CBOT.

## 7. Hypothèses testables

- H1 : répliquer la trajectoire saisonnière moyenne du décembre corn sur nos données contrats (V24 : H/K/N/U/Z disponibles) — fréquence des années « prime dissipée » vs « spike », avec années classées ex ante.
- H2 : conditionner H1 au stocks-to-use de départ (WASDE de mai, daté publication) : la prime est-elle plus grosse quand les stocks sont serrés ?

## 8. Risques et limites

Descriptif (pas de test statistique dur) ; moyenne masque l'asymétrie ; pas directement notre prime EMA.

## 9. EXT associées

EXT018 (principal), EXT025 (la trajectoire saisonnière moyenne est une baseline en soi).

## 10. Conclusion

**Priorité très haute** comme POINT D'ENTRÉE de EXT018 (réplication descriptive d'abord, modèle ensuite).

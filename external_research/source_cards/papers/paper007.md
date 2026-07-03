---
id: PAPER007
source_type: paper
title: The weather premium in the U.S. corn market
priority: very_high
status: analyzed_2026-06-12
note: PDF non disponible localement — Li, Hayes, Jacobs (~2017-2018, Journal of Futures Markets, à confirmer). Doublon découvert (2018) à fusionner.
---
# The weather premium in the U.S. corn market (Li, Hayes, Jacobs)

## 1. Référence

Li, Z., Hayes, D.J., Jacobs, K.L. (~2018). The weather premium in the U.S. corn market. Journal of Futures Markets (à confirmer).

## 2. Sujet

Les futures new-crop (décembre) intègrent-ils une prime de risque météo : un prix systématiquement au-dessus de l'attente rationnelle pendant la période où le rendement est encore incertain, qui se dissipe après la pollinisation ?

## 3. Données

Futures corn décembre (new-crop), plusieurs décennies ; trajectoires printemps→récolte ; années de drought vs normales ; éventuellement options (skew) pour la demande d'assurance.

## 4. Méthode

Comparaison systématique du prix de printemps/été du contrat décembre à son prix de récolte ; décomposition années normales vs années à événement météo ; lien avec la demande de couverture des acheteurs (assurance contre le spike).

## 5. Résultats importants

- En années SANS événement météo majeur, le contrat décembre **décline en moyenne du printemps à la récolte** : il existe une prime météo positive qui se désintègre si le risque ne se matérialise pas.
- La prime compense les vendeurs (shorts) qui portent le risque de spike ; elle est concentrée mai→août (pollinisation).
- En années de drought, le spike domine largement la prime (asymétrie : petite prime fréquente vs grosse perte rare).

## 6. Apport pour notre étude

- **Analogie structurelle directe avec notre objet** : notre prime EMA est aussi une assurance qui se dissipe (compression) sauf événement (ADVERSE). Le mécanisme « short la prime, perdre sur le spike » est exactement notre profil V13-V15 (hit 0.83, pertes = chemins ADVERSE).
- **Feature** : position dans le calendrier de risque US (pré/post pollinisation) comme variable de contexte du CBOT — déjà partiellement chez nous via la saison, mais ancrée ici sur le contrat DÉCEMBRE, pas le nearby.

## 7. Hypothèses testables

- H1 : réplication directe EXT018 : le retour moyen du contrat Z (décembre) de mai à novembre est-il négatif hors années de stress (définies ex ante par l'indice de condition de juillet) sur 2000-2023, net de coûts ?
- H2 : la prime météo CBOT (prix Z − attente) et notre prime EMA sont-elles corrélées en été ? Si oui, une partie de notre « prime locale » V16 serait en fait une prime météo US importée — test descriptif important.

## 8. Risques et limites

Le short systématique de la prime = stratégie à pertes rares mais énormes (2012) — l'espérance peut être positive et la stratégie invendable ; périodes drought rares = inférence fragile ; mapping contrat décembre obligatoire (pas le nearby).

## 9. EXT associées

EXT018 (principal), EXT020, EXT005 (le décembre vs nearby est un spread de courbe).

## 10. Conclusion

**Priorité très haute** — le parallèle conceptuel le plus riche avec notre étude de prime ; EXT018 est une réplication peu coûteuse à fort rendement explicatif.

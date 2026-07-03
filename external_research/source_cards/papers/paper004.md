---
id: PAPER004
source_type: paper
title: Impact of WASDE and NASS reports on corn and soybean futures
priority: very_high
status: analyzed_2026-06-12
note: PDF non disponible localement — analyse fondée sur la littérature publiée (Isengildina-Massa, Irwin, Good, Gomez, ~2008, J. of Agricultural and Applied Economics) ; à vérifier avant citation.
---
# Impact des rapports WASDE et NASS sur corn et soybean futures

## 1. Référence

Isengildina-Massa, O., Irwin, S., Good, D., Gomez, J. (~2008). Impact des rapports WASDE/NASS sur les futures corn/soy. Journal of Agricultural and Applied Economics (à confirmer).

## 2. Sujet

Mesurer l'effet des publications WASDE et des rapports de production NASS sur les prix et la volatilité des futures corn/soy : les rapports bougent-ils encore les marchés, et lesquels ?

## 3. Données

Futures corn/soy CBOT, dates de publication WASDE et NASS Crop Production (souvent publiés le même jour), variances/retours autour des jours de rapport, années 1985-2000s.

## 4. Méthode

Étude d'événement sur la volatilité (variance le jour de rapport vs jours normaux) et sur les retours ; distinction WASDE seul vs WASDE+Crop Production conjoints.

## 5. Résultats importants

- La volatilité des futures corn est significativement plus élevée les jours WASDE — surtout quand WASDE et Crop Production sortent ensemble (août-novembre).
- L'effet varie selon la saison : rapports d'été/automne (incertitude de récolte) > rapports d'hiver.
- L'effet persiste dans le temps : pas d'érosion complète par l'information privée.

## 6. Apport pour notre étude

- **Feature calendaire robuste** : dummy `jour_WASDE` et `jour_WASDE+CropProduction`, et surtout l'interaction avec la SAISON (rapports août-nov = plus gros mouvements). Zéro fuite : calendrier connu à l'avance.
- **Gestion du risque** : nos vetoes V9 incluent déjà un veto WASDE ; ce papier justifie de le moduler par mois (veto fort août-nov, faible hiver).
- Cohérent avec notre V143 (catalyseur CBOT_WASDE 6 épisodes).

## 7. Hypothèses testables

- H1 : la vol réalisée CBOT [J, J+1] des jours WASDE d'août-nov > celle des WASDE d'hiver (réplication simple, étalonne EXT007 avant toute feature directionnelle).
- H2 : pour la prime EMA : les épisodes de compression débutant un jour WASDE ont-ils une demi-vie différente (lien V130/V143) ?

## 8. Risques et limites

Période d'étude ancienne (pré-HFT) ; effets intraday non observables chez nous ; corn US ≠ prime EMA (V18 : WASDE NO_GO sur la prime — ce papier concerne le CBOT, pas la prime, distinction à maintenir).

## 9. EXT associées

EXT007 (principal), EXT032, EXT009 (vol event-day).

## 10. Conclusion

**Priorité très haute** pour le volet CBOT (PROJET2) ; rappel : déjà falsifié pour la prime EMA elle-même (V18).

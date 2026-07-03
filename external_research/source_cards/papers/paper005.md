---
id: PAPER005
source_type: paper
title: The Value of USDA Announcements in the Electronically Traded Corn Futures Market
priority: very_high
status: analyzed_2026-06-12
note: PDF non disponible localement — attribution Huang, Serra, Garcia (seed) ; détails à vérifier avant citation.
---
# The Value of USDA Announcements in the Electronically Traded Corn Futures Market

## 1. Référence

Huang, J., Serra, T., Garcia, P. (~2020). Valeur économique des annonces USDA dans le corn électronique. Revue à confirmer.

## 2. Sujet

À l'ère du trading électronique 24h et de l'information privée abondante, les annonces USDA (WASDE, Grain Stocks, Prospective Plantings) créent-elles encore de la valeur informationnelle mesurable dans le corn ?

## 3. Données

Corn futures électroniques (Globex) haute fréquence autour des annonces, surprises vs attentes d'analystes, période récente (2010s).

## 4. Méthode

Étude d'événement haute fréquence : ajustement des prix dans les minutes suivant l'annonce, valeur de l'information mesurée par l'ampleur et la vitesse de l'ajustement, en fonction de la surprise.

## 5. Résultats importants

- L'ajustement aux surprises USDA est quasi immédiat (minutes) mais l'ANNONCE reste un événement informationnel majeur — la valeur n'a pas disparu avec l'électronique.
- Grain Stocks et WASDE produisent les plus gros ajustements ; les surprises sont le déclencheur, pas la publication en soi.

## 6. Apport pour notre étude

- **Réalisme** : en données quotidiennes, tout l'ajustement est DANS la clôture du jour J → aucune stratégie quotidienne ne peut « trader l'annonce » ; ce qui reste testable : les effets de fond post-annonce (drift J+1→J+20, changement de régime de vol).
- **Gestion du risque** : confirme le veto event-day (ne pas ouvrir de position la veille d'un WASDE quand le signal est marginal).

## 7. Hypothèses testables

- H1 : drift directionnel post-rapport : le signe du retour du jour WASDE prédit-il le retour J+1→J+10 (continuation) ou l'inverse (sur-réaction) ? Ni l'un ni l'autre = marché efficient, et EXT007 se limite aux features de volatilité.
- H2 : les grosses surprises (|retour event-day| > p80) ouvrent-elles une fenêtre de demi-vie de compression différente pour notre prime (lien V130) ?

## 8. Risques et limites

Résultats intraday non transposables directement en quotidien ; période récente courte ; le « day-trade d'annonce » est explicitement hors de notre périmètre (RESEARCH_ONLY, données quotidiennes).

## 9. EXT associées

EXT007, EXT008, EXT032.

## 10. Conclusion

**Priorité très haute** comme garde-fou de réalisme pour tout le bloc événements : chez nous, l'annonce est un référentiel de fenêtres, pas un trade.

---
id: PAPER027
source_type: paper
title: Evaluating the Forecasting Performance of Commodity Futures Prices
priority: very_high
status: analyzed_2026-06-12
note: Reeve & Vigfusson (2011), Fed Board, International Finance Discussion Papers.
---
# Futures vs random walk (Reeve & Vigfusson 2011)

## 1. Référence

Reeve, T.A., Vigfusson, R.J. (2011). Evaluating the Forecasting Performance of Commodity Futures Prices. Federal Reserve Board, IFDP.

## 2. Sujet

Les prix futures sont-ils de meilleurs prédicteurs du prix futur que la marche aléatoire ? Test systématique multi-commodities, multi-horizons.

## 3. Données

Futures et spots de nombreuses commodities (énergie, métaux, agricoles), horizons 3-24 mois, plusieurs décennies.

## 4. Méthode

Comparaison d'erreurs de prévision : futures(t, t+h) vs RW (spot d'aujourd'hui), tests d'égalité de précision (Diebold-Mariano), par commodity et horizon.

## 5. Résultats importants

- **Les futures battent rarement la marche aléatoire de façon significative** ; pour les agricoles, ni l'un ni l'autre ne domine clairement.
- Implication : toute prévision doit prouver sa valeur contre DEUX baselines triviales — RW ET prix futures — sinon elle n'apporte rien.

## 6. Apport pour notre étude

- Fonde EXT025 : le socle de discipline de TOUT le programme externe. Nos modèles internes ont déjà cette culture (V11 : 2 vars bat 6 vars), mais les EXT futurs doivent l'industrialiser : chaque test rapporte {RW, RW+drift, futures-as-forecast, baseline interne pertinente}.
- Définit les métriques du protocole : RMSE relatif au RW + DA + DM-test, par horizon.

## 7. Hypothèses testables

- H1 (EXT025) : sur CBOT corn 2010-2023, mesurer une fois pour toutes : RW vs futures(t,h) vs RW+drift saisonnier, H5/H20/H40/H90 — produit le TABLEAU DE RÉFÉRENCE que tous les EXT citeront.
- H2 : même tableau pour l'EMA officiel (depuis V26) et pour le basis — le basis est-il plus prévisible que le prix ? (Nos V10-V13 disent oui — l'inscrire face aux baselines formelles.)

## 8. Risques et limites

Données pré-2011 (à réestimer sur 2010-2023) ; horizons mensuels chez eux vs quotidiens chez nous ; aucun risque de fuite (baselines pures).

## 9. EXT associées

EXT025 (principal) — prérequis de TOUS les autres EXT.

## 10. Conclusion

**Priorité très haute, à exécuter EN PREMIER à l'étape 3** : EXT025 est trivial à coder, sans risque, et conditionne la lecture de tout le reste.

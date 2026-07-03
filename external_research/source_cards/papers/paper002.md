---
id: PAPER002
source_type: paper
title: Machine learning to predict grains futures prices
priority: high
status: analyzed_2026-06-12
note: Brignoli, Varacca, Gardebroek, Sckokai (~2024, Agricultural Economics) — à confirmer.
---
# Machine learning to predict grains futures prices (Brignoli et al.)

## 1. Référence

Brignoli, P.L., Varacca, A., Gardebroek, C., Sckokai, P. (~2024). Agricultural Economics (à confirmer).

## 2. Sujet

Comparaison rigoureuse LSTM/réseaux récurrents vs modèles économétriques classiques (ARIMA, VAR) pour les futures de grains (corn inclus) : le deep learning apporte-t-il un gain réel hors échantillon ?

## 3. Données

Futures grains quotidiens (corn, blé, soja), exogènes (autres commodities, macro, éventuellement infos USDA), période 2000s-2020s.

## 4. Méthode

Protocole comparatif avec validation temporelle ; LSTM multi-features vs ARIMA/VAR/naïf ; métriques d'erreur et tests de différence.

## 5. Résultats importants

(À confirmer au PDF.) Pattern typique de cette littérature, vraisemblablement confirmé ici : **gains du LSTM faibles à nuls hors échantillon contre des benchmarks bien spécifiés** ; le gain apparent dépend du protocole ; l'avantage se concentre, s'il existe, sur les horizons courts et les périodes volatiles.

## 6. Apport pour notre étude

- Référence publiée pour ancrer notre position interne (V18 : ML NO_GO ; V11 : la simplicité gagne) face à la littérature — utile pour le rapport professionnel.
- Check-list de protocole comparatif propre (mêmes splits, mêmes cibles pour tous les modèles).

## 7. Hypothèses testables

- Aucune feature nouvelle. Sert de **spécification du protocole EXT** : tout modèle complexe (EXT016, EXT021) doit suivre le même cadre comparatif que ce papier, avec DM-test contre la baseline EXT025.

## 8. Risques et limites

Si le papier conclut à un gain DL, vérifier le protocole (fuites classiques : normalisation globale, fenêtres chevauchantes) avant d'y croire ; nos jeux quotidiens sont petits pour le DL.

## 9. EXT associées

EXT025, EXT016, EXT021 (cadrage).

## 10. Conclusion

**Priorité haute** comme référence de protocole et de positionnement ; pas une source de features.

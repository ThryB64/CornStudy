---
id: REPO001
source_type: repository
title: PrayusShrestha/crop-price-prediction
priority: high
status: analyzed_2026-06-12
---
# PrayusShrestha/crop-price-prediction

## 1. Identification

- URL : https://github.com/PrayusShrestha/crop-price-prediction — propriétaire : Prayus Shrestha (étudiant UBC)
- Licence : **absente** → idées seulement
- État : cloné complet ; projet de cours ECON 323 (UBC)
- Langage : Python/PyTorch ; fichiers : `src/final_project.ipynb` (livrable), `src/data_scraper.ipynb`, `src/rnn_model.py`, `src/gru_model.py` (modèles minimalistes ~12 lignes), `data/*.csv` (corn, wheat, oat, lumber, crude_oil, weather)

## 2. Objectif

Mesurer l'influence de la météo sur les prix des corn futures US avec 3 réseaux de neurones (MLP, RNN+Adam+L2, GRU).

## 3. Données utilisées

Marché : corn futures + commodities corrélées (blé, avoine, bois, brut) ; météo US agrégée (`weather_data.csv`). Scrapées d'APIs, période et stations non documentées dans le README.

## 4. Cible prédite

Prix du corn future (régression de niveau — pas direction, pas retour).

## 5. Horizons

Court terme (séquences journalières) ; pas d'horizon économique explicite.

## 6. Modèles

MLP, RNN simple, GRU (PyTorch, une couche + linéaire). Pas de baseline naïve.

## 7. Méthode d'évaluation

Projet de cours : split simple, métriques de régression (à confirmer dans le notebook). **Prédire le NIVEAU de prix avec un réseau récurrent donne presque toujours un R² flatteur et trompeur (le modèle apprend ~prix d'hier)** — comparaison RW indispensable et probablement absente.

## 8. Risques de fuite

Probables : normalisation globale avant split (pratique standard des notebooks étudiants), météo réalisée alignée au jour même sans lag de disponibilité, cible quasi présente dans les features (niveau de prix autorégressif). Aucune gestion walk-forward visible.

## 9. Réutilisable

- **Idée** : liste des commodities corrélées comme contexte (blé déjà chez nous via wheat_corn_z ; avoine/bois non testés et probablement bruit).
- **Contre-exemple pédagogique** : exactement ce que EXT025 doit empêcher (modèle sans baseline RW).

## 10. Faible / inutilisable

Modèles jouets, pas de protocole temporel, pas de baseline, données non documentées. Valeur scientifique faible.

## 11. Hypothèses testables

Aucune nouvelle au-delà de ce que EXT001/EXT002 couvrent déjà mieux via Singh (PAPER001). Conserver uniquement comme témoin de ce qu'un protocole propre doit éviter.

## 12. EXT associées

EXT025 (illustre la nécessité de la baseline), marginalement EXT001/EXT002.

## 13. Conclusion

**Inspiration seulement** (négative surtout). Déclasser de `high` → utile 15 minutes, pas plus. Pas de fiche d'expérience dédiée.

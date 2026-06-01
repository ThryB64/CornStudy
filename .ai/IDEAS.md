# Idées — Etude Mais

Ce fichier reçoit les idées brutes avant découpage en tickets.

## Objectif général

Améliorer progressivement l'étude de prévision maïs : précision, honnêteté du rapport, intégration de nouvelles données.

## Idées validées (à transformer en tickets)

- Lancer le rebuild complet post-paliers 1–6 (features → factors → study).
- Valider la couverture réelle du CQR (cible : 90% empirique).
- Vérifier que Markov-switching converge et produit 3 régimes distincts.
- Mettre à jour la table d'implémentation dans le rapport (SHAP, CQR, Markov → ✅).
- Corriger les series IDs EIA dans `config/sources.yaml` (WGFRPUS2/WGTSTUS1 sont du gazole, pas de l'éthanol).
- Ajouter la couverture CQR et la distribution des régimes dans le rapport.

## Idées en discussion

- NDVI / indices de végétation satellite (hors périmètre actuel).
- ENSO / El Niño comme feature météo globale.
- Ajout d'un dashboard interactif (Streamlit ou Dash).
- Optimisation hyperparamètres LightGBM/XGBoost par Optuna.

## Idées refusées

- Aucune pour l'instant.

## Priorités

1. Rebuild + validation (critique).
2. Mise à jour rapport (simple).
3. Correction sources.yaml (simple).
4. Nouvelles sources de données (différé).

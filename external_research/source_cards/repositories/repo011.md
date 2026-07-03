---
id: REPO011
source_type: repository
title: cchallu/nbeatsx
priority: medium
status: analyzed_2026-06-12
---
# cchallu/nbeatsx

## 1. Identification

- URL : https://github.com/cchallu/nbeatsx — propriétaires : Olivares, Challu et al. (CMU)
- Licence : ✅ MIT — code réutilisable
- État : cloné ; implémentation officielle du papier (arXiv:2104.05522, Int. J. Forecasting)
- Langage : Python/PyTorch ; fichiers : `src/nbeats/nbeats_model.py`, `src/hyperopt_nbeatsx.py`, `nbeatsx_example.ipynb`

## 2. Objectif

NBEATSx = NBEATS + variables exogènes, appliqué au forecast de prix d'électricité (EPF) : ~20 % de gain vs NBEATS, ~5 % vs LEAR/DNN spécialisés, avec décomposition interprétable (tendance/saison/exogènes).

## 3. Données utilisées

Marchés électricité (Nord Pool, PJM, BE, FR, DE) : prix horaires + exogènes (load forecast, génération prévue). Analogie avec nous : exogènes = basis_z, météo prévue, saison.

## 4. Cible prédite

Prix (niveau) multi-pas, horizon 24h dans le papier.

## 5. Horizons

Multi-step configurable. Pour nous : H20-H90 quotidien.

## 6. Modèles

NBEATSx-G/I (stacks génériques/interprétables), TCN en encodeur d'exogènes ; hyperopt 1500 itérations dans le papier.

## 7. Méthode d'évaluation

Sérieuse pour le domaine : 2 ans de test, ensembles, test Giacomini-White, MAE/rMAE/sMAPE/RMSE, validation temporelle (`random_validation 0`). Transposable.

## 8. Risques de fuite

Le pipeline EPF utilise des exogènes PRÉVUS (load forecast) disponibles à J — bonne pratique à copier : chez nous, exogènes = météo PRÉVUE (pas réalisée), basis_z décalé. Risque réel pour nous : hyperopt massif sur petit dataset quotidien (nos ~3500 obs vs leurs dizaines de milliers d'heures) = overfitting quasi garanti → budget d'hyperopt minimal et validation bloquée dans le temps.

## 9. Réutilisable

- **Code** : MIT, Dataset/DataLoader propres.
- **Méthode** : protocole d'évaluation (ensembles + GW test) ; usage d'exogènes prévus.
- **Modèle** : candidat unique côté deep learning (interprétable par décomposition), si jamais on y va.

## 10. Faible / inutilisable

Données électricité (granularité, saisonnalité 24h) très différentes ; nos échantillons sont 10-50× plus petits ; le gain DL n'est pas acquis sur du quotidien agricole (V18 : ML NO_GO déjà établi en interne).

## 11. Hypothèses testables

- H1 (conditionnelle, après EXT025 et les blocs fondamentaux) : NBEATSx avec exogènes {basis_z, saison, météo prévue} sur direction/retour CBOT H20-H40 vs notre logistique 2 vars : le gain dépasse-t-il l'intervalle de bruit (test GW) ? Verdict attendu honnête : probablement REJECT, mais c'est LE test DL propre à faire si on en fait un.

## 12. EXT associées

EXT016 (principal), EXT023 (la variante texte est PAPER020).

## 13. Conclusion

**À garder pour plus tard** : dernier bloc, uniquement après que les benchmarks simples ont fixé le plancher. Ne pas lancer avant EXT025/EXT009/EXT011.

---
id: fdfoneill-wasdeparser
source_type: repository
title: fdfoneill/wasdeparser
priority: very_high
status: analyzed_2026-06-12 (non cloné — analyse via métadonnées GitHub ; à cloner à l'étape 3)
---
# fdfoneill/wasdeparser

## 1. Identification

- URL : https://github.com/fdfoneill/wasdeparser — propriétaire : F. Dan O'Neill (8 stars)
- Licence : à vérifier au clonage
- État : **NON CLONÉ** (découvert après la passe de clonage seed) → premier geste de l'étape 3 : `git clone --depth 1` dans `github_repos/`
- Langage : Python (package)

## 2. Objectif

Faciliter l'accès aux données WASDE (World Agricultural Supply and Demand Estimates) : téléchargement et parsing des fichiers de rapport en données exploitables.

## 3. Données utilisées

Fichiers WASDE USDA (mensuels). L'enjeu pour nous : obtenir les **valeurs telles que publiées à chaque date de rapport** (vintages), pas les séries révisées.

## 4. Cible prédite

Aucune — outil d'ingestion.

## 5. Horizons

N/A. Mensuel, dates de publication officielles USDA (calendrier publié à l'avance, ~12h ET).

## 6. Modèles

Aucun.

## 7. Méthode d'évaluation

À vérifier au clonage : couverture temporelle, gestion des changements de format WASDE (les tableaux changent de structure au fil des ans — risque principal de parsing).

## 8. Risques de fuite

C'est précisément l'outil anti-fuite : si le parsing donne le contenu du rapport du mois M daté de sa publication, on peut construire des surprises sans valeurs révisées (anti_leak_rules n°4). **Critère d'acceptation : prouver sur 3 rapports anciens que les valeurs parsées = valeurs publiées à l'époque (pas les révisions).**

## 9. Réutilisable

Code d'ingestion (sous réserve de licence), structure des tableaux corn US (production, ending stocks, exports, feed use, stocks-to-use).

## 10. Faible / inutilisable

Inconnu avant clonage ; 8 stars = maintenance incertaine ; prévoir fallback : archives WASDE officielles USDA (downloads par date) parsées par nous.

## 11. Hypothèses testables

- H1 (infra) : pipeline vintage WASDE corn US complet 2010→2026 avec une ligne par (rapport, variable), datée publication. Verdict KEEP si 3 vérifications historiques passent.
- H2 : surprise = valeur publiée M − valeur publiée M-1 (même variable, même campagne), z expandant → feature event-day pour EXT007/EXT008.

## 12. EXT associées

EXT026 (principal — infra), EXT007, EXT008, EXT024.

## 13. Conclusion

**À tester immédiatement** (infra prioritaire) : EXT026 conditionne la qualité de tout le bloc WASDE. Cloner + valider les vintages avant toute feature.

---
id: REPO004
source_type: repository
title: mindymallory/RollFutures
priority: very_high
status: analyzed_2026-06-12
---
# mindymallory/RollFutures

## 1. Identification

- URL : https://github.com/mindymallory/RollFutures — propriétaire : Mindy Mallory
- Licence : **absente** → réimplémenter la logique, ne pas copier le code
- État : cloné complet ; 1208 fichiers dont ~1180 CSV de contrats (sorties corn `C_Nearby_volume.csv`, `C_Nearby_dte.csv`, dossiers data/)
- Langage : R (`RollFutures.R`, `RollFutures-overshoot.R`, tests corn `test_corn_nearby.R`, `test_corn_nearby_dte.R`)

## 2. Objectif

Construire une série nearby continue depuis les contrats individuels (Quandl/CME) avec 3 méthodes de roll : **volume takeover** (roll quand le volume du contrat suivant dépasse le courant), **DTE** (n jours avant expiration), **OI** (plus gros open interest du jour).

## 3. Données utilisées

Futures contrat par contrat (Settle, Volume, OpenInterest) via Quandl. Cycle corn `H,K,N,U,Z` explicitement géré. CSV corn pré-générés présents (provenance Quandl, licence inconnue → **méthode seulement, pas les données**).

## 4. Cible prédite

Aucune — outil de construction de données. La qualité du nearby EST le produit.

## 5. Horizons

N/A (hygiène de série continue, affecte tous les horizons).

## 6. Modèles

Logique déterministe de roll ; variante « overshoot » contre les faux signaux de volume (volume du suivant repasse temporairement sous le courant).

## 7. Méthode d'évaluation

Tests visuels et CSV de sortie (corn dte vs volume). Pas de métrique formelle — à définir nous-mêmes (H1 ci-dessous).

## 8. Risques de fuite

**Point crucial** : le roll volume-based décide du contrat de J avec le volume de J (connu en fin de séance). Pour être strictement causal en usage prédictif : roll décidé sur volume(J-1) (anti_leak_rules n°7). Même piège pour le roll OI. À noter explicitement dans EXT006.

## 9. Réutilisable

- **Méthode** : les 3 règles de roll + correctif overshoot (anti aller-retour).
- **Idée d'évaluation** : comparer volume vs DTE vs OI sur le même jeu de contrats et mesurer les artefacts (sauts au roll, autocorrélation artificielle, PnL fantôme d'une stratégie naïve).
- Confirme notre univers contrats V24 (CBOT H/K/N/U/Z).

## 10. Faible / inutilisable

Source Quandl/CME dépréciée (inutilisable pour nous) ; R non packagé ; **pas de back-adjustment** : la série jointe garde les sauts de prix au roll.

## 11. Hypothèses testables

- H1 : notre série continue CBOT vs nearby volume-based causal (volume J-1) : mesurer la différence de retours autour des dates de roll ; si > bruit, les features de retour proches du roll sont contaminées.
- H2 : sensibilité des backtests V13-V17 à la méthode de roll : une stratégie momentum 20j naïve sur nearby DTE vs volume donne-t-elle des PnL significativement différents ?
- H3 : back-adjustment (différence) vs série brute : les sauts de roll gonflent-ils artificiellement basis_z certains mois (notre cœur de signal) ?

## 12. EXT associées

EXT006 (principal), EXT005 (spreads contrat-à-contrat propres), EXT025 (baselines sur série propre), EXT034 (calendar spreads).

## 13. Conclusion

**À tester immédiatement** : EXT006 est peu coûteux et protège tous les autres résultats. Notre amélioration vs le repo : règle causale J-1 + mesure d'artefacts formalisée.

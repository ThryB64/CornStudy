---
id: REPO005
source_type: repository
title: NDelventhal/cot_reports
priority: very_high
status: analyzed_2026-06-12
---
# NDelventhal/cot_reports

## 1. Identification

- URL : https://github.com/NDelventhal/cot_reports — propriétaire : Niall Delventhal
- Licence : ✅ présente, package pip — code réutilisable directement
- État : cloné, package propre (`cot_reports/cot_reports.py`)
- Langage : Python (pandas, requests, beautifulsoup4)

## 2. Objectif

Télécharger les 7 types de rapports COT CFTC en DataFrame : Legacy fut/futopt (1986+), **Supplemental/CIT** (2006+, index traders agri), **Disaggregated fut/futopt** (2006+, Producer/Merchant, Swap, Managed Money, Other), TFF. Fonctions `cot_hist` (bulk→2016), `cot_year`, `cot_all`.

## 3. Données utilisées

CFTC uniquement. Pour le maïs : Legacy long historique ; Disaggregated = catégories fines (Managed Money = spéculatif le plus informatif) ; CIT = index traders (spécifique agri).

## 4. Cible prédite

Aucune — librairie d'accès aux données.

## 5. Horizons

N/A. Hebdomadaire : positions du mardi, **publication vendredi ~15h30 ET**.

## 6. Modèles

Aucun.

## 7. Méthode d'évaluation

N/A. Fiabilité : dépend du format du site CFTC (avertissement explicite du README) → prévoir test de schéma à l'usage.

## 8. Risques de fuite

**LE point critique** (anti_leak_rules n°5) : les fichiers sont indexés par la date de POSITION (mardi). Toute feature doit être décalée à la date de PUBLICATION (vendredi, +3 jours, plus en semaine fériée). Le repo ne fournit PAS le calendrier de publication → à construire (la CFTC publie l'historique des release dates). Vérifier si le NO_GO COT de V18 (−0.084) utilisait déjà le décalage vendredi ; sinon il était même optimiste.

## 9. Réutilisable

- **Code** : oui (licence OK, pip).
- **Données** : les 7 rapports ; pour corn : MM net, variation MM, concentration top-4, CIT net.
- **Idée** : V18 n'a falsifié que le net total. Les features fines (extrêmes de percentile MM, flux hebdo, concentration) ne sont PAS encore falsifiées.

## 10. Faible / inutilisable

Pas de calendrier de publication intégré ; pas de gestion des semaines fériées ; bulk historique s'arrête à 2016 (compléter par `cot_year`).

## 11. Hypothèses testables

- H1 : Managed Money net (z expandant, décalé publication vendredi) en EXTRÊME (>p90/<p10) prédit-il la direction CBOT H5-H40 mieux que la baseline RW ?
- H2 : le FLUX hebdo de MM net (variation, pas niveau) + interaction avec uptrend CBOT (V39-E6 : net long converge en uptrend) améliore-t-il le contexte ADVERSE ?
- H3 : CIT index traders autour des fenêtres de roll indiciel (5e-9e jour ouvré) → pression mécanique mesurable sur le spread nearby-deferred (lien EXT005) ?

## 12. EXT associées

EXT003 (principal), EXT005 (pression de roll indiciel), EXT017 (régimes de positionnement).

## 13. Conclusion

**À tester immédiatement** comme infra EXT003 — mais le test ne vaut que si le calendrier de publication vendredi est construit et prouvé d'abord.

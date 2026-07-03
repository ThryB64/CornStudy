---
id: PAPER020
source_type: paper
title: Text-based corn futures price forecasting using improved NBEATSx
priority: medium_high
status: analyzed_2026-06-12
note: Auteurs (Wang/An/Li selon seed) — Dalian corn. À confirmer.
---
# NBEATSx + texte sur Dalian corn (Wang et al.)

## 1. Référence

Wang et coll. Text-based corn futures price forecasting using improved NBEATSx (Dalian, sentiment Weibo, SHAP).

## 2. Sujet

Améliorer NBEATSx avec des features textuelles (sentiment/attention Weibo) et une sélection SHAP pour les futures maïs de Dalian (Chine).

## 3. Données

Futures corn Dalian quotidiens, indices texte chinois (Weibo, recherche Baidu), variables marché ; années 2010s-2020s.

## 4. Méthode

NBEATSx modifié + pipeline de sélection SHAP ; comparaisons aux variantes sans texte.

## 5. Résultats importants

- Le texte améliore l'erreur de prévision sur Dalian — marché retail-driven où l'attention domestique compte plus qu'aux US.
- SHAP utilisé À L'INTÉRIEUR du protocole de sélection (méthodologie réutilisable indépendamment du texte).

## 6. Apport pour notre étude

- Méthode de sélection SHAP-dans-le-split (EXT015) plus que le texte lui-même : Dalian ≠ CBOT (structure de participants très différente), transférabilité du sentiment faible.
- Si EXT023 s'active un jour : préférer les mesures d'ATTENTION (volume d'articles, persistance) au sentiment — convergent avec le papier news-GDELT 2026 du catalogue qui trouve la même chose sur CBOT.

## 7. Hypothèses testables

- H1 (EXT015) : sélection SHAP estimée DANS chaque split train (jamais sur le test) sur nos features V9 : retrouve-t-elle basis_z+saison (validation croisée de V10-B) ?
- H2 (EXT023, différé) : indice d'attention news corn (GDELT, horodaté) → vol CBOT H1-H5 — seulement si le bloc 4 s'ouvre.

## 8. Risques et limites

Marché chinois (quotas d'import, retail) ; NBEATSx complexe pour notre taille d'échantillon ; le gain « texte » peut être un artefact de protocole (à ne pas répliquer aveuglément).

## 9. EXT associées

EXT015 (principal), EXT016, EXT023.

## 10. Conclusion

**Priorité moyenne-haute**, pour la méthode SHAP-dans-le-split uniquement. Le volet texte reste bloc 4 (différé).

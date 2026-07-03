---
id: PAPER001
source_type: paper
title: Sriramjee Singh - Weather, soil and machine learning for CBOT corn futures prices
priority: very_high
status: analyzed_2026-06-12
note: Thèse Iowa State (2020, DOI 10.31274/td-20240329-290). Doublon découvert (Semantic Scholar) à fusionner. PDF à récupérer pour les détails.
---
# Estimating the impact of weather on CBOT corn futures prices using ML (Singh 2020)

## 1. Référence

Singh, S. (2020). Thèse, Iowa State University. « We apply machine learning methods to weather and soil data » → prix corn futures CBOT.

## 2. Sujet

Mesurer l'effet de la météo (et du sol) sur les corn futures avec du ML : quelles variables météo, quelles fenêtres, quel pouvoir prédictif réel.

## 3. Données

Météo historique par zone de production US (température, précipitations, probablement par district/État), données de sol (capacité de rétention — modulateur du stress hydrique), prix futures CBOT. Fréquence quotidienne/hebdo, fenêtre d'étude multi-années.

## 4. Méthode

ML (forêts/boosting vraisemblablement) sur features météo agrégées spatialement ; à vérifier au PDF : type de split temporel, baselines.

## 5. Résultats importants

(À confirmer au PDF.) Apports attendus de la thèse : (1) l'interaction sol×météo compte (même pluie, stress différent selon le sol) ; (2) les fenêtres de croissance critiques dominent ; (3) le pouvoir prédictif sur les PRIX est limité hors été.

## 6. Apport pour notre étude

- **Design de features** : c'est la source de référence pour EXT001/EXT002 — fenêtres par stade de culture plutôt que fenêtres calendaires fixes ; anomalies vs climatologie plutôt que niveaux ; pondération par État producteur.
- **Modération** : nos V45/V19 ont montré que la météo RÉALISÉE est pricée par anticipation (AUC 0.508). Le test honnête : anomalies par stade + interaction sol, en réalisé = explicatif (catalogue), en PRÉVU = prédictif (EXT033).

## 7. Hypothèses testables

- H1 (EXT001) : anomalies T/P par fenêtre de stade (semis, pollinisation, remplissage), pondérées production, climatologie expandante → direction CBOT H20-H60 vs RW. Attendu faible en réalisé (V45), mais jamais testé par STADE chez nous.
- H2 (EXT002) : stress CUMULÉ (somme d'anomalies négatives sur 14/30/60j) plutôt qu'anomalie instantanée — la non-linéarité cumulative est l'apport ML plausible de la thèse.

## 8. Risques et limites

Thèse = peu relue ; risque de fuite dans le ML d'origine (split, normalisation) à auditer si on s'appuie sur ses chiffres ; météo US dense difficile à reconstituer en historique propre (notre archive V136 ne couvre que depuis 2026).

## 9. EXT associées

EXT001, EXT002 (principales), EXT020, EXT033.

## 10. Conclusion

**Priorité très haute** pour le DESIGN des features météo ; récupérer le PDF (ProQuest/IState) à l'étape 3 avant d'écrire le plan de features définitif.

---
id: REPO002
source_type: repository
title: squeeze-team/AgriJedi
priority: low
status: analyzed_2026-06-12
---
# squeeze-team/AgriJedi (AgroMind)

## 1. Identification

- URL : https://github.com/squeeze-team/AgriJedi — propriétaire : squeeze-team (hackathon)
- Licence : **absente**
- État : cloné ; app full-stack (backend FastAPI + frontend React + docker-compose)
- Langage : Python (29 fichiers) + JS ; fichiers : `backend/app.py`, `backend/services/`, `backend/features/`, `PWHEAMTUSDM.csv`

## 2. Objectif

MVP conversationnel « AI brain for agriculture » France : chaîne LangGraph de 7 agents (géocodage → rendement → marché → risque climat → bio-monitoring → orchestrateur) combinant Sentinel-2 NDVI, Copernicus CLMS, Open-Meteo/Météo-France 14j, NASA POWER, futures blé/maïs, EUR/USD, WTI, US 10Y, régime WASDE.

## 3. Données utilisées

Satellite (NDVI + crop-type), météo prévue 14j + climat historique, marché (futures, FX, taux), WASDE en « régime offre/demande ». Orienté advisory, pas dataset de recherche.

## 4. Cible prédite

Indice de rendement t/ha par département + « price trend » qualitatif. Pas de cible de forecast évaluée.

## 5. Horizons

14 jours (météo) à saison (rendement). Non formalisés.

## 6. Modèles

Agents LLM + heuristiques + baselines phénologiques NDVI par culture. Pas de modèle de prix entraîné/évalué.

## 7. Méthode d'évaluation

Aucune (démo). Aucune métrique de forecast.

## 8. Risques de fuite

N/A (pas de modèle évalué). Si on s'inspirait du pipeline NDVI : attention aux timestamps d'acquisition vs publication (anti_leak_rules, satellite).

## 9. Réutilisable

- **Idée** : baselines phénologiques par culture pour distinguer stress réel et sénescence naturelle (pertinent si EXT022/EXT028 un jour) ; sources de données EU gratuites listées (Copernicus CLMS crop-type, NASA POWER).

## 10. Faible / inutilisable

Pas de recherche, pas d'évaluation, LLM-driven. Le « régime WASDE » est cosmétique.

## 11. Hypothèses testables

Aucune directe. Si EXT022 s'active un jour : reprendre l'idée de baseline phénologique par stade pour normaliser le NDVI (z par stade de culture plutôt que z calendaire).

## 12. EXT associées

EXT022 (lointain), EXT028 (lointain).

## 13. Conclusion

**Inspiration seulement** (catalogue de sources EU). Confirme le classement LOW_PRIORITY de l'étape 1 malgré la priorité seed `high`.

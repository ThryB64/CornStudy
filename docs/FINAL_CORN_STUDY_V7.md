# Étude CBOT/EMA Maïs V7 — Rapport Final

## Résumé exécutif

Ce rapport synthétise les résultats de l'étude V7 du cours du maïs (CBOT et Euronext EMA).
L'étude porte sur les périodes 2000-2023 ; le holdout 2024 est réservé.

## Conclusions principales

| Dimension | Résultat | Verdict |
|---|---|---|
| CBOT direction | Moteur mondial | GO_RESEARCH |
| EMA direction absolue | Non prédictible robustement | NO_GO_AS_MAIN_TARGET |
| EMA/CBOT relatif (basis) | Signal principal recherche | PRIMARY_RESEARCH_SIGNAL |
| Nested stacking V2 | AUC=0.5454 | NO_GO |
| Causalité CBOT→EMA | BIDIRECTIONAL | DESCRIPTIVE |
| Backtests | RESEARCH_ONLY_NOT_TRADING — holdout 2024 non utilisé | RESEARCH_ONLY |

## Protocoles V7

- **Purged CV** avec embargo H jours (leave_one_crop_year)
- **Nested walk-forward stacking** anti-leakage strict inner/outer
- **Correction BH** (Benjamini-Hochberg) sur tous les tests
- **Holdout 2024** gelé — non utilisé dans cette étude

## Expériences complétées

- **Total** : 28 expériences enregistrées
- **DONE/GO_RESEARCH** : 23
- **NO_GO** : 2
- **Artefacts présents** : 28/28

## Réserves

- Source EMA = barchart_proxy_exploratory, non settlement officiel
- Holdout 2024 réservé pour validation finale (V7-28)
- Backtests de recherche uniquement, pas de trading claim

## Pour aller plus loin

Le holdout 2024 peut être déverrouillé via V7-28 (architecture finale de l'indicateur)
pour une validation externe indépendante.

---
*Étude V7 — Généré automatiquement*

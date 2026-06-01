# EMA 00 — Vue d'ensemble du projet

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Phrase directrice

> CBOT explique la tendance mondiale. EMA révèle la prime européenne via le basis.  
> La vraie étude Euronext = basis + transmission CBOT→EMA + découplage + résidu EU spécifique.

## Résultats clés actuels

| Métrique | Valeur | Verdict |
|---|---|---|
| DA direction EMA h20 | 0.4673 | NO_GO |
| IC95% DA EMA | [0.44, 0.49] | — |
| Basis seul → CBOT DA | 0.5840 | SIGNAL FORT |
| Basis seul → CBOT AUC | 0.6336 | SIGNAL FORT |
| Basis mean reversion H20 (z>2) | 70.4% hit rate | CONFIRMÉ |
| CQR prix EMA coverage | 79.2% | NO_GO (requis 88%) |
| Granger EMA→CBOT p-value | 0.0144 (lag 1) | PROMETTEUR — non confirmé OOF |
| % dates avec ≥2 contrats actifs | 14.9% | Courbe quasi-inexistante |

## Roadmap notebooks

| Priorité | Module | Objectif |
|---|---|---|
| P0 | NB-EMA-01 | Audit données EMA v2 |
| P0 | NB-EMA-02 | Contrats et rolls |
| P0 | NB-EMA-03 | Séries continues |
| P0 | NB-EMA-04 | Relation EMA/CBOT (cointegration) |
| P1 ⭐ | NB-EMA-05 | Décomposition retour EMA |
| P1 ⭐ | NB-EMA-06 | Étude résidu EU |
| P1 | NB-EMA-07 | Basis formel (ADF, AR(1), half-life) |
| P1 | VALID-GRANGER-01 | Validation Granger OOF (5 tests) |
| P2 | NB-EMA-08 à 13 | Bloc prédictif |
| P3 | DATA-EU-01/02 | EC MARS + Open-Meteo EU |
| P4 | NB-EMA-14 | Rapport de synthèse final |

## Ce qu'on ne fait pas

- Recommandation commerciale agriculteur (STOCKER/VENDRE)
- Indicateur BULLISH/BEARISH/UNCERTAIN opérationnel
- Claim non validé OOF

## Artefact produit

`artefacts/ema_study/ema_project_overview.json`

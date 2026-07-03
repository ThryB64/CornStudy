# Plan d'exécution — Étape 5 (P2 : modèles avancés disciplinés)

Date : 2026-06-13. Règles : aucun fichier interne modifié ; expériences sous
`external_research/experiments/external_tests/`, résultats sous
`external_research/results/external_tests/` ; holdout 2024+ exclu partout.

## Rappel des conclusions de l'étape 4

Aucune famille fondamentale ne bat la random walk en RMSE ; **aucun KEEP**. Deux **IMPROVE**
sur la **direction** (jamais le RMSE), stables sur 2 sous-périodes :
- **EXT007 — WASDE niveaux de bilan** : ΔDA +6.1 pts H20 (mais RMSE pire car niveaux
  non-stationnaires) ;
- **EXT019 — Crop Condition** : ΔDA +4.4 pts H90, RMSE neutre.

Tout le reste = REJECT (météo réalisée/lags/extrêmes, surprise WASDE, COT, proxys éthanol)
ou DATA_BLOCKED (courbe, basis) ou PARTIAL (prime new-crop, descriptif seulement).

## Question de l'étape 5

Les deux signaux faibles mais stables peuvent-ils devenir un **indicateur robuste de
direction / de risque / de score de vente à H40-H90** — pas un modèle de prix ?

## Familles de variables AUTORISÉES

1. **Marché minimal** : ret_5d, ret_20d, vol_20, saison (sin/cos), CBOT continu validé
   (market.parquet, côté vendeur sans artefact de roll — EXT006), benchmarks EXT025.
2. **WASDE (vintage EXT026 uniquement)**, en **encodages stationnaires** : stocks-to-use
   ratio, z-score expandant, percentile expandant, classe tight/normal/loose (seuils
   expandants), variation lente, variation annuelle, écart à moyenne passée, dummies de
   campagne. **Pas de niveaux bruts non-stationnaires** (cause du RMSE dégradé en étape 4).
3. **Crop Condition (EXT019)** : good/excellent, poor/very-poor, variation hebdo, anomalie
   par semaine de campagne, écart 5 ans, avancement des stades, tendances lentes.
4. **Volatilité** : rendements passés et vol réalisée passée (GARCH/EGARCH/HAR, gates).

## Familles INTERDITES comme prédicteurs principaux

Météo réalisée / lags / extrêmes, COT, surprise WASDE proxy, proxys éthanol/DDG, weather
premium prédictif. Usage permis seulement comme **contexte / régime justifié / negative
control**, jamais comme famille prédictive principale.

## DONNÉES BLOQUÉES

Courbe futures, basis, contrats décembre new-crop, prix éthanol/DDG → `DATA_BLOCKED`,
aucun test artificiel. EXT012 (OU mean-reversion sur basis) = audit DATA_BLOCKED seulement.

## Objectifs / cibles (priorité)

1. **Direction long horizon** : `y_dir_H40`, `y_dir_H90` (signe du log-retour t→t+h).
2. **Direction ternaire** (UP/DOWN/NEUTRAL) avec seuil = quantiles de |retour| **train-only**.
3. **Score de vente** interprétable : P(baisse), P(hausse), incertitude, vendre/attendre.
   Reste dans external_tests, non intégré au modèle principal.
4. **Volatilité future** : vol_H20/H40/H90.
5. **Régression de retour** : mesurée en secondaire seulement (plus l'objectif principal).

## Expériences P2 prévues

| Prio | EXT | Modèle | Cible | Données |
|---|---|---|---|---|
| 1 | EXT024 | supply-demand directionnel (AR, LogReg L2, Ridge clf, VAR) | dir H40/H90 | WASDE stat + crop + marché |
| 1 | EXT015 | SHAP / sélection train-only (RF, XGB, LogReg) | dir H40/H90 (+H20) | idem |
| 1 | EXT017 | régimes de marché | dir par régime | régimes passés |
| 1 | EXT009 | GARCH/EGARCH/GJR | vol H20/H40/H90 | retours CBOT |
| 1 | EXT010 | HAR | vol H20/H40/H90 | vol réalisée |
| 1 | EXT011 | trend-following (momentum, MA, EWMAC) | dir + stratégie | CBOT |
| 2 | EXT014 | BMA / pondération par perf passée | dir | modèles ci-dessus |
| 2 | EXT028 | stacking ensemble (méta-modèle simple) | dir | modèles utiles |
| 3 | EXT016 | NBEATSx exogène | dir/retour | variables validées |
| — | EXT012 | OU mean-reversion | — | **DATA_BLOCKED** (audit only) |

## Scripts à créer

- `_common/ext_harness_dir.py` : harnais directionnel (walk-forward expandant, refit
  annuel purgé, LogReg L2, métriques DA/balanced/AUC/Brier/calibration/confusion/
  precision-recall UP&DOWN, bootstrap temporel + test binomial, stabilité 2 sous-périodes).
- `_common/features_p2.py` : dataset stationnaire WASDE + crop condition + marché.
- `_common/vol_utils.py` : cibles et features de volatilité (réalisée, HAR, GARCH).
- Un `run_EXTxxx.py` par expérience + `README.md` + sorties dans `results/`.

## Sorties attendues

Par expérience : datasets/predictions, `metrics_EXTxxx.csv`, calibration/coefficients/
importance selon le cas, `README_results.md` avec verdict. Synthèse : `step5_results_summary.md`,
`step5_pre_model_audit.md`, `step5_sample_manifest.csv`, matrices mises à jour.

## Risques anti-fuite

Encodages stationnaires strictement train-only (z/percentile/seuils expandants) ; régimes
définis sur info passée seulement ; sélection de variables (EXT015) DANS chaque fenêtre ;
GARCH/HAR réestimés en expandant ; aucun usage du holdout 2024+ ; pas de split aléatoire.

## Risques d'overfitting

Edge faible (3-6 pts DA) → tentation de complexité. Garde-fous : (1) modèles simples
(RW, AR, LogReg 2-3 vars) comme référence à battre ; (2) tout KEEP exige stabilité sur les
**2 sous-périodes** ET significativité (bootstrap/binomial) ; (3) un modèle complexe qui ne
bat pas le simple = REJECT ou NOT_WORTH_YET ; (4) parcimonie imposée (peu de variables).

## Critères de verdict

- **KEEP** : amélioration directionnelle (ou risque) stable sur ≥2 sous-périodes,
  significative, économiquement logique, anti-fuite, pas trop complexe pour le gain.
- **IMPROVE** : signal partiel (un horizon, une sous-période, p marginal), logique mais
  stabilité/significativité insuffisante.
- **REJECT** : pas d'amélioration vs benchmarks simples, instable, surapprentissage,
  complexité injustifiée.
- **DATA_BLOCKED** : données absentes / échantillon trop court / variable non constructible.
- **LEAKAGE_RISK** : disponibilité incertaine, normalisation/sélection globale, futur possible.
- **NOT_WORTH_YET** : trop complexe pour le gain attendu, priorité faible.

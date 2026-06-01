# NB-EMA-10 — Importance des features EMA

## Objectif

Classer les variables candidates par leur pouvoir prédictif sur la cible `y_up_h20` (hausse à 20 jours).

## Méthode

- **Mutual Information** : calculée feature par feature pour gérer les NaN indépendamment (`sub = df[[f, "y_up_h20"]].dropna()`)
- **Corrélation de Spearman** : mesure monotone, robuste aux outliers
- 14 features candidates, dont certaines très creuses (ex. `ema_curve_slope_3` : 3071/3078 NaN)

## Résultats

| Rang | Feature | MI | n obs |
|---|---|---|---|
| 1 | `fedfunds_level_zscore` | 0.357 | ~3 078 |
| 2 | `fedfunds_z24` | ~0.25 | ~3 078 |
| 3 | `ema_cbot_basis_zscore_52w` | ~0.18 | ~3 078 |
| 4 | `corn_logret_20d` | ~0.12 | ~3 078 |
| 5 | `ema_spread_f0_f1` | ~0.09 | ~3 078 |

Features avec MI = NaN : variables trop creuses (< 50 obs valides).

**12 features ont une MI > 0.**

## Interprétation

Le niveau des Fed Funds (z-score expandant) est la variable la plus informative par MI in-sample.

> ⚠️ **SUSPECT — À VÉRIFIER.** `fedfunds_level_zscore` est probablement un **proxy de régime temporel macro** (2021-2022 : hausse des taux + crise Ukraine simultanées), pas nécessairement un driver causal direct du cours EMA. L'importance in-sample peut être entièrement portée par la crise 2021-2022. Vérification requise : permutation importance OOF, importance par année, importance en excluant 2021-2022. (Voir NB2-06)

Le basis et ses dérivés arrivent en 3e position, confirmant leur rôle potentiel.

## Limites

- MI calculée in-sample — biais de sélection non corrigé
- Les features creuses sont exclues automatiquement (< 50 obs valides)
- **Pas de validation OOF de l'importance** (priorité Phase 2 — NB2-06)
- Résultat EXPLORATOIRE — ne pas présenter fedfunds comme causal sans test OOF

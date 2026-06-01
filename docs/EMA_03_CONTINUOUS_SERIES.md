# EMA 03 — Séries Continues EMA (Raw vs Adjusted)

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Résultats clés

| Métrique | Valeur |
|---|---|
| Invariant `raw - adj == cum_adj` | VALIDÉ (0 violation, résidu max 0.00) |
| Couverture (raw et adj) | 79.0% des jours ouvrés |
| Gaps ≥5 jours ouvrés | 46 |
| ADF retours ajustés | Stationnaire (p < 1e-22) |
| Agreement directionnel raw/adj | 98.7% |
| Corrélation retours journaliers | 0.625 |
| Diff. prix abs. moyenne | 54.15 €/t (cumul roll) |
| Diff. prix abs. max | 152.75 €/t |

## Invariant de cohérence

L'égalité `price - adjusted_price = cum_roll_adjustment` est respectée à la tolérance 0.01 sur l'ensemble des 3 377 dates de la série ajustée. La série est arithmétiquement cohérente.

## Stationnarité

Les retours journaliers de la série ajustée sont stationnaires (ADF stat = -11.97, p ≈ 3.9e-22, 19 lags). Hypothesis nulle de racine unitaire rejetée.

## Corrélation faible raw/adj

La corrélation des retours journaliers raw vs adjusted est 0.625 — inférieure aux attentes. Explication : les ajustements de roll modifient structurellement les niveaux de prix, ce qui affecte le calcul des retours aux dates de roll. Les retours de la série ajustée sont les vrais retours d'une position frontière continue.

## Artefact produit

`artefacts/ema_study/ema_continuous_series.json`

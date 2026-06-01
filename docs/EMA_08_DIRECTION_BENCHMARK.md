# EMA 08 — Benchmark Directionnel EMA

> Source exploratoire (Barchart proxy). Résultats expérimentaux. Walk-forward par crop year.

## Résultats clés (5/28 combinaisons GO)

| Feature Set | Cible | DA moyen | IC95% | Verdict |
|---|---|---|---|---|
| cbot_eu_macro | basis_reversion H20 | 0.786 | [0.735, 0.838] | **GO** |
| cbot_basis | basis_reversion H20 | 0.785 | [0.737, 0.834] | **GO** |
| basis_only | basis_reversion H20 | 0.763 | [0.717, 0.814] | **GO** |
| cbot_ema_combined | basis_reversion H20 | 0.726 | [0.616, 0.831] | **GO** |
| all_selected | basis_reversion H20 | — | — | **GO** |

## Verdict direction EMA brute (y_up_h20)

NO_GO — cohérent avec le résultat connu DA = 0.4673.

## Interprétation

**Signal détecté sur la cible `y_up_h20_basis_reversion`** (prédiction de la direction de mean-reversion du basis EMA/CBOT). DA = 0.786 en walk-forward crop year avec IC95% entièrement au-dessus de 0.50.

Ce signal est cohérent avec NB-EMA-07 (hit rate H20 basis = 43%, H60 = 85%) et NB-EMA-07 (AR(1) φ=0.97, demi-vie 22.8j). Le basis est prévisible — pas le prix EMA brut.

**Le prix EMA en direction reste NO_GO** — la décomposition CBOT + basis absorbe tout le signal.

## Artefact produit

`artefacts/ema_study/ema_direction_benchmark.json`

# EMA 02 — Contrats EMA et Analyse des Rolls

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Résultats clés

| Métrique | Valeur |
|---|---|
| Nombre de rolls (front) | 68 |
| Gap moyen absolu | 9.83 €/t |
| Gap médian absolu | 6.00 €/t |
| Gap max absolu | 54.25 €/t |
| % gaps > 5 €/t | 58.8% |
| % gaps > 15 €/t | 19.1% |
| % fenêtres H20 avec roll | 39.5% |
| % fenêtres H40 avec roll | 78.1% |
| % fenêtres H60 avec roll | 98.9% |
| % dates avec ≥2 contrats | 14.9% |

## Implications pour la modélisation

- Les gaps de roll sont significatifs (moy. 9.83 €/t, max 54.25 €/t) — la série ajustée est indispensable pour toute analyse de retour.
- 98.9% des fenêtres H60 contiennent au moins un roll → les modèles H60 doivent impérativement utiliser la série ajustée.
- La courbe EMA reste quasi-inexistante (14.9% des dates avec ≥2 contrats simultanés).

## Roll le plus important

2025-03-05 : +30.0 €/t (EMA_H2025 → EMA_M2025)

## Artefact produit

`artefacts/ema_study/ema_contracts_rolls.json`

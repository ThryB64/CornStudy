# EMA 05 — Décomposition du Retour EMA

> Source exploratoire (Barchart proxy). Résultats expérimentaux.
> **Décomposition descriptive/contemporaine** — régresseurs non décalés. Non utilisable directement pour prédiction.

## Résultats clés

| Métrique | Valeur |
|---|---|
| R² modèle CBOT seul | 21.1% |
| R² modèle CBOT + basis_chg | 93.6% |
| **R² incrémental basis** | **+72.4%** |
| Corrélation CBOT_ret ↔ basis_chg | -0.537 |
| R² rolling moyen 260j | 97.9% |
| R² régime haute volatilité | 95.2% |
| R² régime basse volatilité | 86.6% |

## Interprétation

**Le changement de basis explique 72% de la variance du retour EMA** que CBOT seul n'explique pas. Ce résultat est contemporain : en ajoutant `basis_chg` (variation simultanée du spread EMA-CBOT), on capture presque entièrement le retour journalier EMA.

**Corrélation entre régresseurs** : -0.537. CBOT_ret et basis_chg sont significativement corrélés (multicolinéarité modérée). Les coefficients individuels doivent être interprétés avec prudence.

**Stabilité rolling** : le R² moyen sur fenêtres 260j est 97.9%, indiquant une relation stable dans le temps. La corrélation rolling est plus forte en haute volatilité (95.2%) qu'en basse (86.6%).

## Artefact produit

- `artefacts/ema_study/ema_return_decomposition.json`
- `artefacts/ema_study/ema_residual_series.parquet` (résidus OLS global pour NB-EMA-06)

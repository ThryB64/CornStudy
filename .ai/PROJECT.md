# Projet — Etude Mais

## Nom du projet

Etude Mais — Prévision professionnelle du prix du maïs

## Objectif

Construire une étude de prévision du prix du maïs (contrat CME) honnête, reproductible et opérationnelle. Le rapport final doit refléter exactement ce qui est implémenté, pas ce qui est prévu.

## Résultat final attendu

- Un rapport `docs/PROFESSIONAL_STUDY_REPORT.md` avec table d'implémentation ✅/❌/⚠️ exacte.
- Des benchmarks walk-forward sur 4 horizons (J+5, J+10, J+20, J+30).
- Des intervalles CQR calibrés (couverture cible 90%).
- Des régimes de marché détectés par Markov-switching (3 états : bull/range/bear).
- Une importance des facteurs calculée par SHAP (pas coefficient Ridge).
- Une décision agriculteur (SELL/STORE/WAIT) basée sur le tout.

## Stack technique

- Python 3.12, pandas, numpy, scikit-learn
- LightGBM, XGBoost, shap, statsmodels
- `src/mais/` — package principal
- `data/interim/` — données brutes collectées
- `data/processed/` — features.parquet, targets.parquet, factors.parquet
- `data/artefacts/professional_study/` — sorties étude

## Contraintes importantes

- Anti-leakage strict : `shift(1)` + z-scores expandants sur toutes les données fondamentales.
- Pas de data leakage : aucune donnée future ne peut apparaître dans les features.
- Imports optionnels : lightgbm, xgboost, shap, statsmodels dans des `try/except`.
- EIA éthanol nécessite une vraie clé API (`EIA_API_KEY`) — le collecteur est présent, un proxy corn/oil est utilisé en fallback.

## Ce qu'il ne faut pas casser

- `build_features()` — pipeline principal de features.
- `walk_forward_cqr()` — CQR calibré sur set de calibration séparé.
- `_build_regimes()` — doit retourner `Date, corn_close, return_60d, realized_vol_60d, regime_score, regime`.
- Table d'implémentation dans le rapport — ne jamais marquer ✅ ce qui n'est pas réellement implémenté.

## Philosophie

> "Rendre l'étude honnête, pas impressionnante."

# Projet — Etude Mais

## Nom du projet

Etude Mais — Étude statistique du cours du maïs CBOT & Euronext EMA

## Objectif (pivot 2026-05-20)

Mener une étude statistique et économique complète du cours du maïs CBOT et Euronext EMA, sans prétendre à un outil opérationnel non encore validé.

**Phrase directrice :** CBOT explique la tendance mondiale. EMA révèle la prime européenne via le basis. L'étude Euronext = basis + transmission CBOT→EMA + découplage + résidu EU.

## Résultat final attendu

- `docs/EMA_STUDY_FINAL_REPORT.md` — rapport statistique complet répondant aux 8 questions centrales.
- Cointegration EMA/CBOT confirmée ou infirmée (Engle-Granger + Johansen).
- Half-life du basis mesuré (ADF + AR(1)).
- Décomposition de variance EMA (R² par composante CBOT/EUR/basis/résidu).
- Benchmark directionnel EMA honnête avec IC95% et verdict go/no-go.
- Validation Granger OOF : CONFIRMÉ / PARTIEL / INFIRMÉ.
- Table ✅/❌/⚠️ exacte reflétant les vrais résultats OOF.

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

# EXT024 — Supply-demand directional benchmark

Teste si WASDE état de bilan (stationnaire) + Crop Condition améliorent la DIRECTION
H40/H90 au-delà du marché seul. Logit L2 walk-forward expandant, train-only, holdout
2024+ exclu. `run_EXT024.py` produit dataset, predictions, metrics, calibration,
coefficients, feature_dictionary.

Verdict : **IMPROVE (fort)**. Crop Condition @H90 = meilleur signal (DA 0.60→0.66,
AUC 0.61→0.71, stable) ; WASDE @H40 stabilise la 1re moitié. Fondamentaux complémentaires
du marché, pas autonomes. Détails : `results/.../README_results.md`.

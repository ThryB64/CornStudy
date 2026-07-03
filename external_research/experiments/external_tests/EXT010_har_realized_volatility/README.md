# EXT010 — HAR realized volatility

HAR-RV (Corsi) : vol réalisée h-jours forward sur RV passées 5/22/66 j, OLS expandant.
Comparé à RW de vol et rolling-20. `run_EXT010.py` produit `har_features.csv`,
`volatility_forecasts_EXT010.csv`, `metrics_EXT010.csv`.

Verdict : **KEEP** — HAR bat RW-vol et rolling-20 sur RMSE/MAE/QLIKE à tous les horizons
(avantage croissant à H90). Benchmark de volatilité principal recommandé.

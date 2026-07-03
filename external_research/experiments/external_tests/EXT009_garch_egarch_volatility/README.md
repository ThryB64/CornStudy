# EXT009 — GARCH / EGARCH / GJR-GARCH (risque)

Refit mensuel expandant, prévision h-jours de vol (dist. Student), vs RW-vol et rolling-20.
+ backtest d'un filtre de vol sur le score directionnel H90. `run_EXT009.py` produit
`metrics_EXT009.csv`, `volatility_forecasts_EXT009.csv`, `volatility_filter_backtest.csv`.

Verdict : **KEEP** (outil de risque). EGARCH = meilleur modèle de vol (≈ HAR, asymétrie en
plus). Le filtre de vol neutralise le décile haut de volatilité où le signal directionnel
s'inverse et perd → améliore DA (0.658→0.688) et PnL.

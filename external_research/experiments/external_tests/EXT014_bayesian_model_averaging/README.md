# EXT014 — Bayesian model averaging (BMA-like)

Combinaison pondérée par performance walk-forward passée (laguée) des membres
directionnels (market_only, +wasde, +crop, rw_baserate). `run_EXT014.py` produit
`metrics_EXT014.csv`, `model_weights_over_time.csv`, `bma_predictions.csv`.

Verdict : **IMPROVE** — gain de stabilité/robustesse, bat market_only, mais ne dépasse pas
le meilleur modèle seul par horizon. rw_baserate correctement neutralisé.

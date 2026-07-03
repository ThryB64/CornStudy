# EXT015 — Feature selection / importance (train-only)

Importance par permutation sur le TRAIN (RandomForest régularisé), dans chaque fenêtre
walk-forward (jamais sur tout le dataset). Compare RF toutes variables vs logit top-6
sélectionné train-only vs marché seul. `run_EXT015.py` produit
`feature_importance_by_horizon.csv`, `feature_stability.csv`,
`selected_features_walkforward.csv`, `metrics_EXT015.csv`.

Verdict : **KEEP** (diagnostic). `s2u_z`/`s2u_pctile` (WASDE) + `cond_gd_ex_anom`/
`cond_dev5y`/`cond_poor_vp` (Crop) + saisonnalité ressortent stables ; dummies
`bilan_tight/loose` et momentum court à jeter ; parcimonie > kitchen-sink RF.

# EXT007 — WASDE release features

Niveaux de bilan WASDE (vintage EXT026, `available_from`=publication+1BD) +
dummies calendrier USDA connus ex ante. `run_EXT007.py` produit
`wasde_release_features.csv` + `wasde_feature_dictionary.csv`.

Cible : log-retour CBOT t→t+h. Verdict : **IMPROVE** (gain DA stable +3-6 pts
H5-H40 ; RMSE dégradé par l'encodage en niveaux non-stationnaires — voir
`results/.../README_results.md`).

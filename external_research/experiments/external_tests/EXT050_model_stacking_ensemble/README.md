# EXT050 — Model stacking ensemble

Méta-logit sur les probabilités OOS des membres directionnels, walk-forward.
`run_EXT050.py` produit `metrics_EXT050.csv`, `ensemble_weights.csv`, `ensemble_predictions.csv`.

> Renommé `EXT028` → `EXT050` à l'étape 5 bis : `EXT028` (satellite_usda_report_proxy) ET
> `EXT029` (corn_crush_location_basis) sont déjà réservés dans `ideas_matrix.csv`. `EXT050`
> est hors plage catalogue (EXT001–EXT045) = ID interne étape 5.

Verdict : **REJECT** — le stacking sur-apprend (1re moitié ≤ 0.5, instable) et fait moins
bien que la moyenne simple et le meilleur membre seul (crop@H90 0.665). Parcimonie > empilement.

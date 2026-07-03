# EXT025 — Random walk & futures price benchmark

Hypothèse : aucun modèle ne vaut d'être lu sans tableau de référence des baselines triviales (Reeve & Vigfusson). Voir fiche `experiment_candidates.csv` et plan `docs/step3_execution_plan.md`.

- `run_ext025.py` : génère les prédictions RW / RW+drift / naive-last-return / MA20 pour CBOT (2000-2025) et EMA front (2010-2026), horizons H5/H10/H20/H30/H40/H90, info passée stricte.
- `evaluate_ext025.py` : RMSE/MAE/R²/DA + Diebold-Mariano vs RW (HAC, ajustement Harvey), par segment (`eval_pre2024` headline, `holdout_2024plus` séparé non comparé) et par sous-période.

Exécution : `./venv/bin/python run_ext025.py && ./venv/bin/python evaluate_ext025.py` (depuis la racine projet, chemins relatifs au script).

Résultats : `external_research/results/external_tests/EXT025_random_walk_and_futures_price_benchmark/` — **verdict KEEP** (voir `README_results.md`).

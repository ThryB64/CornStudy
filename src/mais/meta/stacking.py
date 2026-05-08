"""Stacking with walk-forward (no leakage from base to meta)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, META_DB_PARQUET, PREDICTIONS_DIR
from mais.utils import get_logger, read_parquet, write_parquet

from .meta_database import build_meta_database

log = get_logger("mais.meta.stacking")


def run_stacking(target: str = "y_logret_h20",
                 meta_model: str = "ridge") -> str:
    """Build meta-database (if needed) then fit a meta-model walk-forward."""
    if not META_DB_PARQUET.exists():
        try:
            build_meta_database(target=target)
        except FileNotFoundError as e:
            return f"Stacking aborted: {e}"
    meta = read_parquet(META_DB_PARQUET)
    if "y_true" not in meta.columns:
        return "Stacking aborted: meta-database missing y_true."

    pred_cols = [c for c in meta.columns if c.startswith("pred_")]
    if len(pred_cols) < 2:
        return f"Stacking needs >= 2 base models, got {len(pred_cols)}."

    meta = meta.dropna(subset=pred_cols + ["y_true"]).sort_values("Date").reset_index(drop=True)
    n = len(meta)
    if n < 200:
        return f"Stacking aborted: only {n} aligned rows in meta-database."

    # Walk-forward on the meta-table: train on growing window, predict next slice
    cut = max(int(n * 0.5), 100)
    pred = np.full(n, np.nan)
    while cut < n:
        next_cut = min(cut + 21, n)
        X_tr = meta.iloc[:cut][pred_cols].values
        y_tr = meta.iloc[:cut]["y_true"].values
        X_te = meta.iloc[cut:next_cut][pred_cols].values

        model = _build_meta(meta_model)
        model.fit(X_tr, y_tr)
        pred[cut:next_cut] = model.predict(X_te)

        cut = next_cut

    meta["pred_meta"] = pred
    out = ARTEFACTS_DIR / "meta_predictions.parquet"
    write_parquet(meta, out)

    valid = meta.dropna(subset=["pred_meta"])
    rmse = float(np.sqrt(np.mean((valid["pred_meta"] - valid["y_true"]) ** 2)))
    da = float(np.mean(np.sign(valid["pred_meta"]) == np.sign(valid["y_true"])))
    return (
        f"Stacking ({meta_model}) on target={target}\n"
        f"Base models: {len(pred_cols)}\n"
        f"Meta predictions: {valid.shape[0]} rows\n"
        f"RMSE = {rmse:.5f}\n"
        f"Directional accuracy = {da:.1%}\n"
        f"Wrote {out}"
    )


def _build_meta(name: str):
    name = name.lower()
    if name == "ridge":
        from sklearn.linear_model import Ridge
        return Ridge(alpha=1.0)
    if name == "lasso":
        from sklearn.linear_model import Lasso
        return Lasso(alpha=0.001, max_iter=5000)
    if name == "lgbm":
        try:
            import lightgbm as lgb
            return lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05,
                                       num_leaves=15, verbose=-1)
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor
            return GradientBoostingRegressor(n_estimators=200)
    raise ValueError(f"Unknown meta_model: {name}")

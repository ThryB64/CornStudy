"""Walk-forward training loop that produces out-of-fold predictions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mais.models import ModelAdapter
from mais.utils import get_logger

from .splits import generate_walk_forward_splits

log = get_logger("mais.walkforward.runner")


@dataclass
class WalkForwardRun:
    model_name: str
    target: str
    horizon: int
    predictions: pd.DataFrame   # columns: Date, y_true, y_pred, fold
    metrics_per_fold: pd.DataFrame


def walk_forward_run(
    adapter: ModelAdapter,
    features: pd.DataFrame,
    targets: pd.DataFrame,
    target_col: str,
    horizon: int,
    date_col: str = "Date",
    initial_train_years: int = 8,
    step_days: int = 21,
    embargo_days: int = 30,
) -> WalkForwardRun:
    """Run a walk-forward training of ``adapter`` on (features, targets[target_col])."""

    # Align on Date
    merged = features.merge(targets[[date_col, target_col]], on=date_col, how="inner")
    merged = merged.dropna(subset=[target_col]).reset_index(drop=True)
    if len(merged) == 0:
        raise ValueError(f"No rows remain after aligning features and target {target_col}.")

    feat_cols = [c for c in merged.columns if c not in (date_col, target_col)]

    splits = generate_walk_forward_splits(
        merged[date_col],
        initial_train_years=initial_train_years,
        step_days=step_days,
        horizon_days=horizon,
        embargo_days=embargo_days,
    )
    if not splits:
        raise ValueError("No walk-forward folds generated - dataset too small.")

    pred_rows = []
    metric_rows = []

    for fold_id, sp in enumerate(splits):
        X_tr = merged.iloc[sp.train_idx][feat_cols]
        y_tr = merged.iloc[sp.train_idx][target_col]
        X_te = merged.iloc[sp.test_idx][feat_cols]
        y_te = merged.iloc[sp.test_idx][target_col]
        d_te = merged.iloc[sp.test_idx][date_col]

        try:
            adapter.fit(X_tr, y_tr)
            y_hat = adapter.predict(X_te)
        except Exception as e:
            log.warning("fold_failed", fold=fold_id, model=adapter.meta.name, error=str(e))
            continue

        rmse = float(np.sqrt(np.mean((y_hat - y_te.values) ** 2)))
        mae = float(np.mean(np.abs(y_hat - y_te.values)))
        da = float(np.mean(np.sign(y_hat) == np.sign(y_te.values)))

        for d, t, p in zip(d_te.values, y_te.values, y_hat):
            pred_rows.append({
                date_col: d, "fold": fold_id, "y_true": float(t), "y_pred": float(p),
            })
        metric_rows.append({
            "fold": fold_id, "rmse": rmse, "mae": mae, "directional_accuracy": da,
            "test_start": sp.test_start_date, "test_end": sp.test_end_date,
        })

    return WalkForwardRun(
        model_name=adapter.meta.name,
        target=target_col,
        horizon=horizon,
        predictions=pd.DataFrame(pred_rows),
        metrics_per_fold=pd.DataFrame(metric_rows),
    )

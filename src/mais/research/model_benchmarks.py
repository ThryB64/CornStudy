"""Structured model benchmarking with walk-forward validation.

Wraps the study pipeline for use in research notebooks.
Produces organized DataFrames for direct plotting / comparison.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)

from mais.utils import get_logger

log = get_logger("mais.research.model_benchmarks")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def _da_non_neutral(y_true: np.ndarray, y_pred: np.ndarray, threshold: float = 0.002) -> float:
    """DA excluding near-zero predictions (the real directional signal)."""
    mask = np.abs(y_pred) > threshold
    if mask.sum() < 10:
        return float("nan")
    return float(np.mean(np.sign(y_true[mask]) == np.sign(y_pred[mask])))


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    problem: str = "regression",
) -> dict[str, float]:
    nan = float("nan")
    if problem == "classification":
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "auc": float(roc_auc_score(y_true, y_pred)) if len(np.unique(y_true)) == 2 else nan,
            "rmse": nan, "mae": nan, "r2": nan, "da": nan, "da_nn": nan,
        }
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    da   = float(np.mean(np.sign(y_true) == np.sign(y_pred))) if len(y_true) > 1 else nan
    da_nn = _da_non_neutral(y_true, y_pred)
    return {"rmse": rmse, "mae": mae, "r2": r2, "da": da, "da_nn": da_nn,
            "accuracy": nan, "auc": nan}


# ---------------------------------------------------------------------------
# Walk-forward engine
# ---------------------------------------------------------------------------

def walk_forward_benchmark(
    x: pd.DataFrame,
    y: pd.Series,
    models: dict[str, Any],
    *,
    min_train: int = 200,
    test_size: int = 50,
    problem: str = "regression",
    embargo: int = 5,
) -> pd.DataFrame:
    """Walk-forward with expanding window and optional embargo.

    Returns a DataFrame with one row per (model, fold), ready for aggregation.
    """
    n = len(x)
    splits: list[tuple[list[int], list[int]]] = []
    start = min_train
    while start + test_size <= n:
        tr = list(range(0, start))
        te = list(range(start + embargo, min(start + embargo + test_size, n)))
        if len(te) >= 10:
            splits.append((tr, te))
        start += test_size

    if not splits:
        log.warning("walk_forward_no_splits", n=n, min_train=min_train)
        return pd.DataFrame()

    rows = []
    for name, model in models.items():
        for fold_idx, (tr_idx, te_idx) in enumerate(splits):
            t0 = time.time()
            try:
                m = model.__class__(**model.get_params())
                m.fit(x.iloc[tr_idx], y.iloc[tr_idx])
                y_pred = m.predict(x.iloc[te_idx])
                metrics = compute_metrics(y.iloc[te_idx].values, np.array(y_pred), problem)
                rows.append({
                    "model": name,
                    "fold": fold_idx,
                    "train_size": len(tr_idx),
                    "test_size": len(te_idx),
                    "elapsed_s": round(time.time() - t0, 2),
                    **metrics,
                })
            except Exception as e:
                log.warning("model_fold_failed", model=name, fold=fold_idx, error=str(e))
    return pd.DataFrame(rows)


def aggregate_benchmark(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Average metrics across folds per model."""
    metric_cols = ["rmse", "mae", "r2", "da", "da_nn", "accuracy", "auc"]
    metric_cols = [c for c in metric_cols if c in fold_df.columns]
    agg = (
        fold_df.groupby("model")[metric_cols]
        .agg(lambda x: float(np.nanmean(x)))
        .reset_index()
    )
    n_folds = fold_df.groupby("model")["fold"].count().rename("n_folds")
    return agg.merge(n_folds, on="model")


def run_benchmark_suite(
    x: pd.DataFrame,
    y: pd.Series,
    horizon: int,
    target_col: str,
    *,
    models: dict[str, Any] | None = None,
    min_train: int = 300,
    test_size: int = 50,
    problem: str = "regression",
) -> dict[str, pd.DataFrame]:
    """Full benchmark: baselines + provided models. Returns fold_df + summary_df."""
    from sklearn.dummy import DummyClassifier, DummyRegressor
    from sklearn.ensemble import (
        HistGradientBoostingRegressor,
        RandomForestClassifier,
        RandomForestRegressor,
    )
    from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge

    if models is None:
        if problem == "regression":
            models = {
                "baseline_zero":     DummyRegressor(strategy="constant", constant=0),
                "baseline_mean":     DummyRegressor(strategy="mean"),
                "ridge":             Ridge(alpha=1.0),
                "elasticnet":        ElasticNet(alpha=0.01, l1_ratio=0.5),
                "rf":                RandomForestRegressor(n_estimators=100, n_jobs=1, random_state=42),
                "hgb":               HistGradientBoostingRegressor(max_iter=100, random_state=42),
            }
            try:
                import lightgbm as lgb
                models["lgbm"] = lgb.LGBMRegressor(n_estimators=100, verbose=-1, random_state=42)
            except ImportError:
                pass
            try:
                import xgboost as xgb
                models["xgb"] = xgb.XGBRegressor(n_estimators=100, verbosity=0, random_state=42)
            except ImportError:
                pass
        else:
            models = {
                "baseline_majority": DummyClassifier(strategy="most_frequent"),
                "logistic":          LogisticRegression(max_iter=500, random_state=42),
                "rf_clf":            RandomForestClassifier(n_estimators=100, n_jobs=1, random_state=42),
            }

    fold_df = walk_forward_benchmark(
        x, y, models, min_train=min_train, test_size=test_size, problem=problem,
    )
    summary = aggregate_benchmark(fold_df) if not fold_df.empty else pd.DataFrame()
    summary["horizon"] = horizon
    summary["target"] = target_col
    return {"folds": fold_df, "summary": summary}

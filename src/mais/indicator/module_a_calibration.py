"""OOF calibration for Module A context-signal weights."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.indicator.module_a_context import SIGNAL_DEFINITIONS, compute_context_timeseries
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

MODULE_A_CALIBRATION_JSON = ARTEFACTS_DIR / "module_a_calibration.json"


def prepare_weekly_signal_frame(
    context: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    target_col: str = "y_up_h20_ema",
) -> tuple[pd.DataFrame, list[str]]:
    """Join Module A signal columns to target and keep one point per week."""
    signal_cols = [f"signal_{name}" for name in SIGNAL_DEFINITIONS if f"signal_{name}" in context.columns]
    left = context[["Date", *signal_cols]].copy()
    right = targets[["Date", target_col]].copy()
    left["Date"] = pd.to_datetime(left["Date"]).dt.normalize()
    right["Date"] = pd.to_datetime(right["Date"]).dt.normalize()
    merged = left.merge(right, on="Date", how="inner").dropna(subset=[target_col])
    weekly = _one_point_per_week(merged)
    return weekly.reset_index(drop=True), signal_cols


def calibrate_module_a_weights(
    weekly: pd.DataFrame,
    signal_cols: list[str],
    *,
    target_col: str = "y_up_h20_ema",
    min_train_years: int = 3,
    n_random: int = 400,
    random_state: int = 42,
) -> dict[str, Any]:
    """Calibrate non-negative weights summing to one with expanding OOF validation."""
    if not signal_cols:
        raise ValueError("No Module A signal columns available for calibration")
    work = weekly.dropna(subset=[target_col]).copy()
    work["Date"] = pd.to_datetime(work["Date"])
    for col in signal_cols:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)
    equal_weights = np.repeat(1.0 / len(signal_cols), len(signal_cols))
    equal_score = work[signal_cols].to_numpy(dtype=float) @ equal_weights
    equal_da = _directional_accuracy(equal_score, work[target_col].to_numpy(dtype=int))

    rng = np.random.default_rng(random_state)
    splits = _year_splits(work["Date"], min_train_years=min_train_years)
    oof_rows: list[pd.DataFrame] = []
    fold_weights: list[np.ndarray] = []
    for train_idx, valid_idx, year in splits:
        x_train = work.iloc[train_idx][signal_cols].to_numpy(dtype=float)
        y_train = work.iloc[train_idx][target_col].to_numpy(dtype=int)
        weights = fit_nonnegative_weights(x_train, y_train, n_random=n_random, rng=rng)
        fold_weights.append(weights)
        x_valid = work.iloc[valid_idx][signal_cols].to_numpy(dtype=float)
        score = x_valid @ weights
        oof_rows.append(
            pd.DataFrame(
                {
                    "Date": work.iloc[valid_idx]["Date"].to_numpy(),
                    "validation_year": int(year),
                    "y_true": work.iloc[valid_idx][target_col].to_numpy(dtype=int),
                    "score": score,
                    "pred": (score > 0).astype(int),
                }
            )
        )
    oof = pd.concat(oof_rows, ignore_index=True) if oof_rows else pd.DataFrame()
    calibrated_da = (
        float(oof["pred"].astype(int).eq(oof["y_true"].astype(int)).mean()) if not oof.empty else None
    )
    weight_frame = pd.DataFrame(fold_weights, columns=signal_cols) if fold_weights else pd.DataFrame(columns=signal_cols)
    final_weights = fit_nonnegative_weights(
        work[signal_cols].to_numpy(dtype=float),
        work[target_col].to_numpy(dtype=int),
        n_random=n_random,
        rng=np.random.default_rng(random_state + 1),
    )
    weight_std_max = float(weight_frame.std().max()) if not weight_frame.empty else None
    return {
        "target_col": target_col,
        "n_weekly": int(len(work)),
        "n_oof": int(len(oof)),
        "signal_cols": signal_cols,
        "equal_da_weekly": _json_float(equal_da),
        "calibrated_da_weekly": _json_float(calibrated_da),
        "delta_calibrated_minus_equal": _diff(calibrated_da, equal_da),
        "weight_std_max": _json_float(weight_std_max),
        "weights_stable": bool(weight_std_max is not None and weight_std_max < 0.10),
        "final_weights": {col.replace("signal_", ""): _json_float(value) for col, value in zip(signal_cols, final_weights, strict=False)},
        "fold_weights": [
            {col.replace("signal_", ""): _json_float(value) for col, value in zip(signal_cols, weights, strict=False)}
            for weights in fold_weights
        ],
        "verdict": _verdict(calibrated_da, equal_da, weight_std_max),
    }


def fit_nonnegative_weights(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_random: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Fit interpretable weights by constrained random search around equal weights."""
    n_signals = x.shape[1]
    equal = np.repeat(1.0 / n_signals, n_signals)
    candidates = [equal]
    candidates.extend(np.eye(n_signals))
    alpha = np.repeat(6.0, n_signals)
    candidates.extend(rng.dirichlet(alpha, size=n_random))
    best = equal
    best_score = -np.inf
    for weights in candidates:
        score = x @ weights
        da = _directional_accuracy(score, y)
        penalty = 0.01 * float(np.linalg.norm(weights - equal))
        objective = da - penalty
        if objective > best_score:
            best_score = objective
            best = weights
    return best / best.sum()


def run_module_a_calibration(
    *,
    features_path: Path = FEATURES_PARQUET,
    targets_path: Path = EMA_TARGETS_PARQUET,
    output_path: Path = MODULE_A_CALIBRATION_JSON,
    max_date: str | pd.Timestamp = "2022-12-31",
) -> dict[str, Any]:
    """Compute Module A context, calibrate weights OOF and write JSON report."""
    features = pd.read_parquet(features_path)
    targets = pd.read_parquet(targets_path)
    features = features[pd.to_datetime(features["Date"]) <= pd.Timestamp(max_date)].copy()
    context = compute_context_timeseries(features)
    weekly, signal_cols = prepare_weekly_signal_frame(context, targets)
    report = calibrate_module_a_weights(weekly, signal_cols)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_ready(report), indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _directional_accuracy(score: np.ndarray, y: np.ndarray) -> float:
    pred = (score > 0).astype(int)
    return float((pred == y.astype(int)).mean()) if len(y) else float("nan")


def _year_splits(dates: pd.Series, *, min_train_years: int) -> list[tuple[np.ndarray, np.ndarray, int]]:
    years = pd.to_datetime(dates).dt.year.to_numpy()
    unique_years = sorted(pd.unique(years))
    splits: list[tuple[np.ndarray, np.ndarray, int]] = []
    for year in unique_years[min_train_years:]:
        train_idx = np.flatnonzero(years < year)
        valid_idx = np.flatnonzero(years == year)
        if len(train_idx) and len(valid_idx):
            splits.append((train_idx, valid_idx, int(year)))
    return splits


def _one_point_per_week(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["week_start"] = work["Date"] - pd.to_timedelta(work["Date"].dt.weekday, unit="D")
    work["_dow_distance"] = work["Date"].dt.weekday.abs()
    return (
        work.sort_values(["week_start", "_dow_distance", "Date"])
        .groupby("week_start", as_index=False)
        .first()
        .drop(columns=["week_start", "_dow_distance"])
    )


def _verdict(calibrated_da: float | None, equal_da: float | None, weight_std_max: float | None) -> str:
    delta = _diff(calibrated_da, equal_da)
    if delta is not None and delta > 0.01 and weight_std_max is not None and weight_std_max < 0.10:
        return "CALIBRATION_VALIDÉE"
    if delta is not None and delta > 0.01:
        return "CALIBRATION_GAIN_INSTABLE"
    return "CALIBRATION_NEUTRE"


def _diff(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    value = float(left) - float(right)
    return value if np.isfinite(value) else None


def _json_float(value: Any) -> float | None:
    if value is None:
        return None
    out = float(value)
    return out if np.isfinite(out) else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


if __name__ == "__main__":
    result = run_module_a_calibration()
    print(json.dumps(_json_ready(result), indent=2, ensure_ascii=False))

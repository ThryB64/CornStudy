"""Weekly validation of EMA benchmark directional accuracy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import EMA_BENCHMARK_DIR, FEATURES_PARQUET, TARGETS_PARQUET
from mais.research.ema_benchmark import (
    TARGETS,
    _build_benchmark_frame,
    _load_selected_features,
    build_feature_sets,
    walk_forward_da,
)
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

WEEKLY_DA_REPORT = EMA_BENCHMARK_DIR / "weekly_da_report.json"


def compute_weekly_da(
    oof_predictions: pd.DataFrame,
    *,
    day_of_week: int = 0,
    n_bootstrap: int = 1000,
    random_state: int = 42,
) -> dict[str, Any]:
    """Compare daily DA with one validation point per week."""
    required = {"Date", "y_true", "y_pred"}
    missing = required - set(oof_predictions.columns)
    if missing:
        raise ValueError(f"Missing OOF prediction columns: {sorted(missing)}")
    work = oof_predictions.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    work = work.dropna(subset=["Date", "y_true", "y_pred"]).sort_values("Date")
    if work.empty:
        return _empty_weekly_result(n_bootstrap, "empty predictions")
    daily_correct = work["y_true"].astype(int).eq(work["y_pred"].astype(int)).to_numpy()
    weekly = _one_point_per_week(work, day_of_week=day_of_week)
    weekly_correct = weekly["y_true"].astype(int).eq(weekly["y_pred"].astype(int)).to_numpy()
    da_daily = float(daily_correct.mean())
    da_weekly = float(weekly_correct.mean()) if len(weekly_correct) else np.nan
    delta = da_daily - da_weekly if np.isfinite(da_weekly) else np.nan
    return {
        "status": "OK",
        "day_of_week": int(day_of_week),
        "n_daily": int(len(work)),
        "n_weekly": int(len(weekly)),
        "da_daily": _json_float(da_daily),
        "da_weekly": _json_float(da_weekly),
        "da_weekly_ci95_lo": _bootstrap_da_ci(weekly_correct, n_bootstrap=n_bootstrap, random_state=random_state)[0],
        "da_weekly_ci95_hi": _bootstrap_da_ci(weekly_correct, n_bootstrap=n_bootstrap, random_state=random_state)[1],
        "delta_daily_minus_weekly": _json_float(delta),
        "autocorr_flag": bool(np.isfinite(delta) and delta > 0.05),
        "weekly_reference_pass": bool(np.isfinite(da_weekly) and da_weekly >= 0.53),
        "weekly_dates_start": weekly["Date"].min().date().isoformat() if not weekly.empty else None,
        "weekly_dates_end": weekly["Date"].max().date().isoformat() if not weekly.empty else None,
    }


def run_weekly_da_report(
    *,
    features_path: Path = FEATURES_PARQUET,
    cbot_targets_path: Path = TARGETS_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_path: Path = WEEKLY_DA_REPORT,
    max_date: str | pd.Timestamp = "2022-12-31",
    day_of_week: int = 0,
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    """Run weekly DA validation for all EXP-BENCH-02 target and feature sets."""
    features = pd.read_parquet(features_path)
    cbot_targets = pd.read_parquet(cbot_targets_path)
    ema_targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = _build_benchmark_frame(features, cbot_targets, ema_targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_sets = build_feature_sets(selected, available_columns=set(work.columns))

    rows: list[dict[str, Any]] = []
    for target_col in TARGETS:
        if target_col not in work.columns:
            continue
        for feature_set, columns in feature_sets.items():
            usable = [col for col in columns if col in work.columns]
            if not usable:
                rows.append(
                    {
                        "target_col": target_col,
                        "feature_set": feature_set,
                        **_empty_weekly_result(n_bootstrap, "empty feature set"),
                    }
                )
                continue
            frame = work[["Date", target_col, *usable]].dropna(subset=[target_col]).copy()
            result = walk_forward_da(
                frame[usable],
                frame[target_col],
                frame["Date"],
                n_bootstrap=0,
            )
            predictions = result.get("predictions")
            if not isinstance(predictions, pd.DataFrame) or predictions.empty:
                weekly = _empty_weekly_result(n_bootstrap, "no OOF predictions")
            else:
                weekly = compute_weekly_da(
                    predictions,
                    day_of_week=day_of_week,
                    n_bootstrap=n_bootstrap,
                )
            rows.append(
                {
                    "target_col": target_col,
                    "feature_set": feature_set,
                    "n_features": int(len(usable)),
                    **weekly,
                }
            )
    primary = _primary_weekly(rows)
    payload = {
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
        "day_of_week": int(day_of_week),
        "day_name": _day_name(day_of_week),
        "max_date": str(max_date),
        "results": rows,
        "primary_ema_weekly": primary,
        "verdict": _weekly_verdict(primary),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _one_point_per_week(frame: pd.DataFrame, *, day_of_week: int) -> pd.DataFrame:
    work = frame.copy()
    work["week_start"] = work["Date"] - pd.to_timedelta(work["Date"].dt.weekday, unit="D")
    work["_dow_distance"] = (work["Date"].dt.weekday - day_of_week).abs()
    return (
        work.sort_values(["week_start", "_dow_distance", "Date"])
        .groupby("week_start", as_index=False)
        .first()
        .drop(columns=["week_start", "_dow_distance"])
        .reset_index(drop=True)
    )


def _bootstrap_da_ci(
    correct: np.ndarray,
    *,
    n_bootstrap: int,
    random_state: int,
) -> tuple[float | None, float | None]:
    if len(correct) == 0 or n_bootstrap <= 0:
        return None, None
    rng = np.random.default_rng(random_state)
    values = [float(correct[rng.integers(0, len(correct), size=len(correct))].mean()) for _ in range(n_bootstrap)]
    lo, hi = np.nanpercentile(values, [2.5, 97.5])
    return _json_float(lo), _json_float(hi)


def _primary_weekly(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        if row.get("target_col") == "y_up_h20_ema" and row.get("feature_set") == "cbot_ema_combined":
            return row
    return None


def _weekly_verdict(primary: dict[str, Any] | None) -> str:
    if not primary:
        return "NO_PRIMARY_EMA_WEEKLY"
    if primary.get("autocorr_flag"):
        return "DAILY_INFLATED_BY_AUTOCORR"
    if (primary.get("da_weekly") or 0.0) >= 0.53:
        return "WEEKLY_USEFUL"
    return "WEEKLY_NO_GO"


def _empty_weekly_result(n_bootstrap: int, reason: str) -> dict[str, Any]:
    return {
        "status": "SKIPPED",
        "reason": reason,
        "bootstrap_n": int(n_bootstrap),
        "n_daily": 0,
        "n_weekly": 0,
        "da_daily": None,
        "da_weekly": None,
        "da_weekly_ci95_lo": None,
        "da_weekly_ci95_hi": None,
        "delta_daily_minus_weekly": None,
        "autocorr_flag": False,
        "weekly_reference_pass": False,
        "weekly_dates_start": None,
        "weekly_dates_end": None,
    }


def _day_name(day_of_week: int) -> str:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week]


def _json_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
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
    report = run_weekly_da_report()
    print(json.dumps(_json_ready(report["verdict"]), indent=2, ensure_ascii=False))
    print(json.dumps(_json_ready(report["primary_ema_weekly"]), indent=2, ensure_ascii=False))

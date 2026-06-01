"""Benchmark the EMA 3-month storage profitability target."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET
from mais.research.ema_benchmark import _load_selected_features, build_feature_sets, walk_forward_da
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

STORAGE_BENCHMARK_EMA_JSON = ARTEFACTS_DIR / "storage_benchmark_ema.json"
TARGET_COL = "y_storage_profit_3m"
VALUE_COL = "y_storage_value_3m"


def run_storage_benchmark_ema(
    *,
    features_path: Path = FEATURES_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_path: Path = STORAGE_BENCHMARK_EMA_JSON,
    max_date: str | pd.Timestamp = "2022-12-31",
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    """Benchmark whether models predict profitable 3-month EMA storage."""
    features = pd.read_parquet(features_path)
    ema_targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = _build_storage_frame(features, ema_targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_sets = _storage_feature_sets(selected, work.columns)
    rows: list[dict[str, Any]] = []
    for feature_set, columns in feature_sets.items():
        rows.append(_evaluate_storage_set(work, feature_set, columns, n_bootstrap=n_bootstrap))
    baselines = storage_baselines(work)
    best = _best_model(rows)
    payload = {
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
        "target_col": TARGET_COL,
        "value_col": VALUE_COL,
        "max_date": str(max_date),
        "positive_rate": _json_float(work[TARGET_COL].dropna().mean()),
        "n_rows": int(work[TARGET_COL].notna().sum()),
        "baselines": baselines,
        "models": rows,
        "best_model": best,
        "verdict": _verdict(best),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def storage_baselines(frame: pd.DataFrame) -> dict[str, dict[str, float | int | None]]:
    """Compute naive storage baselines from actual 3-month storage value."""
    work = frame.dropna(subset=[TARGET_COL, VALUE_COL]).copy()
    if work.empty:
        return {}
    y = work[TARGET_COL].astype(int)
    value = work[VALUE_COL].astype(float)
    return {
        "always_store": {
            "da": _json_float(y.mean()),
            "avg_gain_eur_t": _json_float(value.mean()),
            "n": int(len(work)),
        },
        "never_store": {
            "da": _json_float((1 - y).mean()),
            "avg_gain_eur_t": 0.0,
            "n": int(len(work)),
        },
        "oracle_store_if_profitable": {
            "da": 1.0,
            "avg_gain_eur_t": _json_float(value.clip(lower=0).mean()),
            "n": int(len(work)),
        },
    }


def _evaluate_storage_set(
    work: pd.DataFrame,
    feature_set: str,
    columns: list[str],
    *,
    n_bootstrap: int,
) -> dict[str, Any]:
    usable = [col for col in columns if col in work.columns]
    frame = work[["Date", TARGET_COL, VALUE_COL, *usable]].dropna(subset=[TARGET_COL, VALUE_COL]).copy()
    result = walk_forward_da(
        frame[usable],
        frame[TARGET_COL],
        frame["Date"],
        n_bootstrap=n_bootstrap,
    )
    predictions = result.pop("predictions", pd.DataFrame())
    economics = _storage_economics(predictions, frame[["Date", VALUE_COL]])
    return {
        "feature_set": feature_set,
        "n_features": int(len(usable)),
        "features": usable,
        "status": result["status"],
        "n_oof": result["n_oof"],
        "da": result["da"],
        "da_ci95_lo": result["da_ci95_lo"],
        "da_ci95_hi": result["da_ci95_hi"],
        "auc": result["auc"],
        "top20_da": result["top20_da"],
        "annual_stability": result["annual_stability"],
        **economics,
    }


def _storage_economics(predictions: pd.DataFrame, values: pd.DataFrame) -> dict[str, Any]:
    if predictions.empty:
        return {"avg_gain_eur_t": None, "pct_store": None, "n_economic": 0}
    joined = predictions.copy()
    joined["Date"] = pd.to_datetime(joined["Date"]).dt.normalize()
    value_frame = values.copy()
    value_frame["Date"] = pd.to_datetime(value_frame["Date"]).dt.normalize()
    joined = joined.merge(value_frame, on="Date", how="left").dropna(subset=[VALUE_COL])
    if joined.empty:
        return {"avg_gain_eur_t": None, "pct_store": None, "n_economic": 0}
    store = joined["y_pred"].astype(int).eq(1)
    gain = np.where(store, joined[VALUE_COL].astype(float), 0.0)
    return {
        "avg_gain_eur_t": _json_float(float(np.mean(gain))),
        "pct_store": _json_float(float(store.mean())),
        "n_economic": int(len(joined)),
    }


def _build_storage_frame(
    features: pd.DataFrame,
    ema_targets: pd.DataFrame,
    *,
    max_date: str | pd.Timestamp,
) -> pd.DataFrame:
    work = features.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    targets = ema_targets[["Date", TARGET_COL, VALUE_COL]].copy()
    targets["Date"] = pd.to_datetime(targets["Date"]).dt.normalize()
    work = work.merge(targets, on="Date", how="inner")
    work = work[work["Date"] <= pd.Timestamp(max_date)].copy()
    if "ema_data_availability_score" in work.columns:
        work = work[pd.to_numeric(work["ema_data_availability_score"], errors="coerce") > 0].copy()
    return work.sort_values("Date").reset_index(drop=True)


def _storage_feature_sets(selected: list[str], available_columns: pd.Index) -> dict[str, list[str]]:
    sets = build_feature_sets(selected, available_columns=set(available_columns))
    return {
        "cbot_only": sets["cbot_only"],
        "ema_curve_only": sets["ema_curve_only"],
        "cbot_ema_combined": sets["cbot_ema_combined"],
        "selected_full": [col for col in selected if col in set(available_columns)],
    }


def _best_model(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [row for row in rows if row.get("da") is not None]
    if not valid:
        return None
    return max(valid, key=lambda row: (row.get("da") or -1, row.get("avg_gain_eur_t") or -999))


def _verdict(best: dict[str, Any] | None) -> str:
    if not best:
        return "NO_VALID_MODEL"
    if (best.get("da") or 0.0) > 0.55 and (best.get("avg_gain_eur_t") or -999.0) > 0:
        return "STORAGE_USEFUL"
    if (best.get("da") or 0.0) > 0.55:
        return "DA_OK_ECONOMICS_WEAK"
    return "STORAGE_NO_GO"


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
    report = run_storage_benchmark_ema()
    print(json.dumps(_json_ready({"verdict": report["verdict"], "best_model": report["best_model"]}), indent=2, ensure_ascii=False))

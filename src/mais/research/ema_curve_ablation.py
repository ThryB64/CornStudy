"""Ablation study for Euronext EMA curve feature families."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, TARGETS_PARQUET
from mais.research.ema_benchmark import (
    _benjamini_hochberg,
    _build_benchmark_frame,
    _load_selected_features,
    _two_rate_p_value,
    build_feature_sets,
    walk_forward_da,
)
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

EMA_CURVE_ABLATION_JSON = ARTEFACTS_DIR / "ema_curve_ablation.json"

EMA_CURVE_FAMILIES: dict[str, list[str]] = {
    "price_levels": [
        "ema_front_price",
        "ema_second_price",
        "ema_third_price",
        "ema_harvest_nov_price",
        "ema_next_march_price",
        "ema_liquid_price",
        "cbot_eur_t",
    ],
    "spreads": [
        "ema_spread_f0_f1",
        "ema_spread_f1_f2",
        "ema_spread_f0_f2",
        "ema_spread_nov_mar",
    ],
    "slope": ["ema_curve_slope_3", "ema_curve_slope_6"],
    "flags": ["ema_contango_flag", "ema_backwardation_flag"],
    "carry": ["ema_carry_front_second", "ema_roll_yield_ann"],
    "liquidity": [
        "ema_oi_total",
        "ema_volume_total",
        "ema_oi_concentration",
        "ema_liquidity_shift",
        "ema_open_interest_available",
        "ema_curve_contract_count",
    ],
    "basis_cbot": [
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        "ema_cbot_rel_strength_20d",
    ],
    "adjusted_returns": ["ema_front_return_5d_adjusted", "ema_front_vol_20d_adjusted"],
    "continuous_lags": [
        "ema_front_price_lag1",
        "ema_front_return_5d_lag1",
        "ema_liquid_price_lag1",
        "ema_liquid_return_5d_lag1",
        "ema_harvest_nov_price_lag1",
        "ema_harvest_nov_return_5d_lag1",
    ],
}


def run_ema_curve_ablation(
    *,
    features_path: Path = FEATURES_PARQUET,
    cbot_targets_path: Path = TARGETS_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_path: Path = EMA_CURVE_ABLATION_JSON,
    target_col: str = "y_up_h20",
    max_date: str | pd.Timestamp = "2022-12-31",
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    """Measure marginal value of EMA curve families over selected CBOT baseline."""
    features = pd.read_parquet(features_path)
    cbot_targets = pd.read_parquet(cbot_targets_path)
    ema_targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = _build_benchmark_frame(features, cbot_targets, ema_targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_sets = build_feature_sets(selected, available_columns=set(work.columns))
    baseline_features = feature_sets["cbot_only"]
    if target_col not in work.columns:
        raise ValueError(f"Target column not available for EMA curve ablation: {target_col}")
    if not baseline_features:
        raise ValueError("No selected CBOT baseline features available for EMA curve ablation")

    baseline = _evaluate_feature_list(
        work,
        target_col,
        baseline_features,
        n_bootstrap=n_bootstrap,
    )
    family_rows: list[dict[str, Any]] = []
    p_values: list[float] = []
    p_value_indices: list[int] = []
    for family, columns in _families_with_all().items():
        available = [col for col in columns if col in work.columns]
        result = _evaluate_feature_list(
            work,
            target_col,
            [*baseline_features, *available],
            n_bootstrap=n_bootstrap,
        )
        row = {
            "family": family,
            "target_col": target_col,
            "n_family_features": int(len(available)),
            "family_features": available,
            "baseline_da": baseline["da"],
            "baseline_auc": baseline["auc"],
            "da_with_family": result["da"],
            "auc_with_family": result["auc"],
            "top20_with_family": result["top20_da"],
            "n_oof": result["n_oof"],
            "delta_da": _diff(result["da"], baseline["da"]),
            "delta_auc": _diff(result["auc"], baseline["auc"]),
            "recommendation": _recommendation(_diff(result["da"], baseline["da"])),
        }
        p_value = _two_rate_p_value(result["da"], result["n_oof"], baseline["da"], baseline["n_oof"])
        row["p_value_vs_baseline"] = p_value
        p_values.append(p_value)
        p_value_indices.append(len(family_rows))
        family_rows.append(row)
    q_values = _benjamini_hochberg(p_values)
    for idx, q_value in zip(p_value_indices, q_values, strict=False):
        family_rows[idx]["bh_q_value"] = q_value
        family_rows[idx]["bh_reject_0_05"] = bool(q_value <= 0.05)

    payload = {
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
        "target_col": target_col,
        "max_date": str(max_date),
        "baseline": {
            "feature_set": "cbot_only",
            "n_features": int(len(baseline_features)),
            "features": baseline_features,
            "da": baseline["da"],
            "auc": baseline["auc"],
            "top20_da": baseline["top20_da"],
            "n_oof": baseline["n_oof"],
        },
        "families": sorted(family_rows, key=lambda row: (row["delta_da"] is None, -(row["delta_da"] or -999))),
        "summary": _summary(family_rows),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _evaluate_feature_list(
    work: pd.DataFrame,
    target_col: str,
    features: list[str],
    *,
    n_bootstrap: int,
) -> dict[str, Any]:
    usable = list(dict.fromkeys([col for col in features if col in work.columns]))
    frame = work[["Date", target_col, *usable]].dropna(subset=[target_col]).copy()
    result = walk_forward_da(
        frame[usable],
        frame[target_col],
        frame["Date"],
        n_bootstrap=n_bootstrap,
    )
    result.pop("predictions", None)
    return result


def _families_with_all() -> dict[str, list[str]]:
    all_cols = sorted({col for cols in EMA_CURVE_FAMILIES.values() for col in cols})
    return {**EMA_CURVE_FAMILIES, "all_ema_curve": all_cols}


def _recommendation(delta_da: float | None) -> str:
    if delta_da is None:
        return "NEUTRE"
    if delta_da > 0.01:
        return "GARDER"
    if delta_da < -0.01:
        return "RETIRER"
    return "NEUTRE"


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_rec: dict[str, int] = {"GARDER": 0, "NEUTRE": 0, "RETIRER": 0}
    for row in rows:
        by_rec[row["recommendation"]] = by_rec.get(row["recommendation"], 0) + 1
    best = max(rows, key=lambda row: row["delta_da"] if row["delta_da"] is not None else -999)
    worst = min(rows, key=lambda row: row["delta_da"] if row["delta_da"] is not None else 999)
    return {
        "recommendation_counts": by_rec,
        "best_family": best["family"],
        "best_delta_da": best["delta_da"],
        "worst_family": worst["family"],
        "worst_delta_da": worst["delta_da"],
    }


def _diff(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    value = float(left) - float(right)
    return value if np.isfinite(value) else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        out = float(value)
        return out if np.isfinite(out) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


if __name__ == "__main__":
    report = run_ema_curve_ablation()
    print(json.dumps(_json_ready(report["summary"]), indent=2, ensure_ascii=False))

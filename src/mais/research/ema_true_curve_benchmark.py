"""Benchmark reliable EMA features when the historical curve is sparse."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import EMA_BENCHMARK_DIR, FEATURES_PARQUET, TARGETS_PARQUET
from mais.research.ema_benchmark import (
    apply_benjamini_hochberg,
    build_feature_sets,
    walk_forward_da,
)
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

TRUE_CURVE_BENCHMARK_JSON = EMA_BENCHMARK_DIR / "ema_true_curve_benchmark.json"
TRUE_CURVE_BENCHMARK_CSV = EMA_BENCHMARK_DIR / "ema_true_curve_benchmark.csv"
TRUE_CURVE_TARGETS = ("y_up_h20", "y_up_h20_ema_raw")

PURE_EMA_RELIABLE_FEATURES: tuple[str, ...] = (
    "ema_front_price_lag1",
    "ema_liquid_price_lag1",
    "ema_harvest_nov_price_lag1",
    "ema_oi_total",
    "ema_volume_total",
    "ema_front_return_5d_adjusted",
    "ema_front_vol_20d_adjusted",
)
BASIS_FEATURES: tuple[str, ...] = (
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
)
CBOT_EUR_T_FEATURES: tuple[str, ...] = ("cbot_eur_t",)
FORBIDDEN_SPARSE_CURVE_TOKENS = ("spread", "slope", "carry", "contango", "backwardation", "roll_yield")


def run_ema_true_curve_benchmark(
    *,
    features_path: Path = FEATURES_PARQUET,
    cbot_targets_path: Path = TARGETS_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_path: Path = TRUE_CURVE_BENCHMARK_JSON,
    table_output_path: Path = TRUE_CURVE_BENCHMARK_CSV,
    max_date: str | pd.Timestamp = "2022-12-31",
    n_bootstrap: int = 1000,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run a sparse-curve-safe benchmark for EMA feature groups."""
    features = pd.read_parquet(features_path)
    cbot_targets = pd.read_parquet(cbot_targets_path)
    ema_targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = _build_true_curve_frame(features, cbot_targets, ema_targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_groups = build_true_curve_feature_groups(selected, available_columns=set(work.columns))

    rows: list[dict[str, Any]] = []
    for target_col in TRUE_CURVE_TARGETS:
        for feature_group, columns in feature_groups.items():
            rows.append(
                _evaluate_group(
                    work,
                    target_col=target_col,
                    feature_group=feature_group,
                    columns=columns,
                    n_bootstrap=n_bootstrap,
                )
            )
    results = apply_benjamini_hochberg(pd.DataFrame(rows), baseline_feature_set="cbot_only")
    decision = decide_true_curve_signal(results)
    payload = {
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
        "max_date": str(max_date),
        "targets": list(TRUE_CURVE_TARGETS),
        "feature_groups": feature_groups,
        "forbidden_sparse_curve_tokens": list(FORBIDDEN_SPARSE_CURVE_TOKENS),
        "results": results.to_dict(orient="records"),
        "decision": decision,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    results.to_csv(table_output_path, index=False)
    return results, decision


def build_true_curve_feature_groups(
    selected_features: list[str],
    *,
    available_columns: set[str],
) -> dict[str, list[str]]:
    """Build feature groups that avoid sparse curve artefacts."""
    selected_sets = build_feature_sets(selected_features, available_columns=available_columns)
    pure = _available(PURE_EMA_RELIABLE_FEATURES, available_columns)
    basis = _available(BASIS_FEATURES, available_columns)
    cbot_eur_t = _available(CBOT_EUR_T_FEATURES, available_columns)
    groups = {
        "cbot_only": selected_sets["cbot_only"],
        "selected_ema_curve_only": _without_sparse_curve_tokens(selected_sets["ema_curve_only"]),
        "reliable_ema_no_basis": pure,
        "reliable_ema_with_basis": [*pure, *basis],
        "reliable_ema_with_basis_and_cbot_eur_t": [*pure, *basis, *cbot_eur_t],
        "basis_only": basis,
        "cbot_eur_t_only": cbot_eur_t,
    }
    return {name: list(dict.fromkeys(cols)) for name, cols in groups.items()}


def decide_true_curve_signal(results: pd.DataFrame) -> dict[str, Any]:
    """Classify whether reliable EMA features contain a usable signal."""
    cbot_target = results[results["target_col"].eq("y_up_h20")]
    cbot_only = _group_row(cbot_target, "cbot_only")
    pure = _group_row(cbot_target, "reliable_ema_no_basis")
    with_basis = _group_row(cbot_target, "reliable_ema_with_basis")
    with_basis_cbot = _group_row(cbot_target, "reliable_ema_with_basis_and_cbot_eur_t")
    basis_only = _group_row(cbot_target, "basis_only")
    cbot_eur_t_only = _group_row(cbot_target, "cbot_eur_t_only")

    pure_pass = _passes_reliability(pure)
    basis_pass = _passes_reliability(with_basis)
    cbot_da = _safe_float(cbot_only.get("da")) if cbot_only is not None else math.nan
    with_basis_da = _safe_float(with_basis.get("da")) if with_basis is not None else math.nan
    pure_da = _safe_float(pure.get("da")) if pure is not None else math.nan
    cbot_eur_t_da = _safe_float(cbot_eur_t_only.get("da")) if cbot_eur_t_only is not None else math.nan

    verdict = "NO_RELIABLE_CURVE_SIGNAL"
    if pure_pass:
        verdict = "PURE_EMA_SIGNAL_CONFIRMED"
    elif basis_pass and math.isfinite(cbot_da) and with_basis_da >= cbot_da + 0.02:
        verdict = "BASIS_DRIVEN_SIGNAL"
    elif (
        math.isfinite(cbot_eur_t_da)
        and math.isfinite(with_basis_da)
        and abs(cbot_eur_t_da - with_basis_da) <= 0.01
        and (not math.isfinite(pure_da) or pure_da < 0.53)
    ):
        verdict = "CBOT_TRANSLATION_DRIVEN"

    return {
        "verdict": verdict,
        "reason": _decision_reason(verdict),
        "cbot_target": {
            "cbot_only": _row_summary(cbot_only),
            "reliable_ema_no_basis": _row_summary(pure),
            "reliable_ema_with_basis": _row_summary(with_basis),
            "reliable_ema_with_basis_and_cbot_eur_t": _row_summary(with_basis_cbot),
            "basis_only": _row_summary(basis_only),
            "cbot_eur_t_only": _row_summary(cbot_eur_t_only),
        },
        "ema_target": {
            "reliable_ema_no_basis": _row_summary(_group_row(results[results["target_col"].eq("y_up_h20_ema_raw")], "reliable_ema_no_basis")),
            "reliable_ema_with_basis": _row_summary(_group_row(results[results["target_col"].eq("y_up_h20_ema_raw")], "reliable_ema_with_basis")),
        },
    }


def _evaluate_group(
    work: pd.DataFrame,
    *,
    target_col: str,
    feature_group: str,
    columns: list[str],
    n_bootstrap: int,
) -> dict[str, Any]:
    usable = [col for col in columns if col in work.columns]
    base = {
        "target_col": target_col,
        "feature_set": feature_group,
        "features": usable,
        "n_features": len(usable),
    }
    if target_col not in work.columns:
        return {**base, **_empty_result(f"missing target {target_col}", n_bootstrap)}
    if not usable:
        return {**base, **_empty_result("empty feature group", n_bootstrap)}
    frame = work[["Date", target_col, *usable]].dropna(subset=[target_col]).copy()
    if frame[target_col].nunique(dropna=True) < 2:
        return {**base, **_empty_result("target has fewer than two classes", n_bootstrap)}
    result = walk_forward_da(frame[usable], frame[target_col], frame["Date"], n_bootstrap=n_bootstrap)
    result.pop("predictions", None)
    return {**base, **result}


def _build_true_curve_frame(
    features: pd.DataFrame,
    cbot_targets: pd.DataFrame,
    ema_targets: pd.DataFrame,
    *,
    max_date: str | pd.Timestamp,
) -> pd.DataFrame:
    work = _normalise_dates(features)
    cbot = _normalise_dates(cbot_targets)
    ema = _normalise_dates(ema_targets)
    if "y_up_h20" in cbot.columns:
        work = work.merge(cbot[["Date", "y_up_h20"]], on="Date", how="left")
    if "y_up_h20_ema_raw" not in ema.columns and "y_up_h20_ema" in ema.columns:
        ema["y_up_h20_ema_raw"] = ema["y_up_h20_ema"]
    if "y_up_h20_ema_raw" in ema.columns:
        work = work.merge(ema[["Date", "y_up_h20_ema_raw"]], on="Date", how="left")
    work = work[work["Date"] <= pd.Timestamp(max_date)].copy()
    if "ema_data_availability_score" in work.columns:
        work = work[pd.to_numeric(work["ema_data_availability_score"], errors="coerce") > 0].copy()
    return work.sort_values("Date").reset_index(drop=True)


def _normalise_dates(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    return work


def _load_selected_features(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    selected = payload.get("selected_features", [])
    if not isinstance(selected, list) or not selected:
        raise ValueError(f"No selected_features in {path}")
    return [str(col) for col in selected]


def _available(columns: tuple[str, ...], available: set[str]) -> list[str]:
    return [col for col in columns if col in available]


def _without_sparse_curve_tokens(columns: list[str]) -> list[str]:
    return [
        col
        for col in columns
        if not any(token in col for token in FORBIDDEN_SPARSE_CURVE_TOKENS)
    ]


def _group_row(results: pd.DataFrame, feature_group: str) -> pd.Series | None:
    row = results[results["feature_set"].eq(feature_group)]
    if row.empty:
        return None
    return row.iloc[0]


def _passes_reliability(row: pd.Series | None) -> bool:
    if row is None or row.get("status") != "OK":
        return False
    return (
        _safe_float(row.get("da")) > 0.55
        and _safe_float(row.get("da_ci95_lo")) > 0.50
        and _safe_float(row.get("auc")) > 0.55
    )


def _row_summary(row: pd.Series | None) -> dict[str, Any] | None:
    if row is None:
        return None
    keys = [
        "target_col",
        "feature_set",
        "status",
        "reason",
        "n_oof",
        "n_features",
        "da",
        "da_ci95_lo",
        "da_ci95_hi",
        "auc",
        "auc_ci95_lo",
        "auc_ci95_hi",
        "top20_da",
        "annual_stability",
        "bh_q_value",
    ]
    return {key: _json_scalar(row.get(key)) for key in keys if key in row}


def _empty_result(reason: str, n_bootstrap: int) -> dict[str, Any]:
    return {
        "status": "SKIPPED",
        "reason": reason,
        "n_train_validation_rows": 0,
        "n_oof": 0,
        "n_splits": 0,
        "bootstrap_n": int(n_bootstrap),
        "da": None,
        "da_ci95_lo": None,
        "da_ci95_hi": None,
        "auc": None,
        "auc_ci95_lo": None,
        "auc_ci95_hi": None,
        "top20_da": None,
        "split_das": [],
        "annual_da": {},
        "annual_stability": None,
        "annual_da_min": None,
        "annual_da_std": None,
    }


def _decision_reason(verdict: str) -> str:
    if verdict == "PURE_EMA_SIGNAL_CONFIRMED":
        return "Pure reliable EMA price/liquidity/adjusted-return features clear reliability thresholds."
    if verdict == "BASIS_DRIVEN_SIGNAL":
        return "Reliable EMA works mainly through CBOT-EMA basis rather than pure local curve information."
    if verdict == "CBOT_TRANSLATION_DRIVEN":
        return "The apparent EMA signal is close to the CBOT EUR/t translation control."
    return "Reliable EMA-only curve features do not clear utility thresholds."


def _safe_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def _json_float(value: Any) -> float | None:
    out = _safe_float(value)
    return out if math.isfinite(out) else None


def _json_scalar(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float):
        return _json_float(value)
    return value


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return _json_scalar(value)
    if isinstance(value, float):
        return _json_float(value)
    return value


if __name__ == "__main__":
    table, true_curve_decision = run_ema_true_curve_benchmark()
    print(table[["target_col", "feature_set", "status", "n_oof", "da", "auc", "top20_da"]])
    print(json.dumps(_json_ready(true_curve_decision), indent=2, ensure_ascii=False))

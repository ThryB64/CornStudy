"""Benchmark EMA raw, adjusted and no-roll direction targets."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import EMA_BENCHMARK_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_benchmark import (
    apply_benjamini_hochberg,
    build_feature_sets,
    walk_forward_da,
)
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

ROLL_TARGET_BENCHMARK_JSON = EMA_BENCHMARK_DIR / "ema_roll_target_benchmark.json"
ROLL_TARGET_BENCHMARK_CSV = EMA_BENCHMARK_DIR / "ema_roll_target_benchmark.csv"
ROLL_TARGET_BENCHMARK_DOC = PROJECT_ROOT / "docs" / "EMA_ROLL_TARGET_AFTER_FIX.md"
ROLL_TARGET_HORIZONS = (20, 40, 60)
ROLL_TARGET_VARIANTS = ("raw", "adjusted", "no_roll")
PRIMARY_FEATURE_SET = "cbot_ema_combined"


def run_ema_roll_target_benchmark(
    *,
    features_path: Path = FEATURES_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_path: Path = ROLL_TARGET_BENCHMARK_JSON,
    table_output_path: Path = ROLL_TARGET_BENCHMARK_CSV,
    doc_output_path: Path = ROLL_TARGET_BENCHMARK_DOC,
    max_date: str | pd.Timestamp = "2022-12-31",
    n_bootstrap: int = 1000,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare EMA direction targets built on raw, adjusted and no-roll series."""
    features = pd.read_parquet(features_path)
    ema_targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = _build_roll_frame(features, ema_targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_sets = build_feature_sets(selected, available_columns=set(work.columns))

    rows: list[dict[str, Any]] = []
    for horizon in ROLL_TARGET_HORIZONS:
        for variant in ROLL_TARGET_VARIANTS:
            target_col = f"y_up_h{horizon}_ema_{variant}"
            for feature_set, columns in feature_sets.items():
                rows.append(
                    _evaluate_target_variant(
                        work,
                        target_col=target_col,
                        target_variant=variant,
                        horizon=horizon,
                        feature_set=feature_set,
                        columns=columns,
                        n_bootstrap=n_bootstrap,
                    )
                )
    results = apply_benjamini_hochberg(pd.DataFrame(rows), baseline_feature_set=PRIMARY_FEATURE_SET)
    decision = decide_roll_target(results)
    payload = {
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
        "max_date": str(max_date),
        "horizons": list(ROLL_TARGET_HORIZONS),
        "variants": list(ROLL_TARGET_VARIANTS),
        "primary_feature_set": PRIMARY_FEATURE_SET,
        "target_tail_integrity": _target_tail_integrity(ema_targets),
        "results": results.to_dict(orient="records"),
        "decision": decision,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    results.to_csv(table_output_path, index=False)
    _write_markdown(payload, doc_output_path)
    return results, decision


def decide_roll_target(results: pd.DataFrame) -> dict[str, Any]:
    """Decide whether roll-aware targets explain the EMA pivot failure."""
    primary = results[results["feature_set"].eq(PRIMARY_FEATURE_SET)].copy()
    by_horizon: dict[str, Any] = {}
    verdict = "ROLL_TARGET_NOT_EXPLAINED"
    best_improvement = -math.inf
    best_row: pd.Series | None = None

    for horizon in ROLL_TARGET_HORIZONS:
        group = primary[primary["horizon"].eq(horizon)]
        raw = _variant_row(group, "raw")
        adjusted = _variant_row(group, "adjusted")
        no_roll = _variant_row(group, "no_roll")
        alternatives = [row for row in (adjusted, no_roll) if row is not None and row.get("status") == "OK"]
        raw_da = _safe_float(raw.get("da")) if raw is not None else math.nan
        best_alt = max(alternatives, key=lambda row: _safe_float(row.get("da")), default=None)
        alt_da = _safe_float(best_alt.get("da")) if best_alt is not None else math.nan
        improvement = alt_da - raw_da if math.isfinite(raw_da) and math.isfinite(alt_da) else math.nan
        if math.isfinite(improvement) and improvement > best_improvement:
            best_improvement = improvement
            best_row = best_alt
        by_horizon[str(horizon)] = {
            "raw": _row_summary(raw),
            "adjusted": _row_summary(adjusted),
            "no_roll": _row_summary(no_roll),
            "best_alternative_variant": str(best_alt["target_variant"]) if best_alt is not None else None,
            "best_alternative_da_minus_raw": _json_float(improvement),
        }

    if best_row is not None:
        best_da = _safe_float(best_row.get("da"))
        best_da_lo = _safe_float(best_row.get("da_ci95_lo"))
        if best_improvement >= 0.03 and best_da > 0.55 and best_da_lo > 0.50:
            verdict = "ROLL_TARGET_FIX_VALIDATED"
        elif best_improvement >= 0.02:
            verdict = "ROLL_TARGET_FIX_PROMISING"

    return {
        "verdict": verdict,
        "reason": _decision_reason(verdict),
        "primary_feature_set": PRIMARY_FEATURE_SET,
        "best_improvement_da": _json_float(best_improvement),
        "best_alternative": _row_summary(best_row),
        "by_horizon": by_horizon,
        "note": "no_roll can be unavailable when every future window crosses a roll.",
    }


def _evaluate_target_variant(
    work: pd.DataFrame,
    *,
    target_col: str,
    target_variant: str,
    horizon: int,
    feature_set: str,
    columns: list[str],
    n_bootstrap: int,
) -> dict[str, Any]:
    usable = [col for col in columns if col in work.columns]
    base = {
        "target_col": target_col,
        "target_variant": target_variant,
        "horizon": int(horizon),
        "feature_set": feature_set,
        "features": usable,
        "n_features": len(usable),
        "target_non_null_rows": int(work[target_col].notna().sum()) if target_col in work.columns else 0,
    }
    if target_col not in work.columns:
        return {**base, **_empty_result(f"missing target {target_col}", n_bootstrap)}
    if not usable:
        return {**base, **_empty_result("empty feature set", n_bootstrap)}
    frame = work[["Date", target_col, *usable]].dropna(subset=[target_col]).copy()
    if frame[target_col].nunique(dropna=True) < 2:
        return {**base, **_empty_result("target has fewer than two classes", n_bootstrap)}
    result = walk_forward_da(frame[usable], frame[target_col], frame["Date"], n_bootstrap=n_bootstrap)
    result.pop("predictions", None)
    return {**base, **result}


def _build_roll_frame(features: pd.DataFrame, ema_targets: pd.DataFrame, *, max_date: str | pd.Timestamp) -> pd.DataFrame:
    work = features.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    targets = ema_targets.copy()
    targets["Date"] = pd.to_datetime(targets["Date"]).dt.normalize()
    target_cols = [
        f"y_up_h{horizon}_ema_{variant}"
        for horizon in ROLL_TARGET_HORIZONS
        for variant in ROLL_TARGET_VARIANTS
        if f"y_up_h{horizon}_ema_{variant}" in targets.columns
    ]
    work = work.merge(targets[["Date", *target_cols]], on="Date", how="left")
    work = work[work["Date"] <= pd.Timestamp(max_date)].copy()
    if "ema_data_availability_score" in work.columns:
        work = work[pd.to_numeric(work["ema_data_availability_score"], errors="coerce") > 0].copy()
    return work.sort_values("Date").reset_index(drop=True)


def _target_tail_integrity(ema_targets: pd.DataFrame) -> list[dict[str, Any]]:
    audits = []
    for horizon in ROLL_TARGET_HORIZONS:
        for variant in ROLL_TARGET_VARIANTS:
            target_col = f"y_up_h{horizon}_ema_{variant}"
            if target_col not in ema_targets.columns:
                audits.append({
                    "target_col": target_col,
                    "horizon": int(horizon),
                    "status": "missing",
                    "tail_integrity_ok": False,
                })
                continue
            tail = ema_targets[target_col].tail(int(horizon))
            audits.append({
                "target_col": target_col,
                "horizon": int(horizon),
                "status": "OK",
                "target_non_null_rows": int(ema_targets[target_col].notna().sum()),
                "tail_nan_count": int(tail.isna().sum()),
                "tail_non_null_count": int(tail.notna().sum()),
                "tail_integrity_ok": bool(tail.isna().all()),
            })
    return audits


def _load_selected_features(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    selected = payload.get("selected_features", [])
    if not isinstance(selected, list) or not selected:
        raise ValueError(f"No selected_features in {path}")
    return [str(col) for col in selected]


def _variant_row(group: pd.DataFrame, variant: str) -> pd.Series | None:
    row = group[group["target_variant"].eq(variant)]
    if row.empty:
        return None
    return row.iloc[0]


def _row_summary(row: pd.Series | None) -> dict[str, Any] | None:
    if row is None:
        return None
    keys = [
        "target_col",
        "target_variant",
        "horizon",
        "feature_set",
        "status",
        "reason",
        "n_oof",
        "n_features",
        "target_non_null_rows",
        "da",
        "da_ci95_lo",
        "da_ci95_hi",
        "auc",
        "auc_ci95_lo",
        "auc_ci95_hi",
        "top20_da",
        "annual_stability",
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
    if verdict == "ROLL_TARGET_FIX_VALIDATED":
        return "Adjusted or no-roll target materially improves EMA DA and clears minimal reliability thresholds."
    if verdict == "ROLL_TARGET_FIX_PROMISING":
        return "Adjusted or no-roll target improves EMA DA, but reliability thresholds are not fully cleared."
    return "Roll-aware targets do not materially improve the primary EMA benchmark."


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


def _fmt_pct(value: Any) -> str:
    value_float = _safe_float(value)
    return "N/A" if not math.isfinite(value_float) else f"{value_float:.1%}"


def _fmt_num(value: Any, digits: int = 3) -> str:
    value_float = _safe_float(value)
    return "N/A" if not math.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    decision = payload["decision"]
    primary_rows = [
        row
        for row in payload["results"]
        if row.get("feature_set") == payload["primary_feature_set"]
    ]
    lines = [
        "# EMA ROLL TARGET AFTER FIX",
        "",
        "> Benchmark raw / adjusted / no-roll après correction de l'intégrité des targets futures.",
        "",
        "## Verdict",
        "",
        f"- Verdict : {decision['verdict']}",
        f"- Raison : {decision['reason']}",
        f"- Meilleure amélioration DA vs raw : {_fmt_pct(decision.get('best_improvement_da'))}",
        "",
        "H60 no-roll peut être structurellement indisponible car presque toutes les fenêtres H60 traversent un roll.",
        "",
        "## Audit tail NaN",
        "",
        "| Target | Horizon | Non-null | Tail non-null | Verdict |",
        "|---|---:|---:|---:|---|",
    ]
    for row in payload["target_tail_integrity"]:
        verdict = "PASS" if row.get("tail_integrity_ok") else "FAIL"
        lines.append(
            f"| {row['target_col']} | {row['horizon']} | {row.get('target_non_null_rows', 0)} | "
            f"{row.get('tail_non_null_count', 0)} | {verdict} |"
        )
    lines += [
        "",
        "## Résultats primaires",
        "",
        "| Horizon | Variante | Statut | n OOF | DA | AUC | Top20 DA |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in primary_rows:
        lines.append(
            f"| {row['horizon']} | {row['target_variant']} | {row['status']} | "
            f"{row.get('n_oof', 0)} | {_fmt_pct(row.get('da'))} | "
            f"{_fmt_num(row.get('auc'))} | {_fmt_pct(row.get('top20_da'))} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    table, roll_decision = run_ema_roll_target_benchmark()
    print(table[["target_col", "feature_set", "status", "n_oof", "da", "auc", "top20_da"]])
    print(json.dumps(_json_ready(roll_decision), indent=2, ensure_ascii=False))

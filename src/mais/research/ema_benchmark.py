"""Benchmark Euronext EMA targets and features against CBOT baselines."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import EMA_BENCHMARK_DIR, FEATURES_PARQUET, TARGETS_PARQUET
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

BENCHMARK_FULL_JSON = EMA_BENCHMARK_DIR / "benchmark_full.json"
PIVOT_DECISION_JSON = EMA_BENCHMARK_DIR / "pivot_decision.json"
BENCHMARK_TABLE_CSV = EMA_BENCHMARK_DIR / "benchmark_full.csv"
TARGETS = ("y_up_h20", "y_up_h20_ema", "y_up_h20_ema_harvest")


def walk_forward_da(
    x: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series | None = None,
    *,
    n_splits: int = 8,
    min_train_years: int = 3,
    n_bootstrap: int = 1000,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run an expanding crop-year walk-forward Ridge benchmark."""
    frame = x.copy()
    frame["__target__"] = y
    frame["__date__"] = pd.to_datetime(dates if dates is not None else x.index)
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=["__target__", "__date__"])
    frame = frame.sort_values("__date__").reset_index(drop=True)
    feature_cols = [col for col in frame.columns if col not in {"__target__", "__date__"}]
    if not feature_cols:
        return _empty_benchmark_result("no feature columns", n_bootstrap)

    splits = _crop_year_splits(frame["__date__"], n_splits=n_splits, min_train_years=min_train_years)
    predictions: list[pd.DataFrame] = []
    split_das: list[dict[str, Any]] = []
    for split_id, (train_idx, valid_idx, valid_year) in enumerate(splits, start=1):
        y_train = frame.loc[train_idx, "__target__"].astype(int)
        y_valid = frame.loc[valid_idx, "__target__"].astype(int)
        if y_train.nunique() < 2 or y_valid.empty:
            continue
        model = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                ("scaler", StandardScaler()),
                ("ridge", RidgeClassifier(alpha=1.0)),
            ]
        )
        model.fit(frame.loc[train_idx, feature_cols], y_train)
        pred = pd.Series(model.predict(frame.loc[valid_idx, feature_cols]), index=valid_idx).astype(int)
        score = pd.Series(model.decision_function(frame.loc[valid_idx, feature_cols]), index=valid_idx)
        fold = pd.DataFrame(
            {
                "Date": frame.loc[valid_idx, "__date__"].to_numpy(),
                "y_true": y_valid.to_numpy(dtype=int),
                "y_pred": pred.to_numpy(dtype=int),
                "score": score.to_numpy(dtype=float),
                "split_id": split_id,
                "validation_year": int(valid_year),
            }
        )
        predictions.append(fold)
        split_das.append(
            {
                "split_id": split_id,
                "validation_year": int(valid_year),
                "n_valid": int(len(fold)),
                "da": _json_float((fold["y_true"] == fold["y_pred"]).mean()),
                "auc": _safe_auc(fold["y_true"], fold["score"]),
            }
        )

    if not predictions:
        return _empty_benchmark_result("no valid walk-forward folds", n_bootstrap)

    oof = pd.concat(predictions, ignore_index=True)
    da = float((oof["y_true"] == oof["y_pred"]).mean())
    auc = _safe_auc(oof["y_true"], oof["score"])
    top20 = _top_fraction_da(oof, fraction=0.20)
    da_ci = _bootstrap_ci(
        oof["y_true"].to_numpy(),
        oof["y_pred"].to_numpy(),
        oof["score"].to_numpy(),
        metric="da",
        n_bootstrap=n_bootstrap,
        random_state=random_state,
    )
    auc_ci = _bootstrap_ci(
        oof["y_true"].to_numpy(),
        oof["y_pred"].to_numpy(),
        oof["score"].to_numpy(),
        metric="auc",
        n_bootstrap=n_bootstrap,
        random_state=random_state + 1,
    )
    annual_da = (
        oof.assign(correct=oof["y_true"].eq(oof["y_pred"]))
        .groupby("validation_year")["correct"]
        .mean()
        .to_dict()
    )
    annual_values = np.array(list(annual_da.values()), dtype=float)
    return {
        "status": "OK",
        "n_train_validation_rows": int(len(frame)),
        "n_oof": int(len(oof)),
        "n_features": int(len(feature_cols)),
        "n_splits": int(len(split_das)),
        "bootstrap_n": int(n_bootstrap),
        "da": da,
        "da_ci95_lo": da_ci[0],
        "da_ci95_hi": da_ci[1],
        "auc": auc,
        "auc_ci95_lo": auc_ci[0],
        "auc_ci95_hi": auc_ci[1],
        "top20_da": top20,
        "split_das": split_das,
        "annual_da": {str(int(k)): _json_float(v) for k, v in annual_da.items()},
        "annual_stability": _json_float(float((annual_values >= 0.50).mean())) if len(annual_values) else None,
        "annual_da_min": _json_float(float(np.nanmin(annual_values))) if len(annual_values) else None,
        "annual_da_std": _json_float(float(np.nanstd(annual_values))) if len(annual_values) else None,
        "predictions": oof,
    }


def build_feature_sets(
    selected_features: list[str],
    available_columns: set[str] | None = None,
) -> dict[str, list[str]]:
    """Create the four feature sets required by EXP-BENCH-02."""
    available = available_columns or set(selected_features)
    selected = [col for col in selected_features if col in available]
    ema_features = [col for col in selected if _is_ema_feature(col)]
    cbot_features = [col for col in selected if _is_cbot_base_feature(col)]
    non_ema_features = [col for col in selected if col not in set(ema_features)]
    return {
        "cbot_only": cbot_features,
        "ema_curve_only": ema_features,
        "cbot_ema_combined": _dedupe([*cbot_features, *ema_features]),
        "cbot_full": non_ema_features,
    }


def decide_pivot(results: pd.DataFrame) -> dict[str, Any]:
    """Apply the EXP-BENCH-02 go/no-go decision tree."""
    ema_row = _primary_row(results, target_col="y_up_h20_ema", feature_set="cbot_ema_combined")
    cbot_row = _primary_row(results, target_col="y_up_h20", feature_set="cbot_full")
    if ema_row is None:
        return {"verdict": "NO_GO", "reason": "primary EMA benchmark missing"}
    if cbot_row is None:
        cbot_row = _primary_row(results, target_col="y_up_h20", feature_set="cbot_only")
    da_ema = _safe_value(ema_row.get("da"))
    auc_ema = _safe_value(ema_row.get("auc"))
    da_lo = _safe_value(ema_row.get("da_ci95_lo"))
    top20 = _safe_value(ema_row.get("top20_da"))
    da_cbot = _safe_value(cbot_row.get("da")) if cbot_row is not None else math.nan
    diff = da_ema - da_cbot if math.isfinite(da_ema) and math.isfinite(da_cbot) else math.nan

    minimal_go = (
        math.isfinite(da_ema)
        and math.isfinite(auc_ema)
        and math.isfinite(da_lo)
        and math.isfinite(top20)
        and da_ema > 0.55
        and auc_ema > 0.55
        and da_lo > 0.50
        and top20 > 0.62
    )
    if not minimal_go:
        verdict = "NO_GO"
        reason = "EMA primary benchmark fails one or more minimal go/no-go criteria"
    elif math.isfinite(diff) and diff > 0.01:
        verdict = "PIVOT_VALIDÉ"
        reason = "EMA primary DA beats CBOT primary DA by more than 1 point"
    elif math.isfinite(diff) and abs(diff) <= 0.01:
        verdict = "PIVOT_UTILE"
        reason = "EMA primary DA is close to CBOT primary DA while passing minimal criteria"
    else:
        verdict = "CBOT_MOTEUR"
        reason = "CBOT primary DA remains ahead by more than 1 point"
    return {
        "verdict": verdict,
        "reason": reason,
        "minimal_go": bool(minimal_go),
        "primary_ema": _row_summary(ema_row),
        "primary_cbot": _row_summary(cbot_row) if cbot_row is not None else None,
        "diff_ema_minus_cbot_da": _json_float(diff),
        "criteria": {
            "da_ema_gt_0_55": bool(math.isfinite(da_ema) and da_ema > 0.55),
            "auc_ema_gt_0_55": bool(math.isfinite(auc_ema) and auc_ema > 0.55),
            "da_ci95_lo_gt_0_50": bool(math.isfinite(da_lo) and da_lo > 0.50),
            "top20_gt_0_62": bool(math.isfinite(top20) and top20 > 0.62),
        },
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
    }


def run_ema_benchmark(
    *,
    features_path: Path = FEATURES_PARQUET,
    cbot_targets_path: Path = TARGETS_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    benchmark_output_path: Path = BENCHMARK_FULL_JSON,
    decision_output_path: Path = PIVOT_DECISION_JSON,
    table_output_path: Path = BENCHMARK_TABLE_CSV,
    max_date: str | pd.Timestamp = "2022-12-31",
    n_bootstrap: int = 1000,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the full EXP-BENCH-02 benchmark and write JSON artefacts."""
    features = pd.read_parquet(features_path)
    cbot_targets = pd.read_parquet(cbot_targets_path)
    ema_targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = _build_benchmark_frame(features, cbot_targets, ema_targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_sets = build_feature_sets(selected, available_columns=set(work.columns))
    rows: list[dict[str, Any]] = []
    for target_col in TARGETS:
        for feature_set, columns in feature_sets.items():
            result = _run_one_feature_set(work, target_col, feature_set, columns, n_bootstrap=n_bootstrap)
            rows.append(result)
    results = pd.DataFrame(rows)
    results = apply_benjamini_hochberg(results)
    decision = decide_pivot(results)
    payload = {
        "source_quality_note": "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement.",
        "max_date": str(max_date),
        "targets": list(TARGETS),
        "feature_sets": dict(feature_sets),
        "results": results.to_dict(orient="records"),
        "decision": decision,
    }
    benchmark_output_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_output_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    decision_output_path.write_text(json.dumps(_json_ready(decision), indent=2, ensure_ascii=False), encoding="utf-8")
    results.to_csv(table_output_path, index=False)
    return results, decision


def apply_benjamini_hochberg(results: pd.DataFrame, *, baseline_feature_set: str = "cbot_full") -> pd.DataFrame:
    """Add approximate p-values and BH q-values for feature-set comparisons."""
    out = results.copy()
    out["comparison_baseline"] = baseline_feature_set
    out["baseline_da"] = np.nan
    out["da_diff_vs_baseline"] = np.nan
    out["p_value_vs_baseline"] = 1.0
    comparisons: list[tuple[int, float]] = []
    for _target_col, group in out.groupby("target_col", sort=False):
        baseline = group[group["feature_set"].eq(baseline_feature_set)]
        if baseline.empty:
            baseline = group[group["feature_set"].eq("cbot_only")]
        if baseline.empty:
            continue
        base_row = baseline.iloc[0]
        for idx, row in group.iterrows():
            out.loc[idx, "baseline_da"] = _safe_value(base_row.get("da"))
            out.loc[idx, "da_diff_vs_baseline"] = _safe_value(row.get("da")) - _safe_value(base_row.get("da"))
            if row["feature_set"] == base_row["feature_set"]:
                continue
            p_value = _two_rate_p_value(row.get("da"), row.get("n_oof"), base_row.get("da"), base_row.get("n_oof"))
            out.loc[idx, "p_value_vs_baseline"] = p_value
            out.loc[idx, "comparison_baseline"] = str(base_row["feature_set"])
            comparisons.append((idx, p_value))
    q_values = _benjamini_hochberg([p for _, p in comparisons])
    for (idx, _), q_value in zip(comparisons, q_values, strict=False):
        out.loc[idx, "bh_q_value"] = q_value
    out["bh_q_value"] = out["bh_q_value"].fillna(1.0)
    out["bh_reject_0_05"] = out["bh_q_value"] <= 0.05
    return out


def _run_one_feature_set(
    work: pd.DataFrame,
    target_col: str,
    feature_set: str,
    columns: list[str],
    *,
    n_bootstrap: int,
) -> dict[str, Any]:
    usable = [col for col in columns if col in work.columns]
    base = {
        "target_col": target_col,
        "feature_set": feature_set,
        "features": usable,
        "n_features": len(usable),
    }
    if target_col not in work.columns:
        return {**base, **_empty_benchmark_result(f"missing target {target_col}", n_bootstrap, include_predictions=False)}
    if not usable:
        return {**base, **_empty_benchmark_result("empty feature set", n_bootstrap, include_predictions=False)}
    frame = work[["Date", target_col, *usable]].dropna(subset=[target_col]).copy()
    result = walk_forward_da(
        frame[usable],
        frame[target_col],
        frame["Date"],
        n_bootstrap=n_bootstrap,
    )
    predictions = result.pop("predictions", None)
    if isinstance(predictions, pd.DataFrame):
        base["prediction_rows"] = int(len(predictions))
    return {**base, **result}


def _build_benchmark_frame(
    features: pd.DataFrame,
    cbot_targets: pd.DataFrame,
    ema_targets: pd.DataFrame,
    *,
    max_date: str | pd.Timestamp,
) -> pd.DataFrame:
    work = features.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    for targets in (cbot_targets, ema_targets):
        target_frame = targets.copy()
        target_frame["Date"] = pd.to_datetime(target_frame["Date"]).dt.normalize()
        wanted = ["Date", *[col for col in TARGETS if col in target_frame.columns]]
        work = work.merge(target_frame[wanted], on="Date", how="left")
    work = work[work["Date"] <= pd.Timestamp(max_date)].copy()
    if "ema_data_availability_score" in work.columns:
        work = work[pd.to_numeric(work["ema_data_availability_score"], errors="coerce") > 0].copy()
    return work.sort_values("Date").reset_index(drop=True)


def _crop_year_splits(
    dates: pd.Series,
    *,
    n_splits: int,
    min_train_years: int,
) -> list[tuple[np.ndarray, np.ndarray, int]]:
    years = pd.to_datetime(dates).dt.year.to_numpy()
    unique_years = sorted(pd.unique(years))
    if len(unique_years) <= min_train_years:
        return []
    validation_years = unique_years[min_train_years:]
    validation_years = validation_years[-n_splits:]
    splits: list[tuple[np.ndarray, np.ndarray, int]] = []
    for year in validation_years:
        train_idx = np.flatnonzero(years < year)
        valid_idx = np.flatnonzero(years == year)
        if len(train_idx) and len(valid_idx):
            splits.append((train_idx, valid_idx, int(year)))
    return splits


def _bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    score: np.ndarray,
    *,
    metric: str,
    n_bootstrap: int,
    random_state: int,
) -> tuple[float | None, float | None]:
    if len(y_true) == 0 or n_bootstrap <= 0:
        return None, None
    rng = np.random.default_rng(random_state)
    values: list[float] = []
    n = len(y_true)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if metric == "da":
            values.append(float((y_true[idx] == y_pred[idx]).mean()))
        else:
            auc = _safe_auc(y_true[idx], score[idx])
            if auc is not None:
                values.append(float(auc))
    if not values:
        return None, None
    lo, hi = np.nanpercentile(values, [2.5, 97.5])
    return _json_float(lo), _json_float(hi)


def _top_fraction_da(oof: pd.DataFrame, *, fraction: float) -> float | None:
    if oof.empty:
        return None
    n_top = max(1, int(math.ceil(len(oof) * fraction)))
    ranked = oof.assign(confidence=oof["score"].abs()).sort_values("confidence", ascending=False).head(n_top)
    return _json_float(float(ranked["y_true"].eq(ranked["y_pred"]).mean()))


def _safe_auc(y_true: pd.Series | np.ndarray, score: pd.Series | np.ndarray) -> float | None:
    y = pd.Series(y_true).dropna()
    s = pd.Series(score).loc[y.index]
    if y.nunique() < 2 or len(y) < 2:
        return None
    try:
        return _json_float(float(roc_auc_score(y.astype(int), s.astype(float))))
    except ValueError:
        return None


def _two_rate_p_value(p1: Any, n1: Any, p2: Any, n2: Any) -> float:
    p1f = _safe_value(p1)
    p2f = _safe_value(p2)
    n1f = _safe_value(n1)
    n2f = _safe_value(n2)
    if not all(math.isfinite(v) for v in (p1f, p2f, n1f, n2f)) or n1f <= 0 or n2f <= 0:
        return 1.0
    se = math.sqrt(max(p1f * (1 - p1f) / n1f + p2f * (1 - p2f) / n2f, 1e-12))
    z = abs(p1f - p2f) / se
    return float(math.erfc(z / math.sqrt(2.0)))


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    p = np.asarray(p_values, dtype=float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q_ranked = np.empty(m, dtype=float)
    prev = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        value = min(prev, ranked[i] * m / rank)
        q_ranked[i] = value
        prev = value
    q = np.empty(m, dtype=float)
    q[order] = np.clip(q_ranked, 0.0, 1.0)
    return [float(v) for v in q]


def _load_selected_features(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    selected = payload.get("selected_features", [])
    if not isinstance(selected, list) or not selected:
        raise ValueError(f"No selected_features in {path}")
    return [str(col) for col in selected]


def _is_ema_feature(col: str) -> bool:
    return col.startswith("ema_") or col == "cbot_eur_t"


def _is_cbot_base_feature(col: str) -> bool:
    return col.startswith(("corn_", "cbot_", "wheat_", "soy_")) and not _is_ema_feature(col)


def _dedupe(columns: list[str]) -> list[str]:
    return list(dict.fromkeys(columns))


def _primary_row(results: pd.DataFrame, *, target_col: str, feature_set: str) -> pd.Series | None:
    row = results[(results["target_col"].eq(target_col)) & (results["feature_set"].eq(feature_set))]
    if row.empty:
        return None
    return row.iloc[0]


def _row_summary(row: pd.Series) -> dict[str, Any]:
    keys = [
        "target_col",
        "feature_set",
        "status",
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
    ]
    return {key: _json_scalar(row.get(key)) for key in keys if key in row}


def _empty_benchmark_result(
    reason: str,
    n_bootstrap: int,
    *,
    include_predictions: bool = True,
) -> dict[str, Any]:
    result: dict[str, Any] = {
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
    if include_predictions:
        result["predictions"] = pd.DataFrame()
    return result


def _safe_value(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def _json_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
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
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_json_ready(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return _json_scalar(value)
    if isinstance(value, float):
        return _json_float(value)
    return value


if __name__ == "__main__":
    table, pivot_decision = run_ema_benchmark()
    print(table[["target_col", "feature_set", "status", "n_oof", "da", "auc", "top20_da"]])
    print(json.dumps(_json_ready(pivot_decision), indent=2, ensure_ascii=False))

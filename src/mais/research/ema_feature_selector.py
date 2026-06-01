"""Feature selection for EMA benchmark experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, TARGETS_PARQUET

EMA_FEATURE_SELECTION_REPORT = ARTEFACTS_DIR / "ema_feature_selection.json"
DEFAULT_TARGET = "y_up_h20"
FEATURE_FAMILIES: dict[str, list[str]] = {
    "ema_curve": ["ema_", "cbot_eur_t"],
    "cbot_base": ["corn_", "cbot_", "wheat_", "soy_"],
    "wasde": ["wasde"],
    "cot": ["cot"],
    "weather": ["gdd", "drought", "precip", "wx_", "weather"],
    "macro": ["eurusd", "ttf", "fred", "macro", "fedfunds", "cpi"],
}


def select_ema_features(
    features: pd.DataFrame,
    target_col: str,
    *,
    targets: pd.DataFrame | None = None,
    nan_threshold: float = 0.30,
    corr_threshold: float = 0.95,
    shap_top_n: int = 50,
    max_model_features: int = 120,
    min_date: str | pd.Timestamp | None = "2010-01-01",
    max_date: str | pd.Timestamp = "2022-12-31",
    require_ema_available: bool = True,
    random_state: int = 42,
) -> tuple[list[str], dict[str, Any]]:
    """Select features for EMA benchmark without touching the OOT period."""
    work = _merge_target(features, targets, target_col)
    work["Date"] = pd.to_datetime(work["Date"])
    date_mask = work["Date"] <= pd.Timestamp(max_date)
    if min_date is not None:
        date_mask &= work["Date"] >= pd.Timestamp(min_date)
    work = work[date_mask].sort_values("Date").reset_index(drop=True)
    if require_ema_available and "ema_data_availability_score" in work.columns:
        work = work[pd.to_numeric(work["ema_data_availability_score"], errors="coerce") > 0]
    work = work.reset_index(drop=True)
    work = work.dropna(subset=[target_col]).reset_index(drop=True)
    candidate_cols = _candidate_feature_columns(work, target_col)
    nan_rates = work[candidate_cols].isna().mean() if candidate_cols else pd.Series(dtype=float)
    after_nan = [col for col in candidate_cols if nan_rates[col] <= nan_threshold]
    after_constant = _drop_constant_columns(work, after_nan)
    after_corr, corr_dropped = _drop_correlated_features(
        work,
        after_constant,
        corr_threshold=corr_threshold,
        nan_rates=nan_rates,
    )
    model_candidates = _preselect_for_model(
        work,
        after_corr,
        target_col,
        max_features=max_model_features,
    )
    selected, importance_rows, validation_auc, importance_method = _histgb_importance_top_n(
        work,
        model_candidates,
        target_col,
        top_n=shap_top_n,
        random_state=random_state,
    )
    selected = selected[: min(80, len(selected))]
    selected_nan = work[selected].isna().mean() if selected else pd.Series(dtype=float)
    report = {
        "target_col": target_col,
        "period_start": work["Date"].min().date().isoformat() if not work.empty else None,
        "period_end": work["Date"].max().date().isoformat() if not work.empty else None,
        "min_date": str(min_date) if min_date is not None else None,
        "max_date": str(max_date),
        "require_ema_available": bool(require_ema_available),
        "n_rows": int(len(work)),
        "n_candidates_initial": int(len(candidate_cols)),
        "n_after_nan_filter": int(len(after_nan)),
        "n_after_constant_filter": int(len(after_constant)),
        "n_after_corr_filter": int(len(after_corr)),
        "n_model_candidates": int(len(model_candidates)),
        "n_selected": int(len(selected)),
        "nan_threshold": float(nan_threshold),
        "corr_threshold": float(corr_threshold),
        "shap_top_n": int(shap_top_n),
        "importance_method": importance_method,
        "validation_auc": _json_float(validation_auc),
        "max_selected_nan_rate": _json_float(float(selected_nan.max())) if len(selected_nan) else None,
        "selected_features": selected,
        "selected_by_family": _count_by_family(selected),
        "dropped_high_nan": [col for col in candidate_cols if col not in after_nan],
        "dropped_constant": [col for col in after_nan if col not in after_constant],
        "dropped_correlated": corr_dropped,
        "importance": importance_rows,
    }
    return selected, report


def run_ema_feature_selection(
    *,
    features_path: Path = FEATURES_PARQUET,
    targets_path: Path = TARGETS_PARQUET,
    target_col: str = DEFAULT_TARGET,
    output_path: Path = EMA_FEATURE_SELECTION_REPORT,
) -> tuple[list[str], dict[str, Any]]:
    """Load project data, select features and write the JSON report."""
    features = pd.read_parquet(features_path)
    targets = pd.read_parquet(targets_path)
    selected, report = select_ema_features(features, target_col, targets=targets)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return selected, report


def _merge_target(
    features: pd.DataFrame,
    targets: pd.DataFrame | None,
    target_col: str,
) -> pd.DataFrame:
    if "Date" not in features.columns:
        raise ValueError("features require a Date column")
    work = features.copy()
    if target_col in work.columns:
        return work
    if targets is None or target_col not in targets.columns:
        raise ValueError(f"Target column not available: {target_col}")
    target_frame = targets[["Date", target_col]].copy()
    target_frame["Date"] = pd.to_datetime(target_frame["Date"])
    work["Date"] = pd.to_datetime(work["Date"])
    return work.merge(target_frame, on="Date", how="inner")


def _candidate_feature_columns(frame: pd.DataFrame, target_col: str) -> list[str]:
    blocked = {"Date", target_col}
    return [
        col
        for col in frame.columns
        if col not in blocked
        and not col.startswith("y_")
        and pd.api.types.is_numeric_dtype(frame[col])
    ]


def _drop_constant_columns(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    kept: list[str] = []
    for col in columns:
        if frame[col].dropna().nunique() > 1:
            kept.append(col)
    return kept


def _drop_correlated_features(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    corr_threshold: float,
    nan_rates: pd.Series,
) -> tuple[list[str], list[dict[str, Any]]]:
    if len(columns) <= 1:
        return columns, []
    corr = frame[columns].replace([np.inf, -np.inf], np.nan).corr().abs()
    dropped: set[str] = set()
    rows: list[dict[str, Any]] = []
    for i, left in enumerate(columns):
        if left in dropped:
            continue
        for right in columns[i + 1 :]:
            if right in dropped:
                continue
            value = corr.loc[left, right]
            if pd.isna(value) or value <= corr_threshold:
                continue
            drop_col = right if nan_rates.get(right, 0.0) >= nan_rates.get(left, 0.0) else left
            keep_col = left if drop_col == right else right
            dropped.add(drop_col)
            rows.append({"dropped": drop_col, "kept": keep_col, "corr_abs": float(value)})
            if drop_col == left:
                break
    return [col for col in columns if col not in dropped], rows


def _preselect_for_model(
    frame: pd.DataFrame,
    columns: list[str],
    target_col: str,
    *,
    max_features: int,
) -> list[str]:
    if len(columns) <= max_features:
        return columns
    y = frame[target_col].astype(float)
    scores: list[tuple[str, float]] = []
    for col in columns:
        series = pd.to_numeric(frame[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        corr = series.corr(y)
        scores.append((col, abs(float(corr)) if pd.notna(corr) else 0.0))
    return [col for col, _ in sorted(scores, key=lambda item: item[1], reverse=True)[:max_features]]


def _histgb_importance_top_n(
    frame: pd.DataFrame,
    columns: list[str],
    target_col: str,
    *,
    top_n: int,
    random_state: int,
) -> tuple[list[str], list[dict[str, Any]], float, str]:
    if not columns:
        return [], [], np.nan, "none"
    x = frame[columns].replace([np.inf, -np.inf], np.nan)
    y = frame[target_col].astype(int)
    if len(frame) < 80 or y.nunique() < 2:
        selected = columns[:top_n]
        return selected, [{"feature": col, "importance": 0.0} for col in selected], np.nan, "insufficient_data"
    split = max(int(len(frame) * 0.80), 1)
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train = pd.DataFrame(imputer.fit_transform(x.iloc[:split]), columns=columns)
    x_valid = pd.DataFrame(imputer.transform(x.iloc[split:]), columns=columns)
    y_train = y.iloc[:split]
    y_valid = y.iloc[split:]
    model = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.05, random_state=random_state)
    model.fit(x_train, y_train)
    if len(y_valid) and y_valid.nunique() > 1:
        proba = model.predict_proba(x_valid)[:, 1]
        validation_auc = float(roc_auc_score(y_valid, proba))
        importance, importance_method = _histgb_shap_importance(model, x_valid, random_state=random_state)
        if importance is None:
            importance = permutation_importance(
                model,
                x_valid,
                y_valid,
                scoring="roc_auc",
                n_repeats=3,
                random_state=random_state,
            ).importances_mean
            importance_method = "histgb_permutation_importance_fallback"
    else:
        validation_auc = np.nan
        importance = np.zeros(len(columns), dtype=float)
        importance_method = "no_validation_class_variance"
    ranked = sorted(zip(columns, importance, strict=False), key=lambda item: item[1], reverse=True)
    selected = [col for col, _ in ranked[:top_n]]
    rows = [{"feature": col, "importance": float(value)} for col, value in ranked]
    return selected, rows, validation_auc, importance_method


def _histgb_shap_importance(
    model: HistGradientBoostingClassifier,
    x_valid: pd.DataFrame,
    *,
    random_state: int,
) -> tuple[np.ndarray | None, str]:
    try:
        import shap

        sample = x_valid
        if len(sample) > 500:
            sample = sample.sample(500, random_state=random_state)
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(sample)
        arr = np.asarray(values)
        if arr.ndim == 3:
            arr = arr[:, :, -1]
        importance = np.abs(arr).mean(axis=0)
        return importance, "histgb_shap_tree_explainer"
    except Exception:
        return None, "histgb_shap_failed"


def _count_by_family(columns: list[str]) -> dict[str, int]:
    counts = dict.fromkeys([*FEATURE_FAMILIES.keys(), "other"], 0)
    for col in columns:
        family = _feature_family(col)
        counts[family] += 1
    return {family: count for family, count in counts.items() if count}


def _feature_family(column: str) -> str:
    lower = column.lower()
    for family, patterns in FEATURE_FAMILIES.items():
        if any(pattern in lower for pattern in patterns):
            return family
    return "other"


def _json_float(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None

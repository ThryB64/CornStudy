"""Feature engineering for USDA FAS Export Sales."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FAS_FEATURE_COLUMNS = [
    "export_sales_weekly_mt",
    "export_sales_accumulated_mt",
    "export_pace_vs_usda_forecast",
    "export_pace_vs_5y_avg",
    "export_sales_weekly_zscore",
    "export_china_pct_total",
    "export_momentum_4w",
    "export_vs_same_week_last_year",
]


def build_fas_features(weekly: pd.DataFrame, out_dates: pd.Series, *, max_stale_days: int = 10) -> pd.DataFrame:
    """Map weekly FAS data to daily features with publication-safe shift(1)."""
    w = _prepare_weekly(weekly)
    base = pd.DataFrame({"Date": pd.to_datetime(pd.Series(out_dates).unique())}).sort_values("Date").reset_index(drop=True)
    if w.empty:
        return _empty_daily(base)

    merged = pd.merge_asof(base, w, left_on="Date", right_on="week_obs", direction="backward")
    feature_cols = [col for col in FAS_FEATURE_COLUMNS if col in merged.columns]
    staleness = (merged["Date"] - merged["week_obs"]).dt.days
    merged.loc[merged["week_obs"].isna(), feature_cols] = np.nan
    merged.loc[staleness > max_stale_days, feature_cols] = np.nan
    out = pd.DataFrame({"Date": merged["Date"].values})
    for col in FAS_FEATURE_COLUMNS:
        out[col] = merged[col].astype(float).shift(1) if col in merged.columns else np.nan
        out.loc[staleness > max_stale_days, col] = np.nan
    out["export_sales_mt"] = out["export_sales_weekly_mt"]
    return out


def evaluate_fas_ablation(
    df: pd.DataFrame,
    *,
    target_col: str = "y_up_h40",
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Document global, export-season and off-season delta AUC for FAS features."""
    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    work = work[(work["Date"] <= pd.Timestamp("2022-12-31")) & work[target_col].notna()].reset_index(drop=True)
    fas_cols = [col for col in FAS_FEATURE_COLUMNS if col in work.columns and work[col].notna().any()]
    base_cols = [
        col
        for col in work.columns
        if col not in {"Date", target_col}
        and not col.startswith("y_")
        and col not in fas_cols
        and pd.api.types.is_numeric_dtype(work[col])
    ]
    masks = {
        "global": pd.Series(True, index=work.index),
        "sept_jan": work["Date"].dt.month.isin([9, 10, 11, 12, 1]),
        "off_season": work["Date"].dt.month.isin([2, 3, 4, 5, 6, 7, 8]),
    }
    windows: dict[str, Any] = {}
    for name, mask in masks.items():
        sub = work[mask].copy()
        y = sub[target_col].astype(int)
        baseline_auc = _oof_auc(sub[base_cols], y) if base_cols else np.nan
        with_auc = _oof_auc(sub[base_cols + fas_cols], y) if base_cols and fas_cols else np.nan
        delta = with_auc - baseline_auc if math.isfinite(baseline_auc) and math.isfinite(with_auc) else np.nan
        windows[name] = {
            "baseline_auc": _json_float(baseline_auc),
            "with_fas_auc": _json_float(with_auc),
            "delta_auc": _json_float(delta),
        }
    payload = {"target_col": target_col, "fas_cols": fas_cols, "windows": windows, "verdict": _verdict(windows)}
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _prepare_weekly(weekly: pd.DataFrame) -> pd.DataFrame:
    w = weekly.copy()
    if w.empty or "Date" not in w.columns:
        return pd.DataFrame()
    w["Date"] = pd.to_datetime(w["Date"])
    w = w.sort_values("Date").drop_duplicates("Date", keep="last")
    sales = pd.to_numeric(w.get("export_sales_mt", np.nan), errors="coerce")
    crop_year = np.where(w["Date"].dt.month >= 9, w["Date"].dt.year + 1, w["Date"].dt.year)
    out = pd.DataFrame({"week_obs": w["Date"].values})
    out["export_sales_weekly_mt"] = sales
    out["export_sales_accumulated_mt"] = (
        pd.Series(sales, index=w.index).groupby(crop_year).cumsum().to_numpy()
        if "export_sales_accumulated_mt" not in w.columns
        else pd.to_numeric(w["export_sales_accumulated_mt"], errors="coerce").to_numpy()
    )
    forecast = pd.to_numeric(w.get("usda_export_forecast_mt", np.nan), errors="coerce")
    out["export_pace_vs_usda_forecast"] = out["export_sales_accumulated_mt"] / forecast.replace(0, np.nan)
    out["export_pace_vs_5y_avg"] = _same_week_5y_ratio(w["Date"], out["export_sales_accumulated_mt"])
    mu = sales.expanding(20).mean()
    sd = sales.expanding(20).std().replace(0, np.nan)
    out["export_sales_weekly_zscore"] = (sales - mu) / sd
    china = pd.to_numeric(w.get("export_china_sales_mt", np.nan), errors="coerce")
    out["export_china_pct_total"] = china / sales.replace(0, np.nan)
    out["export_momentum_4w"] = sales.rolling(4, min_periods=2).mean() - sales.shift(4).rolling(4, min_periods=2).mean()
    out["export_vs_same_week_last_year"] = sales - sales.shift(52)
    return out


def _same_week_5y_ratio(dates: pd.Series, values: pd.Series) -> pd.Series:
    dt = pd.to_datetime(dates)
    iso_week = dt.dt.isocalendar().week.astype(int)
    vals = pd.to_numeric(values, errors="coerce")
    out = pd.Series(np.nan, index=vals.index, dtype=float)
    for i, (week, value) in enumerate(zip(iso_week, vals, strict=False)):
        hist = vals.iloc[:i][iso_week.iloc[:i] == week].tail(5)
        if hist.notna().sum() >= 2 and pd.notna(value):
            out.iloc[i] = float(value / hist.mean()) if hist.mean() else np.nan
    return out


def _empty_daily(base: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    for col in FAS_FEATURE_COLUMNS:
        out[col] = np.nan
    out["export_sales_mt"] = np.nan
    return out


def _oof_auc(features: pd.DataFrame, y: pd.Series) -> float:
    if len(features) < 80 or features.shape[1] == 0 or len(np.unique(y)) < 2:
        return np.nan
    x = features.replace([np.inf, -np.inf], np.nan).dropna(axis=1, how="all")
    if x.shape[1] == 0:
        return np.nan
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=500, random_state=42)),
        ]
    )
    oof = np.full(len(x), np.nan)
    for train_idx, test_idx in KFold(n_splits=5, shuffle=False).split(x):
        y_train = y.iloc[train_idx].astype(int)
        if len(np.unique(y_train)) < 2:
            oof[test_idx] = float(y_train.mean())
            continue
        model.fit(x.iloc[train_idx], y_train)
        oof[test_idx] = model.predict_proba(x.iloc[test_idx])[:, 1]
    mask = ~np.isnan(oof)
    if mask.sum() == 0 or len(np.unique(y.iloc[mask])) < 2:
        return np.nan
    return float(roc_auc_score(y.iloc[mask].astype(int), oof[mask]))


def _verdict(windows: dict[str, Any]) -> str:
    global_delta = windows.get("global", {}).get("delta_auc")
    seasonal_delta = windows.get("sept_jan", {}).get("delta_auc")
    if global_delta is not None and global_delta >= 0.010:
        return "CONFIRMÉ"
    if seasonal_delta is not None and seasonal_delta >= 0.015:
        return "PROMETTEUR"
    if global_delta is not None and global_delta < -0.003:
        return "REJETÉ"
    return "NEUTRE" if global_delta is not None else "INCONCLU"


def _json_float(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None

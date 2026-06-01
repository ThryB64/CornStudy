"""Calendar phenology features for US corn."""

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

PHENO_COLUMNS = [
    "pheno_silking_window",
    "pheno_dough_dent_window",
    "pheno_harvest_window",
    "pheno_growing_season",
    "pheno_week_in_season",
]


def build_phenology_features(dates: pd.Series | pd.DatetimeIndex) -> pd.DataFrame:
    """Build zero-leakage phenology features from the calendar only."""
    dt = pd.to_datetime(pd.Series(dates).reset_index(drop=True))
    iso_week = dt.dt.isocalendar().week.astype(int)
    out = pd.DataFrame({"Date": dt.values})
    out["pheno_silking_window"] = iso_week.between(26, 30).astype(float)
    out["pheno_dough_dent_window"] = iso_week.between(30, 36).astype(float)
    out["pheno_harvest_window"] = iso_week.between(38, 44).astype(float)
    out["pheno_growing_season"] = dt.dt.month.between(5, 10).astype(float)
    season_start = pd.to_datetime(dt.dt.year.astype(str) + "-05-01")
    week_in_season = ((dt - season_start).dt.days // 7 + 1).astype(float)
    out["pheno_week_in_season"] = week_in_season.where(out["pheno_growing_season"].astype(bool), np.nan)
    return out


def evaluate_crop_condition_windows(
    df: pd.DataFrame,
    *,
    target_col: str = "y_up_h40",
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Document crop-condition AUC by seasonal window.

    This accepts a prepared DataFrame so callers can run the real pipeline
    without hard-coded reads from forbidden data folders.
    """
    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    crop_cols = [
        col
        for col in work.columns
        if col.startswith("crop_") or col.startswith("pheno_") or col == "condition_gd_ex_pct"
    ]
    base_cols = [
        col
        for col in work.columns
        if col not in {"Date", target_col}
        and not col.startswith("y_")
        and col not in crop_cols
        and pd.api.types.is_numeric_dtype(work[col])
    ]
    windows = {
        "jun_aug": work["Date"].dt.month.between(6, 8),
        "october": work["Date"].dt.month == 10,
        "off_season": work["Date"].dt.month.isin([11, 12, 1, 2, 3, 4]),
    }
    rows: dict[str, Any] = {}
    for name, mask in windows.items():
        sub = work[mask & work[target_col].notna()].copy()
        if sub.empty:
            rows[name] = {"baseline_auc": None, "with_crop_auc": None, "delta_auc": None}
            continue
        y = sub[target_col].astype(int)
        baseline_auc = _oof_auc(sub[base_cols], y) if base_cols else np.nan
        with_auc = _oof_auc(sub[base_cols + crop_cols], y) if base_cols and crop_cols else np.nan
        delta = with_auc - baseline_auc if math.isfinite(baseline_auc) and math.isfinite(with_auc) else np.nan
        rows[name] = {
            "baseline_auc": _json_float(baseline_auc),
            "with_crop_auc": _json_float(with_auc),
            "delta_auc": _json_float(delta),
        }
    payload = {
        "target_col": target_col,
        "windows": rows,
        "verdict": _verdict(rows.get("jun_aug", {}).get("delta_auc")),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


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


def _verdict(delta_auc: float | None) -> str:
    if delta_auc is None or not math.isfinite(float(delta_auc)):
        return "INCONCLU"
    if float(delta_auc) >= 0.015:
        return "CONFIRMÉ"
    if float(delta_auc) > 0:
        return "PROMETTEUR"
    if float(delta_auc) < -0.003:
        return "REJETÉ"
    return "NEUTRE"


def _json_float(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None

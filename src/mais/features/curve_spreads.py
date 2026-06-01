"""Feature engineering for CBOT corn futures curve spreads."""

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

CURVE_SPREAD_COLUMNS = [
    "curve_zh_spread",
    "curve_kn_spread",
    "curve_nz_spread",
    "curve_contango_flag",
    "curve_zh_spread_ma20",
    "curve_zh_spread_zscore",
    "curve_backwardation_flag",
]


def build_curve_spread_features(futures: pd.DataFrame, *, spot: pd.Series | None = None) -> pd.DataFrame:
    """Build the 7 R&D-03 spread features with shift(1)."""
    df = futures.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    out = pd.DataFrame({"Date": df["Date"].values})
    zcz = _col(df, ["zcz_close", "ZCZ_close", "dec_close"])
    zch = _col(df, ["zch_close", "ZCH_close", "mar_close"])
    zck = _col(df, ["zck_close", "ZCK_close", "may_close"])
    zcn = _col(df, ["zcn_close", "ZCN_close", "jul_close"])
    if any(x is None for x in [zcz, zch, zck, zcn]):
        for col in CURVE_SPREAD_COLUMNS:
            out[col] = np.nan
        return out

    zh = zch - zcz
    kn = zck - zcn
    nz = zcn - zcz
    spot_values = pd.to_numeric(spot, errors="coerce").reset_index(drop=True) if spot is not None else zcz
    out["curve_zh_spread"] = zh.shift(1)
    out["curve_kn_spread"] = kn.shift(1)
    out["curve_nz_spread"] = nz.shift(1)
    out["curve_contango_flag"] = (zcn > spot_values * 1.02).astype(float).shift(1)
    out["curve_zh_spread_ma20"] = zh.rolling(20, min_periods=5).mean().shift(1)
    out["curve_zh_spread_zscore"] = _expanding_zscore(zh).shift(1)
    out["curve_backwardation_flag"] = (zcn < spot_values * 0.98).astype(float).shift(1)
    return out


def evaluate_curve_spreads(
    df: pd.DataFrame,
    *,
    target_col: str = "y_up_h40",
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Document delta AUC and verdict for curve spread features."""
    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    work = work[(work["Date"] <= pd.Timestamp("2022-12-31")) & work[target_col].notna()].reset_index(drop=True)
    curve_cols = [col for col in CURVE_SPREAD_COLUMNS if col in work.columns and work[col].notna().any()]
    base_cols = [
        col
        for col in work.columns
        if col not in {"Date", target_col}
        and not col.startswith("y_")
        and col not in curve_cols
        and pd.api.types.is_numeric_dtype(work[col])
    ]
    y = work[target_col].astype(int)
    baseline_auc = _oof_auc(work[base_cols], y) if base_cols else np.nan
    with_auc = _oof_auc(work[base_cols + curve_cols], y) if base_cols and curve_cols else np.nan
    delta = with_auc - baseline_auc if math.isfinite(baseline_auc) and math.isfinite(with_auc) else np.nan
    payload: dict[str, Any] = {
        "target_col": target_col,
        "curve_cols": curve_cols,
        "baseline_auc": _json_float(baseline_auc),
        "auc_with_curve": _json_float(with_auc),
        "delta_auc": _json_float(delta),
        "verdict": _verdict(delta),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _col(df: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
    return None


def _expanding_zscore(series: pd.Series) -> pd.Series:
    mu = series.expanding(60).mean()
    sd = series.expanding(60).std().replace(0, np.nan)
    return (series - mu) / sd


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


def _verdict(delta_auc: float) -> str:
    if not math.isfinite(delta_auc):
        return "INCONCLU"
    if delta_auc >= 0.008:
        return "CONFIRMÉ"
    if delta_auc > 0:
        return "PROMETTEUR"
    if delta_auc < -0.003:
        return "REJETÉ"
    return "NEUTRE"


def _json_float(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None

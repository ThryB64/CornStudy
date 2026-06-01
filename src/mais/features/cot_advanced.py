"""Advanced normalized COT features.

The raw COT position levels are not stationary because market open interest
changes over time. These helpers normalize managed-money and commercial
positions by total open interest, then express the result as expanding
historical percentiles for interpretable contrarian signals.
"""

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

ADVANCED_COT_COLUMNS = [
    "cot_mm_net_pct_oi",
    "cot_comm_net_pct_oi",
    "cot_mm_pct_oi_percentile",
    "cot_comm_pct_oi_percentile",
    "cot_mm_extreme_long_flag",
    "cot_mm_extreme_short_flag",
    "cot_hedger_pressure",
    "cot_crowding_score",
]


def build_cot_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return the 8 R&D-09 COT features aligned to ``df`` dates.

    The input is expected to already contain publication-lagged COT columns as
    produced by ``build_features()``. Derived ratios are additionally shifted
    by one row so a row never uses its own same-row COT update to construct
    second-order features.
    """
    out = pd.DataFrame({"Date": pd.to_datetime(df["Date"])}) if "Date" in df.columns else pd.DataFrame(index=df.index)
    oi = _numeric(df, ["cot_open_interest", "total_open_interest"])
    mm_net = _numeric(df, ["cot_mm_net", "cot_managed_money_net"])
    comm_net = _numeric(df, ["cot_comm_net", "cot_commercial_net", "cot_pm_net"])

    if oi is None or mm_net is None:
        return _empty(out)

    oi = oi.replace(0.0, np.nan)
    mm_pct = (mm_net / oi).replace([np.inf, -np.inf], np.nan).shift(1)
    out["cot_mm_net_pct_oi"] = mm_pct

    if comm_net is not None:
        comm_pct = (comm_net / oi).replace([np.inf, -np.inf], np.nan).shift(1)
    else:
        comm_pct = pd.Series(np.nan, index=df.index, dtype=float)
    out["cot_comm_net_pct_oi"] = comm_pct

    mm_percentile = expanding_percentile(mm_pct)
    comm_percentile = expanding_percentile(comm_pct)
    out["cot_mm_pct_oi_percentile"] = mm_percentile
    out["cot_comm_pct_oi_percentile"] = comm_percentile
    out["cot_mm_extreme_long_flag"] = (mm_percentile > 0.90).astype(float)
    out.loc[mm_percentile.isna(), "cot_mm_extreme_long_flag"] = np.nan
    out["cot_mm_extreme_short_flag"] = (mm_percentile < 0.10).astype(float)
    out.loc[mm_percentile.isna(), "cot_mm_extreme_short_flag"] = np.nan
    out["cot_hedger_pressure"] = comm_pct
    out["cot_crowding_score"] = (mm_percentile - 0.5).abs() * 2.0
    return out


def expanding_percentile(series: pd.Series, min_periods: int = 20) -> pd.Series:
    """Expanding percentile rank of each value against values available so far."""
    values = pd.to_numeric(series, errors="coerce")
    out = pd.Series(np.nan, index=values.index, dtype=float)
    history: list[float] = []
    for idx, value in values.items():
        if pd.isna(value):
            continue
        history.append(float(value))
        if len(history) < min_periods:
            continue
        arr = np.asarray(history, dtype=float)
        out.loc[idx] = float(np.mean(arr <= float(value)))
    return out


def evaluate_cot_advanced_stability(
    df: pd.DataFrame,
    *,
    target_col: str = "y_up_h40",
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Document delta AUC and 2010-2015 vs 2016-2022 crowding stability.

    ``df`` must include ``Date``, ``target_col``, baseline numeric features, and
    the advanced COT columns. The function is intentionally data-frame based so
    tests and pipelines can call it without hard-coded reads from ``data/``.
    """
    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    work = work[(work["Date"] <= pd.Timestamp("2022-12-31")) & work[target_col].notna()].reset_index(drop=True)
    cot_cols = [col for col in ADVANCED_COT_COLUMNS if col in work.columns and work[col].notna().any()]
    feature_cols = [
        col
        for col in work.columns
        if col not in {"Date", target_col}
        and not col.startswith("y_")
        and pd.api.types.is_numeric_dtype(work[col])
    ]
    baseline_cols = [col for col in feature_cols if col not in cot_cols]
    y = work[target_col].astype(int)
    baseline_auc = _oof_auc(work[baseline_cols], y) if baseline_cols else np.nan
    with_auc = _oof_auc(work[baseline_cols + cot_cols], y) if baseline_cols and cot_cols else np.nan
    delta = with_auc - baseline_auc if math.isfinite(baseline_auc) and math.isfinite(with_auc) else np.nan
    early = work[work["Date"] <= pd.Timestamp("2015-12-31")]
    late = work[(work["Date"] >= pd.Timestamp("2016-01-01")) & (work["Date"] <= pd.Timestamp("2022-12-31"))]
    early_auc = _oof_auc(early[baseline_cols + cot_cols], early[target_col].astype(int)) if len(early) else np.nan
    late_auc = _oof_auc(late[baseline_cols + cot_cols], late[target_col].astype(int)) if len(late) else np.nan
    payload: dict[str, Any] = {
        "target_col": target_col,
        "cot_advanced_cols": cot_cols,
        "baseline_auc": _json_float(baseline_auc),
        "auc_with_cot_advanced": _json_float(with_auc),
        "delta_auc": _json_float(delta),
        "auc_2010_2015": _json_float(early_auc),
        "auc_2016_2022": _json_float(late_auc),
        "crowding_delta_auc_late_minus_early": _json_float(late_auc - early_auc)
        if math.isfinite(early_auc) and math.isfinite(late_auc)
        else None,
        "verdict": _verdict(delta),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _numeric(df: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
    return None


def _empty(out: pd.DataFrame) -> pd.DataFrame:
    for col in ADVANCED_COT_COLUMNS:
        out[col] = np.nan
    return out


def _oof_auc(features: pd.DataFrame, y: pd.Series) -> float:
    if len(features) < 80 or len(np.unique(y)) < 2 or features.shape[1] == 0:
        return np.nan
    x = features.replace([np.inf, -np.inf], np.nan).dropna(axis=1, how="all")
    if x.shape[1] == 0:
        return np.nan
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    model = Pipeline(
        [
            ("imputer", imputer),
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
    if delta_auc > 0.0:
        return "PROMETTEUR"
    if delta_auc < -0.003:
        return "REJETÉ"
    return "NEUTRE"


def _json_float(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None

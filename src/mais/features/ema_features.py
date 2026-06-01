"""Assembly wrapper for EMA feature blocks."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.features.euronext_continuous import load_continuous_feature_block
from mais.features.euronext_curve import EMA_CURVE_FEATURE_COLUMNS
from mais.paths import EMA_CURVE_FEATURES

EMA_AVAILABILITY_COLUMNS = [
    "ema_curve_available",
    "ema_continuous_available",
    "ema_data_availability_score",
]


def build_ema_features(
    dates: pd.Series | pd.DatetimeIndex,
    *,
    curve_features: pd.DataFrame | None = None,
    continuous_features: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Assemble lag-safe Euronext EMA features on a daily Date index."""
    base = pd.DataFrame({"Date": pd.to_datetime(pd.Series(dates).unique())})
    base = base.sort_values("Date").reset_index(drop=True)
    blocks: list[pd.DataFrame] = []
    if curve_features is None and EMA_CURVE_FEATURES.exists():
        curve_features = pd.read_parquet(EMA_CURVE_FEATURES)
    if curve_features is not None and not curve_features.empty:
        blocks.append(_normalise_block(curve_features))

    if continuous_features is None:
        continuous_features = load_continuous_feature_block(base["Date"])
    if continuous_features is not None and len(continuous_features.columns) > 1:
        blocks.append(_normalise_block(continuous_features))

    out = base
    for block in blocks:
        out = out.merge(block, on="Date", how="left")
    out = out.loc[:, ~out.columns.duplicated()].sort_values("Date").reset_index(drop=True)
    assert_no_ema_target_leakage(out)
    if not blocks:
        return out
    out = _add_availability_scores(out)
    return out


def assert_no_ema_target_leakage(features: pd.DataFrame) -> None:
    """Guardrail: EMA target columns must never appear in features."""
    forbidden = [
        col
        for col in features.columns
        if col.lower().startswith("y_") and ("ema" in col.lower() or "euronext" in col.lower())
    ]
    if forbidden:
        raise AssertionError(f"EMA target columns leaked into features: {forbidden}")


def _normalise_block(frame: pd.DataFrame) -> pd.DataFrame:
    block = frame.copy()
    if "Date" not in block.columns and "date" in block.columns:
        block["Date"] = block["date"]
    if "Date" not in block.columns:
        raise ValueError("EMA feature block requires Date or date column")
    block["Date"] = pd.to_datetime(block["Date"]).dt.normalize()
    return block.drop(columns=["date"], errors="ignore").drop_duplicates("Date", keep="last")


def _add_availability_scores(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    curve_cols = [col for col in EMA_CURVE_FEATURE_COLUMNS if col in out.columns]
    continuous_cols = [
        col
        for col in out.columns
        if col.startswith(("ema_front_", "ema_liquid_", "ema_harvest_nov_"))
        and col not in curve_cols
        and col not in EMA_AVAILABILITY_COLUMNS
    ]
    out["ema_curve_available"] = (
        out[curve_cols].notna().any(axis=1).astype(float) if curve_cols else 0.0
    )
    out["ema_continuous_available"] = (
        out[continuous_cols].notna().any(axis=1).astype(float) if continuous_cols else 0.0
    )
    components = out[["ema_curve_available", "ema_continuous_available"]].replace(0.0, np.nan)
    out["ema_data_availability_score"] = components.notna().mean(axis=1)
    return out

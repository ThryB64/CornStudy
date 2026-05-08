"""Belt-weighted weather features (Phase 1 NEW).

Replaces the legacy ~280 ``wx_<state>_*`` columns with ~10 belt-weighted
aggregates. The weights come from ``config/sources.yaml`` (production share
per state). Only the top-5 states are kept individually.

Why this matters
----------------
1. Iowa = 18% production, Tennessee = <0.5%. Treating them equally is wrong.
2. ML models drown in 280 highly-correlated weather columns.
3. Anomalies (z-score vs 30y day-of-year climatology) are far more predictive
   than raw values.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from mais.utils import get_logger, load_sources

log = get_logger("mais.features.weather_belt")

TOP5 = ["iowa", "illinois", "nebraska", "minnesota", "indiana"]

# Map open-meteo / legacy variable names to canonical short names
VARIABLE_ALIASES = {
    "tavg_c":            ["tavg_c", "temperature_2m_mean", "tavg_30_mean"],
    "tmin_c":            ["tmin_c", "temperature_2m_min"],
    "tmax_c":            ["tmax_c", "temperature_2m_max"],
    "prcp_mm":           ["prcp_mm", "precipitation_sum"],
    "prcp_30":           ["prcp_30", "rain_30_sum"],
    "soil_moisture":     ["soil_moisture", "soil_moisture_28_to_100cm_mean"],
    "et0":               ["et0", "et0_fao_evapotranspiration"],
    "rh":                ["rh", "relative_humidity_2m_mean"],
}


def _state_weights() -> dict[str, float]:
    cfg = load_sources()
    src = next((s for s in cfg.get("sources", []) if s["name"] == "openmeteo_states"), None)
    if not src:
        return {}
    return {s["name"]: float(s.get("weight", 0.0)) for s in src.get("states", [])}


def _detect_state_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    """Group columns by state. Column convention: ``wx_<state>_<variable>``."""
    out: dict[str, list[str]] = {}
    for c in df.columns:
        if c == "Date":
            continue
        m = re.match(r"^wx_([a-z_]+?)_(.+)$", str(c))
        if not m:
            continue
        state = m.group(1)
        out.setdefault(state, []).append(c)
    return out


def _aggregate_variable(df: pd.DataFrame, state_cols: dict[str, list[str]],
                         weights: dict[str, float], var_aliases: list[str]) -> pd.Series | None:
    """Weighted-average a given variable across states."""
    series = []
    w = []
    for state, cols in state_cols.items():
        weight = weights.get(state, 0.0)
        if weight <= 0:
            continue
        # Find a matching variable column
        match = None
        for alias in var_aliases:
            for c in cols:
                if c.endswith("_" + alias):
                    match = c
                    break
            if match:
                break
        if not match:
            continue
        series.append(df[match].astype(float))
        w.append(weight)
    if not series:
        return None
    weights_arr = np.array(w, dtype=float)
    weights_arr = weights_arr / weights_arr.sum()
    stacked = pd.concat(series, axis=1)
    return (stacked * weights_arr).sum(axis=1, min_count=1)


def _doy_zscore(s: pd.Series, dates: pd.Series, min_years: int = 5) -> pd.Series:
    """Day-of-year anomaly z-score (expanding to avoid future leakage)."""
    df = pd.DataFrame({"value": s.values, "Date": pd.to_datetime(dates).values})
    df["doy"] = df["Date"].dt.dayofyear
    df["year"] = df["Date"].dt.year

    out = pd.Series(np.nan, index=df.index)
    # For each row, use only past years' DOY values
    grouped = df.groupby("doy")
    for doy, idx in grouped.groups.items():
        sub = df.loc[idx].sort_values("Date").reset_index()
        # Expanding mean/std using past years only
        mean = sub["value"].expanding(min_periods=min_years).mean().shift(1)
        std = sub["value"].expanding(min_periods=min_years).std().shift(1)
        z = (sub["value"] - mean) / std
        out.iloc[sub["index"].values] = z.values
    return out.clip(-6, 6)


def build_weather_belt_features(meteo: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in meteo.columns:
        raise ValueError("meteo DataFrame must have a Date column.")
    df = meteo.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    weights = _state_weights()
    state_cols = _detect_state_columns(df)
    if not weights or not state_cols:
        log.warning("weather_belt_no_data", n_weights=len(weights), n_states=len(state_cols))
        return pd.DataFrame({"Date": df["Date"]})

    out = pd.DataFrame({"Date": df["Date"].values})

    for canon, aliases in VARIABLE_ALIASES.items():
        agg = _aggregate_variable(df, state_cols, weights, aliases)
        if agg is None:
            continue
        out[f"wx_belt_{canon}"] = agg.values
        # Anomaly z-score (expanding by DOY)
        try:
            out[f"wx_belt_{canon}_anom_z"] = _doy_zscore(agg, df["Date"]).values
        except Exception as e:
            log.warning("wx_belt_zscore_failed", var=canon, error=str(e))

    # Drought proxy: cumulative precipitation deficit vs ET0 over 30 days
    if "wx_belt_prcp_mm" in out.columns and "wx_belt_et0" in out.columns:
        deficit = (out["wx_belt_prcp_mm"] - out["wx_belt_et0"]).rolling(30, min_periods=20).sum()
        out["wx_belt_drought_proxy_30"] = deficit

    # Heat stress: count of days >35C in last 30 days
    if "wx_belt_tmax_c" in out.columns:
        out["wx_belt_heat_days_30"] = (out["wx_belt_tmax_c"] > 35).rolling(30, min_periods=20).sum()

    # Keep top5 states individually for the most informative variables
    for state in TOP5:
        if state not in state_cols:
            continue
        cols = state_cols[state]
        for alias in ["temperature_2m_mean", "tavg_c"]:
            for c in cols:
                if c.endswith("_" + alias):
                    out[f"wx_{state}_tavg_anom_z"] = _doy_zscore(
                        df[c].astype(float), df["Date"]
                    ).values
                    break

    # Anti-leakage: weather data for date t was observed at end-of-day t
    feat_cols = [c for c in out.columns if c != "Date"]
    out[feat_cols] = out[feat_cols].shift(1)
    return out

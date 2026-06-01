"""Euronext Matif EMA feature engineering."""

from __future__ import annotations

import numpy as np
import pandas as pd

BUSHEL_TO_TONNE = 39.3679


def build_ema_targets(ema: pd.DataFrame, *, horizons: tuple[int, ...] = (20, 40, 60), price_col: str = "ema_close") -> pd.DataFrame:
    """Build EMA directional, return and price targets."""
    work = ema[["Date", price_col]].copy()
    work["Date"] = pd.to_datetime(work["Date"])
    work = work.sort_values("Date").reset_index(drop=True)
    out = pd.DataFrame({"Date": work["Date"]})
    price = work[price_col].astype(float)
    for horizon in horizons:
        future = price.shift(-int(horizon))
        out[f"y_logret_h{horizon}_ema"] = np.log(future / price)
        out[f"y_up_h{horizon}_ema"] = (future > price).astype(float)
        out.loc[future.isna(), f"y_up_h{horizon}_ema"] = np.nan
        out[f"y_price_h{horizon}_ema"] = future
        out[f"y_down_gt_5pct_h{horizon}_ema"] = (future / price - 1.0 < -0.05).astype(float)
        out[f"y_up_gt_5pct_h{horizon}_ema"] = (future / price - 1.0 > 0.05).astype(float)
    return out


def build_cross_market_features(
    ema: pd.DataFrame,
    cbot: pd.DataFrame,
    eurusd: pd.DataFrame,
    *,
    ema_col: str = "ema_close",
    cbot_col: str = "corn_close",
    eurusd_col: str = "eurusd_rate",
) -> pd.DataFrame:
    """Build lag-safe CBOT/EUR/t, EMA basis and cross-market features."""
    e = ema[["Date", ema_col]].copy()
    c = cbot[["Date", cbot_col]].copy()
    fx = eurusd[["Date", eurusd_col]].copy()
    for frame in (e, c, fx):
        frame["Date"] = pd.to_datetime(frame["Date"])
    merged = e.merge(c, on="Date", how="inner").merge(fx, on="Date", how="inner")
    merged = merged.sort_values("Date").reset_index(drop=True)
    merged["cbot_eur_t"] = (merged[cbot_col].astype(float) / 100.0) / merged[eurusd_col].astype(float) * BUSHEL_TO_TONNE
    merged["cbot_ema_basis"] = merged["cbot_eur_t"] - merged[ema_col].astype(float)
    merged["cbot_ema_basis_zscore"] = expanding_zscore(merged["cbot_ema_basis"]).shift(1)
    merged["eurusd_zscore_52w"] = rolling_zscore(merged[eurusd_col], window=260).shift(1)
    merged["ema_return_5d_lag1"] = np.log(merged[ema_col] / merged[ema_col].shift(5)).shift(1)
    return merged[["Date", "cbot_eur_t", "cbot_ema_basis", "cbot_ema_basis_zscore", "eurusd_zscore_52w", "ema_return_5d_lag1"]]


def build_ema_curve_features(contracts: pd.DataFrame) -> pd.DataFrame:
    """Build front, most-liquid and curve spread features from contract rows."""
    required = {"Date", "contract_code", "settlement"}
    missing = required - set(contracts.columns)
    if missing:
        raise ValueError(f"Missing EMA contract columns: {sorted(missing)}")
    work = contracts.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    if "days_to_expiry" not in work.columns:
        work["days_to_expiry"] = 9999
    if "volume" not in work.columns:
        work["volume"] = 0
    work = work.sort_values(["Date", "days_to_expiry", "volume"])
    front = work.groupby("Date", as_index=False).first()[["Date", "settlement"]].rename(columns={"settlement": "ema_front_settlement"})
    most_liquid = (
        work.sort_values(["Date", "volume"], ascending=[True, False])
        .groupby("Date", as_index=False)
        .first()[["Date", "settlement"]]
        .rename(columns={"settlement": "ema_most_liquid_settlement"})
    )
    wide = work.pivot_table(index="Date", columns="contract_code", values="settlement", aggfunc="last")
    spreads = pd.DataFrame({"Date": wide.index})
    codes = list(wide.columns)
    if len(codes) >= 2:
        spreads["ema_near_deferred_spread"] = wide[codes[0]].to_numpy() - wide[codes[1]].to_numpy()
    else:
        spreads["ema_near_deferred_spread"] = np.nan
    out = front.merge(most_liquid, on="Date", how="outer").merge(spreads, on="Date", how="outer")
    out["ema_contango_flag"] = (out["ema_near_deferred_spread"] < 0).astype(int)
    out["ema_backwardation_flag"] = (out["ema_near_deferred_spread"] > 0).astype(int)
    return out.sort_values("Date").reset_index(drop=True)


def build_euronext_master_features(frames: list[pd.DataFrame], *, expected_sources: tuple[str, ...] = ()) -> pd.DataFrame:
    """Merge Euronext/EU/world feature blocks and compute availability score."""
    if not frames:
        return pd.DataFrame()
    merged = frames[0].copy()
    merged["Date"] = pd.to_datetime(merged["Date"])
    for frame in frames[1:]:
        other = frame.copy()
        other["Date"] = pd.to_datetime(other["Date"])
        merged = merged.merge(other, on="Date", how="outer")
    merged = merged.sort_values("Date").reset_index(drop=True)
    feature_cols = [c for c in merged.columns if c != "Date"]
    merged["data_availability_score"] = merged[feature_cols].notna().mean(axis=1) if feature_cols else 0.0
    for source in expected_sources:
        cols = [c for c in feature_cols if c.startswith(source)]
        if cols:
            merged[f"{source}_available"] = merged[cols].notna().any(axis=1).astype(int)
    return merged


def expanding_zscore(series: pd.Series, *, min_periods: int = 20) -> pd.Series:
    mean = series.expanding(min_periods=min_periods).mean()
    std = series.expanding(min_periods=min_periods).std().replace(0, np.nan)
    return (series - mean) / std


def rolling_zscore(series: pd.Series, *, window: int = 260) -> pd.Series:
    mean = series.rolling(window, min_periods=max(5, min(window, 20))).mean()
    std = series.rolling(window, min_periods=max(5, min(window, 20))).std().replace(0, np.nan)
    return (series - mean) / std

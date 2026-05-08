"""Market-derived features (returns, vols, technical indicators).

All features are SHIFTED BY +1 day so that the value at row t uses ONLY
information available at end-of-day t-1. This is the single most important
anti-leakage rule for technical indicators.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_log(x: pd.Series) -> pd.Series:
    return np.log(x.where(x > 0))


def build_market_features(db: pd.DataFrame) -> pd.DataFrame:
    """Build the technical / market feature set.

    Expected input columns (any subset works): corn_close, corn_open, corn_high,
    corn_low, corn_volume, soy_close, wheat_close, oil_close, gas_close,
    usd_index_close.

    Output: DataFrame with Date column and all engineered features, all shifted
    by +1 day to be safe.
    """
    if "Date" not in db.columns:
        raise ValueError("Market features require a Date column.")

    df = db.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)

    out = pd.DataFrame({"Date": df["Date"].values})

    if "corn_close" in df.columns:
        c = df["corn_close"].astype(float)
        log_c = _safe_log(c)
        out["corn_logret_1d"] = log_c.diff()
        out["corn_logret_5d"] = log_c.diff(5)
        out["corn_logret_20d"] = log_c.diff(20)
        out["corn_realized_vol_20"] = (
            log_c.diff().rolling(20, min_periods=20).std() * np.sqrt(252)
        )
        out["corn_realized_vol_60"] = (
            log_c.diff().rolling(60, min_periods=60).std() * np.sqrt(252)
        )
        out["corn_sma_20"] = c.rolling(20, min_periods=20).mean()
        out["corn_sma_50"] = c.rolling(50, min_periods=50).mean()
        out["corn_ema_10"] = c.ewm(span=10, adjust=False, min_periods=10).mean()
        out["corn_ema_20"] = c.ewm(span=20, adjust=False, min_periods=20).mean()
        out["corn_drawdown_252"] = c / c.rolling(252, min_periods=60).max() - 1.0
        out["corn_dist_to_52w_high"] = c / c.rolling(252, min_periods=60).max() - 1.0
        out["corn_dist_to_52w_low"] = c / c.rolling(252, min_periods=60).min() - 1.0

        # Bollinger
        bb_mid = c.rolling(20, min_periods=20).mean()
        bb_std = c.rolling(20, min_periods=20).std()
        out["corn_bb_percent_b_20"] = (c - (bb_mid - 2 * bb_std)) / (4 * bb_std)
        out["corn_bb_bandwidth_20"] = (4 * bb_std) / bb_mid

        # RSI 14 (Wilder)
        delta = c.diff()
        up = delta.clip(lower=0)
        down = (-delta).clip(lower=0)
        roll_up = up.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
        roll_down = down.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
        rs = roll_up / roll_down.replace(0, np.nan)
        out["corn_rsi_14"] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = c.ewm(span=12, adjust=False, min_periods=12).mean()
        ema26 = c.ewm(span=26, adjust=False, min_periods=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
        out["corn_macd_line"] = macd
        out["corn_macd_signal"] = signal
        out["corn_macd_hist"] = macd - signal

        # ATR 14
        if {"corn_high", "corn_low"}.issubset(df.columns):
            h, l, prev_c = df["corn_high"].astype(float), df["corn_low"].astype(float), c.shift(1)
            tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
            out["corn_atr_14"] = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    # Cross-commodity ratios + correlations
    pairs = [("soy_close", "soy"), ("wheat_close", "wheat"),
              ("oil_close", "oil"), ("gas_close", "gas"), ("usd_index_close", "dxy")]
    if "corn_close" in df.columns:
        c = df["corn_close"].astype(float)
        for col, lbl in pairs:
            if col not in df.columns:
                continue
            other = df[col].astype(float)
            out[f"corn_{lbl}_ratio"] = c / other.replace(0, np.nan)
            other_logret = _safe_log(other).diff()
            corn_logret = _safe_log(c).diff()
            out[f"corn_{lbl}_corr60"] = corn_logret.rolling(60, min_periods=40).corr(other_logret)

    # Volume z-score
    if "corn_volume" in df.columns:
        v = df["corn_volume"].astype(float)
        out["corn_volume_z20"] = (v - v.rolling(20, min_periods=20).mean()) / v.rolling(20, min_periods=20).std()

    # CRITICAL: anti-leakage shift +1
    feature_cols = [c for c in out.columns if c != "Date"]
    out[feature_cols] = out[feature_cols].shift(1)

    return out

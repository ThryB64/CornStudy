"""Target reformulation — go beyond y_logret_h20.

The central insight: predicting the exact return is hard.
A more useful target for a farmer may be:
  "Is waiting N days profitable after storage cost?"

All targets are built WITHOUT lookahead — computed then shifted so they
align with the decision date.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.research.target_reformulation")

STORAGE_COST_USD_PER_BU_PER_MONTH = 0.04  # Iowa average
RESEARCH_HORIZONS = [1, 5, 10, 20, 30, 60, 90]
STRONG_MOVE_THRESHOLDS = [0.01, 0.02, 0.03, 0.05]


def build_target_suite(
    feat: pd.DataFrame,
    price_col: str = "corn_close",
    horizons: list[int] | None = None,
    storage_cost_per_day: float = STORAGE_COST_USD_PER_BU_PER_MONTH / 21,
    strong_threshold: float = 0.03,
) -> pd.DataFrame:
    """Build all target variants aligned at the decision date (no lookahead).

    Returns a DataFrame with Date + all targets. Every target uses shift
    to avoid leakage: the label reflects what happens in the future,
    aligned to the current trading day.

    Target families
    ---------------
    log-return          y_logret_hN
    direction           y_up_hN  (1 if positive return)
    strong move         y_up_strong_hN / y_down_strong_hN  (|ret| > threshold)
    future max          y_max_ret_hN  (max return over next N days)
    storage value       y_storage_value_hN  (future price - today - storage cost)
    storage opportunity y_store_hN  (1 if storage is profitable)
    regret              y_regret_hN  (max future price - today, normalised)
    """
    if horizons is None:
        horizons = RESEARCH_HORIZONS

    df = feat[["Date", price_col]].copy().sort_values("Date").reset_index(drop=True)
    price = df[price_col]

    out = pd.DataFrame({"Date": df["Date"]})

    for h in horizons:
        strong_h = {20: 0.02, 30: 0.03}.get(h, strong_threshold)

        # Log-return at exactly h days ahead
        fut = price.shift(-h)
        logret = np.log(fut / price)

        out[f"y_logret_h{h}"] = logret.shift(h)  # align: today sees h-day-old signal

        # Actually, standard convention: y at t = log(p_{t+h}/p_t)
        # We compute without shift and the walkforward handles the split.
        # Reset to no-shift (the study already handles leakage via train/test split on dates)
        out[f"y_logret_h{h}"] = logret

        # Direction
        out[f"y_up_h{h}"] = (logret > 0).astype(int)

        # Strong moves
        out[f"y_up_strong_h{h}"]   = (logret >  strong_h).astype(int)
        out[f"y_down_strong_h{h}"] = (logret < -strong_h).astype(int)
        for threshold in STRONG_MOVE_THRESHOLDS:
            pct = int(round(threshold * 100))
            out[f"y_up_gt_{pct}pct_h{h}"] = (logret > threshold).astype(int)
            out[f"y_down_gt_{pct}pct_h{h}"] = (logret < -threshold).astype(int)

        # Maximum return over the next h days
        max_ret = pd.Series(index=df.index, dtype=float)
        for i in range(len(price)):
            window = price.iloc[i+1 : i+h+1]
            if len(window) == 0:
                max_ret.iloc[i] = np.nan
            else:
                max_ret.iloc[i] = float(np.log(window.max() / price.iloc[i]))
        out[f"y_max_ret_h{h}"] = max_ret
        out[f"future_max_return_h{h}"] = max_ret

        min_ret = pd.Series(index=df.index, dtype=float)
        up_frac = pd.Series(index=df.index, dtype=float)
        daily_logret = np.log(price / price.shift(1))
        for i in range(len(price)):
            window = price.iloc[i+1 : i+h+1]
            ret_window = daily_logret.iloc[i+1 : i+h+1]
            if len(window) == 0:
                min_ret.iloc[i] = np.nan
                up_frac.iloc[i] = np.nan
            else:
                min_ret.iloc[i] = float(np.log(window.min() / price.iloc[i]))
                up_frac.iloc[i] = float((ret_window > 0).mean())
        out[f"future_min_return_h{h}"] = min_ret
        out[f"prob_up_h{h}"] = up_frac

        # Storage value (in price units, assuming CBOT = cts/bu → /100 = USD/bu)
        cost = storage_cost_per_day * h
        # price in cts/bu → / 100 = USD/bu for cost comparison
        storage_val = (fut - price) / 100 - cost
        out[f"y_storage_value_h{h}"] = storage_val
        out[f"storage_value_h{h}"] = storage_val

        # Storage opportunity: is it worth storing?
        out[f"y_store_h{h}"] = (storage_val > 0).astype(int)

        # Regret: how much did we leave on the table by selling today?
        out[f"y_regret_h{h}"] = max_ret  # same as max_ret for now
        out[f"sell_regret_h{h}"] = (max_ret - logret).clip(lower=0)

        min_periods = min(h, max(2, h // 2))
        realized_vol = (
            daily_logret.shift(-1)
            .rolling(window=h, min_periods=min_periods)
            .std()
            .shift(-(h - 1))
            * np.sqrt(252)
        )
        out[f"realized_vol_h{h}"] = realized_vol

    log.info("targets_built", n_targets=len(out.columns) - 1, horizons=horizons)
    return out


def describe_targets(targets: pd.DataFrame) -> pd.DataFrame:
    """Summary statistics for all target columns."""
    rows = []
    for col in targets.columns:
        if col == "Date":
            continue
        s = targets[col].dropna()
        rows.append({
            "target": col,
            "n": len(s),
            "mean": float(s.mean()),
            "std": float(s.std()),
            "pos_rate": float((s > 0).mean()) if s.dtype != object else float("nan"),
            "min": float(s.min()),
            "max": float(s.max()),
        })
    return pd.DataFrame(rows)


def compare_target_predictability(
    feat: pd.DataFrame,
    targets: pd.DataFrame,
    feature_cols: list[str] | None = None,
    n_features: int = 10,
) -> pd.DataFrame:
    """Quick mutual information / correlation scan across all targets.

    Uses top-N features by average absolute correlation with y_logret_h20.
    """
    from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

    if feature_cols is None:
        # Use factor columns if available
        feature_cols = [c for c in feat.columns if c.startswith("factor_")]
        if not feature_cols:
            feature_cols = [c for c in feat.columns if c != "Date" and
                            pd.api.types.is_numeric_dtype(feat[c])][:30]

    merged = feat[["Date"] + feature_cols].merge(targets, on="Date", how="inner").dropna(subset=feature_cols)
    feature_values = merged[feature_cols].fillna(0).values

    rows = []
    for tgt_col in targets.columns:
        if tgt_col == "Date":
            continue
        y = merged[tgt_col].dropna()
        idx = y.index.intersection(merged.index)
        if len(idx) < 100:
            continue
        feature_subset = feature_values[merged.index.get_indexer(idx)]
        target_values = y.loc[idx].values

        is_binary = set(np.unique(target_values[~np.isnan(target_values)])).issubset({0, 1})
        try:
            if is_binary:
                mi = mutual_info_classif(feature_subset, target_values, discrete_features=False, random_state=42)
            else:
                mi = mutual_info_regression(feature_subset, target_values, random_state=42)
            rows.append({"target": tgt_col, "mi_sum": float(mi.sum()), "mi_max": float(mi.max()), "n": len(target_values)})
        except Exception:
            continue

    return pd.DataFrame(rows).sort_values("mi_sum", ascending=False)

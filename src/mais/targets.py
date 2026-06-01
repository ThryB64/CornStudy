"""Build the targets table.

This module is the **only** place where future-looking targets are constructed.
It is deliberately separated from features so that the anti-leakage audit
(``mais/leakage/audit.py``) can verify that no feature column references the
future.

For each horizon H in the configured research horizons:

- ``y_logret_h{H}``       : log return ``log(P_{t+H}) - log(P_t)``  (regression target)
- ``y_class_h{H}``        : decile class of the log return           (ordinal)
- ``y_up_h{H}``           : 1 if log return > 0                      (binary)
- ``y_up_strong_h{H}``    : 1 if log return > log(1.05)              (binary)
- ``y_down_strong_h{H}``  : 1 if log return < log(0.97)              (binary)
- ``y_realized_vol_h{H}`` : annualised std of next H daily log returns

Decile bins are computed on an **expanding** window so that classes at time t
only use information up to t (no leakage).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import TARGETS_PARQUET
from mais.utils import get_logger, write_parquet

log = get_logger("mais.targets")


DEFAULT_HORIZONS: tuple[int, ...] = (5, 10, 20, 30)
EXTENDED_HORIZONS: tuple[int, ...] = (1, 5, 10, 20, 30, 60, 90)
STRONG_MOVE_THRESHOLDS: tuple[float, ...] = (0.01, 0.02, 0.03, 0.05)
STORAGE_COST_USD_PER_BU_PER_MONTH = 0.04
REQUIRED_RESEARCH_TARGETS: tuple[str, ...] = (
    "y_up_h20",
    "y_up_strong_h20",
    "realized_vol_h20",
    "future_max_return_h30",
    "sell_regret_h30",
)


@dataclass
class TargetSpec:
    horizons: tuple[int, ...] = EXTENDED_HORIZONS
    price_col: str = "corn_close"
    date_col: str = "Date"
    n_class_bins: int = 10
    strong_threshold: float = 0.03
    strong_threshold_by_horizon: dict[int, float] = field(default_factory=lambda: {20: 0.02, 30: 0.03})
    strong_move_thresholds: tuple[float, ...] = STRONG_MOVE_THRESHOLDS
    storage_cost_usd_per_bu_per_day: float = STORAGE_COST_USD_PER_BU_PER_MONTH / 21
    expanding_min_points: int = 252
    extra_metrics: tuple[str, ...] = field(default_factory=lambda: ("realized_vol", "future_max", "future_min", "storage_value", "prob_up", "sell_regret"))


def build_targets(prices: pd.DataFrame, spec: TargetSpec | None = None) -> pd.DataFrame:
    """Construct the multi-horizon targets DataFrame.

    Parameters
    ----------
    prices
        Must contain ``spec.date_col`` and ``spec.price_col``.
    spec
        Configuration. Defaults: horizons (5,10,20,30) on ``corn_close``.

    Returns
    -------
    pd.DataFrame
        Columns: Date, plus for each H one of each y_* family.
        Rows where the H-step-ahead price is unknown are kept with NaN.
    """
    spec = spec or TargetSpec()
    if spec.price_col not in prices.columns:
        raise KeyError(f"Price column '{spec.price_col}' missing from prices DataFrame.")
    if spec.date_col not in prices.columns:
        raise KeyError(f"Date column '{spec.date_col}' missing from prices DataFrame.")

    df = prices[[spec.date_col, spec.price_col]].copy()
    df[spec.date_col] = pd.to_datetime(df[spec.date_col], errors="coerce")
    df = df.dropna(subset=[spec.date_col, spec.price_col]).sort_values(spec.date_col)
    df = df.drop_duplicates(subset=[spec.date_col], keep="last").reset_index(drop=True)

    log_p = np.log(df[spec.price_col].astype(float))
    out = pd.DataFrame({spec.date_col: df[spec.date_col].values})

    for horizon in spec.horizons:
        future_log_p = log_p.shift(-horizon)
        logret = (future_log_p - log_p).rename(f"y_logret_h{horizon}")
        strong_threshold = spec.strong_threshold_by_horizon.get(horizon, spec.strong_threshold)

        out[f"y_logret_h{horizon}"] = logret.values

        # Binary targets
        out[f"y_up_h{horizon}"] = (logret > 0).astype("Int8").where(logret.notna()).values
        out[f"y_up_strong_h{horizon}"] = (
            (logret > strong_threshold).astype("Int8")
            .where(logret.notna()).values
        )
        out[f"y_down_strong_h{horizon}"] = (
            (logret < -strong_threshold).astype("Int8")
            .where(logret.notna()).values
        )
        for threshold in spec.strong_move_thresholds:
            pct = int(round(threshold * 100))
            out[f"y_up_gt_{pct}pct_h{horizon}"] = (
                (logret > threshold).astype("Int8").where(logret.notna()).values
            )
            out[f"y_down_gt_{pct}pct_h{horizon}"] = (
                (logret < -threshold).astype("Int8").where(logret.notna()).values
            )

        # Ordinal class via expanding-window deciles (anti-leakage)
        out[f"y_class_h{horizon}"] = _expanding_quantile_class(
            logret, n_bins=spec.n_class_bins, min_points=spec.expanding_min_points
        ).values

        # Realised vol H-day forward (annualised, sqrt(252))
        # Skip h=1: rolling std on a single element is always NaN
        if "realized_vol" in spec.extra_metrics and horizon >= 2:
            daily_logret = log_p.diff()
            min_periods = min(horizon, max(2, horizon // 2))
            fwd_vol = (
                daily_logret.shift(-1)
                .rolling(window=horizon, min_periods=min_periods)
                .std()
                .shift(-(horizon - 1))
            )
            out[f"y_realized_vol_h{horizon}"] = (fwd_vol * np.sqrt(252)).values
            out[f"realized_vol_h{horizon}"] = out[f"y_realized_vol_h{horizon}"]

        # Max/min return over next H days (vectorised via rolling on reversed series)
        if "future_max" in spec.extra_metrics or "future_min" in spec.extra_metrics:
            max_fwd = _rolling_future(log_p, horizon, agg="max")
            min_fwd = _rolling_future(log_p, horizon, agg="min")
            if "future_max" in spec.extra_metrics:
                out[f"y_max_ret_h{horizon}"] = (max_fwd - log_p).values
                out[f"future_max_return_h{horizon}"] = out[f"y_max_ret_h{horizon}"]
            if "future_min" in spec.extra_metrics:
                out[f"y_min_ret_h{horizon}"] = (min_fwd - log_p).values
                out[f"future_min_return_h{horizon}"] = out[f"y_min_ret_h{horizon}"]

        if "storage_value" in spec.extra_metrics:
            future_price = df[spec.price_col].astype(float).shift(-horizon)
            storage_cost = spec.storage_cost_usd_per_bu_per_day * horizon
            out[f"storage_value_h{horizon}"] = ((future_price - df[spec.price_col].astype(float)) / 100 - storage_cost).values

        if "prob_up" in spec.extra_metrics:
            min_periods = min(horizon, max(2, horizon // 2))
            future_up_frac = (
                (log_p.diff().shift(-1) > 0)
                .astype(float)
                .rolling(window=horizon, min_periods=min_periods)
                .mean()
                .shift(-(horizon - 1))
            )
            out[f"prob_up_h{horizon}"] = future_up_frac.values

        # Asymmetric risk skew: upside potential / downside potential (niveau 6)
        if (f"y_max_ret_h{horizon}" in out.columns and f"y_min_ret_h{horizon}" in out.columns):
            max_up = out[f"y_max_ret_h{horizon}"].clip(lower=0)
            max_dn = (-out[f"y_min_ret_h{horizon}"]).clip(lower=0)
            out[f"y_skew_h{horizon}"] = (max_up / (max_dn + 1e-6)).values

        # Sell regret: how much more could have been made by waiting H days optimally
        if "sell_regret" in spec.extra_metrics and f"y_max_ret_h{horizon}" in out.columns:
            max_ret = out[f"y_max_ret_h{horizon}"]
            out[f"y_sell_regret_h{horizon}"] = (max_ret - logret).clip(lower=0).values
            out[f"sell_regret_h{horizon}"] = out[f"y_sell_regret_h{horizon}"]

    log.info(
        "targets_built",
        horizons=list(spec.horizons),
        rows=len(out),
        n_cols=out.shape[1],
        non_nan_h5=int(out["y_logret_h5"].notna().sum()) if "y_logret_h5" in out else 0,
    )
    return out


def _rolling_future(log_p: pd.Series, horizon: int, agg: str = "max") -> pd.Series:
    """Return the max or min of log_p over the next `horizon` trading days at each t.

    Uses a reverse-rolling trick: reverse the series, apply rolling, reverse back.
    This avoids a slow row-by-row Python loop.
    """
    rev = log_p.iloc[::-1].reset_index(drop=True)
    if agg == "max":
        rolled = rev.shift(1).rolling(window=horizon, min_periods=1).max()
    else:
        rolled = rev.shift(1).rolling(window=horizon, min_periods=1).min()
    result = rolled.iloc[::-1].reset_index(drop=True)
    result.index = log_p.index
    result.iloc[-horizon:] = np.nan
    return result


def _expanding_quantile_class(
    series: pd.Series, n_bins: int = 10, min_points: int = 252
) -> pd.Series:
    """Assign each point an ordinal bin in [0, n_bins-1] using expanding-window
    quantile cuts. Bins at time t are derived ONLY from values strictly before t
    to avoid leakage. Returns NaN for the warm-up period.
    """
    s = series.astype(float).reset_index(drop=True)
    out = pd.Series(np.nan, index=s.index, dtype="float64", name=series.name)

    quantiles = np.linspace(0, 1, n_bins + 1)[1:-1]  # interior cut-points
    valid_mask = s.notna()
    valid_idx = np.flatnonzero(valid_mask.values)

    if len(valid_idx) < min_points + 1:
        return out

    sorted_vals = np.empty(0, dtype=float)

    for i in range(len(s)):
        if i in valid_idx and i >= min_points and sorted_vals.size >= min_points:
                cuts = np.quantile(sorted_vals, quantiles)
                # Bin index for s[i] given monotonic cuts
                out.iloc[i] = float(np.searchsorted(cuts, s.iloc[i], side="right"))
        # Update history with the *current* value (so cut at i+1 uses up to i)
        if valid_mask.iloc[i]:
            sorted_vals = np.sort(np.append(sorted_vals, s.iloc[i]))

    # Clamp to [0, n_bins - 1]
    out = out.clip(lower=0, upper=n_bins - 1)
    return out


def save_targets(targets: pd.DataFrame, path: Path | str = TARGETS_PARQUET) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_parquet(targets, out_path)
    log.info("targets_saved", path=str(out_path), rows=len(targets), cols=targets.shape[1])
    return out_path


def build_and_save(prices: pd.DataFrame, spec: TargetSpec | None = None,
                    path: Path | str = TARGETS_PARQUET) -> pd.DataFrame:
    targets = build_targets(prices, spec)
    save_targets(targets, path)
    return targets

"""Build the targets table.

This module is the **only** place where future-looking targets are constructed.
It is deliberately separated from features so that the anti-leakage audit
(``mais/leakage/audit.py``) can verify that no feature column references the
future.

For each horizon H in {5, 10, 20, 30}:

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

from mais.paths import PROCESSED_DIR, TARGETS_PARQUET
from mais.utils import get_logger, write_parquet

log = get_logger("mais.targets")


DEFAULT_HORIZONS: tuple[int, ...] = (5, 10, 20, 30)


@dataclass
class TargetSpec:
    horizons: tuple[int, ...] = DEFAULT_HORIZONS
    price_col: str = "corn_close"
    date_col: str = "Date"
    n_class_bins: int = 10
    strong_up_threshold: float = 0.05
    strong_down_threshold: float = -0.03
    expanding_min_points: int = 252
    extra_metrics: tuple[str, ...] = field(default_factory=lambda: ("realized_vol",))


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

    for H in spec.horizons:
        future_log_p = log_p.shift(-H)
        logret = (future_log_p - log_p).rename(f"y_logret_h{H}")

        out[f"y_logret_h{H}"] = logret.values

        # Binary targets
        out[f"y_up_h{H}"] = (logret > 0).astype("Int8").where(logret.notna()).values
        out[f"y_up_strong_h{H}"] = (
            (logret > np.log1p(spec.strong_up_threshold)).astype("Int8")
            .where(logret.notna()).values
        )
        out[f"y_down_strong_h{H}"] = (
            (logret < np.log1p(spec.strong_down_threshold)).astype("Int8")
            .where(logret.notna()).values
        )

        # Ordinal class via expanding-window deciles (anti-leakage)
        out[f"y_class_h{H}"] = _expanding_quantile_class(
            logret, n_bins=spec.n_class_bins, min_points=spec.expanding_min_points
        ).values

        # Realised vol H-day forward (annualised, sqrt(252))
        if "realized_vol" in spec.extra_metrics:
            daily_logret = log_p.diff()
            fwd_vol = (
                daily_logret.shift(-H)
                .rolling(window=H, min_periods=max(2, H // 2))
                .std()
                .shift(-(H - 1))
            )
            out[f"y_realized_vol_h{H}"] = (fwd_vol * np.sqrt(252)).values

    log.info(
        "targets_built",
        horizons=list(spec.horizons),
        rows=len(out),
        non_nan_h5=int(out["y_logret_h5"].notna().sum()) if "y_logret_h5" in out else 0,
    )
    return out


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

    # Pre-compute sorted history at each break point. Simple loop OK because
    # this runs once per build (O(N log N) total via np.searchsorted).
    history = []  # sorted list of values seen so far
    sorted_vals = np.empty(0, dtype=float)

    for i in range(len(s)):
        if i in valid_idx and i >= min_points:
            if sorted_vals.size >= min_points:
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

"""Signal persistence and frequency analysis for the Maize Direction Indicator."""

from __future__ import annotations

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.indicator.persistence")

SIGNAL_CODES = {"BULLISH": 1, "BEARISH": -1, "NEUTRAL": 0, "UNCERTAIN": 0}


def _prob_to_signal(
    prob_up: float,
    confidence: float,
    threshold_prob: float = 0.60,
    threshold_conf: float = 0.45,
) -> str:
    if confidence < threshold_conf:
        return "UNCERTAIN"
    if prob_up > threshold_prob:
        return "BULLISH"
    if prob_up < (1.0 - threshold_prob):
        return "BEARISH"
    return "NEUTRAL"


def compute_signal_streak(signal_series: pd.Series) -> pd.Series:
    """Length of the current streak (consecutive same signal) for each row."""
    groups = (signal_series != signal_series.shift()).cumsum()
    return groups.map(groups.value_counts())


def compute_signal_stability_rolling(
    signal_series: pd.Series,
    window: int = 5,
    initial_value: float = 0.5,
) -> pd.Series:
    """Rolling share of days with the same signal as the current day.

    String labels are encoded before the rolling computation so pandas never
    applies numeric operations to object values.  The first row starts neutral
    at ``initial_value`` instead of 0.0.
    """
    if signal_series.empty:
        return pd.Series(dtype=float, index=signal_series.index)

    codes = signal_series.map(SIGNAL_CODES).fillna(0).astype(int)
    result = pd.Series(float(initial_value), index=codes.index, dtype=float)

    for i in range(len(codes)):
        start = max(0, i - window + 1)
        window_vals = codes.iloc[start : i + 1]
        if len(window_vals) < 2:
            result.iloc[i] = float(initial_value)
        else:
            result.iloc[i] = float((window_vals == window_vals.iloc[-1]).mean())

    return result.clip(0.0, 1.0)


def compute_persistence_metrics(
    signals: pd.Series,
) -> dict[str, float]:
    """Core persistence statistics from a signal Series (index = dates)."""
    s = signals.dropna()
    n = len(s)
    if n < 10:
        return {}

    streak = compute_signal_streak(s)
    flipped = (s != s.shift()).fillna(False)

    n_years = max(
        (pd.to_datetime(s.index[-1]) - pd.to_datetime(s.index[0])).days / 365.25,
        1.0,
    )
    n_bullish = int((s == "BULLISH").sum())
    n_bearish = int((s == "BEARISH").sum())
    n_strong = n_bullish + n_bearish

    return {
        "flip_rate": float(flipped.mean()),
        "avg_streak": float(streak.mean()),
        "signal_persistence_3d": float((streak >= 3).mean()),
        "n_total": n,
        "n_bullish": n_bullish,
        "n_bearish": n_bearish,
        "n_neutral": int((s == "NEUTRAL").sum()),
        "n_uncertain": int((s == "UNCERTAIN").sum()),
        "n_years": round(n_years, 2),
        "bullish_per_year": round(n_bullish / n_years, 1),
        "bearish_per_year": round(n_bearish / n_years, 1),
        "strong_per_year": round(n_strong / n_years, 1),
    }


def analyze_persistence(
    calib_preds: pd.DataFrame,
    horizon: int = 20,
    model: str = "ridge_factors",
    threshold_probs: list[float] | None = None,
    threshold_confs: list[float] | None = None,
    max_date: str = "2022-12-31",
) -> pd.DataFrame:
    """Compute persistence metrics for multiple threshold combinations.

    Parameters
    ----------
    calib_preds:
        DataFrame from ``calibrated_predictions.parquet``.
    max_date:
        Upper bound to keep strictly pre-2023 (reserved for IND-08).
    """
    if threshold_probs is None:
        threshold_probs = [0.55, 0.60, 0.65]
    if threshold_confs is None:
        threshold_confs = [0.45, 0.60, 0.65, 0.70]

    p_col = f"p_up_h{horizon}"
    sub = calib_preds[
        (calib_preds["model"] == model)
        & (calib_preds["horizon"] == horizon)
        & (calib_preds["Date"] <= pd.Timestamp(max_date))
    ].copy()

    if p_col not in sub.columns or sub[p_col].isna().all():
        log.warning("p_up_col_missing", col=p_col)
        return pd.DataFrame()

    sub = sub[sub[p_col].notna()].copy()
    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)

    # Proxy confidence = |P(up) - 0.5| * 2  (V1 prob_distance component)
    sub["conf_proxy"] = (sub[p_col] - 0.5).abs() * 2.0

    rows = []
    for tp in threshold_probs:
        for tc in threshold_confs:
            sub["signal"] = [
                _prob_to_signal(float(p), float(c), tp, tc)
                for p, c in zip(sub[p_col], sub["conf_proxy"], strict=False)
            ]
            metrics = compute_persistence_metrics(
                pd.Series(sub["signal"].values, index=sub["Date"].values)
            )
            if not metrics:
                continue
            metrics.update(
                {
                    "threshold_prob": tp,
                    "threshold_conf": tc,
                    "horizon": horizon,
                    "model": model,
                }
            )
            rows.append(metrics)

    df = pd.DataFrame(rows)
    log.info(
        "persistence_done",
        model=model,
        horizon=horizon,
        n_combinations=len(rows),
    )
    return df

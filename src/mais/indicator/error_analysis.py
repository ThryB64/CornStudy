"""Error analysis for the Maize Direction Indicator (IND-08).

Identifies the top prediction errors, classifies them by category,
and aggregates patterns by year, season, and context.
"""

from __future__ import annotations

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.indicator.error_analysis")

SEASON_MAP = {
    2: "pre_semis", 3: "pre_semis",
    4: "semis", 5: "semis",
    6: "croissance",
    7: "pollinisation", 8: "pollinisation",
    9: "recolte", 10: "recolte",
    11: "post_recolte", 12: "post_recolte", 1: "post_recolte",
}

# WASDE typically publishes around day 10 of each month (proxy: day 8–13)
_WASDE_DAYS = frozenset(range(8, 14))


def _classify_error(
    row: pd.Series,
    signal_history: pd.DataFrame,
    false_confidence_threshold: float = 0.65,
) -> str:
    """Classify a single error row into a category."""
    # false_confidence: high confidence but wrong
    if row.get("confidence_v1", 0.0) >= false_confidence_threshold:
        return "false_confidence"

    # wasde_shock: near WASDE publication date (±2 days of day 10)
    date = pd.to_datetime(row["Date"])
    if date.day in _WASDE_DAYS:
        return "wasde_shock"

    # trend_reversal: model was on same side for ≥5 consecutive days before error
    if not signal_history.empty:
        past = signal_history[signal_history["Date"] < date].tail(5)
        if len(past) == 5 and past["signal"].nunique() == 1:
            return "trend_reversal"

    return "other"


def run_error_analysis(
    pred_df: pd.DataFrame,
    top_n: int = 20,
    false_signal_threshold: float = 0.03,
) -> pd.DataFrame:
    """Identify and classify the worst prediction errors.

    Parameters
    ----------
    pred_df:
        Must contain: Date, p_up_h20, y_true, confidence_v1, signal, season, vol_bucket.
    top_n:
        Number of worst errors to analyse (per direction: bullish and bearish).
    false_signal_threshold:
        Minimum absolute return for an error to count as "strong" (default 3%).
    """
    df = pred_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # False bullish: signal BULLISH but actual return < -threshold
    false_bull = df[
        (df["signal"] == "BULLISH") & (df["y_true"] < -false_signal_threshold)
    ].sort_values("y_true").head(top_n).copy()
    false_bull["error_type"] = "false_bullish"

    # False bearish: signal BEARISH but actual return > +threshold
    false_bear = df[
        (df["signal"] == "BEARISH") & (df["y_true"] > false_signal_threshold)
    ].sort_values("y_true", ascending=False).head(top_n).copy()
    false_bear["error_type"] = "false_bearish"

    errors = pd.concat([false_bull, false_bear], ignore_index=True)
    if errors.empty:
        log.warning("no_strong_errors_found")
        return pd.DataFrame()

    errors["season"] = errors["Date"].dt.month.map(SEASON_MAP).fillna("unknown")
    errors["year"] = errors["Date"].dt.year

    # Classify each error
    signal_history = df[["Date", "signal"]].copy()
    errors["error_category"] = errors.apply(
        lambda row: _classify_error(row, signal_history), axis=1
    )

    # Aggregate stats
    log.info(
        "error_analysis_done",
        n_errors=len(errors),
        categories=errors["error_category"].value_counts().to_dict(),
    )
    return errors[
        [
            "Date",
            "year",
            "season",
            "error_type",
            "error_category",
            "y_true",
            "p_up_h20",
            "confidence_v1",
            "signal",
            "vol_bucket",
        ]
    ].reset_index(drop=True)


def summarize_errors(errors: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return aggregate tables for the error report."""
    if errors.empty:
        return {}
    return {
        "by_year": errors.groupby("year").size().reset_index(name="n_errors"),
        "by_season": errors.groupby("season").size().reset_index(name="n_errors"),
        "by_category": errors.groupby("error_category").size().reset_index(name="n_errors"),
        "by_vol_bucket": errors.groupby("vol_bucket").size().reset_index(name="n_errors"),
    }

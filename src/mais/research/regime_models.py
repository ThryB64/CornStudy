"""Regime and seasonal models — specialized models per market context."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.research.regime_models")


# ---------------------------------------------------------------------------
# Regime builders
# ---------------------------------------------------------------------------

def build_regimes_rule_based(
    df: pd.DataFrame,
    price_col: str = "corn_close",
    vol_col: str | None = None,
    ret_window: int = 60,
    vol_window: int = 60,
    bull_threshold: float = 0.15,
    bear_threshold: float = -0.15,
    high_vol_percentile: float = 0.75,
) -> pd.DataFrame:
    """Transparent rule-based regimes — no Markov, fully interpretable.

    Regimes
    -------
    - bull:     rolling return > bull_threshold
    - bear:     rolling return < bear_threshold
    - high_vol: rolling vol > 75th percentile
    - range:    everything else
    """
    d = df[["Date", price_col]].copy().sort_values("Date")
    price = d[price_col]

    d["ret_roll"]  = np.log(price / price.shift(ret_window))
    d["vol_roll"]  = price.pct_change().rolling(vol_window).std() * np.sqrt(252)
    vol_threshold  = d["vol_roll"].quantile(high_vol_percentile)

    d["regime_trend"] = "range"
    d.loc[d["ret_roll"] >  bull_threshold, "regime_trend"] = "bull"
    d.loc[d["ret_roll"] <  bear_threshold, "regime_trend"] = "bear"

    d["regime_vol"] = "normal_vol"
    d.loc[d["vol_roll"] > vol_threshold, "regime_vol"] = "high_vol"

    d["regime"] = d["regime_trend"]  # main regime
    return d[["Date", "ret_roll", "vol_roll", "regime_trend", "regime_vol", "regime"]]


def build_season_labels(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    """Assign each row to an agronomic season."""
    d = df[[date_col]].copy()
    d["month"] = pd.to_datetime(d[date_col]).dt.month
    d["season"] = "post_harvest"
    d.loc[d["month"].isin([3, 4, 5]),    "season"] = "planting"
    d.loc[d["month"].isin([6, 7, 8]),    "season"] = "growing"
    d.loc[d["month"].isin([9, 10, 11]),  "season"] = "harvest"
    d.loc[d["month"].isin([12, 1, 2]),   "season"] = "winter"
    return d[["season"]]


# ---------------------------------------------------------------------------
# Regime-specific benchmarks
# ---------------------------------------------------------------------------

def benchmark_by_regime(
    x: pd.DataFrame,
    y: pd.Series,
    regime_series: pd.Series,
    models: dict | None = None,
    min_obs: int = 50,
) -> pd.DataFrame:
    """Run a simple benchmark per regime (train=all, evaluate per regime).

    This is NOT a walk-forward — it's a conditional evaluation to understand
    when models work. A proper walk-forward per regime would need more data.
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error, r2_score

    if models is None:
        models = {
            "ridge": Ridge(alpha=1.0),
            "rf":    RandomForestRegressor(n_estimators=100, n_jobs=1, random_state=42),
        }

    # Align
    common = x.index.intersection(y.index).intersection(regime_series.index)
    x_ali, y_ali, r_ali = x.loc[common], y.loc[common], regime_series.loc[common]

    rows = []
    for model_name, model in models.items():
        model.fit(x_ali.fillna(0), y_ali)
        preds = pd.Series(model.predict(x_ali.fillna(0)), index=common)

        for regime in r_ali.unique():
            mask = r_ali == regime
            if mask.sum() < min_obs:
                continue
            yt = y_ali.loc[mask].values
            yp = preds.loc[mask].values
            rmse = float(np.sqrt(mean_squared_error(yt, yp)))
            da   = float(np.mean(np.sign(yt) == np.sign(yp)))
            r2   = float(r2_score(yt, yp))
            rows.append({"model": model_name, "regime": regime, "rmse": rmse, "da": da, "r2": r2, "n": int(mask.sum())})

    return pd.DataFrame(rows)


def benchmark_by_season(
    x: pd.DataFrame,
    y: pd.Series,
    seasons: pd.Series,
    models: dict | None = None,
    min_obs: int = 50,
) -> pd.DataFrame:
    """Same as benchmark_by_regime but for agronomic seasons."""
    return benchmark_by_regime(x, y, seasons, models=models, min_obs=min_obs)

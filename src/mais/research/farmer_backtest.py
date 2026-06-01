"""Farmer decision backtest — the true economic evaluation.

The final metric is NOT RMSE. It is:
  "Does the system help farmers earn more per bushel?"

Strategies compared
-------------------
- sell_harvest:      sell 100% at harvest (October)
- sell_dca_monthly:  sell 1/12 each month
- sell_dca_quarterly: sell 25% per quarter
- sell_best_month:   historically best selling month (hindsight-free on train set)
- model_signal:      follow model recommendation
- perfect_hindsight: sell at yearly maximum (upper bound, unachievable)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.research.farmer_backtest")

STORAGE_COST_USD_PER_BU_PER_MONTH = 0.04
BASIS_USD_PER_BU = -0.20


def _cash_price(cbot_cts_per_bu: float, basis: float = BASIS_USD_PER_BU) -> float:
    return cbot_cts_per_bu / 100 + basis


def _storage_cost(months: float) -> float:
    return STORAGE_COST_USD_PER_BU_PER_MONTH * months


def compute_yearly_results(
    price_series: pd.Series,
    decisions: pd.Series | None = None,
    harvest_month: int = 10,
    basis: float = BASIS_USD_PER_BU,
    storage_cost_pm: float = STORAGE_COST_USD_PER_BU_PER_MONTH,
) -> pd.DataFrame:
    """Compute annual revenue for each strategy.

    Parameters
    ----------
    price_series: corn cash proxy (CBOT cts/bu)
    decisions:    pd.Series indexed like price_series, values in
                  {SELL_NOW, SELL_25, SELL_33, SELL_50, STORE, WAIT}
    """
    df = price_series.to_frame("price").copy()
    df.index = pd.to_datetime(df.index)
    df["year"]  = df.index.year
    df["month"] = df.index.month

    # Cash price
    df["cash"] = df["price"] / 100 + basis

    rows = []
    for year, g in df.groupby("year"):
        if len(g) < 100:
            continue
        monthly = g.groupby("month")["cash"].mean()

        # Harvest price (October average)
        p_harvest = monthly.get(harvest_month, monthly.iloc[0])

        # DCA monthly
        p_dca_monthly = float(monthly.mean())

        # DCA quarterly
        q_months = {3: [1, 2, 3], 6: [4, 5, 6], 9: [7, 8, 9], 12: [10, 11, 12]}
        p_dca_qtr = float(np.mean([monthly[monthly.index.isin(ms)].mean()
                                    for ms in q_months.values()]))

        # Perfect hindsight
        p_max = float(monthly.max())

        # Best sell month (train-period rule: sell in the month with historically best return)
        train_data = df[df["year"] < year]
        if len(train_data) > 100:
            hist_best_month = train_data.groupby("month")["cash"].mean().idxmax()
            p_best_hist = float(monthly.get(hist_best_month, p_harvest))
        else:
            p_best_hist = p_harvest

        rows.append({
            "year": int(year),
            "sell_harvest": float(p_harvest),
            "sell_dca_monthly": float(p_dca_monthly) - _storage_cost(6),
            "sell_dca_quarterly": float(p_dca_qtr) - _storage_cost(3),
            "sell_best_hist_month": float(p_best_hist) - _storage_cost(
                abs(hist_best_month - harvest_month) if len(train_data) > 100 else 0
            ),
            "perfect_hindsight": float(p_max) - _storage_cost(12),
            "n_trading_days": len(g),
        })

    return pd.DataFrame(rows)


def add_model_strategy(
    yearly_df: pd.DataFrame,
    price_series: pd.Series,
    decisions: pd.Series,
    strategy_name: str = "model_signal",
    basis: float = BASIS_USD_PER_BU,
) -> pd.DataFrame:
    """Add a model-driven strategy column to yearly results."""
    # Map decision strings to sell fractions
    sell_map = {
        "SELL_NOW": 1.00, "SELL_HARVEST": 1.00,
        "SELL_50": 0.50, "SELL_THIRDS": 0.33, "SELL_25": 0.25,
        "STORE": 0.00, "WAIT": 0.00,
    }

    df = price_series.to_frame("price")
    df.index = pd.to_datetime(df.index)
    df["cash"] = df["price"] / 100 + basis
    df["decision"] = decisions.reindex(df.index).fillna("SELL_NOW")
    df["fraction"] = df["decision"].map(lambda d: sell_map.get(d, 0.5))
    df["year"] = df.index.year
    df["month"] = df.index.month

    # Weighted average revenue
    rev_by_year = {}
    for year, g in df.groupby("year"):
        total_fraction = g["fraction"].sum()
        if total_fraction == 0:
            # Default to harvest
            rev_by_year[year] = float(g[g["month"] == 10]["cash"].mean())
        else:
            rev_by_year[year] = float((g["cash"] * g["fraction"]).sum() / total_fraction)

    yearly_df = yearly_df.copy()
    yearly_df[strategy_name] = yearly_df["year"].map(rev_by_year)
    return yearly_df


def summarize_strategies(yearly_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate yearly results into a strategy comparison table."""
    strategy_cols = [c for c in yearly_df.columns
                     if c not in ("year", "n_trading_days")]
    rows = []
    harvest_col = "sell_harvest"
    hindsight_col = "perfect_hindsight"

    for col in strategy_cols:
        if col == hindsight_col:
            continue
        s = yearly_df[col].dropna()
        if s.empty:
            continue
        harvest = yearly_df.loc[s.index, harvest_col].dropna()
        hindsight = yearly_df.loc[s.index, hindsight_col].dropna() if hindsight_col in yearly_df.columns else None

        beat_harvest = float((s > harvest).mean()) if len(harvest) else float("nan")
        avg_gain = float((s - harvest).mean()) if len(harvest) else float("nan")
        capture = float(s.mean() / hindsight.mean()) if hindsight is not None and float(hindsight.mean()) > 0 else float("nan")

        rows.append({
            "strategy": col,
            "avg_revenue_usd_bu": float(s.mean()),
            "std_revenue": float(s.std()),
            "min_year": float(s.min()),
            "max_year": float(s.max()),
            "pct_years_beat_harvest": beat_harvest,
            "avg_gain_vs_harvest": avg_gain,
            "capture_rate": capture,
            "n_years": len(s),
        })

    return pd.DataFrame(rows).sort_values("avg_revenue_usd_bu", ascending=False)


def run_farmer_backtest(
    price_series: pd.Series,
    decisions: pd.Series | None = None,
    harvest_month: int = 10,
    basis: float = BASIS_USD_PER_BU,
) -> dict[str, pd.DataFrame]:
    """Full backtest returning yearly results + strategy summary."""
    yearly = compute_yearly_results(price_series, harvest_month=harvest_month, basis=basis)
    if decisions is not None:
        yearly = add_model_strategy(yearly, price_series, decisions)
    summary = summarize_strategies(yearly)
    return {"yearly": yearly, "summary": summary}

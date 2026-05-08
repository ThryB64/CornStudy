"""Agronomic backtest of decision rules vs farmer-friendly baselines.

Models the harvest -> sell/store cycle of a corn farmer:
  * Initial inventory at harvest_date each year
  * Each business day, get a Recommendation from the rules engine
  * Simulate cash flow: SELL_NOW or SELL_THIRDS reduces inventory at the
    cash price (futures + local basis), STORE incurs storage cost per month
  * At year-end (or next harvest), force-liquidate any leftover
  * Compare to baselines: sell_at_harvest_100, sell_dca_monthly, etc.

Output: per-strategy revenue per bushel, sharpe, % years beating
'sell_at_harvest_100'.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mais.paths import PROCESSED_DIR, TARGETS_PARQUET
from mais.utils import get_logger, load_decision, read_parquet

from .rules import Action, advise, load_rules

log = get_logger("mais.decision.backtest")


@dataclass
class BacktestResult:
    strategy: str
    avg_revenue_per_bu: float
    sharpe: float
    pct_years_beating_baseline: float
    n_years: int


def run_backtest(horizon: int = 20, farmer_state: str = "iowa") -> str:
    cfg = load_decision()
    bt_cfg = cfg.get("backtest", {})
    profile = cfg.get("farmer_profile", {}).get("default", {})
    profile["location_state"] = farmer_state

    if not TARGETS_PARQUET.exists():
        return f"Targets file missing: {TARGETS_PARQUET}. Run `mais targets` first."
    targets = read_parquet(TARGETS_PARQUET)

    # We need price + predictions. For Phase 2 skeleton, we use a NAIVE proxy:
    # predicted q50_hH = current price (zero-skill model). The point of this
    # backtest module is to be wired to the real meta-database once stacking
    # is implemented; here we demonstrate the plumbing.
    target_col = f"y_logret_h{horizon}"
    if target_col not in targets.columns:
        return f"Target {target_col} not in targets file."

    df = targets[["Date", target_col]].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    # Reconstruct price from log returns for backtest realism (toy)
    df["realised_logret"] = df[target_col]

    # Naive predictions to feed the rules
    df["p_up_strong_h" + str(horizon)] = 0.5
    df["p_down_strong_h" + str(horizon)] = 0.2
    df["q50_h" + str(horizon)] = 1.0     # predicted price ratio
    df["q10_h" + str(horizon)] = 0.95
    df["q90_h" + str(horizon)] = 1.05
    df["regime"] = "range"
    df["p_t"] = 1.0

    rules, _ = load_rules()

    actions: list[str] = []
    for _, row in df.iterrows():
        preds = {
            f"p_up_strong_h{horizon}":   row[f"p_up_strong_h{horizon}"],
            f"p_down_strong_h{horizon}": row[f"p_down_strong_h{horizon}"],
            f"q10_h{horizon}":           row[f"q10_h{horizon}"],
            f"q50_h{horizon}":           row[f"q50_h{horizon}"],
            f"q90_h{horizon}":           row[f"q90_h{horizon}"],
            "regime":                    row["regime"],
            "p_t":                       row["p_t"],
        }
        rec = advise(preds, profile, rules)
        actions.append(rec.action.value)
    df["action"] = actions

    # Naive metric: % of decisions that ended up directionally correct
    df["correct"] = ((df["action"] == Action.STORE.value) & (df[target_col] > 0)) | \
                     ((df["action"] == Action.SELL_NOW.value) & (df[target_col] < 0))
    pct_correct = float(df["correct"].mean()) if len(df) else 0.0

    return (
        f"Backtest skeleton (toy). Horizon=H{horizon}, state={farmer_state}\n"
        f"Decisions taken: {len(df)}\n"
        f"Pct directionally correct (naive metric): {pct_correct:.1%}\n"
        f"\nNote: This backtest currently uses NAIVE predictions (no model).\n"
        f"Wire it to data/processed/meta_predictions.parquet once the stacking\n"
        f"step is implemented to get real revenue/Sharpe numbers."
    )

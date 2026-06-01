"""Economic farmer storage backtest V2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StorageCosts:
    cost_per_month_cents_per_bu: float = 5.0
    interest_rate_annual: float = 0.055
    quality_loss_pct: float = 0.001


def crop_year(dates: pd.Series) -> pd.Series:
    dt = pd.to_datetime(dates)
    return pd.Series(np.where(dt.dt.month >= 9, dt.dt.year + 1, dt.dt.year), index=dates.index, dtype=int)


def run_farmer_backtest_v2(
    prices: pd.DataFrame,
    signals: pd.DataFrame | None = None,
    *,
    price_col: str = "corn_close",
    costs: StorageCosts | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Backtest six farmer sale/storage strategies by crop year."""
    costs = costs or StorageCosts()
    work = prices[["Date", price_col]].copy()
    work["Date"] = pd.to_datetime(work["Date"])
    work = work.sort_values("Date").reset_index(drop=True)
    if signals is not None:
        sig = signals.copy()
        sig["Date"] = pd.to_datetime(sig["Date"])
        work = work.merge(sig, on="Date", how="left")
    if "signal" not in work.columns:
        work["signal"] = "UNCERTAIN"
    work["crop_year"] = crop_year(work["Date"])

    rows = []
    for year, year_df in work.groupby("crop_year"):
        if year < 2015 or year > 2022:
            continue
        rows.extend(_year_strategy_rows(int(year), year_df, price_col, costs))
    result = pd.DataFrame(rows)
    payload = _summarize(result)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _year_strategy_rows(year: int, df: pd.DataFrame, price_col: str, costs: StorageCosts) -> list[dict[str, Any]]:
    harvest = _first_after(df, month=10)
    jan = _first_after(df, month=1)
    mar = _first_after(df, month=3)
    apr = _first_after(df, month=4)
    jul = _first_after(df, month=7)
    if harvest is None:
        return []
    after_harvest = df[df["Date"] >= harvest["Date"]]
    max_price = float(after_harvest[price_col].max())
    rows = []
    strategies = {
        "SELL_HARVEST": [(harvest, 1.0)],
        "SELL_THIRDS": [(harvest, 1 / 3), (_fallback(jan, harvest), 1 / 3), (_fallback(mar, harvest), 1 / 3)],
        "SELL_25_25_25_25": [
            (harvest, 0.25),
            (_fallback(jan, harvest), 0.25),
            (_fallback(apr, harvest), 0.25),
            (_fallback(jul, harvest), 0.25),
        ],
        "SELL_MAX_ORACLE": [(after_harvest.loc[after_harvest[price_col].idxmax()], 1.0)],
    }
    signal_binary = _signal_sale_plan(df, harvest, costs, partial=False)
    signal_partial = _signal_sale_plan(df, harvest, costs, partial=True)
    strategies["SIGNAL_BINARY"] = signal_binary
    strategies["SIGNAL_PARTIAL"] = signal_partial
    for name, plan in strategies.items():
        net_price = _weighted_net_price(plan, harvest, price_col, costs)
        rows.append(
            {
                "crop_year": year,
                "strategy": name,
                "net_price": net_price,
                "capture_pct_of_max": net_price / max_price if max_price else np.nan,
                "max_price": max_price,
            }
        )
    return rows


def _signal_sale_plan(df: pd.DataFrame, harvest: pd.Series, costs: StorageCosts, *, partial: bool) -> list[tuple[pd.Series, float]]:
    after = df[df["Date"] >= harvest["Date"]]
    bearish = after[after["signal"] == "BEARISH"]
    bullish = after[after["signal"] == "BULLISH"]
    if not bearish.empty:
        first_bear = bearish.iloc[0]
        if partial:
            later = bullish.iloc[0] if not bullish.empty and bullish.iloc[0]["Date"] > first_bear["Date"] else after.iloc[-1]
            return [(first_bear, 0.5), (later, 0.5)]
        return [(first_bear, 1.0)]
    if not bullish.empty:
        later = after.iloc[min(len(after) - 1, 60)]
        return [(later, 1.0)]
    thirds = [_first_after(df, month=1), _first_after(df, month=3)]
    return [(harvest, 1 / 3), (_fallback(thirds[0], harvest), 1 / 3), (_fallback(thirds[1], harvest), 1 / 3)]


def _weighted_net_price(
    plan: list[tuple[pd.Series, float]],
    harvest: pd.Series,
    price_col: str,
    costs: StorageCosts,
) -> float:
    total = 0.0
    for sale, weight in plan:
        months = max(0.0, (pd.Timestamp(sale["Date"]) - pd.Timestamp(harvest["Date"])).days / 30.0)
        storage_cost = months * costs.cost_per_month_cents_per_bu
        quality_cost = float(sale[price_col]) * costs.quality_loss_pct * months
        finance_cost = float(sale[price_col]) * costs.interest_rate_annual * months / 12.0
        total += weight * (float(sale[price_col]) - storage_cost - quality_cost - finance_cost)
    return float(total)


def _first_after(df: pd.DataFrame, *, month: int) -> pd.Series | None:
    sub = df[df["Date"].dt.month == month]
    if sub.empty:
        return None
    return sub.sort_values("Date").iloc[0]


def _fallback(value: pd.Series | None, fallback: pd.Series) -> pd.Series:
    return fallback if value is None else value


def _summarize(results: pd.DataFrame) -> dict[str, Any]:
    strategies = {}
    if results.empty:
        return {"verdict": "INCONCLU", "strategies": {}, "worst_year": None}
    harvest = results[results["strategy"] == "SELL_HARVEST"][["crop_year", "net_price"]].rename(columns={"net_price": "harvest_price"})
    merged = results.merge(harvest, on="crop_year", how="left")
    merged["gain_vs_sell_harvest"] = merged["net_price"] - merged["harvest_price"]
    for strategy, sub in merged.groupby("strategy"):
        strategies[strategy] = {
            "mean_gain_vs_sell_harvest": float(sub["gain_vs_sell_harvest"].mean()),
            "winning_crop_years": int((sub["gain_vs_sell_harvest"] > 0).sum()),
            "crop_years": {
                str(int(row["crop_year"])): float(row["gain_vs_sell_harvest"])
                for _, row in sub.sort_values("crop_year").iterrows()
            },
        }
    signal = strategies.get("SIGNAL_PARTIAL") or strategies.get("SIGNAL_BINARY")
    worst_row = merged[merged["strategy"].isin(["SIGNAL_PARTIAL", "SIGNAL_BINARY"])].sort_values("gain_vs_sell_harvest").head(1)
    verdict = "INCONCLU"
    if signal:
        if signal["mean_gain_vs_sell_harvest"] > 0 and signal["winning_crop_years"] >= 5:
            verdict = "CONFIRMÉ"
        elif signal["mean_gain_vs_sell_harvest"] > 0:
            verdict = "PROMETTEUR"
        elif signal["mean_gain_vs_sell_harvest"] < 0:
            verdict = "REJETÉ"
        else:
            verdict = "NEUTRE"
    return {
        "verdict": verdict,
        "strategies": strategies,
        "worst_year": None
        if worst_row.empty
        else {
            "crop_year": int(worst_row.iloc[0]["crop_year"]),
            "strategy": str(worst_row.iloc[0]["strategy"]),
            "gain_vs_sell_harvest": float(worst_row.iloc[0]["gain_vs_sell_harvest"]),
            "cause": "signal économique défavorable sur cette année de validation",
        },
    }

"""Agronomic backtest of farmer selling strategies.

The backtest is deliberately economic rather than ML-centric: one normalized
bushel is available at harvest, strategies sell some or all of it during the
marketing season, and every stored fraction pays explicit storage and quality
costs. The primary metric is the annual capture rate:

    net_price_obtained / annual_max_cash_price

That makes MODEL_SIGNAL comparable to simple farmer baselines even when the
model does not win.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, INTERIM_DIR, PROJECT_ROOT
from mais.utils import get_logger, load_decision, read_parquet

from .rules import Action, advise, load_rules

log = get_logger("mais.decision.backtest")

REPORT_PATH = PROJECT_ROOT / "docs" / "FARMER_BACKTEST_REPORT.md"
REPORT_V2_PATH = PROJECT_ROOT / "docs" / "FARMER_BACKTEST_REPORT_V2.md"
STUDY_DIR = ARTEFACTS_DIR / "professional_study"
CALIBRATED_PREDICTIONS_PARQUET = STUDY_DIR / "calibrated_predictions.parquet"
CQR_RESULTS_PARQUET = STUDY_DIR / "cqr_results.parquet"

STRATEGIES = (
    "SELL_HARVEST",
    "STORE_3M",
    "STORE_6M",
    "MODEL_SIGNAL",
    "CQR_OPTIMAL",
    "BENCHMARK_AVG",
)

STRATEGIES_V2 = (
    "SELL_HARVEST",
    "SELL_MONTHLY",
    "SELL_THIRDS",
    "SELL_THRESHOLD",
    "MODEL_SIGNAL",
    "MODEL_STORAGE_VALUE",
    "CQR_CAUTIOUS",
    "PERFECT_HINDSIGHT",
)


@dataclass(frozen=True)
class BacktestAssumptions:
    basis_usd_per_bu: float
    storage_cost_usd_per_bu_per_month: float
    quality_loss_rate_per_month: float
    initial_inventory_bushels: float
    harvest_mmdd: str
    horizon: int
    farmer_state: str


@dataclass
class BacktestResult:
    strategy: str
    avg_price_obtained: float
    avg_capture_rate: float
    avg_gain_vs_harvest: float
    sharpe: float
    pct_years_beating_harvest: float
    max_drawdown: float
    n_years: int


def run_backtest(horizon: int = 20, farmer_state: str = "iowa") -> str:
    """Run the six-strategy farmer backtest and write the Markdown report."""
    cfg = load_decision()
    bt_cfg = cfg.get("backtest", {})
    profile = dict(cfg.get("farmer_profile", {}).get("default", {}))
    profile["location_state"] = farmer_state
    assumptions = _assumptions(cfg, horizon=horizon, farmer_state=farmer_state)

    prices = _load_cash_prices(assumptions)
    seasons = _build_seasons(prices, bt_cfg, assumptions)
    if len(seasons) < 10:
        msg = (
            "Backtest impossible: moins de 10 saisons exploitables "
            f"({len(seasons)} trouvées). Vérifier features.parquet."
        )
        REPORT_PATH.write_text(f"# Backtest agriculteur\n\n{msg}\n", encoding="utf-8")
        return msg

    model_inputs = _load_model_inputs(horizon)
    cqr_inputs = _load_cqr_inputs(horizon)
    rules, _ = load_rules()

    annual_rows: list[dict[str, Any]] = []
    for season in seasons:
        season_prices = prices[(prices["Date"] >= season["start"]) & (prices["Date"] <= season["end"])].copy()
        annual_max = float(season_prices["cash_price"].max())
        harvest_price = float(season_prices["cash_price"].iloc[0])

        fixed = {
            "SELL_HARVEST": _fixed_sale(season_prices, assumptions, days_after_harvest=0),
            "STORE_3M": _fixed_sale(season_prices, assumptions, days_after_harvest=90),
            "STORE_6M": _fixed_sale(season_prices, assumptions, days_after_harvest=180),
        }
        fixed["BENCHMARK_AVG"] = float(np.mean([fixed["SELL_HARVEST"], fixed["STORE_3M"], fixed["STORE_6M"]]))
        fixed["MODEL_SIGNAL"] = _model_signal_sale(
            season_prices, model_inputs, assumptions, profile, rules
        )
        fixed["CQR_OPTIMAL"] = _cqr_optimal_sale(season_prices, cqr_inputs, assumptions)

        for strategy in STRATEGIES:
            price_obtained = float(fixed[strategy])
            annual_rows.append(
                {
                    "season": int(season["season"]),
                    "strategy": strategy,
                    "start": season["start"],
                    "end": season["end"],
                    "price_obtained": price_obtained,
                    "annual_max_price": annual_max,
                    "harvest_price": harvest_price,
                    "capture_rate": price_obtained / annual_max if annual_max > 0 else np.nan,
                    "regret": annual_max - price_obtained,
                    "gain_vs_harvest": price_obtained - float(fixed["SELL_HARVEST"]),
                }
            )

    annual = pd.DataFrame(annual_rows)
    summary = _summarise(annual)
    _write_report(annual, summary, assumptions, model_inputs, cqr_inputs)

    best = summary.sort_values(["avg_capture_rate", "avg_price_obtained"], ascending=False).iloc[0]
    model = summary[summary["strategy"] == "MODEL_SIGNAL"].iloc[0]
    harvest = summary[summary["strategy"] == "SELL_HARVEST"].iloc[0]
    return (
        "Backtest agriculteur complet écrit dans docs/FARMER_BACKTEST_REPORT.md\n"
        f"Période: {annual['season'].min()}-{annual['season'].max()} ({int(summary['n_years'].max())} saisons)\n"
        f"Meilleure stratégie: {best['strategy']} capture {best['avg_capture_rate']:.1%}\n"
        f"MODEL_SIGNAL capture {model['avg_capture_rate']:.1%} vs "
        f"SELL_HARVEST {harvest['avg_capture_rate']:.1%}"
    )


def run_backtest_v2(horizon: int = 30, farmer_state: str = "iowa") -> str:
    """Run the eight-strategy V2 backtest and write FARMER_BACKTEST_REPORT_V2.md."""
    cfg = load_decision()
    bt_cfg = cfg.get("backtest", {})
    assumptions = _assumptions(cfg, horizon=horizon, farmer_state=farmer_state)

    prices = _load_cash_prices(assumptions)
    seasons = _build_seasons(prices, bt_cfg, assumptions)
    if len(seasons) < 10:
        msg = f"Backtest V2 impossible: {len(seasons)} saisons < 10."
        REPORT_V2_PATH.write_text(f"# Backtest V2\n\n{msg}\n", encoding="utf-8")
        return msg

    model_inputs = _load_model_inputs(horizon)
    cqr_inputs = _load_cqr_inputs(horizon)
    rules, _ = load_rules()

    annual_rows: list[dict[str, Any]] = []
    for season in seasons:
        season_prices = prices[(prices["Date"] >= season["start"]) & (prices["Date"] <= season["end"])].copy()
        annual_max = float(season_prices["cash_price"].max())
        harvest_price = float(season_prices["cash_price"].iloc[0])

        profile = dict(cfg.get("farmer_profile", {}).get("default", {}))
        profile["location_state"] = farmer_state

        results: dict[str, float] = {
            "SELL_HARVEST":  _fixed_sale(season_prices, assumptions, days_after_harvest=0),
            "SELL_MONTHLY":  _sell_monthly(season_prices, assumptions),
            "SELL_THIRDS":   _sell_thirds(season_prices, assumptions),
            "SELL_THRESHOLD": _sell_threshold(season_prices, prices, assumptions),
            "MODEL_SIGNAL":  _model_signal_sale(season_prices, model_inputs, assumptions, profile, rules),
            "MODEL_STORAGE_VALUE": _model_storage_value(season_prices, model_inputs, assumptions),
            "CQR_CAUTIOUS":  _cqr_cautious(season_prices, cqr_inputs, assumptions),
            "PERFECT_HINDSIGHT": annual_max - assumptions.storage_cost_usd_per_bu_per_month * 0.0,
        }

        harvest_rev = results["SELL_HARVEST"]
        monthly_rev = results["SELL_MONTHLY"]
        perfect_rev = results["PERFECT_HINDSIGHT"]

        for strategy in STRATEGIES_V2:
            price_obtained = results[strategy]
            annual_rows.append(
                {
                    "season": int(season["season"]),
                    "strategy": strategy,
                    "start": season["start"],
                    "end": season["end"],
                    "price_obtained": price_obtained,
                    "annual_max_price": annual_max,
                    "harvest_price": harvest_price,
                    "capture_rate": price_obtained / annual_max if annual_max > 0 else np.nan,
                    "vs_harvest": price_obtained - harvest_rev,
                    "vs_monthly": price_obtained - monthly_rev,
                    "regret": perfect_rev - price_obtained,
                }
            )

    annual = pd.DataFrame(annual_rows)
    summary = _summarise_v2(annual)
    _write_report_v2(annual, summary, assumptions, model_inputs, cqr_inputs)

    best = summary[summary["strategy"] != "PERFECT_HINDSIGHT"].sort_values("avg_capture_rate", ascending=False).iloc[0]
    model = summary[summary["strategy"] == "MODEL_SIGNAL"].iloc[0]
    harvest = summary[summary["strategy"] == "SELL_HARVEST"].iloc[0]
    return (
        "Backtest V2 écrit dans docs/FARMER_BACKTEST_REPORT_V2.md\n"
        f"Période: {annual['season'].min()}–{annual['season'].max()} ({int(summary['n_years'].max())} saisons)\n"
        f"Meilleure stratégie réaliste : {best['strategy']} capture {best['avg_capture_rate']:.1%}\n"
        f"MODEL_SIGNAL {model['avg_capture_rate']:.1%} vs SELL_HARVEST {harvest['avg_capture_rate']:.1%}"
    )


def _assumptions(cfg: dict[str, Any], horizon: int, farmer_state: str) -> BacktestAssumptions:
    profile = cfg.get("farmer_profile", {}).get("default", {})
    bt_cfg = cfg.get("backtest", {})
    harvest_dates = bt_cfg.get(f"harvest_dates_{farmer_state}", bt_cfg.get("harvest_dates_iowa", ["10-15"]))
    harvest_mmdd = str(harvest_dates[0] if harvest_dates else "10-15")
    return BacktestAssumptions(
        basis_usd_per_bu=float(profile.get("basis_local_typical_usd_per_bu", -0.20)),
        storage_cost_usd_per_bu_per_month=float(profile.get("storage_cost_usd_per_bu_per_month", 0.04)),
        quality_loss_rate_per_month=float(profile.get("quality_loss_rate_per_month", 0.005)),
        initial_inventory_bushels=float(bt_cfg.get("initial_inventory_bushels", 50_000)),
        harvest_mmdd=harvest_mmdd,
        horizon=int(horizon),
        farmer_state=farmer_state,
    )


def _load_cash_prices(assumptions: BacktestAssumptions) -> pd.DataFrame:
    prices = _read_price_source()
    prices["Date"] = pd.to_datetime(prices["Date"], errors="coerce")
    prices["corn_close"] = pd.to_numeric(prices["corn_close"], errors="coerce")
    prices = prices.dropna(subset=["Date", "corn_close"]).sort_values("Date")
    prices = prices.drop_duplicates("Date", keep="last").reset_index(drop=True)
    median_quote = float(prices["corn_close"].median())
    prices["futures_usd_per_bu"] = prices["corn_close"] / 100.0 if median_quote > 50 else prices["corn_close"]
    prices["cash_price"] = (prices["futures_usd_per_bu"] + assumptions.basis_usd_per_bu).clip(lower=0.01)
    return prices[["Date", "cash_price", "futures_usd_per_bu"]]


def _read_price_source() -> pd.DataFrame:
    candidates = [
        INTERIM_DIR / "market.parquet",
        INTERIM_DIR / "database.parquet",
        FEATURES_PARQUET,
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            return read_parquet(path, columns=["Date", "corn_close"])
        except Exception as exc:
            log.debug("backtest_price_source_skipped", path=str(path), error=str(exc))
    raise FileNotFoundError(
        "No price source with Date/corn_close found. Run `mais migrate-legacy` or `mais features` first."
    )


def _build_seasons(
    prices: pd.DataFrame,
    bt_cfg: dict[str, Any],
    assumptions: BacktestAssumptions,
) -> list[dict[str, Any]]:
    start_bound = pd.Timestamp(bt_cfg.get("start_date", "2010-01-01"))
    end_bound = pd.Timestamp(bt_cfg.get("end_date", "2024-12-31"))
    first_year = max(int(prices["Date"].dt.year.min()), int(start_bound.year))
    last_year = min(int(prices["Date"].dt.year.max()) - 1, int(end_bound.year))
    seasons: list[dict[str, Any]] = []
    for year in range(first_year, last_year + 1):
        start = _first_trading_day_on_or_after(prices, _mmdd_date(year, assumptions.harvest_mmdd))
        next_harvest = _first_trading_day_on_or_after(prices, _mmdd_date(year + 1, assumptions.harvest_mmdd))
        if start is None or next_harvest is None:
            continue
        end = min(next_harvest - pd.Timedelta(days=1), end_bound)
        if start < start_bound:
            continue
        n_days = int(((prices["Date"] >= start) & (prices["Date"] <= end)).sum())
        if n_days >= 120:
            seasons.append({"season": year, "start": start, "end": end})
    return seasons


def _first_trading_day_on_or_after(prices: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    dates = prices.loc[prices["Date"] >= date, "Date"]
    if dates.empty:
        return None
    return pd.Timestamp(dates.iloc[0])


def _mmdd_date(year: int, mmdd: str) -> pd.Timestamp:
    month, day = (int(part) for part in mmdd.split("-", maxsplit=1))
    return pd.Timestamp(year=year, month=month, day=day)


def _fixed_sale(
    season_prices: pd.DataFrame,
    assumptions: BacktestAssumptions,
    days_after_harvest: int,
) -> float:
    target = season_prices["Date"].iloc[0] + pd.Timedelta(days=days_after_harvest)
    row = season_prices[season_prices["Date"] >= target]
    sale = row.iloc[0] if not row.empty else season_prices.iloc[-1]
    return _net_sale_price(
        float(sale["cash_price"]),
        days_held=int((pd.Timestamp(sale["Date"]) - pd.Timestamp(season_prices["Date"].iloc[0])).days),
        assumptions=assumptions,
    )


def _load_model_inputs(horizon: int) -> pd.DataFrame:
    if not CALIBRATED_PREDICTIONS_PARQUET.exists():
        return pd.DataFrame()
    df = read_parquet(CALIBRATED_PREDICTIONS_PARQUET)
    if df.empty or "horizon" not in df.columns:
        return pd.DataFrame()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    h20 = _preferred_model(df[df["horizon"] == horizon], model="ridge_factors")
    h10 = _preferred_model(df[df["horizon"] == 10], model="ridge_factors")
    if h20.empty:
        return pd.DataFrame()
    keep = ["Date", "q10_logret", "q50_logret", "q90_logret", f"p_up_strong_h{horizon}", f"p_down_strong_h{horizon}"]
    out = h20[[c for c in keep if c in h20.columns]].copy()
    out = out.sort_values("Date").drop_duplicates("Date", keep="last")
    if not h10.empty and "p_down_strong_h10" in h10.columns:
        h10_prob = h10[["Date", "p_down_strong_h10"]].sort_values("Date")
        out = pd.merge_asof(out.sort_values("Date"), h10_prob, on="Date", direction="backward")
    return out


def _preferred_model(df: pd.DataFrame, model: str) -> pd.DataFrame:
    if df.empty or "model" not in df.columns:
        return df
    preferred = df[df["model"] == model]
    if not preferred.empty:
        return preferred
    fallback_model = df["model"].value_counts().index[0]
    return df[df["model"] == fallback_model]


def _load_cqr_inputs(horizon: int) -> pd.DataFrame:
    if not CQR_RESULTS_PARQUET.exists():
        return pd.DataFrame()
    df = read_parquet(CQR_RESULTS_PARQUET)
    if df.empty or "horizon" not in df.columns:
        return pd.DataFrame()
    df = df[df["horizon"] == horizon].copy()
    if df.empty:
        return pd.DataFrame()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df.sort_values("Date").drop_duplicates("Date", keep="last")


def _model_signal_sale(
    season_prices: pd.DataFrame,
    model_inputs: pd.DataFrame,
    assumptions: BacktestAssumptions,
    profile: dict[str, Any],
    rules: list[dict[str, Any]],
) -> float:
    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    last_date = pd.Timestamp(season_prices["Date"].iloc[0])
    last_thirds_sale = last_date - pd.Timedelta(days=90)

    for _, row in season_prices.iterrows():
        date = pd.Timestamp(row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        if inventory <= 1e-9:
            break

        preds = _decision_inputs_for_date(date, float(row["cash_price"]), model_inputs, assumptions.horizon)
        rec = advise(preds, profile, rules)
        fraction = _action_fraction(rec_action=rec.action, rec_fraction=rec.sell_fraction)
        if rec.action in {Action.SELL_THIRDS, Action.SELL_THIRDS_OVER_60_DAYS}:
            if (date - last_thirds_sale).days < 20:
                fraction = 0.0
            elif fraction > 0:
                last_thirds_sale = date
        if fraction <= 0:
            continue
        sold = min(inventory, max(0.0, fraction))
        revenue += sold * _quality_adjusted_price(
            float(row["cash_price"]),
            days_held=int((date - pd.Timestamp(season_prices["Date"].iloc[0])).days),
            assumptions=assumptions,
        )
        inventory -= sold

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        revenue += inventory * _quality_adjusted_price(
            float(last["cash_price"]),
            days_held=int((pd.Timestamp(last["Date"]) - pd.Timestamp(season_prices["Date"].iloc[0])).days),
            assumptions=assumptions,
        )
    return revenue - storage_cost


def _decision_inputs_for_date(
    date: pd.Timestamp,
    cash_price: float,
    model_inputs: pd.DataFrame,
    horizon: int,
) -> dict[str, float | str]:
    defaults = {
        f"p_up_strong_h{horizon}": 0.5,
        "p_down_strong_h10": 0.2,
        "q10_h20": cash_price * 0.95,
        "q50_h20": cash_price,
        "q90_h20": cash_price * 1.05,
        "regime": "range",
        "p_t": cash_price,
    }
    if model_inputs.empty:
        return defaults
    prior = model_inputs[model_inputs["Date"] <= date].tail(1)
    if prior.empty:
        return defaults
    row = prior.iloc[0]
    q10 = float(row.get("q10_logret", math.log(0.95)))
    q50 = float(row.get("q50_logret", 0.0))
    q90 = float(row.get("q90_logret", math.log(1.05)))
    return {
        f"p_up_strong_h{horizon}": float(row.get(f"p_up_strong_h{horizon}", 0.5)),
        "p_down_strong_h10": float(row.get("p_down_strong_h10", row.get(f"p_down_strong_h{horizon}", 0.2))),
        "q10_h20": cash_price * math.exp(q10),
        "q50_h20": cash_price * math.exp(q50),
        "q90_h20": cash_price * math.exp(q90),
        "regime": "range",
        "p_t": cash_price,
    }


def _action_fraction(rec_action: Action, rec_fraction: float) -> float:
    if rec_action == Action.STORE or rec_action == Action.WAIT:
        return 0.0
    if rec_action == Action.SELL_NOW:
        return max(0.0, min(1.0, rec_fraction))
    return max(0.0, min(0.33, rec_fraction or 0.33))


def _cqr_optimal_sale(
    season_prices: pd.DataFrame,
    cqr_inputs: pd.DataFrame,
    assumptions: BacktestAssumptions,
) -> float:
    if cqr_inputs.empty:
        return _fixed_sale(season_prices, assumptions, days_after_harvest=90)

    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    start = pd.Timestamp(season_prices["Date"].iloc[0])
    last_date = start
    last_partial_sale = start - pd.Timedelta(days=90)

    for _, row in season_prices.iterrows():
        date = pd.Timestamp(row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        if inventory <= 1e-9:
            break

        prior = cqr_inputs[cqr_inputs["Date"] <= date].tail(1)
        if prior.empty:
            continue
        cqr = prior.iloc[0]
        cost_ratio = assumptions.storage_cost_usd_per_bu_per_month * assumptions.horizon / 30.0 / max(float(row["cash_price"]), 1e-6)
        q_lo = float(cqr.get("q_lo", -cost_ratio))
        q_hi = float(cqr.get("q_hi", cost_ratio))
        midpoint = float(cqr.get("midpoint", 0.0))
        width = q_hi - q_lo

        sell_fraction = 0.0
        if q_hi < 0 or q_lo < -2.0 * cost_ratio:
            sell_fraction = 1.0
        elif width > 3.0 * cost_ratio and (date - last_partial_sale).days >= 20:
            sell_fraction = 0.33
        elif midpoint <= cost_ratio and (date - last_partial_sale).days >= 30:
            sell_fraction = 0.25

        if sell_fraction <= 0:
            continue
        last_partial_sale = date
        sold = min(inventory, sell_fraction)
        revenue += sold * _quality_adjusted_price(
            float(row["cash_price"]),
            days_held=int((date - start).days),
            assumptions=assumptions,
        )
        inventory -= sold

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        revenue += inventory * _quality_adjusted_price(
            float(last["cash_price"]),
            days_held=int((pd.Timestamp(last["Date"]) - start).days),
            assumptions=assumptions,
        )
    return revenue - storage_cost


def _sell_monthly(season_prices: pd.DataFrame, assumptions: BacktestAssumptions) -> float:
    """Sell 1/12 of inventory each month, net of storage and quality costs."""
    if season_prices.empty:
        return 0.0
    start = pd.Timestamp(season_prices["Date"].iloc[0])
    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    n_months = 12
    tranche = 1.0 / n_months
    last_date = start

    for month_idx in range(n_months):
        target = start + pd.DateOffset(months=month_idx)
        row = season_prices[season_prices["Date"] >= target]
        if row.empty:
            break
        sale_row = row.iloc[0]
        date = pd.Timestamp(sale_row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        sold = min(inventory, tranche)
        days_held = int((date - start).days)
        revenue += sold * _quality_adjusted_price(float(sale_row["cash_price"]), days_held, assumptions)
        inventory -= sold

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        days_held = int((pd.Timestamp(last["Date"]) - start).days)
        elapsed = max(0, int((pd.Timestamp(last["Date"]) - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        revenue += inventory * _quality_adjusted_price(float(last["cash_price"]), days_held, assumptions)
    return revenue - storage_cost


def _sell_thirds(season_prices: pd.DataFrame, assumptions: BacktestAssumptions) -> float:
    """Sell 1/3 at harvest, 1/3 in January, 1/3 in June."""
    if season_prices.empty:
        return 0.0
    start = pd.Timestamp(season_prices["Date"].iloc[0])
    targets_months = [0, 3, 8]  # at harvest, 3M later, 8M later (≈ Jun)
    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    last_date = start

    for months_after in targets_months:
        target = start + pd.DateOffset(months=months_after)
        row = season_prices[season_prices["Date"] >= target]
        if row.empty:
            break
        sale_row = row.iloc[0]
        date = pd.Timestamp(sale_row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        sold = min(inventory, 1.0 / 3.0)
        days_held = int((date - start).days)
        revenue += sold * _quality_adjusted_price(float(sale_row["cash_price"]), days_held, assumptions)
        inventory -= sold

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        days_held = int((pd.Timestamp(last["Date"]) - start).days)
        elapsed = max(0, int((pd.Timestamp(last["Date"]) - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        revenue += inventory * _quality_adjusted_price(float(last["cash_price"]), days_held, assumptions)
    return revenue - storage_cost


def _sell_threshold(
    season_prices: pd.DataFrame,
    all_prices: pd.DataFrame,
    assumptions: BacktestAssumptions,
    pct_above: float = 0.05,
    lookback_years: int = 5,
) -> float:
    """Sell all inventory when cash price exceeds 5-year rolling average * (1+pct_above)."""
    if season_prices.empty:
        return 0.0
    start = pd.Timestamp(season_prices["Date"].iloc[0])
    lookback_start = start - pd.DateOffset(years=lookback_years)
    hist = all_prices[(all_prices["Date"] >= lookback_start) & (all_prices["Date"] < start)]
    threshold = float(hist["cash_price"].mean() * (1.0 + pct_above)) if not hist.empty else float("inf")

    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    last_date = start

    for _, row in season_prices.iterrows():
        date = pd.Timestamp(row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        if inventory <= 1e-9:
            break
        if float(row["cash_price"]) >= threshold:
            days_held = int((date - start).days)
            revenue += inventory * _quality_adjusted_price(float(row["cash_price"]), days_held, assumptions)
            inventory = 0.0
            break

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        days_held = int((pd.Timestamp(last["Date"]) - start).days)
        elapsed = max(0, int((pd.Timestamp(last["Date"]) - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        revenue += inventory * _quality_adjusted_price(float(last["cash_price"]), days_held, assumptions)
    return revenue - storage_cost


def _model_storage_value(
    season_prices: pd.DataFrame,
    model_inputs: pd.DataFrame,
    assumptions: BacktestAssumptions,
) -> float:
    """Sell when the model expects storage value (expected gain - storage cost) > 0.

    Uses q50_logret as the expected log-return over the horizon.
    Storage is worthwhile when expected price appreciation > cost of storage.
    """
    if model_inputs.empty:
        return _fixed_sale(season_prices, assumptions, days_after_harvest=90)

    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    start = pd.Timestamp(season_prices["Date"].iloc[0])
    last_date = start

    for _, row in season_prices.iterrows():
        date = pd.Timestamp(row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        if inventory <= 1e-9:
            break

        prior = model_inputs[model_inputs["Date"] <= date].tail(1)
        if prior.empty:
            continue
        q50 = float(prior.iloc[0].get("q50_logret", 0.0))
        expected_return = float(row["cash_price"]) * (np.exp(q50) - 1.0)
        storage_cost_horizon = assumptions.storage_cost_usd_per_bu_per_month * assumptions.horizon / 30.0
        # Sell if expected return < storage cost (not worth holding)
        if expected_return < storage_cost_horizon:
            days_held = int((date - start).days)
            revenue += inventory * _quality_adjusted_price(float(row["cash_price"]), days_held, assumptions)
            inventory = 0.0
            break

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        days_held = int((pd.Timestamp(last["Date"]) - start).days)
        elapsed = max(0, int((pd.Timestamp(last["Date"]) - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        revenue += inventory * _quality_adjusted_price(float(last["cash_price"]), days_held, assumptions)
    return revenue - storage_cost


def _cqr_cautious(
    season_prices: pd.DataFrame,
    cqr_inputs: pd.DataFrame,
    assumptions: BacktestAssumptions,
) -> float:
    """Sell only if q_lo (pessimistic CQR bound) > 0.

    More conservative than CQR_OPTIMAL: refuses to sell unless even the
    pessimistic lower bound of the CQR interval is positive (price expected to fall).
    """
    if cqr_inputs.empty:
        return _fixed_sale(season_prices, assumptions, days_after_harvest=0)

    inventory = 1.0
    revenue = 0.0
    storage_cost = 0.0
    start = pd.Timestamp(season_prices["Date"].iloc[0])
    last_date = start

    for _, row in season_prices.iterrows():
        date = pd.Timestamp(row["Date"])
        elapsed = max(0, int((date - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        last_date = date
        if inventory <= 1e-9:
            break

        prior = cqr_inputs[cqr_inputs["Date"] <= date].tail(1)
        if prior.empty:
            continue
        q_lo = float(prior.iloc[0].get("q_lo", 0.0))
        # Sell if even the optimistic lower bound shows likely decline
        if q_lo < 0:
            days_held = int((date - start).days)
            revenue += inventory * _quality_adjusted_price(float(row["cash_price"]), days_held, assumptions)
            inventory = 0.0
            break

    if inventory > 1e-9:
        last = season_prices.iloc[-1]
        days_held = int((pd.Timestamp(last["Date"]) - start).days)
        elapsed = max(0, int((pd.Timestamp(last["Date"]) - last_date).days))
        storage_cost += inventory * assumptions.storage_cost_usd_per_bu_per_month * elapsed / 30.0
        revenue += inventory * _quality_adjusted_price(float(last["cash_price"]), days_held, assumptions)
    return revenue - storage_cost


def _net_sale_price(cash_price: float, days_held: int, assumptions: BacktestAssumptions) -> float:
    months = days_held / 30.0
    storage_cost = assumptions.storage_cost_usd_per_bu_per_month * months
    return _quality_adjusted_price(cash_price, days_held, assumptions) - storage_cost


def _quality_adjusted_price(cash_price: float, days_held: int, assumptions: BacktestAssumptions) -> float:
    months = days_held / 30.0
    quality_multiplier = max(0.0, 1.0 - assumptions.quality_loss_rate_per_month * months)
    return cash_price * quality_multiplier


def _summarise_v2(annual: pd.DataFrame) -> pd.DataFrame:
    """Summarise V2 backtest results with all 8 strategies."""
    harvest = annual[annual["strategy"] == "SELL_HARVEST"][["season", "price_obtained"]]
    harvest = harvest.rename(columns={"price_obtained": "harvest_revenue"})
    monthly = annual[annual["strategy"] == "SELL_MONTHLY"][["season", "price_obtained"]]
    monthly = monthly.rename(columns={"price_obtained": "monthly_revenue"})
    perfect = annual[annual["strategy"] == "PERFECT_HINDSIGHT"][["season", "price_obtained"]]
    perfect = perfect.rename(columns={"price_obtained": "perfect_revenue"})

    merged = annual.merge(harvest, on="season", how="left")
    merged = merged.merge(monthly, on="season", how="left")
    merged = merged.merge(perfect, on="season", how="left")

    rows = []
    for strategy in STRATEGIES_V2:
        sub = merged[merged["strategy"] == strategy]
        if sub.empty:
            continue
        gains_vs_harvest = sub["price_obtained"] - sub["harvest_revenue"]
        gains_vs_monthly = sub["price_obtained"] - sub["monthly_revenue"]
        regrets = sub["perfect_revenue"] - sub["price_obtained"]
        sharpe = float(gains_vs_harvest.mean() / gains_vs_harvest.std(ddof=0)) if float(gains_vs_harvest.std(ddof=0)) > 1e-12 else 0.0
        rows.append(
            {
                "strategy": strategy,
                "avg_price_obtained": float(sub["price_obtained"].mean()),
                "avg_capture_rate": float(sub["capture_rate"].mean()),
                "avg_vs_harvest": float(gains_vs_harvest.mean()),
                "avg_vs_monthly": float(gains_vs_monthly.mean()),
                "avg_regret": float(regrets.mean()),
                "pct_years_wins": float((gains_vs_harvest > 0).mean()),
                "sharpe": sharpe,
                "n_years": int(sub["season"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values("avg_capture_rate", ascending=False).reset_index(drop=True)


def _write_report_v2(
    annual: pd.DataFrame,
    summary: pd.DataFrame,
    assumptions: BacktestAssumptions,
    model_inputs: pd.DataFrame,
    cqr_inputs: pd.DataFrame,
) -> None:
    REPORT_V2_PATH.parent.mkdir(parents=True, exist_ok=True)
    period = f"{annual['season'].min()}–{annual['season'].max()}"
    n_seasons = int(summary["n_years"].max())
    lines = [
        "# Backtest agriculteur V2 — 8 stratégies",
        "",
        "## Objectif",
        "",
        "Comparer 8 stratégies de vente de maïs, de la plus simple (vente à récolte) à la borne",
        "théorique (hindsight parfait). La question centrale : *à quel point le modèle aide-t-il,*",
        "*et dans quelles conditions ?*",
        "",
        "## Hypothèses",
        "",
        f"- Horizon décision : J+{assumptions.horizon}",
        f"- État/profil : `{assumptions.farmer_state}`",
        f"- Période : `{period}` ({n_seasons} saisons)",
        f"- Basis local : {assumptions.basis_usd_per_bu:.2f} USD/bu",
        f"- Coût stockage : {assumptions.storage_cost_usd_per_bu_per_month:.2f} USD/bu/mois",
        f"- Perte qualité : {assumptions.quality_loss_rate_per_month:.2%}/mois",
        f"- Prédictions modèle : {'calibrated_predictions.parquet' if not model_inputs.empty else 'non disponibles — fallback'}",
        f"- CQR : {'cqr_results.parquet' if not cqr_inputs.empty else 'non disponibles — fallback'}",
        "",
        "> **PERFECT_HINDSIGHT** = borne théorique : vente au prix maximum observé dans la saison.",
        "> C'est un plafond irréalisable, fourni uniquement comme référence de regret.",
        "",
        "## Résumé par stratégie",
        "",
        "| Stratégie | Prix moyen USD/bu | Capture rate | vs Récolte | vs Mensuel | Regret | % années gagne | Sharpe | N |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        marker = " ⭐" if row["strategy"] == "PERFECT_HINDSIGHT" else ""
        lines.append(
            "| `{s}`{m} | {p:.3f} | {c:.1%} | {vh:+.3f} | {vm:+.3f} | {r:.3f} | {w:.1%} | {sh:.2f} | {n:d} |".format(
                s=row["strategy"],
                m=marker,
                p=row["avg_price_obtained"],
                c=row["avg_capture_rate"],
                vh=row["avg_vs_harvest"],
                vm=row["avg_vs_monthly"],
                r=row["avg_regret"],
                w=row["pct_years_wins"],
                sh=row["sharpe"],
                n=int(row["n_years"]),
            )
        )

    # Per-year tables
    ordered = [s for s in STRATEGIES_V2 if s in annual["strategy"].unique()]
    pivot_capture = annual.pivot(index="season", columns="strategy", values="capture_rate")[ordered]
    pivot_vs = annual.pivot(index="season", columns="strategy", values="vs_harvest")[ordered]

    lines.extend(
        [
            "",
            "## Capture rate par année",
            "",
            _markdown_table(pivot_capture, fmt="{:.1%}"),
            "",
            "## Delta vs SELL_HARVEST par année (USD/bu)",
            "",
            _markdown_table(pivot_vs, fmt="{:+.3f}"),
        ]
    )

    # Bad year analysis: years where MODEL_SIGNAL underperforms SELL_HARVEST
    model_ann = annual[annual["strategy"] == "MODEL_SIGNAL"][["season", "vs_harvest", "capture_rate"]]
    bad_years = model_ann[model_ann["vs_harvest"] < 0].sort_values("vs_harvest")
    if not bad_years.empty:
        lines += [
            "",
            "## Analyse des mauvaises années (MODEL_SIGNAL < SELL_HARVEST)",
            "",
            "| Année | Delta USD/bu | Capture rate |",
            "|---:|---:|---:|",
        ]
        for _, r in bad_years.iterrows():
            lines.append(f"| {int(r['season'])} | {r['vs_harvest']:+.3f} | {r['capture_rate']:.1%} |")
        lines += [
            "",
            (
                "Dans ces années, le modèle a tenu l'inventaire trop longtemps ou a vendu trop tôt. "
                "Un marché en tendance baissière prolongée ou une forte hausse initiale manquée "
                "sont les causes typiques."
            ),
        ]

    lines += [
        "",
        "## Interprétation",
        "",
        (
            "- `SELL_HARVEST` et `SELL_THIRDS` définissent la baseline réaliste la plus accessible."
        ),
        (
            "- `SELL_MONTHLY` est un DCA (dollar-cost averaging) sur l'année : robuste mais ne "
            "profite pas des pics."
        ),
        (
            "- `MODEL_SIGNAL` et `MODEL_STORAGE_VALUE` bénéficient des prédictions calibrées. "
            "Un gain vs récolte significatif valide l'utilité pratique du modèle."
        ),
        (
            "- `CQR_CAUTIOUS` est plus conservateur : ne vend que si la borne basse de l'intervalle "
            "est négative — réduit les ventes prématurées mais peut manquer la fenêtre de hausse."
        ),
        (
            "- `PERFECT_HINDSIGHT` est irréalisable et sert uniquement à mesurer le *regret* "
            "théorique maximum de chaque stratégie."
        ),
    ]
    REPORT_V2_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summarise(annual: pd.DataFrame) -> pd.DataFrame:
    harvest = annual[annual["strategy"] == "SELL_HARVEST"][["season", "price_obtained"]]
    harvest = harvest.rename(columns={"price_obtained": "harvest_revenue"})
    merged = annual.merge(harvest, on="season", how="left")
    rows = []
    for strategy, sub in merged.groupby("strategy", sort=False):
        gains = sub["price_obtained"] - sub["harvest_revenue"]
        sharpe = float(gains.mean() / gains.std(ddof=0)) if float(gains.std(ddof=0)) > 1e-12 else 0.0
        rows.append(
            BacktestResult(
                strategy=strategy,
                avg_price_obtained=float(sub["price_obtained"].mean()),
                avg_capture_rate=float(sub["capture_rate"].mean()),
                avg_gain_vs_harvest=float(gains.mean()),
                sharpe=sharpe,
                pct_years_beating_harvest=float((sub["price_obtained"] > sub["harvest_revenue"]).mean()),
                max_drawdown=_max_drawdown(gains.cumsum()),
                n_years=int(sub["season"].nunique()),
            ).__dict__
        )
    return pd.DataFrame(rows).sort_values("avg_capture_rate", ascending=False).reset_index(drop=True)


def _max_drawdown(cumulative: pd.Series) -> float:
    if cumulative.empty:
        return 0.0
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    return float(drawdown.min())


def _write_report(
    annual: pd.DataFrame,
    summary: pd.DataFrame,
    assumptions: BacktestAssumptions,
    model_inputs: pd.DataFrame,
    cqr_inputs: pd.DataFrame,
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    period = f"{annual['season'].min()}-{annual['season'].max()}"
    lines = [
        "# Backtest agriculteur",
        "",
        "## Hypothèses",
        "",
        f"- Horizon décision : J+{assumptions.horizon}",
        f"- État/profil : `{assumptions.farmer_state}`",
        f"- Période : `{period}` ({int(summary['n_years'].max())} saisons)",
        f"- Basis local : {assumptions.basis_usd_per_bu:.2f} USD/bu",
        f"- Coût stockage : {assumptions.storage_cost_usd_per_bu_per_month:.2f} USD/bu/mois",
        f"- Perte qualité : {assumptions.quality_loss_rate_per_month:.2%}/mois",
        f"- Inventaire simulé : {assumptions.initial_inventory_bushels:,.0f} bu, métriques ramenées en USD/bu",
        f"- Source modèle : {'prédictions calibrées professional_study' if not model_inputs.empty else 'fallback sans prédictions calibrées'}",
        f"- Source CQR : {'cqr_results.parquet' if not cqr_inputs.empty else 'fallback STORE_3M'}",
        "",
        "## Résumé stratégies",
        "",
        "| Stratégie | Prix net USD/bu | Capture rate | Gain vs récolte | Sharpe gain | Années > récolte | Max drawdown | N |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            "| `{strategy}` | {price:.3f} | {capture:.1%} | {gain:+.3f} | {sharpe:.2f} | "
            "{win:.1%} | {dd:.3f} | {n:d} |".format(
                strategy=row["strategy"],
                price=row["avg_price_obtained"],
                capture=row["avg_capture_rate"],
                gain=row["avg_gain_vs_harvest"],
                sharpe=row["sharpe"],
                win=row["pct_years_beating_harvest"],
                dd=row["max_drawdown"],
                n=int(row["n_years"]),
            )
        )

    pivot_price = annual.pivot(index="season", columns="strategy", values="price_obtained")
    pivot_capture = annual.pivot(index="season", columns="strategy", values="capture_rate")
    ordered_cols = [s for s in STRATEGIES if s in pivot_price.columns]
    lines.extend(
        [
            "",
            "## Prix net annuel USD/bu",
            "",
            _markdown_table(pivot_price[ordered_cols], fmt="{:.3f}"),
            "",
            "## Capture rate annuel",
            "",
            _markdown_table(pivot_capture[ordered_cols], fmt="{:.1%}"),
            "",
            "## Lecture",
            "",
            (
                "Le capture rate est le prix net obtenu par la stratégie divisé par le meilleur "
                "prix cash observé dans la saison. Les coûts de stockage et la perte qualité "
                "sont déduits avant le calcul. `BENCHMARK_AVG` est la moyenne mécanique de "
                "`SELL_HARVEST`, `STORE_3M` et `STORE_6M`."
            ),
            "",
            (
                "`MODEL_SIGNAL` utilise les règles agriculteur avec les prédictions calibrées "
                "disponibles. Le résultat est conservé tel quel même si une baseline simple "
                "fait mieux : c'est la mesure économique réelle du système à ce stade."
            ),
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _markdown_table(df: pd.DataFrame, fmt: str) -> str:
    out = df.reset_index()
    lines = [
        "| " + " | ".join(str(c) for c in out.columns) + " |",
        "| " + " | ".join("---:" for _ in out.columns) + " |",
    ]
    for _, row in out.iterrows():
        vals = []
        for pos, col in enumerate(out.columns):
            val = row[col]
            if pos == 0 and pd.notna(val):
                vals.append(str(int(val)) if float(val).is_integer() else str(val))
            elif isinstance(val, float) and np.isfinite(val):
                vals.append(fmt.format(val))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

import json

import numpy as np
import pandas as pd

from mais.research.archive.farmer_backtest_v2 import StorageCosts, run_farmer_backtest_v2
from mais.research.archive.storage_targets import (
    assert_storage_targets_not_in_features,
    build_storage_targets,
)


def _prices() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2010-01-04", "2022-12-30")
    seasonal = 30 * np.sin(np.arange(len(dates)) / 90.0)
    price = 420 + seasonal + np.cumsum(rng.normal(0, 1.5, len(dates)))
    return pd.DataFrame({"Date": dates, "corn_close": price})


def _signals(prices: pd.DataFrame) -> pd.DataFrame:
    sig = prices[["Date"]].copy()
    month = pd.to_datetime(sig["Date"]).dt.month
    sig["signal"] = np.where(month.isin([10, 11]), "BULLISH", np.where(month.isin([2, 3]), "BEARISH", "UNCERTAIN"))
    return sig


def test_storage_targets_no_leakage():
    features = pd.DataFrame({"Date": pd.bdate_range("2020-01-01", periods=10), "x": np.arange(10)})
    assert_storage_targets_not_in_features(features)
    targets = build_storage_targets(_prices().head(400))
    assert {"y_storage_value_1m", "y_max_opportunity_3m", "y_sell_partial_flag"}.issubset(targets.columns)


def test_backtest_all_strategies_documented(tmp_path):
    out = tmp_path / "backtest_results.json"
    payload = run_farmer_backtest_v2(_prices(), _signals(_prices()), output_path=out)
    strategies = payload["strategies"]
    assert {"SELL_HARVEST", "SELL_THIRDS", "SELL_25_25_25_25", "SIGNAL_BINARY", "SIGNAL_PARTIAL", "SELL_MAX_ORACLE"}.issubset(strategies)
    assert json.loads(out.read_text(encoding="utf-8"))["verdict"] == payload["verdict"]


def test_annual_gain_distribution():
    payload = run_farmer_backtest_v2(_prices(), _signals(_prices()))
    gains = payload["strategies"]["SIGNAL_PARTIAL"]["crop_years"]
    assert {str(y) for y in range(2015, 2023)}.issubset(gains)


def test_storage_costs_deducted():
    prices = _prices()
    signals = _signals(prices)
    with_costs = run_farmer_backtest_v2(prices, signals)
    no_costs = run_farmer_backtest_v2(
        prices,
        signals,
        costs=StorageCosts(cost_per_month_cents_per_bu=0.0, interest_rate_annual=0.0, quality_loss_pct=0.0),
    )
    assert (
        no_costs["strategies"]["SELL_MAX_ORACLE"]["mean_gain_vs_sell_harvest"]
        >= with_costs["strategies"]["SELL_MAX_ORACLE"]["mean_gain_vs_sell_harvest"]
    )


def test_worst_year_identified():
    payload = run_farmer_backtest_v2(_prices(), _signals(_prices()))
    assert payload["worst_year"] is not None
    assert "cause" in payload["worst_year"]


def test_verdict_honest():
    payload = run_farmer_backtest_v2(_prices(), _signals(_prices()))
    assert payload["verdict"] in {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}

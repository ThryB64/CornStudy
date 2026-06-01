from __future__ import annotations

import numpy as np
import pandas as pd

import mais.features.euronext_continuous as cont


def _row(
    date: str,
    code: str,
    expiry: str,
    price: float,
    *,
    oi: float | None,
    volume: float = 100.0,
) -> dict[str, object]:
    month_code = code.split("_", 1)[1][0]
    contract_year = int(code[-4:])
    return {
        "date": date,
        "contract_code": code,
        "source_symbol": code.replace("EMA_", "XB"),
        "source": "barchart_proxy_exploratory",
        "import_verdict": "usable",
        "settlement": np.nan,
        "close_or_last": price,
        "volume": volume,
        "open_interest": oi,
        "expiry_date": expiry,
        "month_code": month_code,
        "contract_year": contract_year,
    }


def _contracts() -> pd.DataFrame:
    rows = [
        _row("2026-05-01", "EMA_M2026", "2026-06-05", 200.0, oi=1000, volume=80),
        _row("2026-05-01", "EMA_Q2026", "2026-08-05", 205.0, oi=2000, volume=120),
        _row("2026-05-01", "EMA_X2026", "2026-11-05", 210.0, oi=500, volume=40),
        _row("2026-05-01", "EMA_X2027", "2027-11-05", 220.0, oi=100, volume=20),
        _row("2026-05-02", "EMA_M2026", "2026-06-05", 201.0, oi=900, volume=70),
        _row("2026-05-02", "EMA_Q2026", "2026-08-05", 206.0, oi=3000, volume=140),
        _row("2026-05-02", "EMA_X2026", "2026-11-05", 211.0, oi=500, volume=40),
        _row("2026-05-02", "EMA_X2027", "2027-11-05", 221.0, oi=100, volume=20),
        _row("2026-05-25", "EMA_M2026", "2026-06-05", 202.0, oi=800, volume=70),
        _row("2026-05-25", "EMA_Q2026", "2026-08-05", 207.0, oi=3500, volume=150),
        _row("2026-05-25", "EMA_X2026", "2026-11-05", 212.0, oi=500, volume=40),
        _row("2026-05-25", "EMA_X2027", "2027-11-05", 222.0, oi=100, volume=20),
        _row("2026-12-10", "EMA_X2026", "2026-11-05", 229.0, oi=10, volume=5),
        _row("2026-12-10", "EMA_X2027", "2027-11-05", 230.0, oi=900, volume=60),
    ]
    return pd.DataFrame(rows)


def test_curve_daily_ranks_by_expiry_and_oi() -> None:
    curve = cont.build_curve_daily(_contracts())
    may_1 = curve[curve["date"].eq(pd.Timestamp("2026-05-01"))]

    assert may_1.loc[may_1["contract_code"].eq("EMA_M2026"), "rank_by_expiry"].item() == 1
    assert may_1.loc[may_1["contract_code"].eq("EMA_Q2026"), "rank_by_oi"].item() == 1
    assert set(curve["source_quality"]) == {"exploratory"}


def test_roll_event_flag_on_contract_change() -> None:
    front = cont.build_front_continuous(_contracts(), min_dte=15)
    rolls = front[front["roll_event"].astype(bool)]

    assert rolls["date"].tolist() == [pd.Timestamp("2026-05-25"), pd.Timestamp("2026-12-10")]
    may_roll = rolls[rolls["date"].eq(pd.Timestamp("2026-05-25"))].iloc[0]
    assert may_roll["prev_contract_code"] == "EMA_M2026"
    assert may_roll["contract_code"] == "EMA_Q2026"
    assert may_roll["roll_adjustment"] == 5.0


def test_adjusted_minus_raw_equals_cumulative_roll() -> None:
    front = cont.build_front_continuous(_contracts(), min_dte=15)
    adjusted = cont.build_front_adjusted(front)

    total_roll = front["roll_adjustment"].sum()
    assert adjusted["series_name"].iloc[-1] == "front_adjusted"
    assert adjusted["cum_roll_adjustment"].iloc[-1] == total_roll
    assert front["price"].iloc[-1] - adjusted["adjusted_price"].iloc[-1] == total_roll


def test_liquid_series_selects_highest_oi_within_dte_window() -> None:
    liquid = cont.build_liquid_continuous(_contracts(), min_dte=15, max_dte=370)
    may_1 = liquid[liquid["date"].eq(pd.Timestamp("2026-05-01"))].iloc[0]

    assert may_1["contract_code"] == "EMA_Q2026"
    assert may_1["open_interest"] == 2000
    assert may_1["liquidity_rank_source"] == "open_interest"


def test_liquid_series_falls_back_to_volume_when_oi_missing() -> None:
    contracts = _contracts()
    contracts["open_interest"] = np.nan

    liquid = cont.build_liquid_continuous(contracts, min_dte=15, max_dte=370)
    may_1 = liquid[liquid["date"].eq(pd.Timestamp("2026-05-01"))].iloc[0]

    assert may_1["contract_code"] == "EMA_Q2026"
    assert may_1["liquidity_rank_source"] == "volume"


def test_harvest_nov_selection_mai_2026() -> None:
    harvest = cont.build_harvest_november(_contracts())
    may = harvest[harvest["date"].eq(pd.Timestamp("2026-05-01"))].iloc[0]

    assert may["contract_code"] == "EMA_X2026"
    assert may["series_name"] == "harvest_nov"


def test_harvest_nov_selection_decembre_2026() -> None:
    harvest = cont.build_harvest_november(_contracts())
    december = harvest[harvest["date"].eq(pd.Timestamp("2026-12-10"))].iloc[0]

    assert december["contract_code"] == "EMA_X2027"


def test_no_duplicate_dates() -> None:
    for series in [
        cont.build_front_continuous(_contracts()),
        cont.build_liquid_continuous(_contracts()),
        cont.build_harvest_november(_contracts()),
    ]:
        assert not series["date"].duplicated().any()


def test_build_and_save_continuous_series_writes_outputs(tmp_path, monkeypatch) -> None:
    output_paths = {
        "EMA_CURVE_DAILY": tmp_path / "ema_curve_daily.parquet",
        "EMA_FRONT_RAW": tmp_path / "ema_front_continuous_raw.parquet",
        "EMA_FRONT_ADJUSTED": tmp_path / "ema_front_continuous_adjusted.parquet",
        "EMA_LIQUID_RAW": tmp_path / "ema_liquid_continuous_raw.parquet",
        "EMA_LIQUID_ADJUSTED": tmp_path / "ema_liquid_continuous_adjusted.parquet",
        "EMA_MOST_LIQUID": tmp_path / "ema_most_liquid_continuous.parquet",
        "EMA_HARVEST_NOV": tmp_path / "ema_harvest_nov.parquet",
    }
    for name, path in output_paths.items():
        monkeypatch.setattr(cont, name, path)

    summary = cont.build_and_save_continuous_series(_contracts())

    assert set(summary) == {path.name for path in output_paths.values()}
    assert all(path.exists() for path in output_paths.values())
    assert pd.read_parquet(output_paths["EMA_FRONT_ADJUSTED"])["adjusted_price"].notna().any()


def test_load_continuous_feature_block_uses_adjusted_price(tmp_path, monkeypatch) -> None:
    dates = pd.date_range("2026-01-01", periods=7, freq="D")
    adjusted = pd.DataFrame({
        "date": dates,
        "price": [999.0] * len(dates),
        "adjusted_price": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0],
    })
    harvest = pd.DataFrame({"date": dates, "price": [210.0, 211.0, 212.0, 213.0, 214.0, 215.0, 216.0]})
    front_path = tmp_path / "front_adjusted.parquet"
    liquid_path = tmp_path / "liquid_adjusted.parquet"
    harvest_path = tmp_path / "harvest.parquet"
    adjusted.to_parquet(front_path, index=False)
    adjusted.to_parquet(liquid_path, index=False)
    harvest.to_parquet(harvest_path, index=False)
    monkeypatch.setattr(cont, "EMA_FRONT_ADJUSTED", front_path)
    monkeypatch.setattr(cont, "EMA_LIQUID_ADJUSTED", liquid_path)
    monkeypatch.setattr(cont, "EMA_HARVEST_NOV", harvest_path)

    features = cont.load_continuous_feature_block(pd.Series(dates))

    assert features.loc[features["Date"].eq(pd.Timestamp("2026-01-02")), "ema_front_price_lag1"].item() == 100.0
    assert features.loc[features["Date"].eq(pd.Timestamp("2026-01-02")), "ema_liquid_price_lag1"].item() == 100.0
    assert features.loc[features["Date"].eq(pd.Timestamp("2026-01-02")), "ema_harvest_nov_price_lag1"].item() == 210.0

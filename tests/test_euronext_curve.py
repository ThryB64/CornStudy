from __future__ import annotations

import numpy as np
import pandas as pd

import mais.features.euronext_curve as curve


def _inputs(periods: int = 30) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2026-01-01", periods=periods)
    rows: list[dict[str, object]] = []
    for i, day in enumerate(dates):
        rows.extend(
            [
                {
                    "date": day,
                    "contract_code": "EMA_H2026",
                    "month_code": "H",
                    "price": 200.0 + i,
                    "rank_by_expiry": 1,
                    "rank_by_oi": 2,
                    "days_to_expiry": 30,
                    "volume": 100 + i,
                    "open_interest": 1000 + i,
                },
                {
                    "date": day,
                    "contract_code": "EMA_M2026",
                    "month_code": "M",
                    "price": 205.0 + i,
                    "rank_by_expiry": 2,
                    "rank_by_oi": 1,
                    "days_to_expiry": 120,
                    "volume": 200 + i,
                    "open_interest": 3000 + i,
                },
                {
                    "date": day,
                    "contract_code": "EMA_Q2026",
                    "month_code": "Q",
                    "price": 212.0 + i,
                    "rank_by_expiry": 3,
                    "rank_by_oi": 3,
                    "days_to_expiry": 210,
                    "volume": 50 + i,
                    "open_interest": 500 + i,
                },
            ]
        )
    contracts = pd.DataFrame(rows)
    front = pd.DataFrame({"date": dates, "price": 200.0 + np.arange(periods)})
    adjusted = pd.DataFrame({"date": dates, "price": 999.0, "adjusted_price": 100.0 + np.arange(periods)})
    harvest = pd.DataFrame({"date": dates, "price": 230.0 + np.arange(periods)})
    cbot = pd.DataFrame({"Date": dates, "corn_close": 500.0 + np.arange(periods)})
    eurusd = pd.DataFrame({"Date": dates, "eurusd_rate": 1.10})
    return contracts, front, adjusted, harvest, cbot, eurusd


def test_contango_flag_correct() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()

    features = curve.build_curve_features(
        contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    assert features["ema_contango_flag"].iloc[1] == 1.0
    assert features["ema_backwardation_flag"].iloc[1] == 0.0


def test_basis_calculation() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()

    features = curve.build_curve_features(
        contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    expected_cbot_eur_t = (500.0 / 100.0) / 1.10 * curve.BUSHEL_TO_TONNE
    assert features["cbot_eur_t"].iloc[1] == expected_cbot_eur_t
    assert features["ema_cbot_basis"].iloc[1] == 200.0 - expected_cbot_eur_t


def test_shift1_applied_to_all_features() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()

    features = curve.build_curve_features(
        contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    assert features[curve.EMA_CURVE_FEATURE_COLUMNS].iloc[0].isna().all()
    assert features["ema_front_price"].iloc[1] == 200.0
    assert features["ema_second_price"].iloc[1] == 205.0


def test_no_future_leak() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs(periods=40)
    features_a = curve.build_curve_features(
        contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )
    future_changed = contracts.copy()
    future_changed.loc[future_changed["date"].eq(pd.Timestamp("2026-02-05")), "price"] += 500.0

    features_b = curve.build_curve_features(
        future_changed,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    cols = ["ema_second_price", "ema_curve_slope_3", "ema_roll_yield_ann"]
    pd.testing.assert_series_equal(features_a.loc[10, cols], features_b.loc[10, cols])


def test_output_columns_complete() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()

    features = curve.build_curve_features(
        contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    assert set(curve.EMA_CURVE_FEATURE_COLUMNS).issubset(features.columns)
    assert len(curve.EMA_CURVE_FEATURE_COLUMNS) >= 18


def test_adjusted_returns_use_adjusted_price() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()

    features = curve.build_curve_features(
        contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    expected = np.log(105.0 / 100.0)
    assert features["ema_front_return_5d_adjusted"].iloc[6] == expected


def test_single_contract_curve_features_are_nan_not_false_flat() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()
    one_contract = contracts[contracts["rank_by_expiry"].eq(1)].copy()

    features = curve.build_curve_features(
        one_contract,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    row = features.iloc[1]
    assert pd.isna(row["ema_spread_f0_f1"])
    assert pd.isna(row["ema_curve_slope_3"])
    assert pd.isna(row["ema_curve_slope_6"])
    assert pd.isna(row["ema_contango_flag"])
    assert pd.isna(row["ema_backwardation_flag"])
    assert pd.isna(row["ema_carry_front_second"])


def test_two_contract_curve_keeps_front_second_but_masks_third_slope() -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()
    two_contracts = contracts[contracts["rank_by_expiry"].le(2)].copy()

    features = curve.build_curve_features(
        two_contracts,
        front,
        harvest,
        cbot,
        eurusd,
        front_adjusted=adjusted,
    )

    row = features.iloc[1]
    assert row["ema_spread_f0_f1"] == -5.0
    assert row["ema_contango_flag"] == 1.0
    assert row["ema_backwardation_flag"] == 0.0
    assert pd.isna(row["ema_curve_slope_3"])
    assert pd.notna(row["ema_curve_slope_6"])


def test_build_and_save_curve_features(tmp_path) -> None:
    contracts, front, adjusted, harvest, cbot, eurusd = _inputs()
    curve_path = tmp_path / "curve.parquet"
    front_path = tmp_path / "front.parquet"
    adjusted_path = tmp_path / "front_adjusted.parquet"
    harvest_path = tmp_path / "harvest.parquet"
    cbot_path = tmp_path / "database.parquet"
    eurusd_path = tmp_path / "eurusd.csv"
    output_path = tmp_path / "ema_curve_features.parquet"
    contracts.to_parquet(curve_path, index=False)
    front.to_parquet(front_path, index=False)
    adjusted.to_parquet(adjusted_path, index=False)
    harvest.to_parquet(harvest_path, index=False)
    cbot.to_parquet(cbot_path, index=False)
    eurusd.to_csv(eurusd_path, index=False)

    features = curve.build_and_save_curve_features(
        curve_path=curve_path,
        front_raw_path=front_path,
        front_adjusted_path=adjusted_path,
        harvest_nov_path=harvest_path,
        cbot_path=cbot_path,
        eurusd_path=eurusd_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert len(pd.read_parquet(output_path)) == len(features)

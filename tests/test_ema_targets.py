from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.features.ema_targets import (
    EMA_TARGET_COLUMNS,
    assert_ema_targets_not_in_features,
    build_and_save_ema_targets,
    build_ema_targets,
    load_ema_storage_costs,
)


def _front_frame(n: int = 140) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame(
        {
            "date": dates,
            "price": np.linspace(200.0, 240.0, n),
            "adjusted_price": np.linspace(900.0, 800.0, n),
        }
    )


def _harvest_frame(n: int = 80) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame({"date": dates, "price": np.linspace(205.0, 215.0, n)})


def test_build_ema_targets_columns_and_tail_nans() -> None:
    targets = build_ema_targets(_front_frame(), _harvest_frame())

    assert list(targets.columns) == ["Date", *EMA_TARGET_COLUMNS]
    assert len(EMA_TARGET_COLUMNS) == 30
    assert targets["y_up_h20_ema"].tail(20).isna().all()
    assert targets["y_up_h20_ema_raw"].tail(20).isna().all()
    assert targets["y_up_h20_ema_adjusted"].tail(20).isna().all()
    assert targets["y_up_h20_ema_no_roll"].tail(20).isna().all()
    assert targets["target_crosses_roll_h20"].tail(20).isna().all()
    assert targets["y_price_h60_ema"].tail(60).isna().all()
    assert targets["y_price_h60_ema_raw"].tail(60).isna().all()
    assert targets["y_storage_value_6m"].tail(120).isna().all()
    assert targets["y_storage_value_6m_raw"].tail(120).isna().all()


def test_ema_targets_use_raw_price_not_adjusted_price() -> None:
    targets = build_ema_targets(_front_frame(), _harvest_frame(), storage_costs={"1m": 1.5, "3m": 4.5, "6m": 9.0})

    assert targets["y_up_h20_ema"].dropna().iloc[0] == 1.0
    assert targets["y_up_h20_ema_raw"].dropna().iloc[0] == 1.0
    assert targets["y_up_h20_ema_adjusted"].dropna().iloc[0] == 0.0
    assert targets["y_price_h20_ema"].iloc[0] == pytest.approx(_front_frame()["price"].iloc[20])
    assert targets["y_price_h20_ema_raw"].iloc[0] == pytest.approx(_front_frame()["price"].iloc[20])


def test_ema_no_roll_targets_are_masked_when_future_window_crosses_roll() -> None:
    front = _front_frame()
    front["roll_event"] = False
    front.loc[5, "roll_event"] = True

    targets = build_ema_targets(front, _harvest_frame())

    assert targets["target_crosses_roll_h20"].iloc[0] == 1.0
    assert targets["y_up_h20_ema_raw"].iloc[0] == 1.0
    assert pd.isna(targets["y_up_h20_ema_no_roll"].iloc[0])
    assert targets["target_crosses_roll_h20"].iloc[5] == 0.0
    assert targets["y_up_h20_ema_no_roll"].iloc[5] == 1.0


def test_storage_costs_are_deducted_and_profit_is_binary() -> None:
    front = _front_frame()
    targets = build_ema_targets(front, _harvest_frame(), storage_costs={"1m": 2.0, "3m": 7.0, "6m": 11.0})

    expected = front["price"].iloc[60] - front["price"].iloc[0] - 7.0
    assert targets["y_storage_value_3m"].iloc[0] == pytest.approx(expected)
    assert targets["y_storage_profit_3m"].dropna().isin([0.0, 1.0]).all()


def test_harvest_targets_are_built_from_harvest_series() -> None:
    harvest = _harvest_frame()
    harvest["price"] = 300.0
    harvest.loc[20:, "price"] = 250.0
    targets = build_ema_targets(_front_frame(), harvest)

    assert targets["y_up_h20_ema_harvest"].dropna().iloc[0] == 0.0


def test_assert_ema_targets_not_in_features_rejects_leakage() -> None:
    features = pd.DataFrame({"Date": pd.bdate_range("2024-01-01", periods=2), "y_up_h20_ema": [1.0, 0.0]})

    with pytest.raises(ValueError, match="EMA target leakage"):
        assert_ema_targets_not_in_features(features)


def test_load_storage_costs_and_save_targets(tmp_path) -> None:
    cfg = tmp_path / "decision.yaml"
    cfg.write_text(
        """
euronext_ema:
  storage_costs_eur_per_tonne:
    1m: 2.5
    3m: 6.5
""",
        encoding="utf-8",
    )
    front_path = tmp_path / "front.parquet"
    harvest_path = tmp_path / "harvest.parquet"
    output_path = tmp_path / "ema_targets.parquet"
    _front_frame().to_parquet(front_path, index=False)
    _harvest_frame().to_parquet(harvest_path, index=False)

    costs = load_ema_storage_costs(cfg)
    saved = build_and_save_ema_targets(
        front_raw_path=front_path,
        front_adjusted_path=None,
        harvest_nov_path=harvest_path,
        output_path=output_path,
        decision_config_path=cfg,
    )

    assert costs == {"1m": 2.5, "3m": 6.5, "6m": 9.0}
    assert output_path.exists()
    assert saved["y_storage_value_3m"].iloc[0] == pytest.approx(_front_frame()["price"].iloc[60] - _front_frame()["price"].iloc[0] - 6.5)

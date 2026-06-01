from __future__ import annotations

import numpy as np
import pandas as pd

from mais.features.euronext import (
    build_cross_market_features,
    build_ema_curve_features,
    build_ema_targets,
    build_euronext_master_features,
)


def test_build_ema_targets_no_feature_leakage_shape():
    ema = pd.DataFrame({"Date": pd.bdate_range("2024-01-01", periods=70), "ema_close": np.linspace(200, 230, 70)})

    targets = build_ema_targets(ema, horizons=(20, 40))

    assert "y_up_h20_ema" in targets.columns
    assert "y_price_h40_ema" in targets.columns
    assert targets["y_up_h40_ema"].tail(40).isna().all()


def test_cross_market_features_basis_and_lagged_zscore():
    dates = pd.bdate_range("2024-01-01", periods=60)
    ema = pd.DataFrame({"Date": dates, "ema_close": np.linspace(190, 210, 60)})
    cbot = pd.DataFrame({"Date": dates, "corn_close": np.linspace(500, 540, 60)})
    eurusd = pd.DataFrame({"Date": dates, "eurusd_rate": np.linspace(1.05, 1.10, 60)})

    features = build_cross_market_features(ema, cbot, eurusd)

    assert "cbot_ema_basis" in features.columns
    assert "cbot_ema_basis_zscore" in features.columns
    assert pd.isna(features["cbot_ema_basis_zscore"].iloc[0])
    assert features["cbot_ema_basis"].notna().all()


def test_ema_curve_features_spreads_flags():
    contracts = pd.DataFrame(
        {
            "Date": [pd.Timestamp("2024-01-01")] * 2,
            "contract_code": ["EMA_H2024", "EMA_M2024"],
            "settlement": [205.0, 207.0],
            "days_to_expiry": [60, 150],
            "volume": [100, 50],
        }
    )

    features = build_ema_curve_features(contracts)

    assert features["ema_near_deferred_spread"].iloc[0] == -2.0
    assert features["ema_contango_flag"].iloc[0] == 1


def test_euronext_master_features_data_availability():
    dates = pd.bdate_range("2024-01-01", periods=3)
    left = pd.DataFrame({"Date": dates, "ema_close": [200.0, 201.0, np.nan]})
    right = pd.DataFrame({"Date": dates, "eu_yield_estimate_tha": [7.2, np.nan, 7.1]})

    features = build_euronext_master_features([left, right], expected_sources=("ema", "eu"))

    assert "data_availability_score" in features.columns
    assert "ema_available" in features.columns
    assert "eu_available" in features.columns
    assert features["data_availability_score"].between(0, 1).all()

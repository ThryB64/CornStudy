from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

import mais.features as features_module
from mais.features.ema_features import (
    assert_no_ema_target_leakage,
    build_ema_features,
)


def test_build_ema_features_no_files_does_not_force_columns() -> None:
    dates = pd.bdate_range("2026-01-01", periods=3)
    continuous = pd.DataFrame({"Date": dates})

    result = build_ema_features(
        dates,
        curve_features=pd.DataFrame(),
        continuous_features=continuous,
    )

    assert result.columns.tolist() == ["Date"]


def test_build_ema_features_assembles_curve_and_continuous() -> None:
    dates = pd.bdate_range("2026-01-01", periods=3)
    curve = pd.DataFrame({
        "Date": dates,
        "ema_front_price": [np.nan, 200.0, 201.0],
        "ema_cbot_basis": [np.nan, 15.0, 16.0],
    })
    continuous = pd.DataFrame({
        "Date": dates,
        "ema_front_price_lag1": [np.nan, 199.0, 200.0],
    })

    result = build_ema_features(
        dates,
        curve_features=curve,
        continuous_features=continuous,
    )

    assert "ema_front_price" in result.columns
    assert "ema_front_price_lag1" in result.columns
    assert "ema_data_availability_score" in result.columns
    assert result["ema_curve_available"].tolist() == [0.0, 1.0, 1.0]
    assert result["ema_continuous_available"].tolist() == [0.0, 1.0, 1.0]


def test_ema_target_columns_rejected() -> None:
    frame = pd.DataFrame({
        "Date": pd.bdate_range("2026-01-01", periods=3),
        "y_ema_up_h20": [0, 1, 0],
    })

    with pytest.raises(AssertionError):
        assert_no_ema_target_leakage(frame)


def test_build_features_merges_ema_block_when_available(tmp_path, monkeypatch) -> None:
    dates = pd.bdate_range("2026-01-01", periods=30)
    interim = tmp_path / "interim"
    interim.mkdir()
    db = pd.DataFrame({
        "Date": dates,
        "corn_close": np.linspace(500.0, 530.0, len(dates)),
        "corn_high": np.linspace(501.0, 531.0, len(dates)),
        "corn_low": np.linspace(499.0, 529.0, len(dates)),
        "corn_volume": 1000.0,
    })
    db.to_parquet(interim / "database.parquet", index=False)

    def fake_ema_features(input_dates: pd.Series) -> pd.DataFrame:
        return pd.DataFrame({
            "Date": pd.to_datetime(input_dates),
            "ema_cbot_basis": np.arange(len(input_dates), dtype=float),
            "ema_data_availability_score": 1.0,
        })

    monkeypatch.setattr(features_module, "build_ema_features", fake_ema_features)

    result = features_module.build_features(interim_dir=interim, out=tmp_path / "features.parquet")

    assert "ema_cbot_basis" in result.columns
    assert "ema_data_availability_score" in result.columns
    assert result["ema_cbot_basis"].notna().all()


def test_build_features_skips_ema_when_no_block(tmp_path, monkeypatch) -> None:
    dates = pd.bdate_range("2026-01-01", periods=10)
    interim = tmp_path / "interim"
    interim.mkdir()
    pd.DataFrame({"Date": dates, "corn_close": np.linspace(500.0, 510.0, len(dates))}).to_parquet(
        interim / "database.parquet",
        index=False,
    )

    def fake_empty_ema(input_dates: pd.Series) -> pd.DataFrame:
        return pd.DataFrame({"Date": pd.to_datetime(input_dates)})

    monkeypatch.setattr(features_module, "build_ema_features", fake_empty_ema)

    result = features_module.build_features(interim_dir=interim, out=tmp_path / "features.parquet")

    assert "ema_cbot_basis" not in result.columns
    assert "ema_data_availability_score" not in result.columns


def test_factor_metadata_contains_euronext_curve_family() -> None:
    with open("config/factor_metadata.yaml", encoding="utf-8") as metadata_file:
        metadata = yaml.safe_load(metadata_file)
    family = next(item for item in metadata["families"] if item["name"] == "euronext_curve")

    assert family["n_feature_cols"] == 37
    assert family["source_quality"] == "exploratory"
    assert "shift(1)" in family["anti_leakage"]

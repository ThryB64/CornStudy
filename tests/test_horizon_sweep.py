from pathlib import Path

import numpy as np
import pandas as pd

from mais.features import build_multi_horizon_targets
from mais.research.horizon_sweep import (
    build_horizon_targets,
    identify_robust_zone,
    run_horizon_sweep,
    run_single_horizon,
)


def test_build_horizon_targets_anti_leakage_direction():
    prices = pd.DataFrame(
        {
            "Date": pd.bdate_range("2020-01-01", periods=6),
            "corn_close": [100.0, 110.0, 121.0, 100.0, 90.0, 99.0],
        }
    )

    targets = build_horizon_targets(prices, [2])

    expected = np.log(121.0 / 100.0)
    assert np.isclose(targets.loc[0, "y_cont_h2"], expected)
    assert targets.loc[0, "y_up_h2"] == 1.0
    assert targets["y_cont_h2"].tail(2).isna().all()


def test_feature_helper_builds_strong_move_targets():
    prices = pd.Series([100.0, 104.0, 98.0, 101.0])

    targets = build_multi_horizon_targets(prices, [1])

    assert {"y_up_gt_3pct_h1", "y_down_gt_3pct_h1"}.issubset(targets.columns)
    assert targets.loc[0, "y_up_gt_3pct_h1"] == 1.0
    assert targets.loc[1, "y_down_gt_3pct_h1"] == 1.0


def test_run_single_horizon_caps_dates_pre_2023(synthetic_features, synthetic_prices):
    features = synthetic_features.copy()
    # Add a simple predictive feature so the model has a stable numeric matrix.
    features["trend"] = np.arange(len(features), dtype=float)
    targets = build_horizon_targets(synthetic_prices[["Date", "corn_close"]], [5])

    result = run_single_horizon(features, targets, horizon=5, model_name="ridge_factors")

    assert result["horizon"] == 5
    assert result["n_obs_test"] >= 100
    assert result["max_train_or_test_date"] <= "2022-12-31"


def test_identify_robust_zone_requires_neighboring_horizons():
    rows = []
    for h in [1, 2, 3, 4, 5, 7]:
        rows.append(
            {
                "horizon": h,
                "model": "ridge_factors",
                "da": 0.62,
                "auc": 0.66,
                "n_obs_test": 120,
                "delta_da_vs_seasonal": 0.03,
            }
        )
        rows.append(
            {
                "horizon": h,
                "model": "seasonal_naive",
                "da": 0.55,
                "auc": 0.50,
                "n_obs_test": 120,
                "delta_da_vs_seasonal": 0.0,
            }
        )

    zone = identify_robust_zone(pd.DataFrame(rows))

    assert zone == [1, 2, 3, 4, 5, 7]


def test_run_horizon_sweep_writes_expected_outputs(
    synthetic_features,
    synthetic_prices,
    tmp_path: Path,
):
    results = run_horizon_sweep(
        synthetic_features,
        synthetic_prices[["Date", "corn_close"]],
        tmp_path,
        horizons=[1, 2, 3],
    )

    assert set(results["horizon"]) == {1, 2, 3}
    assert (tmp_path / "horizon_sweep_results.parquet").exists()
    assert (tmp_path / "horizon_sweep_results.csv").exists()
    assert (tmp_path / "horizon_sweep_zone.json").exists()
    assert (tmp_path / "horizon_sweep_curve.png").exists()
    assert (tmp_path / "horizon_sweep_report.txt").exists()

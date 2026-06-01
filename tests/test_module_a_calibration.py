from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.indicator.module_a_calibration import (
    calibrate_module_a_weights,
    fit_nonnegative_weights,
    prepare_weekly_signal_frame,
    run_module_a_calibration,
)


def _context_targets(n: int = 420) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2015-01-01", periods=n)
    signal = np.sin(np.arange(n) / 7)
    context = pd.DataFrame(
        {
            "Date": dates,
            "signal_bilan_mondial": signal,
            "signal_bilan_stocks_eu": signal * 0.8,
            "signal_crop_condition_eu": -signal * 0.2,
            "signal_brazil_supply_pressure": signal * 0.1,
            "signal_ukraine_corridor": 0.0,
            "signal_us_crop_condition": signal * 0.4,
            "signal_china_demand": signal * 0.3,
            "signal_wasde_surprise": signal,
            "signal_export_pace_eu": signal * 0.5,
            "signal_cot_positioning": signal * 0.2,
            "signal_futures_structure": signal * 0.6,
            "signal_eur_usd_competitive": signal * 0.4,
        }
    )
    targets = pd.DataFrame({"Date": dates, "y_up_h20_ema": (signal > 0).astype(float)})
    return context, targets


def test_fit_nonnegative_weights_sum_to_one() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(100, 4))
    y = (x[:, 0] > 0).astype(int)
    weights = fit_nonnegative_weights(x, y, n_random=20, rng=rng)

    assert np.isclose(weights.sum(), 1.0)
    assert (weights >= 0).all()


def test_prepare_weekly_signal_frame() -> None:
    context, targets = _context_targets()
    weekly, signal_cols = prepare_weekly_signal_frame(context, targets)

    assert weekly["Date"].is_monotonic_increasing
    assert signal_cols
    assert "y_up_h20_ema" in weekly.columns


def test_calibrate_module_a_weights_reports_delta() -> None:
    context, targets = _context_targets()
    weekly, signal_cols = prepare_weekly_signal_frame(context, targets)
    report = calibrate_module_a_weights(weekly, signal_cols, min_train_years=1, n_random=30)

    assert report["n_weekly"] > 0
    assert report["calibrated_da_weekly"] is not None
    assert np.isclose(sum(report["final_weights"].values()), 1.0)
    assert report["verdict"] in {"CALIBRATION_VALIDÉE", "CALIBRATION_GAIN_INSTABLE", "CALIBRATION_NEUTRE"}


def test_run_module_a_calibration_writes_json(tmp_path) -> None:
    dates = pd.bdate_range("2015-01-01", periods=420)
    x = np.sin(np.arange(len(dates)) / 7)
    features = pd.DataFrame(
        {
            "Date": dates,
            "wasde_stocks_to_use_calc_z": -x,
            "ema_cbot_basis_zscore_52w": -x,
            "crop_ge_zscore_seasonal": -x,
            "soy_close": -x,
            "drought_composite": x,
            "export_china_pct_total": x,
            "wasde_ending_stocks_surprise_vs_5y": -x,
            "export_sales_weekly_zscore": x,
            "cot_mm_pct_oi_percentile": np.where(x > 0, 20, 80),
            "ema_backwardation_flag": (x > 0).astype(float),
            "ema_contango_flag": (x < 0).astype(float),
            "cbot_eur_t": x,
        }
    )
    targets = pd.DataFrame({"Date": dates, "y_up_h20_ema": (x > 0).astype(float)})
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "targets.parquet"
    output_path = tmp_path / "module_a_calibration.json"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)

    report = run_module_a_calibration(
        features_path=features_path,
        targets_path=targets_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))["verdict"] == report["verdict"]

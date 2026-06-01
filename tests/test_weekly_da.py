from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from mais.research.weekly_da import compute_weekly_da, run_weekly_da_report


def _oof_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=40)
    y_true = np.tile([0, 1], 20)
    y_pred = y_true.copy()
    y_pred[1::5] = 1 - y_pred[1::5]
    return pd.DataFrame({"Date": dates, "y_true": y_true, "y_pred": y_pred, "score": y_pred * 2 - 1})


def _benchmark_fixture(seed: int = 11) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    corn_signal = rng.normal(size=n)
    ema_signal = 0.8 * corn_signal + rng.normal(scale=0.6, size=n)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": corn_signal,
            "ema_signal": ema_signal,
            "cbot_eur_t": ema_signal * 0.2,
            "ema_data_availability_score": 1.0,
        }
    )
    cbot_targets = pd.DataFrame({"Date": dates, "y_up_h20": (corn_signal > 0).astype(float)})
    ema_targets = pd.DataFrame(
        {
            "Date": dates,
            "y_up_h20_ema": (ema_signal > 0).astype(float),
            "y_up_h20_ema_harvest": (ema_signal > 0).astype(float),
        }
    )
    selected = ["corn_signal", "ema_signal", "cbot_eur_t"]
    return features, cbot_targets, ema_targets, selected


def test_compute_weekly_da_filters_one_point_per_week() -> None:
    report = compute_weekly_da(_oof_frame(), n_bootstrap=100)

    assert report["n_daily"] == 40
    assert report["n_weekly"] == 8
    assert 0 <= report["da_weekly"] <= 1
    assert report["da_weekly_ci95_lo"] <= report["da_weekly"] <= report["da_weekly_ci95_hi"]


def test_compute_weekly_da_flags_autocorr_when_daily_is_higher() -> None:
    dates = pd.bdate_range("2024-01-01", periods=20)
    y_true = np.ones(20, dtype=int)
    y_pred = np.ones(20, dtype=int)
    y_pred[::5] = 0
    oof = pd.DataFrame({"Date": dates, "y_true": y_true, "y_pred": y_pred})

    report = compute_weekly_da(oof, n_bootstrap=50)

    assert report["da_daily"] > report["da_weekly"]
    assert report["autocorr_flag"] is True


def test_compute_weekly_da_requires_columns() -> None:
    with pytest.raises(ValueError, match="Missing OOF prediction columns"):
        compute_weekly_da(pd.DataFrame({"Date": pd.bdate_range("2024-01-01", periods=2)}))


def test_run_weekly_da_report_writes_json(tmp_path) -> None:
    features, cbot_targets, ema_targets, selected = _benchmark_fixture()
    features_path = tmp_path / "features.parquet"
    cbot_targets_path = tmp_path / "targets.parquet"
    ema_targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "weekly_da_report.json"
    features.to_parquet(features_path, index=False)
    cbot_targets.to_parquet(cbot_targets_path, index=False)
    ema_targets.to_parquet(ema_targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    report = run_weekly_da_report(
        features_path=features_path,
        cbot_targets_path=cbot_targets_path,
        ema_targets_path=ema_targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        n_bootstrap=25,
    )

    assert output_path.exists()
    assert report["primary_ema_weekly"]["target_col"] == "y_up_h20_ema"
    assert report["primary_ema_weekly"]["n_weekly"] > 0

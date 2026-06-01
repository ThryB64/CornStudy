from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.ema_price_cqr_study import (
    build_price_feature_columns,
    build_price_frame,
    evaluate_price_intervals,
    run_ema_price_cqr_study,
    walk_forward_price_intervals,
    winkler_loss,
)


def _fixture(seed: int = 17) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    trend = np.linspace(160, 240, n)
    signal = np.sin(np.arange(n) / 25)
    price = trend + 8 * signal + rng.normal(scale=1.5, size=n)
    features = pd.DataFrame(
        {
            "Date": dates,
            "ema_front_price_lag1": pd.Series(price).shift(1).bfill(),
            "ema_cbot_basis": signal,
            "ema_cbot_basis_zscore_52w": signal / 2,
            "cbot_eur_t": price - 4 + rng.normal(scale=1.0, size=n),
            "ema_oi_total": 1000 + 50 * signal,
            "ema_data_availability_score": 1.0,
        }
    )
    targets = pd.DataFrame(
        {
            "Date": dates,
            "y_price_h20_ema_raw": pd.Series(price).shift(-20),
            "y_price_h60_ema_raw": pd.Series(price).shift(-60),
        }
    )
    selected = ["ema_front_price_lag1", "ema_cbot_basis", "cbot_eur_t", "ema_oi_total"]
    return features, targets, selected


def test_winkler_loss_penalises_misses() -> None:
    y = pd.Series([10.0, 20.0])
    lo = pd.Series([8.0, 12.0])
    hi = pd.Series([12.0, 18.0])

    score = winkler_loss(y, lo, hi, alpha=0.10)

    assert score.iloc[0] == 4.0
    assert score.iloc[1] > score.iloc[0]


def test_build_price_frame_adds_seasonal_baseline() -> None:
    features, targets, _selected = _fixture()

    frame = build_price_frame(
        features,
        targets,
        target_col="y_price_h20_ema_raw",
        max_date="2022-12-31",
        seasonal_lag=20,
    )

    assert "seasonal_naive_price" in frame.columns
    assert frame["seasonal_naive_price"].notna().sum() > 0
    assert frame["ema_data_availability_score"].min() > 0


def test_walk_forward_price_intervals_baseline_outputs_intervals() -> None:
    features, targets, _selected = _fixture()
    frame = build_price_frame(
        features,
        targets,
        target_col="y_price_h20_ema_raw",
        max_date="2022-12-31",
        seasonal_lag=20,
    )

    preds = walk_forward_price_intervals(
        frame,
        target_col="y_price_h20_ema_raw",
        model_name="naive_current",
        model_kind="baseline",
        point_col="ema_front_price_lag1",
        n_splits=2,
    )

    assert not preds.empty
    assert {"q_lo", "q_hi", "midpoint", "validation_year"}.issubset(preds.columns)
    assert (preds["q_hi"] >= preds["q_lo"]).all()


def test_evaluate_price_intervals_returns_coverage_and_winkler() -> None:
    dates = pd.bdate_range("2024-01-01", periods=5)
    preds = pd.DataFrame(
        {
            "Date": dates,
            "y_true": [10, 12, 14, 16, 18],
            "q_lo": [9, 10, 12, 14, 15],
            "q_hi": [11, 13, 15, 18, 17],
            "midpoint": [10, 11.5, 13.5, 16, 16],
        }
    )

    metrics = evaluate_price_intervals(preds, target_col="target", target_coverage=0.90)

    assert metrics["coverage"] == 0.8
    assert metrics["winkler_loss"] > 0
    assert metrics["sharpness_mean_width"] > 0


def test_run_ema_price_cqr_study_writes_outputs(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_json = tmp_path / "cqr.json"
    output_md = tmp_path / "cqr.md"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    payload = run_ema_price_cqr_study(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_json_path=output_json,
        output_markdown_path=output_md,
        seasonal_lag=20,
        n_splits=2,
        n_estimators=20,
    )

    assert output_json.exists()
    assert output_md.exists()
    assert payload["results"]
    assert payload["decision"]["verdict"] in {
        "CQR_PRICE_PROMISING",
        "CQR_PRICE_PARTIAL",
        "CQR_PRICE_NO_GO",
    }
    assert build_price_feature_columns(selected, build_price_frame(features, targets, target_col="y_price_h20_ema_raw", max_date="2022-12-31"))

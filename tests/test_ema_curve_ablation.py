from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.ema_curve_ablation import _recommendation, run_ema_curve_ablation


def _fixture(seed: int = 13) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    corn_signal = rng.normal(size=n)
    basis = rng.normal(size=n)
    y = (0.5 * corn_signal + basis > 0).astype(float)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": corn_signal,
            "ema_cbot_basis": basis,
            "ema_cbot_basis_zscore_52w": basis * 0.4 + rng.normal(scale=0.2, size=n),
            "ema_spread_f0_f1": rng.normal(size=n),
            "ema_curve_slope_3": rng.normal(size=n),
            "ema_oi_total": rng.normal(size=n),
            "ema_data_availability_score": 1.0,
        }
    )
    cbot_targets = pd.DataFrame({"Date": dates, "y_up_h20": y})
    ema_targets = pd.DataFrame(
        {
            "Date": dates,
            "y_up_h20_ema": y,
            "y_up_h20_ema_harvest": y,
        }
    )
    selected = ["corn_signal"]
    return features, cbot_targets, ema_targets, selected


def test_recommendation_thresholds() -> None:
    assert _recommendation(0.02) == "GARDER"
    assert _recommendation(-0.02) == "RETIRER"
    assert _recommendation(0.005) == "NEUTRE"
    assert _recommendation(None) == "NEUTRE"


def test_run_ema_curve_ablation_writes_json(tmp_path) -> None:
    features, cbot_targets, ema_targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    cbot_targets_path = tmp_path / "targets.parquet"
    ema_targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "ema_curve_ablation.json"
    features.to_parquet(features_path, index=False)
    cbot_targets.to_parquet(cbot_targets_path, index=False)
    ema_targets.to_parquet(ema_targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    report = run_ema_curve_ablation(
        features_path=features_path,
        cbot_targets_path=cbot_targets_path,
        ema_targets_path=ema_targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        n_bootstrap=10,
    )

    assert output_path.exists()
    assert report["baseline"]["feature_set"] == "cbot_only"
    assert any(row["family"] == "basis_cbot" for row in report["families"])
    assert all("bh_q_value" in row for row in report["families"])


def test_ablation_classifies_helpful_family(tmp_path) -> None:
    features, cbot_targets, ema_targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    cbot_targets_path = tmp_path / "targets.parquet"
    ema_targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "ema_curve_ablation.json"
    features.to_parquet(features_path, index=False)
    cbot_targets.to_parquet(cbot_targets_path, index=False)
    ema_targets.to_parquet(ema_targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    report = run_ema_curve_ablation(
        features_path=features_path,
        cbot_targets_path=cbot_targets_path,
        ema_targets_path=ema_targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        n_bootstrap=10,
    )
    basis = next(row for row in report["families"] if row["family"] == "basis_cbot")

    assert basis["delta_da"] > 0
    assert basis["recommendation"] in {"GARDER", "NEUTRE"}

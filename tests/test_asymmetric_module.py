from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.indicator.direction import MaizeDirectionIndicator
from mais.research.asymmetric_module import (
    assign_asymmetric_actions,
    calibrate_asymmetric_thresholds,
    evaluate_asymmetric_module,
)


def _synthetic_frame(n: int = 140) -> pd.DataFrame:
    dates = pd.date_range("2015-01-05", periods=n, freq="7D")
    x_down = np.r_[np.linspace(-2.0, 2.0, n // 2), np.linspace(2.0, -2.0, n - n // 2)]
    x_up = np.sin(np.linspace(0.0, 8.0 * np.pi, n))
    down_target = (x_down > 0.45).astype(int)
    up_target = (x_up > 0.35).astype(int)
    return pd.DataFrame(
        {
            "Date": dates,
            "x_down": x_down,
            "x_up": x_up,
            "x_noise": np.cos(np.linspace(0.0, 3.0 * np.pi, n)),
            "y_down_gt_5pct_h40": down_target,
            "y_up_gt_5pct_h40": up_target,
            "move_cents_h40": np.where(down_target == 1, -24.0, np.where(up_target == 1, 20.0, 2.0)),
        }
    )


def test_downside_score_auc_documented():
    _, metrics = evaluate_asymmetric_module(_synthetic_frame(), feature_cols=["x_down", "x_up", "x_noise"])

    assert metrics["downside_auc"] is not None
    assert metrics["downside_auc"] >= 0.65
    assert len(metrics["downside_auc_ci95"]) == 2


def test_upside_score_auc_documented():
    _, metrics = evaluate_asymmetric_module(_synthetic_frame(), feature_cols=["x_down", "x_up", "x_noise"])

    assert metrics["upside_auc"] is not None
    assert metrics["upside_auc"] >= 0.65
    assert len(metrics["upside_auc_ci95"]) == 2


def test_scores_not_identical():
    scored, _ = evaluate_asymmetric_module(_synthetic_frame(), feature_cols=["x_down", "x_up", "x_noise"])

    different = (scored["downside_risk_score"].round(6) != scored["upside_opportunity_score"].round(6)).mean()
    assert different >= 0.80


def test_thresholds_calibrated():
    scored, metrics = evaluate_asymmetric_module(_synthetic_frame(), feature_cols=["x_down", "x_up", "x_noise"])
    thresholds, curve = calibrate_asymmetric_thresholds(scored)
    actions = assign_asymmetric_actions(
        scored["downside_risk_score"],
        scored["upside_opportunity_score"],
        thresholds=thresholds,
    )

    assert metrics["thresholds"]["lambda_value"] in {1.5, 2.0, 2.5, 3.0}
    assert metrics["thresholds"]["threshold_up"] != 0.60
    assert curve
    assert set(actions.unique()) <= {"VENDRE_MAINTENANT", "STOCKER", "VENDRE_PARTIEL_50PCT", "ATTENDRE"}


def test_economic_evaluation_documented(tmp_path):
    output_path = tmp_path / "asymmetric_results.json"
    _, metrics = evaluate_asymmetric_module(
        _synthetic_frame(),
        feature_cols=["x_down", "x_up", "x_noise"],
        output_path=output_path,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert "perte_evitee_mean" in metrics["economic_evaluation"]
    assert "gain_manque_mean" in metrics["economic_evaluation"]
    assert "regret_moyen" in metrics["economic_evaluation"]
    assert payload["economic_evaluation"]["by_crop_year"]


def test_direction_signal_exposes_asymmetric_scores():
    down, up = MaizeDirectionIndicator._asymmetric_scores(
        {5: 0.62, 10: 0.64, 20: 0.66, 30: 0.65},
        {20: 0.41, 30: 0.36},
        {20: 0.18, 30: 0.20},
    )

    assert 0.0 <= down <= 1.0
    assert 0.0 <= up <= 1.0
    assert up > down

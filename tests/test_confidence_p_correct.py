from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd
import pytest

from mais.indicator.calibration import fit_p_correct_model as indicator_fit_p_correct_model
from mais.research.p_correct_model import (
    META_FEATURES,
    build_p_correct_frame,
    fit_p_correct_model,
    validate_meta_features_no_leakage,
)


def _synthetic_consensus(n: int = 96) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2015-01-05", periods=n, freq="7D")
    angle = np.linspace(0.0, 8.0 * np.pi, n)
    proba = 0.5 + 0.42 * np.sin(angle)
    disagreement = 0.02 + 0.10 * (np.cos(angle) + 1.0) / 2.0
    pred_up = (proba >= 0.5).astype(int)
    direction_correct = ((np.abs(proba - 0.5) * 2.0 > 0.45) & (disagreement < 0.09)).astype(int)
    actual_up = np.where(direction_correct == 1, pred_up, 1 - pred_up)
    consensus = pd.DataFrame(
        {
            "Date": dates,
            "consensus_proba": proba,
            "disagreement": disagreement,
            "actual_up_majority": actual_up,
            "signal": np.where(pred_up == 1, "BULLISH", "BEARISH"),
            "regime_score": np.sin(angle / 2.0),
            "days_since_wasde": np.arange(n) % 30,
            "wasde_surprise_abs": np.abs(np.cos(angle)),
            "cot_extreme_flag": (np.arange(n) % 11 == 0).astype(int),
        }
    )
    profitability = pd.DataFrame(
        {
            "Date": dates,
            "gain_net_signal": np.where((direction_correct == 1) & (disagreement < 0.075), 14.0, -6.0),
        }
    )
    return consensus, profitability


def test_build_p_correct_frame_creates_two_targets():
    consensus, profitability = _synthetic_consensus()

    frame = build_p_correct_frame(consensus, profitability=profitability)

    assert "y_direction_correct" in frame.columns
    assert "y_decision_profitable" in frame.columns
    assert set(frame["y_direction_correct"].unique()) == {0, 1}
    assert set(frame["y_decision_profitable"].unique()) == {0, 1}


def test_fit_direction_p_correct_model_returns_calibration_metrics():
    consensus, profitability = _synthetic_consensus()
    frame = build_p_correct_frame(consensus, profitability=profitability)

    model, metrics, reliability = fit_p_correct_model(frame, target_col="y_direction_correct")
    p_correct = model.predict_proba(frame)

    assert np.all((p_correct >= 0.0) & (p_correct <= 1.0))
    assert metrics["target"] == "y_direction_correct"
    assert metrics["ece"] < 0.35
    assert metrics["brier_score"] < 0.35
    assert not reliability.empty


def test_fit_decision_profitable_model_is_separate_target():
    consensus, profitability = _synthetic_consensus()
    frame = build_p_correct_frame(consensus, profitability=profitability)

    _, metrics, _ = fit_p_correct_model(frame, target_col="y_decision_profitable")

    assert metrics["target"] == "y_decision_profitable"
    assert metrics["n_train"] > metrics["n_eval"]


def test_indicator_calibration_exposes_fit_p_correct_model():
    consensus, profitability = _synthetic_consensus()
    frame = build_p_correct_frame(consensus, profitability=profitability)

    _, metrics, _ = indicator_fit_p_correct_model(frame, target_col="y_direction_correct")

    assert metrics["features"] == list(META_FEATURES)


def test_p_correct_outputs_are_serializable(tmp_path):
    consensus, profitability = _synthetic_consensus()
    frame = build_p_correct_frame(consensus, profitability=profitability)
    model_path = tmp_path / "p_correct_model.pkl"
    reliability_path = tmp_path / "reliability_curve.json"

    fit_p_correct_model(
        frame,
        target_col="y_direction_correct",
        output_model_path=model_path,
        output_reliability_path=reliability_path,
    )

    with model_path.open("rb") as file:
        loaded = pickle.load(file)
    payload = json.loads(reliability_path.read_text(encoding="utf-8"))
    assert loaded.features == META_FEATURES
    assert payload["target"] == "y_direction_correct"
    assert "reliability_curve" in payload


def test_leakage_prone_meta_features_are_rejected():
    with pytest.raises(ValueError, match="Forbidden leakage-prone"):
        validate_meta_features_no_leakage(["prob_distance", "gain_net_signal"])

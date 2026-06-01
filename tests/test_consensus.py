import json

import pandas as pd

from mais.indicator.consensus import (
    compute_consensus_score,
    decide_signal_with_consensus,
    run_consensus_from_model_zoo,
    vote_pondere,
    zone_labels,
)
from mais.indicator.direction import MaizeDirectionIndicator


def test_disagreement_forces_uncertain():
    decision = decide_signal_with_consensus(
        {20: 0.82, 25: 0.18, 30: 0.78},
        confidence=0.90,
        auc_weights={20: 0.65, 25: 0.65, 30: 0.65},
        main_horizon=20,
        disagreement_threshold=0.08,
    )

    assert decision["consensus"]["disagreement"] > 0.08
    assert decision["label"] == "UNCERTAIN"


def test_direction_label_uses_consensus_disagreement_guardrail():
    indicator = MaizeDirectionIndicator(
        calibrated_preds=pd.DataFrame(),
        shap_df=pd.DataFrame(),
        config={
            "signal_rules": {
                "uncertain_confidence_threshold": 0.35,
                "bullish_prob_threshold": 0.60,
                "bearish_prob_threshold": 0.60,
                "min_prob_gap": 0.15,
                "neutral_max_gap": 0.10,
            },
            "confidence": {"version": "v4", "threshold": 0.35},
            "confidence_score": {},
            "consensus": {"enabled": True, "disagreement_threshold": 0.08},
        },
    )
    consensus = compute_consensus_score(
        {20: 0.82, 25: 0.18, 30: 0.78},
        auc_weights={20: 0.65, 25: 0.65, 30: 0.65},
        main_horizon=20,
    )

    assert indicator._label({20: 0.82, 25: 0.18, 30: 0.78}, 0.90, consensus) == "UNCERTAIN"


def test_consensus_score_bounds():
    result = compute_consensus_score(
        {10: 0.61, 15: 0.63, 20: 0.66, 25: None, 30: 0.64},
        auc_weights={10: 0.60, 15: 0.62, 20: 0.66, 30: 0.64},
        main_horizon=20,
    )

    assert 0.0 <= result["consensus_score"] <= 1.0
    assert result["n_horizons"] == 4
    assert result["consensus_direction"] == "BULLISH"


def test_zone_labels_coherence():
    labels = zone_labels({18: 0.61, 20: 0.62, 22: 0.60, 25: 0.59, 28: 0.63, 30: 0.64})

    assert labels["Z3_mensuel"] == "BULLISH"


def test_no_future_data_in_auc_weights_and_outputs(tmp_path):
    model_zoo_dir = tmp_path / "model_zoo"
    output_dir = tmp_path / "indicator"
    model_zoo_dir.mkdir()
    oof = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2021-01-01", "2021-01-01", "2023-01-02"]),
            "horizon": [5, 10, 5],
            "fold": [0, 0, 1],
            "model": ["ridge", "ridge", "ridge"],
            "p_up": [0.62, 0.64, 0.99],
            "y_true_up": [1, 1, 0],
        }
    )
    results = pd.DataFrame(
        {
            "horizon": [5, 10],
            "model": ["ridge", "ridge"],
            "auc": [0.61, 0.63],
            "da": [0.60, 0.62],
            "da_top20pct": [0.70, 0.72],
        }
    )
    oof.to_parquet(model_zoo_dir / "model_zoo_oof_predictions.parquet", index=False)
    results.to_parquet(model_zoo_dir / "model_zoo_results.parquet", index=False)
    (model_zoo_dir / "model_zoo_selected_models.json").write_text(
        json.dumps(["ridge"]),
        encoding="utf-8",
    )

    consensus = run_consensus_from_model_zoo(
        model_zoo_dir=model_zoo_dir,
        output_dir=output_dir,
        max_date=pd.Timestamp("2022-12-31"),
        main_horizon=5,
    )

    assert consensus["Date"].max() <= pd.Timestamp("2022-12-31")
    assert vote_pondere({5: 0.60, 10: 0.70}, {5: 0.61, 10: 0.63}) > 0.60
    assert (output_dir / "consensus_results.parquet").exists()
    assert (output_dir / "consensus_metafeatures.parquet").exists()
    assert (output_dir / "consensus_seuils_calibration.yaml").exists()

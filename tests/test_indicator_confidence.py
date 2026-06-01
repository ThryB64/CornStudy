import numpy as np
import pandas as pd

from mais.indicator.calibration import PlattCalibrator
from mais.indicator.direction import MaizeDirectionIndicator
from mais.indicator.persistence import compute_signal_stability_rolling
from mais.research.confidence_study import compute_adaptive_threshold


def test_signal_stability_non_zero():
    signals = pd.Series(["BULLISH", "BULLISH", "UNCERTAIN", "BEARISH"])

    stability = compute_signal_stability_rolling(signals, window=5, initial_value=0.5)

    assert stability.iloc[0] == 0.5
    assert (stability > 0.0).all()
    assert stability.between(0.0, 1.0).all()


def test_indicator_confidence_uses_neutral_stability_default():
    indicator = MaizeDirectionIndicator(
        calibrated_preds=pd.DataFrame(),
        shap_df=pd.DataFrame(),
        config={
            "signal_rules": {"uncertain_confidence_threshold": 0.35},
            "confidence_score": {
                "probability_distance_weight": 0.30,
                "model_agreement_weight": 0.25,
                "interval_width_weight": 0.25,
                "signal_stability_weight": 0.20,
                "signal_stability_init": 0.5,
            },
            "confidence": {"version": "v1", "threshold": 0.35, "signal_stability_init": 0.5},
        },
    )

    _, _, _, stability = indicator._compute_confidence_components(
        {5: 0.61, 10: 0.60, 20: 0.62, 30: 0.59},
        avg_width=0.10,
    )

    assert stability == 0.5


def test_adaptive_threshold_gives_signals():
    scores = pd.Series(np.linspace(0.20, 0.80, 260))

    threshold = compute_adaptive_threshold(scores, target_pct=0.30)
    signals_per_year = int((scores >= threshold).sum())

    assert 0.25 <= threshold <= 0.55
    assert signals_per_year >= 20


def test_platt_outputs_valid_probabilities():
    y_prob = np.linspace(0.05, 0.95, 100)
    y_true = (y_prob > 0.5).astype(float)

    calibrated = PlattCalibrator(c=1.0).fit(y_prob, y_true).transform(y_prob)

    assert np.isfinite(calibrated).all()
    assert ((calibrated >= 0.0) & (calibrated <= 1.0)).all()


def test_confidence_v4_bounds_and_no_da_regression_fixture():
    probs = pd.Series([0.62, 0.61, 0.39, 0.38, 0.59, 0.41])
    y_true = pd.Series([1, 1, 0, 0, 1, 0], dtype=float)
    confidence = pd.Series(
        [
            MaizeDirectionIndicator._compute_confidence_v4(
                auc_contexte=0.655,
                accord_modeles=0.75,
                prob_up_raw=float(p),
                cqr_width_norm=0.40,
                signal_stability=0.75,
            )
            for p in probs
        ]
    )
    selected = confidence >= 0.35
    da = ((probs[selected] > 0.5) == (y_true[selected] > 0.5)).mean()

    assert confidence.between(0.0, 1.0).all()
    assert da >= 0.595

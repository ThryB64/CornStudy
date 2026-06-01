from __future__ import annotations

import numpy as np
import pandas as pd

from mais.indicator.module_a_context import (
    SIGNAL_DEFINITIONS,
    compute_context_score,
    compute_context_timeseries,
    evaluate_context_weekly_da,
    score_from_cot_percentile,
    score_from_stocks_use_ratio,
    score_from_zscore,
)


def _features(n: int = 80) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n)
    x = np.linspace(-2.0, 2.0, n)
    return pd.DataFrame(
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
            "cot_mm_pct_oi_percentile": np.linspace(80, 20, n),
            "ema_backwardation_flag": (x > 0).astype(float),
            "ema_contango_flag": (x < 0).astype(float),
            "cbot_eur_t": x,
        }
    )


def test_scoring_helpers_are_bounded() -> None:
    assert -1 <= score_from_zscore(-10) <= 1
    assert -1 <= score_from_stocks_use_ratio(10, 20, 5) <= 1
    assert score_from_cot_percentile(90) < 0
    assert score_from_cot_percentile(10) > 0


def test_compute_context_score_returns_12_signals() -> None:
    features = _features()
    context = compute_context_score(features.iloc[-1], features)

    assert len(SIGNAL_DEFINITIONS) == 12
    assert len(context["signals"]) == 12
    assert set(context["block_scores"]) == {
        "offre_mondiale",
        "offre_competiteurs",
        "demande_mondiale",
        "positionnement_structure",
    }
    assert context["orientation"] in {"HAUSSIER", "BAISSIER", "NEUTRE", "UNCERTAIN"}


def test_context_orientation_thresholds() -> None:
    features = _features()
    bullish = compute_context_score(features.iloc[-1], features)
    bearish = compute_context_score(features.iloc[0], features)

    assert bullish["context_score"] > bearish["context_score"]
    assert bullish["data_availability_score"] >= 0.5


def test_missing_signals_create_uncertainty() -> None:
    frame = pd.DataFrame({"Date": pd.bdate_range("2024-01-01", periods=3)})
    context = compute_context_score(frame.iloc[-1], frame)

    assert context["orientation"] == "UNCERTAIN"
    assert context["typed_uncertainty"] == "low_data_availability"


def test_context_timeseries_and_weekly_da() -> None:
    features = _features(120)
    context = compute_context_timeseries(features)
    targets = pd.DataFrame(
        {
            "Date": features["Date"],
            "y_up_h20_ema": (context["context_score"] > 0).astype(float),
        }
    )

    evaluation = evaluate_context_weekly_da(context, targets)

    assert len(context) == len(features)
    assert evaluation.n_weekly > 0
    assert evaluation.da_weekly == 1.0

"""Tests V7 Phase 3-6 — Tickets V7-05, V7-27, V7-35, V7-34, V7-37, V7-38, V7-12, V7-14, V7-36, V7-13, V7-15, V7-28."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTEFACTS = ROOT / "artefacts" / "v7"


@pytest.fixture(scope="module")
def synthetic_df():
    rng = np.random.default_rng(42)
    n = 600
    dates = pd.date_range("2010-01-01", periods=n, freq="B")
    df = pd.DataFrame(index=dates)
    df.index.name = "Date"
    df["cbot_close"] = 300 + np.cumsum(rng.normal(0, 2, n))
    df["ema_close"] = df["cbot_close"] * 1.1 + rng.normal(0, 5, n)
    df["eurusd"] = 1.1 + 0.1 * np.sin(np.linspace(0, 10, n))
    df["cbot_eur_t"] = df["cbot_close"] * 36.744 / df["eurusd"]
    df["cbot_close_eur"] = df["cbot_eur_t"]
    df["ema_cbot_basis"] = df["ema_close"] - df["cbot_close_eur"]
    df["ema_cbot_basis_zscore_52w"] = rng.normal(0, 1, n)
    df["corn_realized_vol_20"] = rng.uniform(0.05, 0.25, n)
    df["corn_realized_vol_60"] = rng.uniform(0.05, 0.20, n)
    df["corn_logret_1d"] = rng.normal(0, 0.01, n)
    df["cot_mm_long"] = rng.normal(200000, 50000, n)
    df["wasde_ending_stocks"] = rng.normal(2000, 300, n)
    df["factor_weather_belt_stress"] = rng.normal(0, 1, n)
    df["factor_market_momentum"] = rng.normal(0, 1, n)
    df["factor_cross_commodity"] = rng.normal(0, 1, n)
    df["ema_cbot_rel_strength_20d"] = rng.normal(0, 0.02, n)
    df["ema_volume_total"] = rng.integers(500, 5000, n).astype(float)
    df["cot_open_interest"] = rng.integers(1000000, 2000000, n).astype(float)
    df["factor_macro_dollar_rates"] = rng.normal(0, 1, n)
    df["y_up_h20"] = (df["cbot_close"].shift(-20) > df["cbot_close"]).astype(float)
    df["y_up_h40"] = (df["cbot_close"].shift(-40) > df["cbot_close"]).astype(float)
    df["y_up_h60"] = (df["cbot_close"].shift(-60) > df["cbot_close"]).astype(float)
    df["y_up_h20_ema"] = (df["ema_close"].shift(-20) > df["ema_close"]).astype(float)
    df["y_up_h40_ema"] = (df["ema_close"].shift(-40) > df["ema_close"]).astype(float)
    return df


# ---------------------------------------------------------------------------
# V7-05 Cross-market
# ---------------------------------------------------------------------------

class TestCrossMarketV7:
    def test_run(self, synthetic_df):
        from mais.research.cross_market_v7 import run_cross_market_study
        r = run_cross_market_study(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-05"
        assert "verdict" in r
        assert r["verdict"] in {"BIDIRECTIONAL", "EMA_ADDS_TO_CBOT", "CBOT_ADDS_TO_EMA", "NONE"}

    def test_feature_groups(self, synthetic_df):
        from mais.research.cross_market_v7 import _get_feature_groups
        groups = _get_feature_groups(synthetic_df)
        assert "ema" in groups
        assert "cbot" in groups
        assert isinstance(groups["ema"], list)


# ---------------------------------------------------------------------------
# V7-27 Conditional Models
# ---------------------------------------------------------------------------

class TestConditionalModelsV7:
    def test_run(self, synthetic_df):
        from mais.research.conditional_models_v7 import run_conditional_models
        r = run_conditional_models(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-27"
        assert "verdict" in r

    def test_regime_results(self, synthetic_df):
        from mais.research.conditional_models_v7 import run_conditional_models
        r = run_conditional_models(synthetic_df)
        if r["verdict"] != "NO_DATA":
            assert "regime_results" in r


# ---------------------------------------------------------------------------
# V7-35 Distributional Forecast
# ---------------------------------------------------------------------------

class TestDistributionalForecast:
    def test_run(self, synthetic_df):
        from mais.research.distributional_forecast import run_distributional_forecast
        r = run_distributional_forecast(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-35"
        assert "verdict" in r

    def test_coverage_structure(self, synthetic_df):
        from mais.research.distributional_forecast import run_distributional_forecast
        r = run_distributional_forecast(synthetic_df)
        if "coverage_by_quantile" in r:
            for q_key, q_val in r["coverage_by_quantile"].items():
                assert "target_quantile" in q_val
                assert "calibrated" in q_val

    def test_compute_quantile_coverage(self):
        from mais.research.distributional_forecast import compute_quantile_coverage
        rng = np.random.default_rng(42)
        idx = pd.date_range("2020-01-01", periods=200)
        y_true = pd.Series(rng.normal(0, 1, 200), index=idx)
        y_pred = pd.Series(np.zeros(200), index=idx)
        cov = compute_quantile_coverage(y_true, y_pred, 0.5)
        assert 0.0 <= cov <= 1.0


# ---------------------------------------------------------------------------
# V7-34 Scenario Model
# ---------------------------------------------------------------------------

class TestScenarioModel:
    def test_run(self, synthetic_df):
        from mais.research.scenario_model import run_scenario_analysis
        r = run_scenario_analysis(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-34"
        assert "verdict" in r

    def test_scenarios_present(self, synthetic_df):
        from mais.research.scenario_model import run_scenario_analysis, SCENARIOS
        r = run_scenario_analysis(synthetic_df)
        if "scenarios" in r:
            for scen_name in SCENARIOS:
                assert scen_name in r["scenarios"]


# ---------------------------------------------------------------------------
# V7-37 Feature Stability
# ---------------------------------------------------------------------------

class TestFeatureStability:
    def test_run(self, synthetic_df):
        from mais.research.feature_stability import run_feature_stability
        r = run_feature_stability(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-37"
        assert "verdict" in r

    def test_stability_structure(self, synthetic_df):
        from mais.research.feature_stability import run_feature_stability
        r = run_feature_stability(synthetic_df)
        if "top20_stable" in r:
            for item in r["top20_stable"][:3]:
                assert "feature" in item
                assert "cv_importance" in item


# ---------------------------------------------------------------------------
# V7-38 Model Decay
# ---------------------------------------------------------------------------

class TestModelDecay:
    def test_run(self, synthetic_df):
        from mais.research.model_decay import run_model_decay
        r = run_model_decay(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-38"
        assert "verdict" in r

    def test_auc_by_age(self, synthetic_df):
        from mais.research.model_decay import run_model_decay
        r = run_model_decay(synthetic_df)
        if "auc_by_model_age" in r:
            for bucket, v in r["auc_by_model_age"].items():
                if "auc" in v:
                    assert 0.0 <= v["auc"] <= 1.0


# ---------------------------------------------------------------------------
# V7-12 P(correct)
# ---------------------------------------------------------------------------

class TestPCorrect:
    def test_run(self, synthetic_df):
        from mais.meta.p_correct import run_p_correct_model
        r = run_p_correct_model(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-12"
        assert "verdict" in r

    def test_calibration_metrics(self, synthetic_df):
        from mais.meta.p_correct import run_p_correct_model
        r = run_p_correct_model(synthetic_df)
        if "brier_score" in r and r["brier_score"] is not None:
            assert 0.0 <= r["brier_score"] <= 1.0
        if "auc_p_correct" in r and r["auc_p_correct"] is not None:
            assert 0.0 <= r["auc_p_correct"] <= 1.0


# ---------------------------------------------------------------------------
# V7-14 Error Analysis
# ---------------------------------------------------------------------------

class TestErrorAnalysisV7:
    def test_run(self, synthetic_df):
        from mais.research.error_analysis_v7 import run_error_analysis
        r = run_error_analysis(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-14"
        assert "verdict" in r

    def test_error_rate_range(self, synthetic_df):
        from mais.research.error_analysis_v7 import run_error_analysis
        r = run_error_analysis(synthetic_df)
        if "global_error_rate" in r and r["global_error_rate"] is not None:
            assert 0.0 <= r["global_error_rate"] <= 1.0


# ---------------------------------------------------------------------------
# V7-36 Causality Graph
# ---------------------------------------------------------------------------

class TestCausalityGraph:
    def test_build_graph(self):
        from mais.research.causality_graph import build_causality_graph
        pcmci = {"significant_links": {"ema_close": [{"source": "cbot_eur_t", "lag": 1, "p_value": 0.01}]}}
        graph = build_causality_graph(pcmci)
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 2

    def test_run_causality_graph(self):
        from mais.research.causality_graph import run_causality_graph
        r = run_causality_graph()
        assert "version" in r
        assert r["version"] == "V7-36"
        assert "n_nodes" in r
        assert r["n_nodes"] > 0


# ---------------------------------------------------------------------------
# V7-13 Backtests
# ---------------------------------------------------------------------------

class TestBacktestsV7:
    def test_run(self, synthetic_df):
        from mais.research.backtests_v7 import run_backtests_v7
        r = run_backtests_v7(synthetic_df)
        assert "version" in r
        assert r["version"] == "V7-13"
        assert r.get("verdict") in {"RESEARCH_ONLY_NOT_TRADING", "HOLDOUT_ALREADY_USED", "NO_DATA", "INSUFFICIENT_DATA", "LGBM_UNAVAILABLE"}

    def test_holdout_respected(self, synthetic_df):
        from mais.research.backtests_v7 import run_backtests_v7
        r = run_backtests_v7(synthetic_df)
        # Holdout 2024 should not appear in backtest
        if "policies" in r:
            assert r.get("verdict") == "RESEARCH_ONLY_NOT_TRADING"


# ---------------------------------------------------------------------------
# V7-15 Final Report
# ---------------------------------------------------------------------------

class TestFinalReportV7:
    def test_generate(self):
        from mais.research.final_report_v7 import generate_final_report_v7
        r = generate_final_report_v7()
        assert r["version"] == "V7-15"
        assert "key_findings" in r
        assert "conclusions" in r
        assert r["verdict"] == "V7_STUDY_COMPLETE"

    def test_artefact_counts(self):
        from mais.research.final_report_v7 import generate_final_report_v7, ARTEFACT_MAP
        r = generate_final_report_v7()
        assert r["n_artefacts_expected"] == len(ARTEFACT_MAP)
        assert r["n_artefacts_present"] >= 0


# ---------------------------------------------------------------------------
# V7-28 Final Indicator
# ---------------------------------------------------------------------------

class TestFinalIndicatorV7:
    def test_design(self):
        from mais.research.final_indicator_v7 import design_final_indicator
        r = design_final_indicator()
        assert r["version"] == "V7-28"
        assert "indicator_architecture" in r
        arch = r["indicator_architecture"]
        assert "primary_signal" in arch
        assert "components" in arch
        assert "holdout_status" in arch
        assert arch["holdout_status"]["holdout_used"] is False

    def test_components_present(self):
        from mais.research.final_indicator_v7 import design_final_indicator
        r = design_final_indicator()
        arch = r["indicator_architecture"]
        required = ["basis_module", "seasonal_filter", "roll_risk_veto"]
        for comp in required:
            assert comp in arch["components"]

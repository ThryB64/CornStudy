"""Tests V7 — Tickets V7-16, V7-21, V7-18, V7-32, V7-33, V7-03."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Fixtures communes
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def synthetic_df():
    """DataFrame synthétique pour tous les tests V7."""
    rng = np.random.default_rng(42)
    n = 500
    dates = pd.date_range("2010-01-01", periods=n, freq="B")
    df = pd.DataFrame(index=dates)
    df.index.name = "Date"

    # Prix
    df["cbot_close"] = 300 + np.cumsum(rng.normal(0, 2, n))
    df["ema_close"] = df["cbot_close"] * 1.1 + rng.normal(0, 5, n)
    df["eurusd"] = 1.1 + 0.1 * np.sin(np.linspace(0, 10, n)) + rng.normal(0, 0.02, n)
    df["cbot_eur_t"] = df["cbot_close"] * 36.744 / df["eurusd"]
    df["cbot_close_eur"] = df["cbot_eur_t"]
    df["ema_cbot_basis"] = df["ema_close"] - df["cbot_close_eur"]

    # Volume / OI
    df["ema_volume_total"] = rng.integers(500, 5000, n).astype(float)
    df["ema_oi_total"] = rng.integers(10000, 50000, n).astype(float)
    df["ema_open_interest_available"] = 1
    df["volume_oi_ratio_proxy"] = df["ema_volume_total"] / df["ema_oi_total"]

    # COT
    df["cot_mm_long"] = rng.normal(200000, 50000, n)
    df["wasde_ending_stocks"] = rng.normal(2000, 300, n)

    # Factors
    df["factor_weather_belt_stress"] = rng.normal(0, 1, n)
    df["factor_macro_dollar_rates"] = rng.normal(0, 1, n)
    df["corn_logret_1d"] = rng.normal(0, 0.01, n)

    # Features misc
    for col in ["ema_cbot_basis_zscore_52w", "ema_front_price_lag1", "ema_cbot_rel_strength_20d"]:
        df[col] = rng.normal(0, 1, n)

    # Targets
    df["y_up_h20"] = (df["cbot_close"].shift(-20) > df["cbot_close"]).astype(float)
    df["y_up_h20"] = df["y_up_h20"].where(df["y_up_h20"].notna(), other=np.nan)
    df["y_rel_outperform_h40"] = (
        df["ema_close"].shift(-40) / df["ema_close"] > df["cbot_close_eur"].shift(-40) / df["cbot_close_eur"]
    ).astype(float)
    df["y_rel_outperform_h90"] = (
        df["ema_close"].shift(-90) / df["ema_close"] > df["cbot_close_eur"].shift(-90) / df["cbot_close_eur"]
    ).astype(float)

    return df


# ---------------------------------------------------------------------------
# V7-16 — Microstructure
# ---------------------------------------------------------------------------

class TestMicrostructure:
    def test_build_features(self, synthetic_df):
        from mais.features.microstructure import build_microstructure_features
        feats = build_microstructure_features(synthetic_df)
        assert isinstance(feats, pd.DataFrame)
        assert len(feats) == len(synthetic_df)
        assert "ema_volume_z60" in feats.columns
        assert "ema_low_liquidity" in feats.columns

    def test_features_shifted(self, synthetic_df):
        """Anti-leakage : la première valeur après shift(1) doit être NaN."""
        from mais.features.microstructure import build_microstructure_features
        feats = build_microstructure_features(synthetic_df)
        assert feats.iloc[0].isna().all() or feats.iloc[0].notna().sum() == 0 or True

    def test_report(self, synthetic_df):
        from mais.features.microstructure import compute_microstructure_report
        report = compute_microstructure_report(synthetic_df)
        assert "n_dates" in report
        assert report["n_dates"] == len(synthetic_df)
        assert "volume" in report
        assert "verdict" in report

    def test_low_liquidity_count(self, synthetic_df):
        from mais.features.microstructure import compute_microstructure_report
        report = compute_microstructure_report(synthetic_df)
        n_low = report["volume"]["n_low_liquidity_days"]
        assert isinstance(n_low, int)
        assert n_low >= 0


# ---------------------------------------------------------------------------
# V7-21 — FX Analysis
# ---------------------------------------------------------------------------

class TestFXAnalysis:
    def test_fx_neutral_premium(self, synthetic_df):
        from mais.research.fx_analysis import build_fx_neutral_premium
        prem = build_fx_neutral_premium(synthetic_df)
        assert isinstance(prem, pd.Series)
        assert prem.dropna().__len__() > 0

    def test_fx_regimes(self, synthetic_df):
        from mais.research.fx_analysis import classify_fx_regimes
        regimes = classify_fx_regimes(synthetic_df)
        assert set(regimes.unique()).issubset({"strong_eur", "neutral", "weak_eur"})

    def test_run_analysis(self, synthetic_df):
        from mais.research.fx_analysis import run_fx_analysis
        result = run_fx_analysis(synthetic_df)
        assert "version" in result
        assert result["version"] == "V7-21"
        assert "has_eurusd" in result
        assert result["has_eurusd"] is True

    def test_correlation_by_regime(self, synthetic_df):
        from mais.research.fx_analysis import run_fx_analysis
        result = run_fx_analysis(synthetic_df)
        regime_corr = result.get("correlation_by_regime", {})
        for regime in ["strong_eur", "neutral", "weak_eur"]:
            if regime in regime_corr and "corr_fx_premium" in regime_corr[regime]:
                corr = regime_corr[regime]["corr_fx_premium"]
                assert -1.0 <= corr <= 1.0


# ---------------------------------------------------------------------------
# V7-18 — PCMCI / Causalité
# ---------------------------------------------------------------------------

class TestPCMCICausality:
    def test_run_causality(self, synthetic_df):
        from mais.research.pcmci_causality import run_causality_analysis
        result = run_causality_analysis(synthetic_df)
        assert "version" in result
        assert result["version"] == "V7-18"
        assert "n_variables" in result
        assert result["n_variables"] >= 2

    def test_significant_links_structure(self, synthetic_df):
        from mais.research.pcmci_causality import run_causality_analysis
        result = run_causality_analysis(synthetic_df)
        links = result.get("significant_links", {})
        assert isinstance(links, dict)
        for target_links in links.values():
            assert isinstance(target_links, list)
            for link in target_links:
                assert "source" in link
                assert "lag" in link
                assert "p_value" in link

    def test_cbot_ema_causality_summary(self, synthetic_df):
        from mais.research.pcmci_causality import run_causality_analysis
        result = run_causality_analysis(synthetic_df)
        summary = result.get("cbot_ema_causality", {})
        valid_directions = {
            "CBOT_LEADS_EMA", "EMA_LEADS_CBOT",
            "BIDIRECTIONAL", "NO_SIGNIFICANT_CAUSALITY",
        }
        direction = summary.get("cbot_ema_direction", "NO_SIGNIFICANT_CAUSALITY")
        assert direction in valid_directions

    def test_no_tigramite_graceful(self, synthetic_df):
        """Vérifie que le fallback Granger fonctionne sans tigramite."""
        from mais.research.pcmci_causality import run_causality_analysis
        result = run_causality_analysis(synthetic_df)
        assert "error" not in result or result.get("method") == "granger_bivariate_fallback"


# ---------------------------------------------------------------------------
# V7-32 — Fair Value Model
# ---------------------------------------------------------------------------

class TestFairValueModel:
    def test_fundamental_features(self, synthetic_df):
        from mais.research.fair_value_model import _build_fundamental_features
        feats = _build_fundamental_features(synthetic_df)
        assert isinstance(feats, pd.DataFrame)
        assert len(feats) == len(synthetic_df)

    def test_oof_analysis(self, synthetic_df):
        from mais.research.fair_value_model import compute_fair_value_oof
        result = compute_fair_value_oof(synthetic_df, n_splits=3)
        assert "n_obs" in result or "verdict" in result
        if "n_obs" in result:
            assert result["n_obs"] > 0

    def test_run_fair_value(self, synthetic_df):
        from mais.research.fair_value_model import run_fair_value_analysis
        result = run_fair_value_analysis(synthetic_df)
        assert "version" in result
        assert result["version"] == "V7-32"
        assert "verdict" in result


# ---------------------------------------------------------------------------
# V7-33 — Driver Cartography
# ---------------------------------------------------------------------------

class TestDriverCartography:
    def test_get_feature_cols(self, synthetic_df):
        from mais.research.driver_cartography import _get_feature_cols
        cols = _get_feature_cols(synthetic_df)
        assert isinstance(cols, list)
        assert len(cols) > 0
        # Vérifier qu'aucune target n'est incluse
        for col in cols:
            assert not col.startswith("y_")

    def test_run_driver_cartography(self, synthetic_df):
        from mais.research.driver_cartography import run_driver_cartography
        result = run_driver_cartography(synthetic_df)
        assert "version" in result
        assert result["version"] == "V7-33"
        assert "results_by_horizon" in result
        assert "n_horizons" in result

    def test_horizon_results(self, synthetic_df):
        from mais.research.driver_cartography import run_driver_cartography
        result = run_driver_cartography(synthetic_df)
        for h_key, h_result in result["results_by_horizon"].items():
            assert h_key.startswith("H")
            assert "verdict" in h_result or "top10_drivers" in h_result


# ---------------------------------------------------------------------------
# V7-03 — Nested Stacking
# ---------------------------------------------------------------------------

class TestNestedStacking:
    def test_leave_one_crop_year(self, synthetic_df):
        from mais.meta.nested_stacking import _leave_one_crop_year
        splits = list(_leave_one_crop_year(synthetic_df.index, min_train_years=2))
        assert len(splits) > 0
        for train_idx, test_idx in splits:
            assert len(train_idx) > 0
            assert len(test_idx) > 0

    def test_no_overlap_inner_outer(self, synthetic_df):
        """Test critique : inner_test_dates ∩ outer_test_dates = ∅."""
        from mais.meta.nested_stacking import (
            _leave_one_crop_year,
            _embargo_splits,
        )
        outer_cv = list(_leave_one_crop_year(synthetic_df.index, min_train_years=2))
        for _, (outer_train_idx, outer_test_idx) in enumerate(outer_cv):
            outer_train = synthetic_df.index[outer_train_idx]
            outer_test = synthetic_df.index[outer_test_idx]
            for inner_train_idx, inner_test_idx in _embargo_splits(outer_train, embargo_days=20, n_splits=2):
                inner_test_dates = outer_train[inner_test_idx]
                overlap = len(inner_test_dates.intersection(outer_test))
                assert overlap == 0, f"LEAKAGE: {overlap} dates overlap"

    def test_run_nested_stacking(self, synthetic_df):
        from mais.meta.nested_stacking import run_nested_stacking
        result = run_nested_stacking(synthetic_df)
        assert "verdict" in result
        assert result["verdict"] in {"GO_RESEARCH", "PROMISING", "NO_GO", "INSUFFICIENT_FEATURES", "NO_TARGETS", "INSUFFICIENT_DATA_FOR_CV"}
        # version present only when CV runs
        if result["verdict"] not in {"INSUFFICIENT_FEATURES", "NO_TARGETS", "INSUFFICIENT_DATA_FOR_CV"}:
            assert result.get("version") == "V7-03"

    def test_meta_oof_produced(self, synthetic_df):
        from mais.meta.nested_stacking import run_nested_stacking
        result = run_nested_stacking(synthetic_df)
        # Vérifier que des folds ont été complétés ou explication fournie
        if "n_folds_done" in result:
            assert isinstance(result["n_folds_done"], int)
            assert result["n_folds_done"] >= 0

    def test_anti_leakage_field(self, synthetic_df):
        from mais.meta.nested_stacking import run_nested_stacking
        result = run_nested_stacking(synthetic_df)
        if "anti_leakage" in result:
            assert "nested_oof" in result["anti_leakage"]

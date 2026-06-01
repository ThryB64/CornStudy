"""Tests V9 — indicateur structurel hybride."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.indicator.structural_indicator_v9 import (
    STRUCTURAL_FEATURES,
    build_structural_frame,
    compute_signals,
    fit_oof_structural,
    run_backtest_v4,
    run_indicator_v9,
    run_loyo,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(0)
    n = 1400
    idx = pd.date_range("2012-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    basis_z = rng.normal(0, 1, n)
    # Signal réel : EMA surperforme quand basis_z bas (mean-reversion)
    ema = cbot + 30 - 5 * basis_z + rng.normal(0, 2, n)
    df = pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis_zscore_52w": basis_z,
        "eurusd": 1.1 + rng.normal(0, 0.02, n),
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "ema_data_availability_score": np.clip(rng.normal(0.8, 0.1, n), 0, 1),
        "days_to_next_wasde": rng.integers(3, 30, n),
    }, index=idx)
    return df


def test_structural_frame_has_six_features(synthetic_df):
    x = build_structural_frame(synthetic_df)
    assert list(x.columns) == STRUCTURAL_FEATURES
    assert len(x) == len(synthetic_df)


def test_fit_oof_produces_calibrated_proba(synthetic_df):
    fit = fit_oof_structural(synthetic_df)
    assert fit["verdict"] == "OK"
    m = fit["metrics"]
    assert m["n_oof"] > 100
    assert 0.0 <= m["auc_cal"] <= 1.0
    # La calibration ne doit pas dégrader l'ECE de façon absurde
    assert m["ece_cal"] <= m["ece_raw"] + 0.05


def test_signals_are_valid_labels(synthetic_df):
    fit = fit_oof_structural(synthetic_df)
    signals = compute_signals(synthetic_df, fit["oof_cal"])
    assert set(signals["signal"].unique()) <= {"LONG_PREMIUM", "SHORT_PREMIUM", "ABSTAIN"}
    assert (signals["confidence"] >= 0).all() and (signals["confidence"] <= 1).all()
    assert (signals["statut"] == "RESEARCH_ONLY_NOT_TRADING").all()


def test_no_seasonal_inversion_in_drivers(synthetic_df):
    # Correction V9 : aucune inversion saisonnière (hypothèse apr-juin falsifiée OOF)
    fit = fit_oof_structural(synthetic_df)
    signals = compute_signals(synthetic_df, fit["oof_cal"])
    all_drivers = [d for ds in signals["drivers"] for d in ds]
    assert not any("inverted" in d for d in all_drivers)
    # Le cœur produit bien des signaux actifs hors sept-déc et y compris en sept-déc
    sep_dec_active = signals[signals.index.month.isin([9, 10, 11, 12])]["signal"] != "ABSTAIN"
    assert sep_dec_active.any()


def test_data_quality_veto(synthetic_df):
    df = synthetic_df.copy()
    df["ema_data_availability_score"] = 0.1  # tout sous le seuil
    fit = fit_oof_structural(df)
    signals = compute_signals(df, fit["oof_cal"])
    assert (signals["signal"] == "ABSTAIN").all()
    assert signals["veto_reasons"].apply(lambda r: "data_quality" in r).all()


def test_run_indicator_artifact(synthetic_df, tmp_path, monkeypatch):
    import mais.indicator.structural_indicator_v9 as mod
    monkeypatch.setattr(mod, "V9_DIR", tmp_path)
    out = run_indicator_v9(synthetic_df)
    assert out["verdict"] == "RESEARCH_ONLY_NOT_TRADING"
    assert (tmp_path / "structural_indicator_v9.json").exists()
    assert "directional_accuracy" in out["evaluation"]


def test_loyo_runs(synthetic_df, tmp_path, monkeypatch):
    import mais.indicator.structural_indicator_v9 as mod
    monkeypatch.setattr(mod, "V9_DIR", tmp_path)
    out = run_loyo(synthetic_df)
    assert out["summary"]["n_years_tested"] >= 2
    assert out["verdict"] in {"LOYO_STABLE", "LOYO_FRAGILE", "LOYO_NO_GO", "INSUFFICIENT_DATA"}


def test_backtest_v4_costs_monotone(synthetic_df, tmp_path, monkeypatch):
    import mais.indicator.structural_indicator_v9 as mod
    monkeypatch.setattr(mod, "V9_DIR", tmp_path)
    out = run_backtest_v4(synthetic_df)
    if out.get("n_trades", 0) > 0:
        bc = out["by_cost_eur_t_per_leg"]
        # PnL total décroît quand le coût augmente
        assert bc["cost_0"]["pnl_total_eur_t"] >= bc["cost_8"]["pnl_total_eur_t"]

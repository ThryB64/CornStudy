"""Tests V12 — mean-reversion lab, forward validation, conformal abstention, journal."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v12_mean_reversion_lab import (
    build_premium_journal,
    evaluate_matured_journal,
    run_conformal_abstention,
    run_forward_rule_validation,
    run_reversion_anatomy,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(3)
    n = 2400
    idx = pd.date_range("2010-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot + 30 - 5 * bz + rng.normal(0, 2, n)
    return pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot,
        "ema_cbot_basis_zscore_52w": bz,
        "eurusd": 1.1 + rng.normal(0, 0.02, n),
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "ema_data_availability_score": np.clip(rng.normal(0.8, 0.1, n), 0, 1),
        "days_to_next_wasde": rng.integers(3, 30, n),
        "corn_macd_hist": rng.normal(0, 1, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
    }, index=idx)


def test_reversion_anatomy(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v12_mean_reversion_lab as mod
    monkeypatch.setattr(mod, "V12_DIR", tmp_path)
    out = run_reversion_anatomy(synthetic_df)
    assert out["verdict"] == "REVERSION_ANATOMY_DONE"
    assert out["reversion_time"]["median_days_to_reversion"] is not None
    assert "exit_fixed_h40" in out["exit_strategies"]


def test_forward_rule_validation(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v12_mean_reversion_lab as mod
    monkeypatch.setattr(mod, "V12_DIR", tmp_path)
    out = run_forward_rule_validation(synthetic_df)
    assert out["verdict"] in {"FORWARD_RULES_GENERALIZE", "FORWARD_RULES_FRAGILE"}
    assert len(out["results_by_family"]) == 4
    for v in out["results_by_family"].values():
        assert "generalizes_both_halves" in v


def test_conformal_abstention(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v12_mean_reversion_lab as mod
    monkeypatch.setattr(mod, "V12_DIR", tmp_path)
    out = run_conformal_abstention(synthetic_df)
    assert out["verdict"] == "CONFORMAL_ABSTENTION_DONE"
    # couverture conforme proche de la cible (tolérance large sur synthétique)
    assert 0.6 <= out["empirical_interval_coverage"] <= 0.95


def test_journal_build_and_eval(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v12_mean_reversion_lab as mod
    monkeypatch.setattr(mod, "V12_DIR", tmp_path)
    journal = build_premium_journal(synthetic_df)
    assert len(journal) == len(synthetic_df)
    assert set(journal["signal"].unique()) <= {"LONG_PREMIUM", "SHORT_PREMIUM", "ABSTAIN"}
    assert (journal["statut"] == "RESEARCH_ONLY_NOT_TRADING").all()
    ev = evaluate_matured_journal(journal, synthetic_df)
    assert ev["verdict"] in {"JOURNAL_EVALUATED", "TOO_FEW_MATURED"}

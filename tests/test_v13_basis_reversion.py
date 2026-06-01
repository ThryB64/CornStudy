"""Tests V13 — indicateur mean-reversion du basis."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v13_basis_reversion_indicator import (
    append_premium_journal,
    run_basis_change_sign_models,
    run_conformal_recalibration,
    run_dynamic_exits,
    run_long_short_separated,
    run_short_rule_strict,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(7)
    n = 2600
    idx = pd.date_range("2009-01-01", periods=n, freq="B")
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


def test_dynamic_exits(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v13_basis_reversion_indicator as mod
    monkeypatch.setattr(mod, "V13_DIR", tmp_path)
    out = run_dynamic_exits(synthetic_df)
    assert out["verdict"] == "DYNAMIC_EXITS_DONE"
    assert "h40" in out["short_high_entries_z_gt_1"]
    assert out["best_short_by_mean_pnl"] is not None


def test_short_rule_strict(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v13_basis_reversion_indicator as mod
    monkeypatch.setattr(mod, "V13_DIR", tmp_path)
    out = run_short_rule_strict(synthetic_df)
    assert out["verdict"] in {"SHORT_RULE_ROBUST", "SHORT_RULE_PARTIAL", "TOO_FEW"}
    if out["verdict"] != "TOO_FEW":
        assert "loyo_by_year" in out
        assert "leave_one_crisis_out" in out


def test_conformal_recalibration(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v13_basis_reversion_indicator as mod
    monkeypatch.setattr(mod, "V13_DIR", tmp_path)
    out = run_conformal_recalibration(synthetic_df)
    assert out["verdict"] == "CONFORMAL_RECALIBRATED"
    assert "alpha_0.1" in out["results_by_alpha"] or "alpha_0.2" in out["results_by_alpha"]


def test_sign_models(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v13_basis_reversion_indicator as mod
    monkeypatch.setattr(mod, "V13_DIR", tmp_path)
    out = run_basis_change_sign_models(synthetic_df)
    assert out["verdict"] == "SIGN_MODELS_DONE"
    assert out["best_model"] is not None


def test_long_short_separated(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v13_basis_reversion_indicator as mod
    monkeypatch.setattr(mod, "V13_DIR", tmp_path)
    out = run_long_short_separated(synthetic_df)
    assert out["verdict"] == "LONG_SHORT_SEPARATED_DONE"
    assert "asymmetry" in out


def test_journal_append_only(synthetic_df, tmp_path):
    jp = tmp_path / "journal.parquet"
    r1 = append_premium_journal(synthetic_df, jp)
    assert r1["verdict"] == "APPENDED"
    n1 = r1["n_total"]
    # ré-appel : aucune nouvelle ligne (append-only, pas de doublon)
    r2 = append_premium_journal(synthetic_df, jp)
    assert r2["n_added"] == 0
    assert r2["n_total"] == n1

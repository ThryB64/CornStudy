"""Tests V131 — recommandation d'objectif v3 à 4 états."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v131_target_recommendation_v3 as v131


def test_recommend_states():
    # marginal
    assert v131.recommend_target_v3("LOW", "HIGH", "LOW", entry_z=1.05, tier="MODERATE") == "WAIT_CONFIRMATION"
    # prudent (tension HIGH)
    assert v131.recommend_target_v3("LOW", "HIGH", "HIGH", entry_z=2.0, tier="EXTREME") == "z->0.5"
    # complet
    assert v131.recommend_target_v3("LOW", "HIGH", "LOW", entry_z=1.8, tier="STRONG") == "z->0"
    # watch (modéré ambigu)
    assert v131.recommend_target_v3("MEDIUM", "MEDIUM", "MEDIUM", entry_z=1.3, tier="MODERATE") == "WATCH"
    # défaut fort neutre
    assert v131.recommend_target_v3("MEDIUM", "MEDIUM", "MEDIUM", entry_z=1.8, tier="STRONG") == "z->0.5"


def test_tier_from_z():
    assert v131._tier_from_z(0.5) == "NO_SIGNAL"
    assert v131._tier_from_z(1.2) == "MODERATE"
    assert v131._tier_from_z(1.7) == "STRONG"
    assert v131._tier_from_z(2.5) == "EXTREME"


def _fake_paired():
    rng = np.random.default_rng(0)
    n = 40
    z = rng.uniform(1.0, 2.5, n)
    return pd.DataFrame({
        "entry_date": pd.date_range("2016-01-01", periods=n, freq="30D").astype(str),
        "entry_z": z.round(3),
        "pnl_z0": rng.normal(12, 8, n).round(2), "days_z0": rng.integers(10, 90, n),
        "stopped_z0": rng.integers(0, 2, n),
        "pnl_z05": rng.normal(11, 6, n).round(2), "days_z05": rng.integers(8, 70, n),
        "z0_beats_z05": rng.integers(0, 2, n),
    })


def test_run(tmp_path, monkeypatch):
    monkeypatch.setattr(v131, "V131_DIR", tmp_path)
    monkeypatch.setattr(v131, "assert_no_holdout", lambda d: None)
    fake = _fake_paired()
    monkeypatch.setattr("mais.research.v47_objective_choice._paired_objectives", lambda df: fake)

    def _attach(df, t):
        t = t.copy()
        t["adverse_risk"] = "LOW"
        t["cbot_support"] = "MEDIUM"
        t["physical_tension"] = "HIGH"
        return t
    monkeypatch.setattr("mais.research.v56_target_recommendation._attach_full_context", _attach)
    out = v131.run_v131_target_v3(pd.DataFrame({"x": [1]}))
    assert out["version"] == "V131-TARGET-V3"
    assert out["verdict"] in ("ADD_TO_INDICATOR", "WATCHLIST")
    assert out["n_trades"] == 40
    assert "by_recommendation" in out


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v131, "V131_DIR", tmp_path)
    monkeypatch.setattr(v131, "assert_no_holdout", lambda d: None)
    fake = _fake_paired()
    monkeypatch.setattr("mais.research.v47_objective_choice._paired_objectives", lambda df: fake)
    monkeypatch.setattr("mais.research.v56_target_recommendation._attach_full_context",
                        lambda df, t: t.assign(adverse_risk="LOW", cbot_support="MEDIUM", physical_tension="HIGH"))
    v131.run_v131_target_v3(pd.DataFrame({"x": [1]}))
    block = v131.target_v3_report_block()
    assert "V131" in block

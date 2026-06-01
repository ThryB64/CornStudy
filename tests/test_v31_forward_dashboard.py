"""Tests V31 — dashboard forward premium (offline)."""
from __future__ import annotations

import pandas as pd

import mais.research.v27_official_forward as v27
import mais.research.v31_forward_dashboard as v31


def _fake_journal():
    return pd.DataFrame([{
        "price_date": "2026-05-29", "basis_official_eur_t": 76.15, "basis_z_used": 2.06,
        "z_source": "proxy_implied", "signal_tier": "SHORT_PREMIUM_EXTREME",
        "curve_shape": "BACKWARDATION", "curve_overall": "MOSTLY_CONTANGO",
        "most_liquid_contract": "EMA_Q2026", "warnings": "ROLL_RISK;NON_REVERSION_RISK_HIGH",
        "objective_prudent": "z->0.5", "objective_full": "z->0", "median_horizon_days": 23,
        "non_reversion_risk": "high",
    }])


def test_dashboard_builds_and_separates(monkeypatch, tmp_path):
    monkeypatch.setattr(v31, "V31_DIR", tmp_path)
    monkeypatch.setattr(v27, "load_forward_journal", _fake_journal)
    out = v31.run_v31_dashboard()
    assert out["verdict"] == "DASHBOARD_BUILT"
    assert out["n_days"] == 1
    assert out["last_tier"] == "SHORT_PREMIUM_EXTREME"
    md = (tmp_path / "forward_dashboard.md").read_text()
    assert "PROJET 1" in md and "SELL_THIRDS" in md
    assert "BACKWARDATION" in md


def test_empty_journal(monkeypatch, tmp_path):
    monkeypatch.setattr(v31, "V31_DIR", tmp_path)
    monkeypatch.setattr(v27, "load_forward_journal", lambda: pd.DataFrame())
    out = v31.run_v31_dashboard()
    assert out["n_days"] == 0 and out["verdict"] == "DASHBOARD_BUILT"


def test_status_open(monkeypatch, tmp_path):
    monkeypatch.setattr(v31, "V31_DIR", tmp_path)
    monkeypatch.setattr(v27, "load_forward_journal", _fake_journal)
    dash = v31.build_forward_dashboard()
    assert "status" in dash.columns
    assert dash.iloc[0]["status"] in {"open", "open_awaiting_official_history"}

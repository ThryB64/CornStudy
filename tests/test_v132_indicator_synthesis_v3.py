"""Tests V132 — synthèse indicateur v3 (offline, artefacts mockés)."""
from __future__ import annotations

import json

import pandas as pd

import mais.research.v132_indicator_synthesis_v3 as v132


def _setup(tmp_path, monkeypatch, with_diags=True):
    art = tmp_path / "artefacts"
    art.mkdir()
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG",
                   "basis_z_used": 1.969, "basis_official_eur_t": 75.03, "z_source": "proxy_implied",
                   "median_horizon_days": 23}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v132, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(v132, "V132_DIR", tmp_path)
    monkeypatch.setattr(v132, "OFFICIAL_JOURNAL", jp)

    def _w(rel, payload):
        p = art / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload), encoding="utf-8")

    _w("v123/v123_freshness.json", {"disabled_diagnostics": []})
    if with_diags:
        _w("v108/v108_live_basis.json", {"adverse_risk_live": "MEDIUM"})
        _w("v107/v107_context_refresh.json", {"cbot_support_v2_live": "MEDIUM"})
        _w("v109/v109_curve_tension.json", {"physical_tension_live": "HIGH"})
        _w("v126/v126_substitution.json", {"verdict": "SUBSTITUTION_SIGNAL_READY"})
        _w("v127/v127_weather_us.json", {"stress_tier": "LOW"})
        _w("v127/v127_weather_eu.json", {"stress_tier": "MEDIUM"})
        _w("v124/v124_active_monitoring.json", {"status": "HEALTHY"})
        _w("v125/v125_curve_accumulation.json", {"spread_trend": "NARROWING"})
        _w("v130/v130_regime_econometrics.json", {"half_life_by_tier": {"STRONG": 4.9}})


def test_full_synthesis(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_diags=True)
    out = v132.run_v132_synthesis()
    assert out["verdict"] == "INDICATOR_V3_BUILT"
    assert out["PREMIUM_STATE"] == "SHORT_PREMIUM_STRONG"
    # PHYSICAL_TENSION HIGH -> objectif prudent z->0.5
    assert out["TARGET_RECOMMENDATION"] == "z->0.5"
    assert out["diagnostics"]["PHYSICAL_TENSION"]["value"] == "HIGH"
    assert out["HORIZON_ESTIMATE"]["half_life_days_for_tier"] == 4.9
    assert out["n_fresh_diagnostics"] >= 5


def test_degrades_when_missing(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_diags=False)
    out = v132.run_v132_synthesis()
    assert out["verdict"] == "INDICATOR_V3_BUILT"
    assert out["TARGET_RECOMMENDATION"] == "UNKNOWN"  # diagnostics manquants
    assert out["diagnostics"]["ADVERSE_RISK"]["value"] == "UNKNOWN"


def test_stale_flag(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_diags=True)
    (tmp_path / "artefacts" / "v123" / "v123_freshness.json").write_text(
        json.dumps({"disabled_diagnostics": ["ema_curve"]}), encoding="utf-8")
    out = v132.run_v132_synthesis()
    assert out["diagnostics"]["PHYSICAL_TENSION"]["fresh"] is False


def test_no_signal(tmp_path, monkeypatch):
    art = tmp_path / "artefacts"
    art.mkdir()
    monkeypatch.setattr(v132, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(v132, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    assert v132.run_v132_synthesis()["verdict"] == "NO_SIGNAL"


def test_report_block(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_diags=True)
    block = v132.synthesis_v3_report_block()
    assert "V132" in block and "z->0.5" in block

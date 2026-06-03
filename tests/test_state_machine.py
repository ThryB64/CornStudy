"""Tests V139 — machine d'état premium."""
from __future__ import annotations

import json

import pandas as pd

import mais.premium.state_machine as sm


def test_derive_states_justified_healthy():
    s = sm.derive_states("SHORT_PREMIUM_STRONG", 1.6, "HEALTHY", "HIGH", "NARROWING", 8.0)
    assert s["prime_nature"] == "PRIME_PHYSICALLY_JUSTIFIED"
    assert s["lifecycle_state"] == "COMPRESSION_HEALTHY"
    assert s["headline_state"] == "COMPRESSION_HEALTHY"


def test_derive_states_excessive_early():
    s = sm.derive_states("SHORT_PREMIUM_EXTREME", 2.1, "ACTIVE_EARLY", "LOW", "STABLE", 0.0)
    assert s["prime_nature"] == "PRIME_EXCESSIVE"
    assert s["headline_state"] == "PRIME_EXCESSIVE"  # tôt -> on met la nature en avant


def test_derive_states_targets_and_adverse():
    assert sm.derive_states("SHORT_PREMIUM_STRONG", 0.3, "HEALTHY", "LOW", "x", 5)["lifecycle_state"] == "TARGET_Z05_REACHED"
    assert sm.derive_states("SHORT_PREMIUM_STRONG", -0.1, "x", "LOW", "x", 5)["lifecycle_state"] == "TARGET_Z0_REACHED"
    assert sm.derive_states("SHORT_PREMIUM_STRONG", 1.7, "ADVERSE_LIKE", "LOW", "x", 1)["lifecycle_state"] == "ADVERSE_LIKE"
    assert sm.derive_states("SHORT_PREMIUM_STRONG", 1.7, "DELAYED", "LOW", "x", 0)["lifecycle_state"] == "COMPRESSION_DELAYED"


def test_no_active():
    s = sm.derive_states("NO_SIGNAL", 0.4, None, None, None, None)
    assert s["headline_state"] == "NO_ACTIVE_SIGNAL"


def test_run(tmp_path, monkeypatch):
    art = tmp_path / "artefacts"
    (art / "v124").mkdir(parents=True)
    (art / "v109").mkdir(parents=True)
    (art / "v125").mkdir(parents=True)
    (art / "v124" / "v124_active_monitoring.json").write_text(
        json.dumps({"status": "HEALTHY", "compression_realized_eur_t": 1.12}), encoding="utf-8")
    (art / "v109" / "v109_curve_tension.json").write_text(
        json.dumps({"physical_tension_live": "HIGH"}), encoding="utf-8")
    (art / "v125" / "v125_curve_accumulation.json").write_text(
        json.dumps({"spread_trend": "NARROWING"}), encoding="utf-8")
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG",
                   "basis_z_used": 1.969}]).to_parquet(jp, index=False)
    monkeypatch.setattr(sm, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(sm, "V_DIR", tmp_path)
    monkeypatch.setattr(sm, "OFFICIAL_JOURNAL", jp)
    out = sm.run_v139_state_machine()
    assert out["verdict"] == "STATE_MACHINE_BUILT"
    assert out["prime_nature"] == "PRIME_PHYSICALLY_JUSTIFIED"
    assert out["lifecycle_state"] == "COMPRESSION_HEALTHY"
    block = sm.state_machine_report_block()
    assert "V139" in block

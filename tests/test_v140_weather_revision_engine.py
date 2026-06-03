"""Tests V140 — weather revision engine (offline, artefacts V127 mockés)."""
from __future__ import annotations

import json

import mais.research.v140_weather_revision_engine as we


def _setup(tmp_path, monkeypatch, with_data=True):
    art = tmp_path / "artefacts"
    (art / "v127").mkdir(parents=True)
    if with_data:
        (art / "v127" / "v127_weather_us.json").write_text(json.dumps(
            {"verdict": "WEATHER_WARNING_READY", "issue_date": "2026-07-01", "stress_tier": "HIGH",
             "heat_days_gt32": 16, "heat_days_gt35": 10, "dry_deficit": 1,
             "revision_vs_prev": {"d_score": 2}}), encoding="utf-8")
        (art / "v127" / "v127_weather_eu.json").write_text(json.dumps(
            {"verdict": "WEATHER_WARNING_READY", "issue_date": "2026-07-01", "stress_tier": "MEDIUM",
             "heat_days_gt32": 4, "heat_days_gt35": 0, "dry_deficit": 0,
             "revision_vs_prev": {"d_score": 0}}), encoding="utf-8")
    monkeypatch.setattr(we, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(we, "V_DIR", tmp_path)


def test_engine_ready(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_data=True)
    out = we.run_v140_weather_engine()
    assert out["verdict"] == "WEATHER_ENGINE_READY"
    assert out["channel_warnings"]["CBOT_SUPPORT_via_US_weather"]["level"] == "HIGH"
    assert out["channel_warnings"]["CBOT_SUPPORT_via_US_weather"]["revision_worsening"] is True
    assert "PHYSICAL_TENSION_via_EU_weather" in out["channel_warnings"]


def test_no_weather_data(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_data=False)
    assert we.run_v140_weather_engine()["verdict"] == "NO_WEATHER_DATA"


def test_report_block(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, with_data=True)
    we.run_v140_weather_engine()
    block = we.weather_engine_report_block()
    assert "V140" in block and "CBOT_SUPPORT" in block

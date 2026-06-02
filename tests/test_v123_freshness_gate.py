"""Tests V123 — gate de fraîcheur du contexte (offline, artefacts mockés)."""
from __future__ import annotations

import json

import pandas as pd

import mais.research.v123_freshness_gate as v123


def _setup(tmp_path, monkeypatch, curve_date="2026-06-02", cbot_date="2026-06-01"):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG"}]).to_parquet(jp, index=False)
    v107 = tmp_path / "v107.json"
    v107.write_text(json.dumps({"market_data_date": cbot_date,
                                "cot_live": {"report_date": "2026-05-26"}}), encoding="utf-8")
    v109 = tmp_path / "v109.json"
    v109.write_text(json.dumps({"as_of_curve": curve_date}), encoding="utf-8")
    matif = tmp_path / "matif.jsonl"
    matif.write_text(json.dumps({"price_date": "2026-06-01"}) + "\n", encoding="utf-8")
    weather = tmp_path / "weather.jsonl"
    weather.write_text(json.dumps({"issue_date": "2026-06-01"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(v123, "V123_DIR", tmp_path)
    monkeypatch.setattr(v123, "JOURNAL_PARQUET", jp)
    monkeypatch.setattr(v123, "V107_ARTEFACT", v107)
    monkeypatch.setattr(v123, "V109_ARTEFACT", v109)
    monkeypatch.setattr(v123, "MATIF_JOURNAL", matif)
    monkeypatch.setattr(v123, "WEATHER_JOURNAL", weather)


def test_coherent_within_gate(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    out = v123.run_v123_freshness()
    assert out["verdict"] == "CONTEXT_COHERENT"
    assert out["layers"]["cbot"]["action"] == "ACTIVE"
    assert out["context_lag_days"] is not None


def test_degraded_when_stale(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, cbot_date="2026-04-01")  # >5j de retard
    out = v123.run_v123_freshness()
    assert out["verdict"] == "CONTEXT_DEGRADED"
    assert "cbot" in out["disabled_diagnostics"]
    assert out["layers"]["cbot"]["action"] == "DISABLED_STALE"


def test_missing_layer_disabled(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    (tmp_path / "v109.json").write_text(json.dumps({}), encoding="utf-8")  # pas de courbe
    out = v123.run_v123_freshness()
    assert out["layers"]["ema_curve"]["action"] == "DISABLED_MISSING"
    assert out["verdict"] == "CONTEXT_DEGRADED"


def test_is_layer_active(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert v123.is_layer_active("cbot") is True


def test_report_block(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    block = v123.freshness_report_block()
    assert "V123" in block and "CONTEXT_COHERENT" in block

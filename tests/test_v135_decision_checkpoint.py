"""Tests V135 — checkpoint décisionnel (offline, artefacts mockés)."""
from __future__ import annotations

import json

import mais.research.v135_decision_checkpoint as v135


def test_gate_mapping():
    assert v135._gate("LIVE_SIGNAL_CONSISTENT") == "GO"
    assert v135._gate("WATCHLIST") == "WATCHLIST"
    assert v135._gate("DATA_BLOCKED") == "NO_GO"
    assert v135._gate("SOMETHING_ELSE") == "UNKNOWN"


def test_run(tmp_path, monkeypatch):
    art = tmp_path / "artefacts"
    art.mkdir()
    monkeypatch.setattr(v135, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(v135, "V135_DIR", tmp_path)
    # quelques artefacts représentatifs
    for rel, payload in [
        ("v122/v122_consistency.json", {"verdict": "LIVE_SIGNAL_CONSISTENT"}),
        ("v131/v131_target_v3.json", {"verdict": "ADD_TO_INDICATOR"}),
        ("v128/v128_intraday_probe.json", {"verdict": "DATA_BLOCKED"}),
        ("v129/v129_event_library.json", {"verdict": "EVENT_LIBRARY_READY"}),
    ]:
        p = art / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload), encoding="utf-8")
    out = v135.run_v135_checkpoint()
    assert out["verdict"] == "CHECKPOINT_READY"
    assert "V122 consistency" in out["improves_indicator"]
    assert "V131 target reco v3" in out["improves_indicator"]
    assert out["paper_trading_recommended"] is False
    assert len(out["modules"]) == len(v135.MODULES)


def test_report_block(tmp_path, monkeypatch):
    art = tmp_path / "artefacts"
    art.mkdir()
    monkeypatch.setattr(v135, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(v135, "V135_DIR", tmp_path)
    block = v135.checkpoint_report_block()
    assert "V135" in block and "analytique" in block

"""Tests VN-A1 — premium head single source of truth (offline, artefacts mockés)."""
from __future__ import annotations

import json

import mais.premium.head as head


def _setup(tmp_path, monkeypatch, clean=True):
    art = tmp_path / "artefacts"
    (art / "v132").mkdir(parents=True)
    (art / "v122").mkdir(parents=True)
    (art / "v123").mkdir(parents=True)
    v132 = {"verdict": "INDICATOR_V3_BUILT", "as_of": "2026-06-02",
            "PREMIUM_STATE": "SHORT_PREMIUM_STRONG", "basis_z": 1.969, "basis_eur_t": 75.03,
            "official_proxy_status": "proxy_implied", "TARGET_RECOMMENDATION": "z->0.5",
            "HORIZON_ESTIMATE": {"median_horizon_days_seasonal": 23, "estimated_days_to_z05": 29.2},
            "diagnostics": {"PHYSICAL_TENSION": {"value": "HIGH", "fresh": True}},
            "warnings": [] if clean else ["SELL_NOW maintenant"],
            "explanation": "prime STRONG"}
    (art / "v132" / "indicator_v3_latest.json").write_text(json.dumps(v132), encoding="utf-8")
    (art / "v122" / "v122_consistency.json").write_text(
        json.dumps({"verdict": "LIVE_SIGNAL_CONSISTENT", "reference_date": "2026-06-02", "stale_layers": []}),
        encoding="utf-8")
    (art / "v123" / "v123_freshness.json").write_text(
        json.dumps({"verdict": "CONTEXT_COHERENT", "context_lag_days": 1, "disabled_diagnostics": []}),
        encoding="utf-8")
    monkeypatch.setattr(head, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(head, "PREMIUM_DIR", tmp_path / "premium")
    (tmp_path / "premium").mkdir()
    monkeypatch.setattr(head, "HEAD_PATH", tmp_path / "premium" / "premium_daily_head.json")


def test_build_head(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, clean=True)
    h = head.build_premium_head()
    assert h["verdict"] == "PREMIUM_HEAD_BUILT"
    assert h["scope"] == "PREMIUM_ONLY"
    assert h["PREMIUM_STATE"] == "SHORT_PREMIUM_STRONG"
    assert h["TARGET_RECOMMENDATION"] == "z->0.5"
    assert h["scope_clean"] is True
    assert (tmp_path / "premium" / "premium_daily_head.json").exists()


def test_scope_clean_detects_legacy(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, clean=False)  # warning contient SELL_NOW
    h = head.build_premium_head()
    assert h["scope_clean"] is False


def test_no_state(tmp_path, monkeypatch):
    art = tmp_path / "artefacts"
    (art / "v132").mkdir(parents=True)
    (art / "v132" / "indicator_v3_latest.json").write_text(json.dumps({"verdict": "NO_SIGNAL"}), encoding="utf-8")
    monkeypatch.setattr(head, "ARTEFACTS_DIR", art)
    assert head.build_premium_head()["verdict"] == "NO_PREMIUM_STATE"


def test_report_block(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, clean=True)
    block = head.premium_head_report_block()
    assert "Premium head" in block and "z->0.5" in block

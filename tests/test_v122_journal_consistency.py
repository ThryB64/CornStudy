"""Tests V122 — cohérence journal + politique de révision auditée (2026-06-01 STRONG vs EXTREME)."""
from __future__ import annotations

import json

import pandas as pd

import mais.research.v122_journal_consistency as v122


def _journal(tmp_path, tier="SHORT_PREMIUM_EXTREME", z=2.039, settle=227.0):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([
        {"price_date": "2026-05-29", "signal_tier": "SHORT_PREMIUM_EXTREME", "basis_z_used": 2.056,
         "official_front_settlement": 227.0, "basis_official_eur_t": 76.15, "cbot_cents_bu": 446.75,
         "eurusd": 1.1659, "cbot_eur_t": 150.85, "warnings": "NON_REVERSION_RISK_HIGH"},
        {"price_date": "2026-06-01", "signal_tier": tier, "basis_z_used": z,
         "official_front_settlement": settle, "basis_official_eur_t": 75.93, "cbot_cents_bu": 447.25,
         "eurusd": 1.1655, "cbot_eur_t": 151.07, "warnings": "NON_REVERSION_RISK_HIGH"},
    ]).to_parquet(jp, index=False)
    return jp


def _patch(monkeypatch, tmp_path, jp):
    monkeypatch.setattr(v122, "V122_DIR", tmp_path)
    monkeypatch.setattr(v122, "JOURNAL_DIR", tmp_path)
    monkeypatch.setattr(v122, "JOURNAL_PARQUET", jp)
    monkeypatch.setattr(v122, "REVISION_LOG", tmp_path / "revision_log.jsonl")
    monkeypatch.setattr(v122, "DAILY_LATEST", tmp_path / "no_daily.json")
    monkeypatch.setattr(v122, "V101_ARTEFACT", tmp_path / "no_v101.json")
    monkeypatch.setattr(v122, "V99_ARTEFACT", tmp_path / "no_v99.json")


def test_record_status():
    assert v122.classify_record_status("2026-06-01", "2026-06-01") == "PROVISIONAL"
    assert v122.classify_record_status("2026-06-01", "2026-06-02") == "FINAL"


def test_revise_same_day_extreme_to_strong(tmp_path, monkeypatch):
    # journal a 2026-06-01 EXTREME (z 2.039) ; recalcul du même jour -> STRONG (z 1.88, settlement révisé)
    jp = _journal(tmp_path, tier="SHORT_PREMIUM_EXTREME", z=2.039, settle=227.0)
    _patch(monkeypatch, tmp_path, jp)
    recomputed = {"verdict": "OFFICIAL_SIGNAL_COMPUTED", "price_date": "2026-06-01",
                  "signal_tier": "SHORT_PREMIUM_STRONG", "basis_z_used": 1.88,
                  "official_front_settlement": 224.25, "warnings": ["NON_REVERSION_RISK_HIGH"]}
    res = v122.revise_same_day(recomputed, as_of="2026-06-01")
    assert res["status"] == "REVISED"
    assert res["new_signal_tier"] == "SHORT_PREMIUM_STRONG"
    assert "signal_tier" in res["changes"] and "basis_z_used" in res["changes"]
    # le journal est mis à jour et tracé
    j = pd.read_parquet(jp)
    row = j[j["price_date"].astype(str) == "2026-06-01"].iloc[0]
    assert row["signal_tier"] == "SHORT_PREMIUM_STRONG"
    assert row["record_status"] == "REVISED"
    log = (tmp_path / "revision_log.jsonl").read_text().strip().splitlines()
    assert len(log) == 1
    assert json.loads(log[0])["changes"]["signal_tier"]["old"] == "SHORT_PREMIUM_EXTREME"


def test_revise_refused_when_final(tmp_path, monkeypatch):
    jp = _journal(tmp_path)
    _patch(monkeypatch, tmp_path, jp)
    recomputed = {"verdict": "OFFICIAL_SIGNAL_COMPUTED", "price_date": "2026-06-01",
                  "signal_tier": "SHORT_PREMIUM_STRONG", "basis_z_used": 1.88}
    res = v122.revise_same_day(recomputed, as_of="2026-06-02")  # 06-01 est désormais passé -> FINAL
    assert res["status"] == "REFUSED_FINAL"
    j = pd.read_parquet(jp)  # inchangé
    assert j[j["price_date"].astype(str) == "2026-06-01"].iloc[0]["signal_tier"] == "SHORT_PREMIUM_EXTREME"


def test_no_change_when_identical(tmp_path, monkeypatch):
    jp = _journal(tmp_path)
    _patch(monkeypatch, tmp_path, jp)
    same = {"verdict": "OFFICIAL_SIGNAL_COMPUTED", "price_date": "2026-06-01",
            "signal_tier": "SHORT_PREMIUM_EXTREME", "basis_z_used": 2.039,
            "official_front_settlement": 227.0}
    res = v122.revise_same_day(same, as_of="2026-06-01")
    assert res["status"] == "NO_CHANGE"


def test_consistency_check_consistent(tmp_path, monkeypatch):
    jp = _journal(tmp_path)
    _patch(monkeypatch, tmp_path, jp)
    out = v122.consistency_check(as_of="2026-06-01")
    assert out["verdict"] == "LIVE_SIGNAL_CONSISTENT"
    assert out["reference_signal_tier"] == "SHORT_PREMIUM_EXTREME"
    assert out["duplicate_dates"] == []


def test_consistency_detects_layer_mismatch(tmp_path, monkeypatch):
    jp = _journal(tmp_path)
    _patch(monkeypatch, tmp_path, jp)
    # V101 prétend STRONG pour la même date alors que le journal dit EXTREME
    (tmp_path / "no_v101.json").write_text(json.dumps(
        {"verdict": "OFFICIAL_SYNTHESIS_FIXED", "as_of": "2026-06-01",
         "signal_tier": "SHORT_PREMIUM_STRONG"}), encoding="utf-8")
    out = v122.consistency_check(as_of="2026-06-01")
    assert out["verdict"] == "LIVE_SIGNAL_INCONSISTENT"
    assert any(m["layer"] == "v101" for m in out["mismatched_layers"])


def test_report_block(tmp_path, monkeypatch):
    jp = _journal(tmp_path)
    _patch(monkeypatch, tmp_path, jp)
    block = v122.consistency_report_block(as_of="2026-06-01")
    assert "V122" in block and "LIVE_SIGNAL_CONSISTENT" in block

"""Tests V133 — rapport forward mensuel v2 (offline)."""
from __future__ import annotations

import json

import pandas as pd

import mais.research.v133_monthly_forward_report_v2 as v133


def _setup(tmp_path, monkeypatch):
    art = tmp_path / "artefacts"
    art.mkdir()
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([
        {"price_date": "2026-05-29", "signal_tier": "SHORT_PREMIUM_EXTREME", "basis_official_eur_t": 76.15},
        {"price_date": "2026-06-01", "signal_tier": "SHORT_PREMIUM_EXTREME", "basis_official_eur_t": 75.93},
        {"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG", "basis_official_eur_t": 75.03},
    ]).to_parquet(jp, index=False)
    monkeypatch.setattr(v133, "ARTEFACTS_DIR", art)
    monkeypatch.setattr(v133, "V133_DIR", tmp_path)
    monkeypatch.setattr(v133, "REPORTS_DIR", tmp_path / "monthly")
    monkeypatch.setattr(v133, "OFFICIAL_JOURNAL", jp)
    (art / "v122").mkdir()
    (art / "v122" / "v122_consistency.json").write_text(
        json.dumps({"verdict": "LIVE_SIGNAL_CONSISTENT"}), encoding="utf-8")
    (art / "v124").mkdir()
    (art / "v124" / "v124_active_monitoring.json").write_text(
        json.dumps({"status": "HEALTHY", "mfe_eur_t": 1.1, "mae_eur_t": 0.0}), encoding="utf-8")


def test_run(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    out = v133.run_v133_monthly_v2()
    assert out["verdict"] == "MONTHLY_REPORT_V2_BUILT"
    assert out["n_official_days"] == 3
    assert out["consistency_verdict"] == "LIVE_SIGNAL_CONSISTENT"
    assert out["active_signal_status"] == "HEALTHY"
    assert "2026-05" in out["by_month"] and "2026-06" in out["by_month"]
    assert (tmp_path / "monthly" / "latest.md").exists()


def test_no_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(v133, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    assert v133.run_v133_monthly_v2()["verdict"] == "NO_JOURNAL"


def test_report_block(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    v133.run_v133_monthly_v2()
    block = v133.monthly_v2_report_block()
    assert "V133" in block and "LIVE_SIGNAL_CONSISTENT" in block

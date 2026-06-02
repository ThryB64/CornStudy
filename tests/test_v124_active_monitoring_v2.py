"""Tests V124 — santé du signal actif v2 (statuts par paliers 10/20/30 j)."""
from __future__ import annotations

import pandas as pd

import mais.research.v124_active_monitoring_v2 as v124


def test_classify_rules():
    assert v124._classify(days=5, compression=0, mfe=0, cur_z=1.8) == "ACTIVE_EARLY"
    assert v124._classify(days=12, compression=3, mfe=4, cur_z=1.6) == "HEALTHY"
    assert v124._classify(days=12, compression=0, mfe=2, cur_z=1.9) == "SLOW"
    assert v124._classify(days=22, compression=1, mfe=3, cur_z=1.7) == "ADVERSE_LIKE"
    assert v124._classify(days=35, compression=-1, mfe=2, cur_z=2.1) == "DELAYED"
    assert v124._classify(days=10, compression=5, mfe=8, cur_z=0.4) == "TARGET_HIT_z05"
    assert v124._classify(days=10, compression=9, mfe=12, cur_z=-0.1) == "TARGET_HIT_z0"


def _journal(tmp_path, rows):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame(rows).to_parquet(jp, index=False)
    return jp


def test_healthy_episode(tmp_path, monkeypatch):
    rows = [
        {"price_date": "2026-06-01", "signal_tier": "SHORT_PREMIUM_EXTREME", "basis_z_used": 2.04,
         "basis_official_eur_t": 76.0, "median_horizon_days": 23},
        {"price_date": "2026-06-12", "signal_tier": "SHORT_PREMIUM_STRONG", "basis_z_used": 1.6,
         "basis_official_eur_t": 68.0, "median_horizon_days": 23},
    ]
    jp = _journal(tmp_path, rows)
    monkeypatch.setattr(v124, "V124_DIR", tmp_path)
    monkeypatch.setattr(v124, "OFFICIAL_JOURNAL", jp)
    out = v124.monitor_active_signal_v2()
    assert out["verdict"] == "ACTIVE_MONITORING_READY"
    assert out["status"] == "HEALTHY"
    assert out["compression_realized_eur_t"] == 8.0
    assert out["days_since_entry"] == 11


def test_no_active_signal(tmp_path, monkeypatch):
    jp = _journal(tmp_path, [{"price_date": "2026-06-01", "signal_tier": "NO_SIGNAL",
                              "basis_z_used": 0.5, "basis_official_eur_t": 40.0, "median_horizon_days": 23}])
    monkeypatch.setattr(v124, "V124_DIR", tmp_path)
    monkeypatch.setattr(v124, "OFFICIAL_JOURNAL", jp)
    assert v124.monitor_active_signal_v2()["verdict"] == "NO_ACTIVE_SIGNAL"


def test_report_block(tmp_path, monkeypatch):
    rows = [
        {"price_date": "2026-06-01", "signal_tier": "SHORT_PREMIUM_EXTREME", "basis_z_used": 2.04,
         "basis_official_eur_t": 76.0, "median_horizon_days": 23},
        {"price_date": "2026-06-12", "signal_tier": "SHORT_PREMIUM_STRONG", "basis_z_used": 1.6,
         "basis_official_eur_t": 68.0, "median_horizon_days": 23},
    ]
    jp = _journal(tmp_path, rows)
    monkeypatch.setattr(v124, "V124_DIR", tmp_path)
    monkeypatch.setattr(v124, "OFFICIAL_JOURNAL", jp)
    block = v124.active_monitoring_v2_report_block()
    assert "V124" in block and "HEALTHY" in block

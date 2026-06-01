"""Tests V102 — suivi dynamique du signal actif (offline, journal mocké)."""
from __future__ import annotations

import pandas as pd

import mais.research.v102_active_signal_monitoring as v102


def _journal(rows):
    return pd.DataFrame(rows)


def test_healthy_compressing(tmp_path, monkeypatch):
    jp = tmp_path / "j.parquet"
    _journal([
        {"price_date": pd.Timestamp("2026-05-29"), "signal_tier": "SHORT_PREMIUM_EXTREME",
         "basis_official_eur_t": 76.0, "basis_z_used": 2.05},
        {"price_date": pd.Timestamp("2026-06-01"), "signal_tier": "SHORT_PREMIUM_EXTREME",
         "basis_official_eur_t": 74.0, "basis_z_used": 1.9},
    ]).to_parquet(jp, index=False)
    monkeypatch.setattr(v102, "V102_DIR", tmp_path)
    monkeypatch.setattr(v102, "OFFICIAL_JOURNAL", jp)
    out = v102.monitor_active_signal()
    assert out["verdict"] == "ACTIVE_SIGNAL_MONITORED"
    assert out["compression_realized_eur_t"] == 2.0
    assert out["status"] == "HEALTHY_COMPRESSING"


def test_adverse_like(tmp_path, monkeypatch):
    jp = tmp_path / "j.parquet"
    rows = [{"price_date": pd.Timestamp("2026-04-01") + pd.Timedelta(days=3 * k),
             "signal_tier": "SHORT_PREMIUM_MODERATE",
             "basis_official_eur_t": 50.0 + (k % 2), "basis_z_used": 1.2}
            for k in range(10)]  # ~27 jours, pas de compression, MFE faible
    _journal(rows).to_parquet(jp, index=False)
    monkeypatch.setattr(v102, "V102_DIR", tmp_path)
    monkeypatch.setattr(v102, "OFFICIAL_JOURNAL", jp)
    out = v102.monitor_active_signal()
    assert out["days_since_entry"] >= 20
    assert out["status"] in ("ADVERSE_LIKE_LOW_MFE_LONG", "WARNING_COMPRESSION_DELAYED")


def test_no_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(v102, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    assert v102.monitor_active_signal()["verdict"] == "NO_OFFICIAL_JOURNAL"

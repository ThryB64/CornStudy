"""Tests V144 — validation officielle vs proxy par jalons."""
from __future__ import annotations

import pandas as pd

import mais.premium.official_proxy_validation as pv


def _journal(tmp_path, n):
    jp = tmp_path / "journal.parquet"
    dates = pd.bdate_range("2026-05-29", periods=n)
    pd.DataFrame({"price_date": [str(d.date()) for d in dates],
                  "basis_official_eur_t": [75.0] * n}).to_parquet(jp, index=False)
    return jp


def test_not_enough(tmp_path, monkeypatch):
    monkeypatch.setattr(pv, "OFFICIAL_JOURNAL", _journal(tmp_path, 3))
    monkeypatch.setattr(pv, "V_DIR", tmp_path)
    assert pv.run_v144_proxy_validation()["verdict"] == "NOT_ENOUGH"


def test_stage_10(tmp_path, monkeypatch):
    monkeypatch.setattr(pv, "OFFICIAL_JOURNAL", _journal(tmp_path, 15))
    monkeypatch.setattr(pv, "V_DIR", tmp_path)
    out = pv.run_v144_proxy_validation()
    assert out["verdict"] == "STAGE_10_TECHNICAL_OK"
    assert out["z_official_rolling"] is None


def test_no_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(pv, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    assert pv.run_v144_proxy_validation()["verdict"] == "NO_JOURNAL"

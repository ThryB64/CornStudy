"""Tests V103 — dashboard proxy/officiel (offline)."""
from __future__ import annotations

import json

import pandas as pd

import mais.research.v103_proxy_official_dashboard as v103


def test_run_v103(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([
        {"price_date": pd.Timestamp("2026-05-29"), "signal_tier": "SHORT_PREMIUM_EXTREME",
         "basis_official_eur_t": 76.15, "basis_z_used": 2.056, "z_source": "proxy_implied"},
        {"price_date": pd.Timestamp("2026-06-01"), "signal_tier": "SHORT_PREMIUM_EXTREME",
         "basis_official_eur_t": 75.93, "basis_z_used": 2.039, "z_source": "proxy_implied"},
    ]).to_parquet(jp, index=False)
    audit = tmp_path / "proxy.json"
    audit.write_text(json.dumps({"correlation": 0.94, "mae_eur_t": 37.3, "rmse_eur_t": 40.3,
                                 "verdict": "PROXY_FORBIDDEN"}), encoding="utf-8")
    monkeypatch.setattr(v103, "V103_DIR", tmp_path)
    monkeypatch.setattr(v103, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(v103, "PROXY_AUDIT", audit)
    monkeypatch.setattr(v103, "DASHBOARD_MD", tmp_path / "dash.md")
    out = v103.run_v103_dashboard()
    assert out["version"] == "V103-PROXY-OFFICIAL-DASHBOARD"
    assert out["days_accumulated"] == 2
    assert out["next_milestone"] == 10
    assert out["verdict"] == "PROXY_RESEARCH_ONLY"
    assert out["historical_proxy_vs_official"]["verdict"] == "PROXY_FORBIDDEN"
    assert (tmp_path / "dash.md").exists()


def test_run_v103_no_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(v103, "V103_DIR", tmp_path)
    monkeypatch.setattr(v103, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    monkeypatch.setattr(v103, "PROXY_AUDIT", tmp_path / "absent.json")
    monkeypatch.setattr(v103, "DASHBOARD_MD", tmp_path / "dash.md")
    out = v103.run_v103_dashboard()
    assert out["days_accumulated"] == 0

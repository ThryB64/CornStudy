"""Tests V59 — rapport forward mensuel (offline, journaux synthétiques)."""
from __future__ import annotations

import pandas as pd

import mais.research.v59_monthly_forward_report as v59


def _signals():
    return pd.DataFrame([
        {"price_date": "2026-05-29", "signal_tier": "SHORT_PREMIUM_EXTREME",
         "basis_official_eur_t": 76.1, "basis_z_used": 2.05, "z_source": "proxy_implied", "warnings": "ROLL_RISK"},
        {"price_date": "2026-06-01", "signal_tier": "SHORT_PREMIUM_EXTREME",
         "basis_official_eur_t": 75.9, "basis_z_used": 2.03, "z_source": "proxy_implied", "warnings": ""},
        {"price_date": "2026-06-02", "signal_tier": "NO_SIGNAL",
         "basis_official_eur_t": 40.0, "basis_z_used": 0.3, "z_source": "proxy_implied", "warnings": ""},
    ])


def _matif():
    return pd.DataFrame([{"price_date": "2026-06-01", "matif_wheat_corn_ratio": 0.914}])


def test_build_monthly():
    m = v59.build_monthly(_signals(), _matif())
    assert set(m["month"]) == {"2026-05", "2026-06"}
    jun = m[m["month"] == "2026-06"].iloc[0]
    assert jun["n_official_days"] == 2
    assert jun["n_signals"] == 1
    assert abs(jun["mean_matif_wheat_corn_ratio"] - 0.914) < 1e-6


def test_run_v59(tmp_path, monkeypatch):
    sig_path = tmp_path / "sig.parquet"
    _signals().to_parquet(sig_path, index=False)
    mat_path = tmp_path / "matif.jsonl"
    mat_path.write_text('{"price_date": "2026-06-01", "matif_wheat_corn_ratio": 0.914}\n', encoding="utf-8")
    monkeypatch.setattr(v59, "V59_DIR", tmp_path)
    monkeypatch.setattr(v59, "REPORT_MD", tmp_path / "FORWARD_MONTHLY_REPORT.md")
    monkeypatch.setattr(v59, "SIGNAL_JOURNAL", sig_path)
    monkeypatch.setattr(v59, "MATIF_JOURNAL", mat_path)
    monkeypatch.setattr(v59, "WEATHER_JOURNAL", tmp_path / "none.jsonl")
    out = v59.run_v59_report()
    assert out["version"] == "V59-MONTHLY-FORWARD"
    assert out["n_months"] == 2
    assert (tmp_path / "FORWARD_MONTHLY_REPORT.md").exists()
    md = (tmp_path / "FORWARD_MONTHLY_REPORT.md").read_text(encoding="utf-8")
    assert "nan" not in md.lower()


def test_run_v59_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(v59, "V59_DIR", tmp_path)
    monkeypatch.setattr(v59, "REPORT_MD", tmp_path / "r.md")
    monkeypatch.setattr(v59, "SIGNAL_JOURNAL", tmp_path / "none.parquet")
    monkeypatch.setattr(v59, "MATIF_JOURNAL", tmp_path / "none.jsonl")
    monkeypatch.setattr(v59, "WEATHER_JOURNAL", tmp_path / "none.jsonl")
    out = v59.run_v59_report()
    assert out["thin_data"] is True
    assert out["n_signal_days"] == 0

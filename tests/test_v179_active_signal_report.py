"""V179 — rapport signal actif : assemblage lecture seule, markdown, statuts."""
from __future__ import annotations

import json

import pandas as pd

from mais.premium import v179_active_signal_report as v179


def _core_ok():
    return {"verdict": "ACTIVE_MONITORING_READY", "status": "HEALTHY",
            "entry_date": "2026-05-29", "current_date": "2026-06-11",
            "days_since_entry": 13, "entry_tier": "SHORT_PREMIUM_EXTREME",
            "current_tier": "SHORT_PREMIUM_STRONG", "entry_z": 2.056, "current_z": 1.872,
            "entry_basis_eur_t": 76.15, "current_basis_eur_t": 73.79,
            "compression_realized_eur_t": 2.36, "mfe_eur_t": 3.56, "mae_eur_t": 0.28,
            "distance_to_z05": 1.372, "distance_to_z0": 1.872, "median_horizon_days": 23}


def _journal():
    dates = pd.date_range("2026-05-29", periods=9, freq="B").strftime("%Y-%m-%d")
    return pd.DataFrame({"price_date": dates, "basis_official_eur_t": 75.0,
                         "basis_z_used": 1.9, "signal_tier": "SHORT_PREMIUM_STRONG",
                         "cbot_eur_t": 142.0, "record_status": "FINAL"})


def test_report_built_and_markdown(monkeypatch, tmp_path):
    import mais.research.v124_active_monitoring_v2 as v124
    monkeypatch.setattr(v124, "monitor_active_signal_v2", _core_ok)
    monkeypatch.setattr(v179, "_load_official", _journal)
    monkeypatch.setattr(v179, "V179_DIR", tmp_path)
    monkeypatch.setattr(v179, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(v179, "CURVE_HISTORY", tmp_path / "absent1.parquet")
    monkeypatch.setattr(v179, "MATIF_HISTORY", tmp_path / "absent2.parquet")
    monkeypatch.setattr(v179, "HEAD", tmp_path / "absent3.json")
    monkeypatch.setattr(v179, "STATE_MACHINE", tmp_path / "absent4.json")
    out = v179.run_v179_active_signal_report()
    assert out["verdict"] == "REPORT_BUILT"
    assert out["signal_status"] == "HEALTHY"
    assert len(out["daily_table"]) == 9
    md = (tmp_path / "reports" / "latest.md").read_text(encoding="utf-8")
    assert "HEALTHY" in md and "2026-05-29" in md and "Jour par jour" in md


def test_no_active_signal_short_circuit(monkeypatch, tmp_path):
    import mais.research.v124_active_monitoring_v2 as v124
    monkeypatch.setattr(v124, "monitor_active_signal_v2",
                        lambda: {"verdict": "NO_ACTIVE_SIGNAL"})
    monkeypatch.setattr(v179, "V179_DIR", tmp_path)
    out = v179.run_v179_active_signal_report()
    assert out["verdict"] == "NO_ACTIVE_SIGNAL"
    assert json.loads((tmp_path / "v179_active_signal.json").read_text())["verdict"] == "NO_ACTIVE_SIGNAL"


def test_context_merges_curve_and_matif(monkeypatch, tmp_path):
    import mais.research.v124_active_monitoring_v2 as v124
    monkeypatch.setattr(v124, "monitor_active_signal_v2", _core_ok)
    monkeypatch.setattr(v179, "_load_official", _journal)
    j = _journal()
    curve = pd.DataFrame({"price_date": j["price_date"], "front_next_spread": 9.25,
                          "curve_shape": "BACKWARDATION"})
    matif = pd.DataFrame({"price_date": j["price_date"], "ratio": 1.41})
    (tmp_path / "d").mkdir()
    curve.to_parquet(tmp_path / "d" / "curve.parquet", index=False)
    matif.to_parquet(tmp_path / "d" / "matif.parquet", index=False)
    monkeypatch.setattr(v179, "CURVE_HISTORY", tmp_path / "d" / "curve.parquet")
    monkeypatch.setattr(v179, "MATIF_HISTORY", tmp_path / "d" / "matif.parquet")
    monkeypatch.setattr(v179, "V179_DIR", tmp_path)
    monkeypatch.setattr(v179, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(v179, "HEAD", tmp_path / "absent.json")
    monkeypatch.setattr(v179, "STATE_MACHINE", tmp_path / "absent.json")
    out = v179.run_v179_active_signal_report()
    row = out["daily_table"][0]
    assert row["curve_spread"] == 9.25
    assert row["matif_wheat_corn"] == 1.41

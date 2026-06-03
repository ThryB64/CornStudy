"""Tests VN-C4 — forecast revision tape (offline, journal mocké)."""
from __future__ import annotations

import json

import mais.research.v_forecast_revision_tape as rt


def _journal(tmp_path, n=3):
    p = tmp_path / "wx.jsonl"
    lines = []
    for i in range(n):
        lines.append(json.dumps({"status": "OK", "region": "us", "issue_date": f"2026-06-0{i+1}",
                                 "heat_days_gt32": 5 + i * 2, "heat_days_gt35": i, "precip_total_mm": 10 - i,
                                 "stress_score": 1 + i}))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_forward_only_when_thin(tmp_path, monkeypatch):
    p = tmp_path / "wx.jsonl"
    p.write_text(json.dumps({"status": "OK", "region": "us", "issue_date": "2026-06-01",
                             "heat_days_gt32": 5, "stress_score": 1}) + "\n", encoding="utf-8")
    monkeypatch.setattr(rt, "WX_JOURNAL", p)
    monkeypatch.setattr(rt, "V_DIR", tmp_path)
    monkeypatch.setattr(rt, "TAPE", tmp_path / "tape.parquet")
    assert rt.run_v_revision_tape()["verdict"] == "FORWARD_ONLY_ACCUMULATING"


def test_revision_tape_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "WX_JOURNAL", _journal(tmp_path, 3))
    monkeypatch.setattr(rt, "V_DIR", tmp_path)
    monkeypatch.setattr(rt, "TAPE", tmp_path / "tape.parquet")
    out = rt.run_v_revision_tape()
    assert out["verdict"] == "REVISION_TAPE_READY"
    assert out["n_revisions"] == 2  # 3 émissions -> 2 révisions
    assert out["by_region_last"]["us"]["d_heat32"] == 2.0
    assert (tmp_path / "tape.parquet").exists()


def test_build_revision_tape(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "WX_JOURNAL", _journal(tmp_path, 3))
    t = rt.build_revision_tape("us")
    assert len(t) == 2
    assert "d_score" in t.columns

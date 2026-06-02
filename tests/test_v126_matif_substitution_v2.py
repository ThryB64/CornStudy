"""Tests V126 — substitution MATIF v2 (offline, master mocké)."""
from __future__ import annotations

import json

import mais.research.v126_matif_substitution_v2 as v126


def _journal(tmp_path, n=2):
    p = tmp_path / "matif.jsonl"
    lines = []
    for i in range(n):
        lines.append(json.dumps({"status": "OK", "price_date": f"2026-06-0{i+1}",
                                 "matif_wheat_corn_ratio": 0.91 + i * 0.001,
                                 "matif_wheat_settle": 207.5, "matif_corn_settle": 227.0}))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_build_ratio_history(tmp_path, monkeypatch):
    monkeypatch.setattr(v126, "MATIF_JSONL", _journal(tmp_path, 3))
    h = v126.build_ratio_history()
    assert len(h) == 3
    assert "ratio" in h.columns


def test_signal_ready_when_proxy_confirmed(tmp_path, monkeypatch):
    monkeypatch.setattr(v126, "V126_DIR", tmp_path)
    monkeypatch.setattr(v126, "MATIF_JSONL", _journal(tmp_path, 2))
    monkeypatch.setattr(v126, "RATIO_HISTORY", tmp_path / "hist.parquet")
    monkeypatch.setattr(v126, "_proxy_relation_on_master",
                        lambda: {"n": 2000, "corr_ratio_basis": 0.59, "n_active": 300,
                                 "corr_ratio_basis_active": 0.42})
    out = v126.run_v126_substitution()
    assert out["verdict"] == "SUBSTITUTION_SIGNAL_READY"
    assert out["proxy_relation_confirmed"] is True
    assert out["matif_ratio_last"] is not None
    assert out["historical_official_status"] == "WAITING_DATA"


def test_data_blocked_when_no_master(tmp_path, monkeypatch):
    monkeypatch.setattr(v126, "V126_DIR", tmp_path)
    monkeypatch.setattr(v126, "MATIF_JSONL", _journal(tmp_path, 1))
    monkeypatch.setattr(v126, "RATIO_HISTORY", tmp_path / "hist.parquet")
    monkeypatch.setattr(v126, "_proxy_relation_on_master", lambda: None)
    assert v126.run_v126_substitution()["verdict"] == "DATA_BLOCKED"


def test_proxy_ok_forward_accumulating(tmp_path, monkeypatch):
    monkeypatch.setattr(v126, "V126_DIR", tmp_path)
    monkeypatch.setattr(v126, "MATIF_JSONL", _journal(tmp_path, 1))
    monkeypatch.setattr(v126, "RATIO_HISTORY", tmp_path / "hist.parquet")
    monkeypatch.setattr(v126, "_proxy_relation_on_master",
                        lambda: {"n": 2000, "corr_ratio_basis": 0.1, "n_active": 300,
                                 "corr_ratio_basis_active": 0.05})
    out = v126.run_v126_substitution()
    assert out["verdict"] == "PROXY_OK_FORWARD_ACCUMULATING"


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v126, "V126_DIR", tmp_path)
    monkeypatch.setattr(v126, "MATIF_JSONL", _journal(tmp_path, 2))
    monkeypatch.setattr(v126, "RATIO_HISTORY", tmp_path / "hist.parquet")
    monkeypatch.setattr(v126, "_proxy_relation_on_master",
                        lambda: {"n": 2000, "corr_ratio_basis": 0.59, "n_active": 300,
                                 "corr_ratio_basis_active": 0.42})
    block = v126.substitution_v2_report_block()
    assert "V126" in block and "SUBSTITUTION_SIGNAL_READY" in block

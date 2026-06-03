"""Tests VN-A3 — audit du signe de courbe."""
from __future__ import annotations

import pandas as pd

import mais.premium.curve_sign_audit as cs


def test_consistent(tmp_path, monkeypatch):
    h = pd.DataFrame({"price_date": pd.to_datetime(["2026-05-29", "2026-06-01"]),
                      "front_next_spread": [15.25, 11.75], "curve_shape": ["BACKWARDATION", "BACKWARDATION"]})
    p = tmp_path / "hist.parquet"
    h.to_parquet(p, index=False)
    monkeypatch.setattr(cs, "CURVE_HISTORY", p)
    monkeypatch.setattr(cs, "V_DIR", tmp_path)
    out = cs.audit_curve_signs()
    assert out["verdict"] == "CURVE_SIGN_CONSISTENT"
    assert out["n_mismatch"] == 0


def test_inconsistent(tmp_path, monkeypatch):
    h = pd.DataFrame({"price_date": pd.to_datetime(["2026-05-29"]),
                      "front_next_spread": [-5.0], "curve_shape": ["BACKWARDATION"]})  # spread<0 mais labellisé BACKW
    p = tmp_path / "hist.parquet"
    h.to_parquet(p, index=False)
    monkeypatch.setattr(cs, "CURVE_HISTORY", p)
    monkeypatch.setattr(cs, "V_DIR", tmp_path)
    out = cs.audit_curve_signs()
    assert out["verdict"] == "CURVE_SIGN_INCONSISTENT"
    assert out["n_mismatch"] == 1


def test_no_history(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "CURVE_HISTORY", tmp_path / "absent.parquet")
    assert cs.audit_curve_signs()["verdict"] == "NO_CURVE_HISTORY"

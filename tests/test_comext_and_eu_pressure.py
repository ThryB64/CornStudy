"""Tests VN-C2/C3 — COMEXT bulk (best-effort honnête) + tension physique UE."""
from __future__ import annotations

import pandas as pd

import mais.collect.comext_bulk as cx
import mais.research.v_eu_physical_pressure as ep


def test_comext_data_blocked_offline():
    out = cx.run_comext_status(try_network=False)
    assert out["verdict"] == "DATA_BLOCKED_THIS_RUN"
    assert "PARTIAL_BEST_EFFORT" in out["requalified_from"]


def test_comext_series_ready_with_mock():
    s = pd.DataFrame({"imports": [1, 2, 3]},
                     index=pd.period_range("2025-01", periods=3, freq="M").astype(str))
    out = cx.run_comext_status(try_network=True, fetch=lambda: s)
    assert out["verdict"] == "COMEXT_SERIES_READY"
    assert out["n_months"] == 3


def test_comext_fetch_failure_returns_none():
    def _boom():
        raise RuntimeError("network")
    assert cx.fetch_comext_maize(try_network=True, fetch=_boom) is None


def test_eu_pressure_watchlist(tmp_path, monkeypatch):
    monkeypatch.setattr(ep, "V_DIR", tmp_path)
    out = ep.run_eu_physical_pressure(try_network=False)
    # COMEXT bloqué ce run -> WATCHLIST
    assert out["verdict"] == "WATCHLIST_PARTIAL_COMPONENTS"
    assert "comext" in out["components"]
    assert "YoY" in out["detrend_policy"]

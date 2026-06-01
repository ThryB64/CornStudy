"""Tests V109 — courbe EMA officielle live -> PHYSICAL_TENSION (offline, fetch mocké)."""
from __future__ import annotations

import pandas as pd

import mais.collect.euronext_official_live as live
import mais.research.v109_ema_curve_live_tension as v109


def _curve(spread_backwardation=True):
    # front liquide = Q2026 (Aug), next = X2026 (Nov)
    aug = 224.25 if spread_backwardation else 210.0
    return pd.DataFrame({
        "price_date": [pd.Timestamp("2026-06-01")] * 4,
        "contract_month": [6, 8, 11, 3],
        "contract_year": [2026, 2026, 2026, 2027],
        "contract_code": ["EMA_M2026", "EMA_Q2026", "EMA_X2026", "EMA_H2027"],
        "settlement": [214.25, aug, 212.5, 216.0],
        "open_interest": [636.0, 15091.0, 12379.0, 2056.0],
    })


def test_curve_structure_backwardation():
    st = v109.curve_structure(_curve(True))
    assert st["front_contract"] == "EMA_Q2026"
    assert st["next_contract"] == "EMA_X2026"
    assert st["backwardation"] is True
    assert st["front_next_spread"] > 0


def test_run_v109(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": pd.Timestamp("2026-06-01"), "basis_z_used": 2.04}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v109, "V109_DIR", tmp_path)
    monkeypatch.setattr(v109, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(live, "fetch_official_ema", lambda *a, **k: _curve(True))
    out = v109.run_v109_curve_tension(try_network=True)
    assert out["version"] == "V109-EMA-CURVE-TENSION"
    assert out["physical_tension_live"] == "HIGH"  # backwardation marquée + signal actif
    assert out["verdict"] == "PHYSICAL_TENSION_LIVE_UNBLOCKED"


def test_run_v109_contango(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": pd.Timestamp("2026-06-01"), "basis_z_used": 2.04}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v109, "V109_DIR", tmp_path)
    monkeypatch.setattr(v109, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(live, "fetch_official_ema", lambda *a, **k: _curve(False))
    out = v109.run_v109_curve_tension(try_network=True)
    assert out["physical_tension_live"] in ("LOW", "MEDIUM")  # contango -> moins de tension


def test_offline():
    assert v109.run_v109_curve_tension(try_network=False)["verdict"] == "OFFLINE_SKIP"

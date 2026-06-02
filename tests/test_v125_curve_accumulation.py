"""Tests V125 — accumulation de la courbe EMA + tendance de tension (offline)."""
from __future__ import annotations

import pandas as pd

import mais.research.v125_curve_accumulation as v125


def _store(spreads_by_date):
    """Store multi-dates : front Q (most liquid) vs X next ; spread = settle_Q - settle_X."""
    rows = []
    for d, (q_settle, x_settle) in spreads_by_date.items():
        rows += [
            {"price_date": pd.Timestamp(d), "contract_month": 8, "contract_year": 2026,
             "contract_code": "EMA_Q2026", "settlement": q_settle, "open_interest": 15000.0},
            {"price_date": pd.Timestamp(d), "contract_month": 11, "contract_year": 2026,
             "contract_code": "EMA_X2026", "settlement": x_settle, "open_interest": 12000.0},
            {"price_date": pd.Timestamp(d), "contract_month": 3, "contract_year": 2027,
             "contract_code": "EMA_H2027", "settlement": x_settle - 2, "open_interest": 2000.0},
        ]
    return pd.DataFrame(rows)


def test_build_curve_history():
    store = _store({"2026-05-29": (227.0, 211.75), "2026-06-01": (224.25, 212.5)})
    hist = v125.build_curve_history(store)
    assert len(hist) == 2
    assert hist["front_contract"].iloc[0] == "EMA_Q2026"
    assert bool(hist["backwardation"].all())


def test_narrowing_trend(tmp_path, monkeypatch):
    monkeypatch.setattr(v125, "V125_DIR", tmp_path)
    monkeypatch.setattr(v125, "CURVE_HISTORY", tmp_path / "hist.parquet")
    sp = tmp_path / "store.parquet"
    # spread +15.25 -> +11.75 : NARROWING ; dernier spread 11.75 >= 5 -> HIGH
    _store({"2026-05-29": (227.0, 211.75), "2026-06-01": (224.25, 212.5)}).to_parquet(sp, index=False)
    monkeypatch.setattr(v125, "SNAPSHOT_STORE", sp)
    out = v125.run_v125_curve_accumulation()
    assert out["verdict"] == "CURVE_HISTORY_BUILT"
    assert out["n_days_accumulated"] == 2
    assert out["spread_trend"] == "NARROWING"
    assert out["physical_tension_tier"] == "HIGH"


def test_widening_trend(tmp_path, monkeypatch):
    monkeypatch.setattr(v125, "V125_DIR", tmp_path)
    monkeypatch.setattr(v125, "CURVE_HISTORY", tmp_path / "hist.parquet")
    sp = tmp_path / "store.parquet"
    # spread +2 -> +8 : WIDENING
    _store({"2026-05-29": (214.0, 212.0), "2026-06-01": (220.0, 212.0)}).to_parquet(sp, index=False)
    monkeypatch.setattr(v125, "SNAPSHOT_STORE", sp)
    out = v125.run_v125_curve_accumulation()
    assert out["spread_trend"] == "WIDENING"
    assert out["physical_tension_tier"] == "HIGH"


def test_no_history(tmp_path, monkeypatch):
    monkeypatch.setattr(v125, "SNAPSHOT_STORE", tmp_path / "absent.parquet")
    assert v125.run_v125_curve_accumulation()["verdict"] == "NO_CURVE_HISTORY"


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v125, "V125_DIR", tmp_path)
    monkeypatch.setattr(v125, "CURVE_HISTORY", tmp_path / "hist.parquet")
    sp = tmp_path / "store.parquet"
    _store({"2026-05-29": (227.0, 211.75), "2026-06-01": (224.25, 212.5)}).to_parquet(sp, index=False)
    monkeypatch.setattr(v125, "SNAPSHOT_STORE", sp)
    block = v125.curve_accumulation_report_block()
    assert "V125" in block and "NARROWING" in block

"""Tests V30 — structure de courbe officielle (contango/backwardation), offline."""
from __future__ import annotations

import pandas as pd

import mais.research.v30_official_curve_structure as v30


def _fake_snapshot(tmp_path):
    rows = [
        ("2026-05-29", 6, 2026, "M", "EMA_M2026", 236.0, 1137, 681),
        ("2026-05-29", 8, 2026, "Q", "EMA_Q2026", 227.0, 14447, 2001),
        ("2026-05-29", 11, 2026, "X", "EMA_X2026", 211.75, 12253, 1465),
        ("2026-05-29", 3, 2027, "H", "EMA_H2027", 215.50, 2049, 55),
        ("2026-05-29", 8, 2027, "Q", "EMA_Q2027", 219.25, 0, None),  # filler illiquide
    ]
    df = pd.DataFrame(rows, columns=["price_date", "contract_month", "contract_year", "month_code",
                                     "contract_code", "settlement", "open_interest", "volume"])
    p = tmp_path / "official_daily.parquet"
    df.to_parquet(p, index=False)
    return p


def test_curve_drops_illiquid_and_classifies(tmp_path, monkeypatch):
    monkeypatch.setattr(v30, "OFFICIAL_PARQUET", _fake_snapshot(tmp_path))
    monkeypatch.setattr(v30, "V30_DIR", tmp_path)
    out = v30.compute_curve_structure()
    assert out["verdict"] == "OFFICIAL_CURVE_CHARACTERISED"
    assert "EMA_Q2027" not in out["contracts"]  # OI 0 et volume None -> exclu
    assert out["most_liquid_contract"] == "EMA_Q2026"
    assert out["nearby_shape"] == "BACKWARDATION"  # 236 > 227
    assert out["front_second_spread_eur_t"] == 9.0


def test_curve_context_compact(tmp_path, monkeypatch):
    monkeypatch.setattr(v30, "OFFICIAL_PARQUET", _fake_snapshot(tmp_path))
    monkeypatch.setattr(v30, "V30_DIR", tmp_path)
    ctx = v30.curve_context_for_journal()
    assert ctx["curve_shape"] == "BACKWARDATION"
    assert ctx["most_liquid_contract"] == "EMA_Q2026"


def test_no_data_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(v30, "OFFICIAL_PARQUET", tmp_path / "missing.parquet")
    assert v30.compute_curve_structure()["verdict"] == "NO_OFFICIAL_DATA"

"""Tests V26 — parser officiel Euronext + validation niveaux (offline-safe)."""
from __future__ import annotations

from mais.collect.euronext_official_live import parse_official_prices
from mais.research.v26_official_ema_validation import run_proxy_vs_official_levels

SAMPLE_HTML = """
<table><tr><td> Prices - 29 May 2026 Delivery Bid Ask Last Time +/- Day Vol. Open High Low Settl. O.I
Jun 2026 233.75 238.75 235.00 20:02 -18.25 681 247.75 247.75 230.75 236.00 1,137
Aug 2026 226.25 229.00 227.75 20:14 0.50 2,001 229.00 229.00 222.00 227.00 14,447
Nov 2026 211.00 212.25 211.50 20:06 -2.75 1,465 214.50 214.50 211.00 211.75 12,253
Mar 2027 - - - - 0.00 - - - - 215.50 2,049
</td></tr></table>
"""


def test_parse_official_prices():
    price_date, rows = parse_official_prices(SAMPLE_HTML)
    assert price_date is not None and str(price_date) == "2026-05-29"
    assert len(rows) == 4
    aug = next(r for r in rows if r["contract_month"] == 8)
    assert aug["month_code"] == "Q"
    assert aug["settlement"] == 227.00
    assert aug["open_interest"] == 14447.0
    assert aug["contract_code"] == "EMA_Q2026"
    assert aug["is_proxy"] is False
    # missing values -> None
    mar = next(r for r in rows if r["contract_month"] == 3)
    assert mar["last"] is None and mar["settlement"] == 215.50


def test_no_january_in_official():
    _, rows = parse_official_prices(SAMPLE_HTML)
    assert all(r["month_code"] in {"H", "M", "Q", "X"} for r in rows)


def test_proxy_vs_official_levels_runs(tmp_path, monkeypatch):
    import mais.research.v26_official_ema_validation as mod
    monkeypatch.setattr(mod, "V26_DIR", tmp_path)
    out = run_proxy_vs_official_levels(official_basis=76.0)
    assert out["verdict"] in {"PROXY_VS_OFFICIAL_LEVELS_DONE", "MISSING_PROXY", "MISSING_BASIS_COL"}

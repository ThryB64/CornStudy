"""Tests V128 — probe intraday CBOT aligné + accumulation forward (offline, fetch mocké)."""
from __future__ import annotations

import pandas as pd

import mais.research.intraday_aligned_basis as v60i
import mais.research.v128_intraday_aligned_probe as v128


def _intraday():
    # 3 jours, barres horaires 10h->20h UTC ; move = close - barre@settle
    idx = []
    vals = []
    for day in ("2026-05-29", "2026-06-01", "2026-06-02"):
        for h in range(10, 21):
            idx.append(pd.Timestamp(f"{day} {h:02d}:00:00"))
            vals.append(440 + h * 0.1 + (1 if day == "2026-06-02" else 0))
    return pd.DataFrame({"close": vals}, index=pd.DatetimeIndex(idx))


def test_daily_moves():
    m = v128._daily_settle_close_moves(_intraday())
    assert len(m) == 3
    assert "move" in m.columns


def test_run_watchlist(tmp_path, monkeypatch):
    monkeypatch.setattr(v128, "V128_DIR", tmp_path)
    monkeypatch.setattr(v128, "JOURNAL", tmp_path / "intraday.jsonl")
    monkeypatch.setattr(v60i, "fetch_cbot_intraday", lambda try_network=True, **k: _intraday())
    out = v128.run_v128_intraday(try_network=True)
    assert out["verdict"] == "WATCHLIST"
    assert out["historical_status"] == "DATA_BLOCKED_PAID"
    assert out["journal_appended_today"] == 3
    # ré-exécution : pas de doublon
    out2 = v128.run_v128_intraday(try_network=True)
    assert out2["journal_appended_today"] == 0
    assert out2["journal_days_total"] == 3


def test_data_blocked_offline(monkeypatch):
    monkeypatch.setattr(v60i, "fetch_cbot_intraday", lambda try_network=True, **k: pd.DataFrame())
    out = v128.run_v128_intraday(try_network=False)
    assert out["verdict"] == "DATA_BLOCKED"


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v128, "V128_DIR", tmp_path)
    monkeypatch.setattr(v128, "JOURNAL", tmp_path / "intraday.jsonl")
    monkeypatch.setattr(v60i, "fetch_cbot_intraday", lambda try_network=True, **k: _intraday())
    v128.run_v128_intraday(try_network=True)
    block = v128.intraday_probe_report_block()
    assert "V128" in block and "WATCHLIST" in block

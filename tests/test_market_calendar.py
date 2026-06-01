"""Tests V42-01 — calendrier de marché Euronext."""
from __future__ import annotations

import pandas as pd

from mais.calendar import (
    classify_session,
    expected_settlement_date,
    is_euronext_holiday,
    is_trading_day,
    is_weekend,
    next_trading_day,
    previous_trading_day,
    sessions_between,
)


def test_weekend_is_no_session():
    assert is_weekend("2026-05-30")  # samedi
    assert is_weekend("2026-05-31")  # dimanche
    assert classify_session("2026-05-30") == "NO_SESSION_WEEKEND"
    assert not is_trading_day("2026-05-31")


def test_friday_and_monday_are_trading():
    assert is_trading_day("2026-05-29")  # vendredi
    assert is_trading_day("2026-06-01")  # lundi
    assert classify_session("2026-06-01") == "TRADING_SESSION"


def test_euronext_holidays_2026():
    # Pâques 2026 = 5 avril -> Vendredi saint 3 avr, Lundi de Pâques 6 avr
    for d in ["2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-12-25"]:
        assert is_euronext_holiday(d), d
        assert classify_session(d) in {"NO_SESSION_HOLIDAY", "NO_SESSION_WEEKEND"}
    assert is_trading_day("2026-07-14")  # 14 juillet : Euronext ouvert


def test_settlement_falls_back_to_friday_on_weekend():
    assert expected_settlement_date("2026-05-31") == pd.Timestamp("2026-05-29").date()
    assert next_trading_day("2026-05-29") == pd.Timestamp("2026-06-01").date()
    assert previous_trading_day("2026-06-01") == pd.Timestamp("2026-05-29").date()


def test_sessions_table_marks_weekend():
    tbl = sessions_between("2026-05-29", "2026-06-01")
    assert len(tbl) == 4
    sat = tbl[tbl["date"] == "2026-05-30"].iloc[0]
    assert sat["session"] == "NO_SESSION_WEEKEND" and not sat["trading_session"]

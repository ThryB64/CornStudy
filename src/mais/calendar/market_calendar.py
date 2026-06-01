"""V42-01 — Calendrier de marché Euronext (Paris) pour la collecte officielle EMA.

But : ne plus confondre week-end / jour férié / donnée réellement manquante. Un samedi ou un jour férié
sans settlement n'est PAS une panne ; c'est `NO_SESSION`. Seul un jour de marché sans donnée est
`DATA_MISSING`.

Jours fériés Euronext Paris (bourse fermée) : 1 jan, Vendredi saint, Lundi de Pâques, 1 mai, 25 déc,
26 déc. (Calcul de Pâques par l'algorithme de Gauss/Meeus, valable côté grégorien.)

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import pandas as pd


def _easter_sunday(year: int) -> date:
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month = (h + m - 7 * n + 114) // 31
    day = ((h + m - 7 * n + 114) % 31) + 1
    return date(year, month, day)


@lru_cache(maxsize=64)
def _holidays_for_year(year: int) -> frozenset[date]:
    easter = _easter_sunday(year)
    return frozenset({
        date(year, 1, 1),                 # Nouvel an
        easter - timedelta(days=2),        # Vendredi saint
        easter + timedelta(days=1),        # Lundi de Pâques
        date(year, 5, 1),                 # Fête du travail
        date(year, 12, 25),               # Noël
        date(year, 12, 26),               # Lendemain de Noël
    })


# Exposé pour inspection/tests (année courante par défaut, voir is_euronext_holiday pour le calcul exact).
EURONEXT_HOLIDAYS = _holidays_for_year(pd.Timestamp.today().year)


def _as_date(d) -> date:
    return pd.Timestamp(d).date()


def is_weekend(d) -> bool:
    return _as_date(d).weekday() >= 5


def is_euronext_holiday(d) -> bool:
    dd = _as_date(d)
    return dd in _holidays_for_year(dd.year)


def is_trading_day(d) -> bool:
    return not is_weekend(d) and not is_euronext_holiday(d)


def classify_session(d) -> str:
    if is_weekend(d):
        return "NO_SESSION_WEEKEND"
    if is_euronext_holiday(d):
        return "NO_SESSION_HOLIDAY"
    return "TRADING_SESSION"


def previous_trading_day(d) -> date:
    cur = _as_date(d) - timedelta(days=1)
    while not is_trading_day(cur):
        cur -= timedelta(days=1)
    return cur


def next_trading_day(d) -> date:
    cur = _as_date(d) + timedelta(days=1)
    while not is_trading_day(cur):
        cur += timedelta(days=1)
    return cur


def expected_settlement_date(d) -> date:
    """Dernière date où un settlement Euronext est normalement attendu à la date `d` (incluse)."""
    dd = _as_date(d)
    return dd if is_trading_day(dd) else previous_trading_day(dd)


def sessions_between(start, end) -> pd.DataFrame:
    """Table calendrier (option B) : une ligne par jour calendaire avec son statut de session."""
    rng = pd.date_range(_as_date(start), _as_date(end), freq="D")
    rows = [{"date": ts.date().isoformat(), "weekday": ts.day_name(),
             "session": classify_session(ts), "trading_session": is_trading_day(ts)} for ts in rng]
    return pd.DataFrame(rows)

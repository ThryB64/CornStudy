"""V22-LIVE-02 — Contrôle de fraîcheur des données et gate de staleness pour l'indicateur.

Un indicateur quotidien ne doit JAMAIS signaler sur des données périmées. On calcule la dernière date
disponible de chaque source clé (CBOT, EMA, FX, basis) et le retard (staleness) vs aujourd'hui.

Règle :
  staleness <= 2 jours ouvrés -> OK
  staleness 3 à 5 jours ouvrés -> WARNING_STALE
  staleness > 5 jours ouvrés   -> NO_SIGNAL_STALE (l'indicateur s'abstient : UNCERTAIN_DATA_STALE)

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

STALE_OK = 2
STALE_WARNING = 5


def _last_date(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    return s.index.max() if len(s) else None


def _busday_gap(d0, d1) -> int | None:
    if d0 is None or d1 is None:
        return None
    a = np.datetime64(pd.Timestamp(d0).date(), "D")
    b = np.datetime64(pd.Timestamp(d1).date(), "D")
    return int(np.busday_count(a, b))


def _trading_gap(d0, d1) -> int | None:
    """Retard en JOURS DE MARCHÉ Euronext (week-ends ET jours fériés exclus)."""
    if d0 is None or d1 is None:
        return None
    from mais.calendar import is_trading_day
    a, b = pd.Timestamp(d0).date(), pd.Timestamp(d1).date()
    if b <= a:
        return 0
    n, cur = 0, a
    while cur < b:
        cur += pd.Timedelta(days=1)
        if is_trading_day(cur):
            n += 1
    return n


def staleness_verdict(staleness_days: int | None) -> str:
    if staleness_days is None:
        return "NO_SIGNAL_STALE"
    if staleness_days <= STALE_OK:
        return "OK"
    if staleness_days <= STALE_WARNING:
        return "WARNING_STALE"
    return "NO_SIGNAL_STALE"


def compute_freshness(df: pd.DataFrame, as_of: pd.Timestamp | None = None) -> dict[str, Any]:
    """Dernières dates par source + staleness vs as_of (défaut : aujourd'hui)."""
    as_of = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.today().normalize()
    last_cbot = _last_date(df, "cbot_eur_t")
    last_ema = _last_date(df, "ema_close")
    last_fx = _last_date(df, "eurusd")
    last_basis = _last_date(df, "ema_cbot_basis_zscore_52w")
    # staleness = retard de la donnée la plus contraignante, en JOURS DE MARCHÉ (week-ends/fériés exclus)
    gaps = {
        "cbot": _trading_gap(last_cbot, as_of),
        "ema": _trading_gap(last_ema, as_of),
        "fx": _trading_gap(last_fx, as_of),
        "basis": _trading_gap(last_basis, as_of),
    }
    worst = max((g for g in gaps.values() if g is not None), default=None)
    verdict = staleness_verdict(worst)

    # Contexte calendrier : un retard nul en jours de marché malgré des jours calendaires écoulés
    # = NO_SESSION normal (week-end / férié), pas une panne.
    from mais.calendar import classify_session, expected_settlement_date, is_trading_day
    expected = expected_settlement_date(as_of)
    skipped = []
    if last_basis is not None:
        cur = pd.Timestamp(last_basis).normalize() + pd.Timedelta(days=1)
        while cur <= as_of.normalize():
            if not is_trading_day(cur):
                skipped.append({"date": cur.date().isoformat(), "session": classify_session(cur)})
            cur += pd.Timedelta(days=1)
    calendar = {
        "session_today": classify_session(as_of),
        "today_is_trading_day": is_trading_day(as_of),
        "last_expected_settlement": expected.isoformat(),
        "non_session_days_since_last_data": skipped,
        "missing_explained_by_calendar": bool(worst is not None and worst == 0 and skipped),
    }
    return {
        "as_of": str(as_of.date()),
        "last_cbot_date": str(last_cbot.date()) if last_cbot is not None else None,
        "last_ema_date": str(last_ema.date()) if last_ema is not None else None,
        "last_fx_date": str(last_fx.date()) if last_fx is not None else None,
        "last_basis_date": str(last_basis.date()) if last_basis is not None else None,
        "staleness_days_by_source": gaps,
        "staleness_days": worst,
        "freshness_verdict": verdict,
        "signal_allowed": verdict != "NO_SIGNAL_STALE",
        "calendar": calendar,
        "rule": "OK<=2j ; WARNING 3-5j ; NO_SIGNAL>5j (jours de marché Euronext, week-ends/fériés exclus)",
    }

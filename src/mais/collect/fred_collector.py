"""FRED collector via the official ``fredapi`` package.

Interim macro (fedfunds/CPI) point-in-time : valeur de PREMIÈRE publication (ALFRED), effective au
jour ouvré suivant la publication. Le legacy datait au 1er du mois observé (~6 semaines de fuite CPI).
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BusinessDay, MonthEnd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.fred")

PIT_SERIES = ("FEDFUNDS", "CPIAUCNS")


def _first_release(fred, sid: str) -> pd.DataFrame:
    a = fred.get_series_all_releases(sid)
    a["realtime_start"] = pd.to_datetime(a["realtime_start"])
    a["date"] = pd.to_datetime(a["date"])
    first = a.sort_values("realtime_start").groupby("date").first()
    # vintages ALFRED antérieurs à 1990 = chargement en bloc : borne basse = fin du mois observé
    first["known"] = np.maximum(first["realtime_start"], first.index + MonthEnd(0))
    first["value"] = pd.to_numeric(first["value"], errors="coerce")
    return first[["value", "known"]]


def build_macro_interim(fred, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Features mensuelles legacy calculées sur les valeurs publiées, datées à la publication."""
    m = pd.concat({sid.lower(): _first_release(fred, sid)["value"] for sid in PIT_SERIES}, axis=1)
    m = m.asfreq("MS")
    c, f = m["cpiaucns"], m["fedfunds"]
    m["cpi_mom_pct"] = c.pct_change(1, fill_method=None) * 100.0
    m["cpi_yoy_pct"] = c.pct_change(12, fill_method=None) * 100.0
    r = c.rolling(24, min_periods=12)
    m["cpi_z24"] = ((c - r.mean()) / r.std(ddof=0)).clip(-6, 6)
    m["fedfunds_chg_1m"] = f.diff(1)
    m["fedfunds_chg_3m"] = f.diff(3)
    m["fedfunds_ma_3"] = f.rolling(3, min_periods=1).mean()
    rf = f.rolling(24, min_periods=12)
    m["fedfunds_z24"] = ((f - rf.mean()) / rf.std(ddof=0)).clip(-6, 6)
    m["real_fed_rate"] = f - m["cpi_yoy_pct"]
    # une ligne mensuelle n'est complète qu'une fois CPI ET fedfunds publiés
    known = pd.concat({sid.lower(): _first_release(fred, sid)["known"] for sid in PIT_SERIES}, axis=1)
    m["effective"] = known.max(axis=1).reindex(m.index) + BusinessDay(1)
    m = m.dropna(subset=["effective"]).sort_values("effective")
    m = m.drop_duplicates("effective", keep="last").set_index("effective")
    daily = m.reindex(sessions[sessions >= m.index.min()], method="ffill")
    daily.index.name = "Date"
    return daily.reset_index()


def download(out_dir: Path, src: dict) -> str:
    try:
        from fredapi import Fred
    except ImportError as e:
        raise NotImplementedError("fredapi not installed - `pip install fredapi`") from e

    api_key_env = src.get("api_key_env", "FRED_API_KEY")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise NotImplementedError(
            f"Set ${api_key_env} (free key at https://fred.stlouisfed.org/docs/api/api_key.html)"
        )
    fred = Fred(api_key=api_key)
    series_ids = src.get("series", [])
    rows = {}
    for sid in series_ids:
        try:
            s = fred.get_series(sid)
            rows[sid.lower()] = s
            log.info("fred_series_ok", sid=sid, n=len(s))
        except Exception as e:
            log.warning("fred_series_failed", sid=sid, error=str(e))
    if not rows:
        raise RuntimeError("FRED returned no series")
    df = pd.concat(rows, axis=1)
    df.index.name = "Date"
    df = df.reset_index()
    out = out_dir / "fred_macro.csv"
    df.to_csv(out, index=False)
    db = INTERIM_DIR / "database.parquet"
    if db.exists():
        sessions = pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(db, columns=["Date"])["Date"]))
        macro = build_macro_interim(fred, sessions)
        macro.to_parquet(INTERIM_DIR / "macro_fred.parquet", index=False)
        log.info("fred_macro_interim_saved", rows=len(macro), last=str(macro["Date"].max().date()))
    return f"{len(rows)} series, {len(df)} rows"

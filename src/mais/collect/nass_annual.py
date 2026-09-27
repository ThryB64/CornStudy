"""NASS QuickStats — surfaces, rendement, production maïs US, point-in-time par version.

Versions : MAR ACREAGE (Prospective Plantings), JUN ACREAGE (Acreage), AUG..NOV FORECAST (Crop Production,
même jour que le WASDE), YEAR (bilan final, écrasé à chaque révision).
Datage : prévisions = publication nominale (load_time si cohérent, sinon dernier jour ouvré de mars/juin
ou date WASDE du mois) ; bilan final = load_time si antérieur au 30/09 N+1 (révision), sinon 30/09 N+1.
Remplace les interims legacy quickstats/production (rendements 1 252-3 637 bu/ac, datés au 1er janvier).
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BMonthEnd

from mais.paths import DATA_DIR, INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.nass_annual")

API = "https://quickstats.nass.usda.gov/api/api_GET/"
SERIES = {
    "CORN - ACRES PLANTED": "planted",
    "CORN, GRAIN - ACRES HARVESTED": "harvested",
    "CORN, GRAIN - YIELD, MEASURED IN BU / ACRE": "yield",
    "CORN, GRAIN - PRODUCTION, MEASURED IN BU": "production",
}
MONTHS = {"MAR": 3, "JUN": 6, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11}
FIRST_YEAR = 1995


def _fetch(key: str, short_desc: str) -> pd.DataFrame:
    q = urllib.parse.urlencode({
        "key": key, "commodity_desc": "CORN", "agg_level_desc": "NATIONAL", "source_desc": "SURVEY",
        "freq_desc": "ANNUAL", "short_desc": short_desc, "year__GE": FIRST_YEAR, "format": "JSON",
    })
    with urllib.request.urlopen(API + "?" + q, timeout=180) as resp:
        return pd.DataFrame(json.loads(resp.read().decode("utf-8"))["data"])


def _wasde_release(year: int, month: int) -> pd.Timestamp:
    path = DATA_DIR / "wasde_raw" / "release_dates.csv"
    if path.exists():
        rel = pd.read_csv(path, dtype={"yymm": str}).set_index("yymm")["release_date"]
        key = f"{year % 100:02d}{month:02d}"
        if key in rel.index:
            return pd.Timestamp(rel[key])
    return pd.Timestamp(year, month, 14)


def release_date(year: int, period: str, load_time: pd.Timestamp) -> pd.Timestamp | None:
    if period == "YEAR":
        revision = pd.Timestamp(year + 1, 9, 30)
        if load_time.year < year + 1:
            return None  # année en cours : « YEAR » recopie la dernière prévision
        return min(load_time.normalize(), revision)
    mon = MONTHS.get(period.split()[2]) if period.startswith("YEAR - ") else None
    if mon is None:
        return None
    nominal = (pd.Timestamp(year, mon, 1) + BMonthEnd(0)) if mon in (3, 6) else _wasde_release(year, mon)
    lt = load_time.normalize()
    return lt if nominal - pd.Timedelta(days=5) <= lt <= nominal + pd.Timedelta(days=20) else nominal


def build_events(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["short_desc"].isin(SERIES)].copy()
    df["var"] = df["short_desc"].map(SERIES)
    df["value"] = pd.to_numeric(df["Value"].astype(str).str.replace(",", ""), errors="coerce")
    df["year"] = df["year"].astype(int)
    df["load_time"] = pd.to_datetime(df["load_time"])
    df["Date"] = [release_date(y, p, lt) for y, p, lt in
                  zip(df["year"], df["reference_period_desc"], df["load_time"], strict=True)]
    df = df.dropna(subset=["Date", "value"])
    return df[["Date", "year", "reference_period_desc", "var", "value"]].sort_values(["Date", "year"])


def build_daily(events: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """État connu à chaque publication pour la campagne courante, puis ffill quotidien."""
    rows = []
    for d in sorted(events["Date"].unique()):
        known = events[events["Date"] <= d]
        cur = int(known["year"].max())
        row = {"Date": d, "nass_crop_year": cur}
        for var in SERIES.values():
            v = known[(known["year"] == cur) & (known["var"] == var)].sort_values("Date")
            row[f"nass_{var}"] = v["value"].iloc[-1] if len(v) else np.nan
            row[f"nass_{var}_rev"] = (v["value"].iloc[-1] - v["value"].iloc[-2]) if len(v) >= 2 else np.nan
            row[f"_{var}_fresh"] = bool(len(v)) and v["Date"].iloc[-1] == d
        finals = known[(known["var"] == "yield") & (known["reference_period_desc"] == "YEAR")
                       & (known["year"] < cur)]
        if len(finals) >= 5 and pd.notna(row["nass_yield"]):
            b = np.polyfit(finals["year"], finals["value"], 1)
            row["nass_yield_vs_trend"] = row["nass_yield"] - np.polyval(b, cur)
        rows.append(row)
    ev = pd.DataFrame(rows)
    # une révision n'est une « surprise » que le jour de sa publication → portée limitée à ~1 mois
    for var in SERIES.values():
        ev.loc[~ev[f"_{var}_fresh"], f"nass_{var}_rev"] = np.nan
    ev = ev.drop(columns=[c for c in ev.columns if c.startswith("_")]).set_index("Date")
    daily = ev.reindex(sessions[sessions >= ev.index.min()], method="ffill")
    rev_cols = [c for c in daily.columns if c.endswith("_rev")]
    stale = pd.Series(ev.index, index=ev.index).reindex(daily.index, method="ffill")
    age = (daily.index - pd.DatetimeIndex(stale.values)).days
    daily.loc[age > 35, rev_cols] = np.nan
    daily.index.name = "Date"
    return daily.reset_index()


def download(out_dir: Path, src: dict) -> str:
    key = os.environ.get(src.get("api_key_env", "NASS_API_KEY"))
    if not key:
        raise RuntimeError("NASS_API_KEY manquant")
    raw = pd.concat([_fetch(key, sd) for sd in SERIES], ignore_index=True)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    raw.to_csv(Path(out_dir) / "nass_annual_raw.csv", index=False)
    events = build_events(raw)
    events.to_csv(Path(out_dir) / "nass_annual_events.csv", index=False)
    db = INTERIM_DIR / "database.parquet"
    sessions = pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(db, columns=["Date"])["Date"]))
    daily = build_daily(events, sessions)
    daily.to_parquet(INTERIM_DIR / "nass_annual.parquet", index=False)
    log.info("nass_annual_saved", events=len(events), last=str(events["Date"].max().date()))
    return f"{len(events)} publications, dernière {events['Date'].max().date()}"

"""Exports brésiliens de maïs (Comex Stat MDIC/SECEX, NCM 1005.90.10) — mensuel, sans clé.

Volume (t) + valeur FOB (USD) → prix FOB implicite (USD/t). Le mois M est publié par le SECEX
dans les premiers jours ouvrés de M+1 → daté au 10 de M+1 (conservateur), shift(1) dans build_features.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.brazil_exports")

API = "https://api-comexstat.mdic.gov.br/general"
NCM_CORN = "10059010"
FIRST_YEAR = 1997
AVAILABILITY_DAY = 10


def _fetch(first: int, last: int) -> list[dict]:
    body = {"flow": "export", "monthDetail": True, "period": {"from": f"{first}-01", "to": f"{last}-12"},
            "filters": [{"filter": "ncm", "values": [NCM_CORN]}], "details": [],
            "metrics": ["metricKG", "metricFOB"]}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))["data"]["list"]
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(30 * (attempt + 1))
    return []


def build_monthly(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["year"] + "-" + df["monthNumber"] + "-01")
    df["br_corn_exports_t"] = pd.to_numeric(df["metricKG"]) / 1000.0
    df["br_corn_exports_fob_usd"] = pd.to_numeric(df["metricFOB"])
    df = df.sort_values("month").drop_duplicates("month", keep="last").set_index("month")
    df = df.asfreq("MS")
    df["br_corn_exports_t"] = df["br_corn_exports_t"].fillna(0.0)
    vol = df["br_corn_exports_t"]
    df["br_corn_fob_usd_t"] = df["br_corn_exports_fob_usd"] / vol.where(vol > 1000)
    df["br_corn_exports_yoy_t"] = vol - vol.shift(12)
    df["br_corn_exports_12m_t"] = vol.rolling(12, min_periods=12).sum()
    e = vol.expanding(min_periods=24)
    df["br_corn_exports_z"] = (vol - e.mean()) / e.std()
    df["Date"] = df.index + pd.DateOffset(months=1) + pd.Timedelta(days=AVAILABILITY_DAY - 1)
    cols = ["Date", "br_corn_exports_t", "br_corn_fob_usd_t", "br_corn_exports_yoy_t",
            "br_corn_exports_12m_t", "br_corn_exports_z"]
    return df.reset_index(drop=True)[cols].replace([np.inf, -np.inf], np.nan)


def download(out_dir: Path, src: dict) -> str:
    rows = _fetch(FIRST_YEAR, date.today().year)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_dir / "comexstat_corn_raw.csv", index=False)
    monthly = build_monthly(rows)
    monthly = monthly[monthly["Date"] <= pd.Timestamp(date.today())]
    monthly.to_parquet(INTERIM_DIR / "brazil_exports.parquet", index=False)
    log.info("brazil_exports_saved", months=len(monthly), last=str(monthly["Date"].max().date()))
    return f"{len(monthly)} mois, dernier disponible {monthly['Date'].max().date()}"

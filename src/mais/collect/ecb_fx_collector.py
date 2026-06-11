"""V174 — Taux de change de référence BCE, officiel et horodaté.

Le journal officiel convertit le CBOT en EUR/t avec un eurusd yfinance (timing flou). La BCE publie un
taux de référence USD/EUR daté (14:15 CET) : il est PUBLIC AVANT le settlement Euronext (DSP 18:30 CET)
du même jour -> utilisable le jour J sans fuite. Source gratuite SDMX, archive append-only committée.

RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import urllib.request
from datetime import datetime
from typing import Any

import pandas as pd

from mais.paths import PROJECT_ROOT as ROOT

ECB_URL = ("https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
           "?startPeriod={start}&format=csvdata")
ARCHIVE_PATH = ROOT / "data" / "official_forward" / "ecb_eurusd.parquet"


def parse_ecb_csv(text: str) -> pd.DataFrame:
    """CSV SDMX -> colonnes Date (str), eurusd_ecb (USD par EUR, convention du journal)."""
    from io import StringIO
    df = pd.read_csv(StringIO(text))
    if "TIME_PERIOD" not in df.columns or "OBS_VALUE" not in df.columns:
        return pd.DataFrame()
    out = df[["TIME_PERIOD", "OBS_VALUE"]].rename(
        columns={"TIME_PERIOD": "Date", "OBS_VALUE": "eurusd_ecb"})
    out["Date"] = out["Date"].astype(str)
    out["eurusd_ecb"] = pd.to_numeric(out["eurusd_ecb"], errors="coerce")
    return out.dropna().reset_index(drop=True)


def fetch_ecb_eurusd(start: str = "2026-05-25", write: bool = True) -> dict[str, Any]:
    """Récupère les taux BCE depuis `start` et les fusionne dans l'archive committée."""
    url = ECB_URL.format(start=start)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mais-research/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            text = r.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        return {"verdict": "WAITING_DATA", "reason": f"{type(e).__name__}"}
    df = parse_ecb_csv(text)
    if df.empty:
        return {"verdict": "WAITING_DATA", "reason": "réponse vide"}
    if write:
        ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if ARCHIVE_PATH.exists():
            old = pd.read_parquet(ARCHIVE_PATH)
            df = pd.concat([old, df], ignore_index=True).drop_duplicates(subset=["Date"], keep="last")
        df = df.sort_values("Date").reset_index(drop=True)
        df.to_parquet(ARCHIVE_PATH, index=False)
    return {"verdict": "ECB_FX_COLLECTED", "n_days": int(len(df)),
            "first": str(df["Date"].iloc[0]), "last": str(df["Date"].iloc[-1]),
            "collected_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}


def load_ecb_eurusd() -> pd.DataFrame:
    return pd.read_parquet(ARCHIVE_PATH) if ARCHIVE_PATH.exists() else pd.DataFrame()

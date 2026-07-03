"""Yahoo Finance collector for OHLCV market series."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.yfinance")

# Yahoo renvoie parfois un download vide sur period="max" pour les futures (throttling
# transitoire). On retente, puis on se rabat sur des fenêtres plus courtes fusionnées avec
# le CSV existant pour ne pas perdre l'historique.
_MAX_ATTEMPTS = 4
_FALLBACK_PERIODS = ("10y", "5y", "2y", "1y", "6mo", "1mo")


def _fetch(yf, ticker: str, period: str) -> pd.DataFrame | None:
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=False,
                     progress=False, threads=False)
    if df is None or df.empty:
        return None
    return df


def _normalise(df: pd.DataFrame, name: str) -> pd.DataFrame:
    # yfinance >= 0.2 renvoie des colonnes MultiIndex (champ, ticker) même pour un seul
    # ticker : on aplatit sur le niveau champ, sinon le filtre de colonnes ne matche rien
    # et le CSV sort vide.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={"Date": "Date"})
    if "Datetime" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"Datetime": "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    cols_lower = {c: str(c).lower().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=cols_lower)
    prefix = name.split("_", 1)[1] if "_" in name else name
    keep = [c for c in df.columns if c == "date" or c in
            {"open", "high", "low", "close", "adj_close", "volume"}]
    df = df[keep].rename(columns={"date": "Date"})
    df = df.rename(columns={c: f"{prefix}_{c}" for c in df.columns if c != "Date"})
    value_cols = [c for c in df.columns if c != "Date"]
    if not value_cols or df[value_cols].dropna(how="all").empty:
        raise RuntimeError(f"No value columns after normalisation (schema change?) for {name}")
    return df


def download(out_dir: Path, src: dict) -> str:
    try:
        import yfinance as yf
    except ImportError as e:
        raise NotImplementedError("yfinance not installed - `pip install yfinance`") from e

    ticker = src["ticker"]
    name = src["name"]
    log.info("yf_download_start", ticker=ticker, name=name)

    raw = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            raw = _fetch(yf, ticker, "max")
        except Exception as e:  # transient yahoo errors
            log.info("yf_download_retry", ticker=ticker, attempt=attempt, error=str(e))
            raw = None
        if raw is not None:
            break
        if attempt < _MAX_ATTEMPTS:
            time.sleep(2 * attempt)

    fallback_used = None
    if raw is None:
        for period in _FALLBACK_PERIODS:
            try:
                raw = _fetch(yf, ticker, period)
            except Exception:
                raw = None
            if raw is not None:
                fallback_used = period
                log.info("yf_download_fallback", ticker=ticker, period=period)
                break

    if raw is None:
        raise RuntimeError(f"Empty download for {ticker}")

    df = _normalise(raw, name)

    out = out_dir / f"{name}.csv"
    # Sur fallback (fenêtre courte) : fusionner avec l'existant pour préserver l'historique.
    if fallback_used and out.exists():
        try:
            prev = pd.read_csv(out)
            prev["Date"] = pd.to_datetime(prev["Date"]).dt.normalize()
            merged = pd.concat([prev, df], ignore_index=True)
            merged = merged.drop_duplicates(subset="Date", keep="last").sort_values("Date")
            df = merged.reset_index(drop=True)
        except Exception as e:
            log.info("yf_merge_skip", ticker=ticker, error=str(e))

    df.to_csv(out, index=False)
    suffix = f" (fallback {fallback_used})" if fallback_used else ""
    log.info("yf_download_done", ticker=ticker, rows=len(df), out=str(out), fallback=fallback_used)
    return f"{len(df)} rows{suffix}"

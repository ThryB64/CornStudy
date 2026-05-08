"""Yahoo Finance collector for OHLCV market series."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.yfinance")


def download(out_dir: Path, src: dict) -> str:
    try:
        import yfinance as yf
    except ImportError as e:
        raise NotImplementedError("yfinance not installed - `pip install yfinance`") from e

    ticker = src["ticker"]
    name = src["name"]
    log.info("yf_download_start", ticker=ticker, name=name)

    df = yf.download(ticker, period="max", interval="1d", auto_adjust=False,
                     progress=False, threads=False)
    if df is None or df.empty:
        raise RuntimeError(f"Empty download for {ticker}")

    # Normalise: DatetimeIndex -> Date column, lowercase, prefix with name
    df = df.reset_index().rename(columns={"Date": "Date"})
    if "Datetime" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"Datetime": "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    cols_lower = {c: str(c).lower().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=cols_lower)
    # Prefix
    prefix = name.split("_", 1)[1] if "_" in name else name
    keep = [c for c in df.columns if c == "date" or c in
            {"open", "high", "low", "close", "adj_close", "volume"}]
    df = df[keep].rename(columns={"date": "Date"})
    df = df.rename(columns={c: f"{prefix}_{c}" for c in df.columns if c != "Date"})

    out = out_dir / f"{name}.csv"
    df.to_csv(out, index=False)
    log.info("yf_download_done", ticker=ticker, rows=len(df), out=str(out))
    return f"{len(df)} rows"

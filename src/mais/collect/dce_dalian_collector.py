"""Dalian Commodity Exchange (DCE) corn futures collector.

DCE corn (品种: 玉米, code: c) — quoted in CNY/tonne, lot = 10 t.
Primary source: yfinance ticker "DCE:C0" or similar via investing.com proxy.
Fallback: direct DCE website scrape (requires requests + BeautifulSoup).

This is a STUB for Phase 1. DCE data is not freely available on Yahoo Finance
for continuous contracts. Recommended free options:
  1. Barchart.com (limited free tier, DCE corn continuous = "CAH25" style)
  2. Quandl/NASDAQ Data Link: dataset DCE/CORN (if subscribed)
  3. Manual download from DCE website: http://www.dce.com.cn

The feature we ultimately need: dce_corn_price_usd_t (after CNY→USD FX conversion)
and the derived china_import_incentive signal.

Output CSV columns:
  Date, dce_corn_close_cny_t, dce_corn_volume, dce_corn_open_interest
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.dce_dalian")

# Known working tickers for DCE corn on various free providers
_YF_CANDIDATES = [
    "0#DCE:C",   # not standard but try
]


def download(out_dir: Path, src: dict) -> str:
    """Download DCE corn price data. Returns row count string."""
    # Try manual fallback first (most reliable for DCE)
    fallback = out_dir / "dce_corn_manual.csv"
    if fallback.exists():
        df = pd.read_csv(fallback, parse_dates=["Date"])
        _normalise_and_save(df, out_dir)
        return f"{len(df)} rows (manual fallback)"

    # Try yfinance (low success rate for DCE)
    try:
        import yfinance as yf
        for ticker in _YF_CANDIDATES:
            try:
                raw = yf.download(
                    ticker,
                    period="max",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
                if raw is not None and not raw.empty and len(raw) > 50:
                    log.info("dce_yf_ok", ticker=ticker, rows=len(raw))
                    df = raw.reset_index()
                    _normalise_and_save(df, out_dir)
                    return f"{len(df)} rows ({ticker})"
            except Exception as exc:
                log.warning("dce_yf_fail", ticker=ticker, error=str(exc))
    except ImportError:
        pass

    raise NotImplementedError(
        "DCE Dalian corn data not available via free APIs.\n"
        "Options:\n"
        "  1. Download manually from http://www.dce.com.cn (corn futures history)\n"
        "     Save as data/raw/dce_dalian/dce_corn_manual.csv with columns: "
        "Date, dce_corn_close_cny_t, dce_corn_volume\n"
        "  2. Subscribe to NASDAQ Data Link (Quandl) dataset DCE/CORN\n"
        "  3. Use Barchart API (paid) for continuous DCE corn contract\n"
        "Note: CNY/USD FX conversion is applied in build_features()."
    )


def _normalise_and_save(df: pd.DataFrame, out_dir: Path) -> None:
    result = normalise_dce_corn(df)
    out = out_dir / "dce_corn.csv"
    result.to_csv(out, index=False)
    log.info("dce_saved", rows=len(result), out=str(out))


def normalise_dce_corn(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise DCE manual/yfinance corn history to project schema."""
    df = df.copy()
    # Rename date column
    for date_col in ("Date", "date", "Datetime"):
        if date_col in df.columns:
            df = df.rename(columns={date_col: "Date"})
            break
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    # Normalise column names to our schema
    col_map = {
        "close": "dce_corn_close_cny_t",
        "Close": "dce_corn_close_cny_t",
        "volume": "dce_corn_volume",
        "Volume": "dce_corn_volume",
        "open_interest": "dce_corn_open_interest",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    keep = ["Date"] + [c for c in df.columns if c.startswith("dce_")]
    if not any(c.startswith("dce_") for c in df.columns):
        # Fallback: use whatever close-like column is present
        close_cols = [c for c in df.columns if "close" in c.lower() or "price" in c.lower()]
        if close_cols:
            df = df.rename(columns={close_cols[0]: "dce_corn_close_cny_t"})
            keep = ["Date", "dce_corn_close_cny_t"]
    result = df[[c for c in keep if c in df.columns]]
    result = result.dropna(subset=["dce_corn_close_cny_t"] if "dce_corn_close_cny_t" in result.columns else [])
    return result.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def build_china_import_incentive(
    dce: pd.DataFrame,
    cbot_usd_t: pd.Series,
    usd_cny: pd.Series,
    *,
    china_tariff_rate: float = 0.01,
    pacific_freight_usd_t: float = 45.0,
    port_handling_usd_t: float = 12.0,
) -> pd.DataFrame:
    """Build China import parity and incentive using lag-safe observed inputs."""
    work = dce.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    aligned = pd.DataFrame(
        {
            "Date": work["Date"],
            "dce_corn_close_cny_t": pd.to_numeric(work["dce_corn_close_cny_t"], errors="coerce"),
            "cbot_usd_t": pd.Series(cbot_usd_t).reset_index(drop=True).astype(float),
            "usd_cny": pd.Series(usd_cny).reset_index(drop=True).astype(float),
        }
    )
    aligned["dce_corn_price_usd_t"] = aligned["dce_corn_close_cny_t"] / aligned["usd_cny"].replace(0, np.nan)
    aligned["china_import_parity_usd_t"] = (
        aligned["cbot_usd_t"] * (1.0 + float(china_tariff_rate))
        + float(pacific_freight_usd_t)
        + float(port_handling_usd_t)
    )
    aligned["china_import_incentive"] = aligned["dce_corn_price_usd_t"] - aligned["china_import_parity_usd_t"]
    aligned["china_import_incentive_flag"] = (aligned["china_import_incentive"] > 0).astype(int)
    return aligned

"""Euronext Matif corn futures collector (EMA).

Downloads daily OHLCV for the Euronext corn continuous front contract.
Primary source: yfinance (EMA=F).  Fallback: manual CSV in data/raw/euronext_ema/.

Output CSV columns: Date, ema_open, ema_high, ema_low, ema_close, ema_volume
Units: EUR/tonne (Euronext EMA is quoted in EUR/tonne, lot = 50 t)

Yahoo Finance coverage note: Euronext futures availability on yfinance is limited.
If EMA=F returns empty, use the fallback path and load from a manually downloaded
Euronext export (available from euronext.com > Products > Derivatives > Agricultural).
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.euronext_ema")

# Yahoo Finance tickers to try in order (coverage varies)
_YF_TICKERS = ["EMA=F", "ZCE=F"]

# Current official Euronext EMA active delivery months.
CURRENT_OFFICIAL_EMA_MONTHS = {"H": 3, "M": 6, "Q": 8, "X": 11}
LEGACY_OR_INVESTIGATION_EMA_MONTHS = {"F": 1}
EMA_CONTRACT_MONTHS = {
    **CURRENT_OFFICIAL_EMA_MONTHS,
    **LEGACY_OR_INVESTIGATION_EMA_MONTHS,
}
EMA_MONTH_TO_CODE = {v: k for k, v in EMA_CONTRACT_MONTHS.items()}
CURRENT_EMA_MONTH_NAME_TO_CODE = {
    "mar": "H",
    "march": "H",
    "jun": "M",
    "june": "M",
    "aug": "Q",
    "august": "Q",
    "nov": "X",
    "november": "X",
}
LEGACY_EMA_MONTH_NAME_TO_CODE = {
    "jan": "F",
    "january": "F",
}
EMA_MONTH_NAME_TO_CODE = {
    **CURRENT_EMA_MONTH_NAME_TO_CODE,
    **LEGACY_EMA_MONTH_NAME_TO_CODE,
}


def _parse_contract_label_with_months(
    label: str,
    *,
    allowed_months: dict[str, int],
    allowed_month_names: dict[str, str],
) -> str:
    """Parse a contract label with an explicit allowed month set."""
    cleaned = str(label).strip()
    match = re.search(r"([A-Za-z]{3,9})\s+(\d{4})", cleaned)
    if not match:
        match = re.search(r"EMA[_\s-]?([A-Za-z])\s?(\d{2,4})", cleaned, flags=re.IGNORECASE)
        if not match:
            raise ValueError(f"Cannot parse EMA contract label: {label!r}")
        code = match.group(1).upper().strip()
        year_raw = match.group(2)
        year = int(year_raw) + 2000 if len(year_raw) == 2 else int(year_raw)
        if code not in allowed_months:
            raise ValueError(f"Unsupported EMA month code: {code}")
        return f"EMA_{code}{year}"
    month = match.group(1).lower()
    year = int(match.group(2))
    code = allowed_month_names.get(month)
    if code is None:
        raise ValueError(f"Unsupported EMA month name: {month}")
    return f"EMA_{code}{year}"


def parse_active_contract_label(label: str) -> str:
    """Parse active Euronext EMA labels. Only H/M/Q/X are importable."""
    return _parse_contract_label_with_months(
        label,
        allowed_months=CURRENT_OFFICIAL_EMA_MONTHS,
        allowed_month_names=CURRENT_EMA_MONTH_NAME_TO_CODE,
    )


def parse_provider_contract_label(label: str, *, allow_legacy: bool = False) -> str:
    """Parse provider labels, optionally allowing legacy months for investigation."""
    allowed_months = EMA_CONTRACT_MONTHS if allow_legacy else CURRENT_OFFICIAL_EMA_MONTHS
    allowed_names = EMA_MONTH_NAME_TO_CODE if allow_legacy else CURRENT_EMA_MONTH_NAME_TO_CODE
    return _parse_contract_label_with_months(
        label,
        allowed_months=allowed_months,
        allowed_month_names=allowed_names,
    )


def parse_contract_label(label: str) -> str:
    """Parse active labels such as ``Jun 2026`` into EMA contract codes."""
    return parse_active_contract_label(label)


def normalise_ema_history(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise a yfinance or Euronext manual export to the EMA schema."""
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[0]) for c in df.columns]
    if "Datetime" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"Datetime": "Date"})
    if "date" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"date": "Date"})
    if "Date" not in df.columns:
        raise ValueError("EMA history requires a Date column")
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    rename = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=rename)
    df = df.rename(columns={"date": "Date"})
    col_map = {
        "open": "ema_open",
        "high": "ema_high",
        "low": "ema_low",
        "close": "ema_close",
        "last": "ema_close",
        "settlement": "ema_close",
        "settle": "ema_close",
        "adj_close": "ema_adj_close",
        "volume": "ema_volume",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "ema_close" not in df.columns:
        raise ValueError("EMA history requires close/settlement/last price")
    for col in ["ema_open", "ema_high", "ema_low"]:
        if col not in df.columns:
            df[col] = df["ema_close"]
    if "ema_volume" not in df.columns:
        df["ema_volume"] = np.nan
    keep = ["Date", "ema_open", "ema_high", "ema_low", "ema_close", "ema_volume"]
    optional = [c for c in df.columns if c.startswith("ema_") and c not in keep]
    result = df[keep + optional].dropna(subset=["ema_close"])
    return result.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def validate_ema_history(df: pd.DataFrame, *, min_rows: int = 3500) -> dict[str, float | int | bool]:
    """Return basic quality metrics for an EMA history frame."""
    if df.empty:
        return {"n_rows": 0, "nan_rate_close": 1.0, "max_business_gap_days": 0, "quality_ok": False}
    work = normalise_ema_history(df) if "ema_close" not in df.columns else df.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    dates = work["Date"].sort_values().reset_index(drop=True)
    business_gaps = dates.diff().dt.days.dropna()
    max_gap = int(business_gaps.max()) if not business_gaps.empty else 0
    nan_rate = float(work["ema_close"].isna().mean())
    quality_ok = bool(len(work) >= min_rows and nan_rate < 0.02 and max_gap <= 14)
    return {
        "n_rows": int(len(work)),
        "nan_rate_close": nan_rate,
        "max_business_gap_days": max_gap,
        "quality_ok": quality_ok,
    }


def download(out_dir: Path, src: dict) -> str:
    """Download EMA price history. Returns row count string."""
    fallback = out_dir / "ema_manual.csv"
    if fallback.exists():
        df = normalise_ema_history(pd.read_csv(fallback))
        out = out_dir / "euronext_ema.csv"
        df.to_csv(out, index=False)
        quality = validate_ema_history(df)
        log.info("ema_fallback_manual", rows=len(df), quality=quality)
        return f"{len(df)} rows (manual fallback, quality_ok={quality['quality_ok']})"

    try:
        import yfinance as yf
    except ImportError as e:
        raise NotImplementedError("yfinance not installed — pip install yfinance") from e

    df: pd.DataFrame | None = None
    used_ticker = None
    for ticker in _YF_TICKERS:
        try:
            raw = yf.download(
                ticker, period="max", interval="1d",
                auto_adjust=False, progress=False, threads=False,
            )
            if raw is not None and not raw.empty and len(raw) > 100:
                df = raw
                used_ticker = ticker
                log.info("ema_yf_ok", ticker=ticker, rows=len(raw))
                break
        except Exception as exc:
            log.warning("ema_yf_fail", ticker=ticker, error=str(exc))

    if df is None or df.empty:
        # Check for manual fallback CSV
        # Last resort: build a CBOT→EUR/t proxy (circular for CBOT features, but usable for infra validation)
        proxy_rows = _build_cbot_proxy(out_dir)
        if proxy_rows > 0:
            return f"{proxy_rows} rows (CBOT proxy — replace with real EMA from euronext.com)"
        raise NotImplementedError(
            "EMA=F not available on yfinance and no manual fallback found.\n"
            "Download history from euronext.com > Products > Derivatives > "
            "Agricultural > Corn > Historical data, save as data/raw/euronext_ema/ema_manual.csv\n"
            "Columns needed: Date, Open, High, Low, Close, Volume"
        )

    df = normalise_ema_history(df.reset_index())

    out = out_dir / "euronext_ema.csv"
    df.to_csv(out, index=False)
    log.info("ema_saved", ticker=used_ticker, rows=len(df), out=str(out))
    return f"{len(df)} rows ({used_ticker})"


def _build_cbot_proxy(out_dir: Path) -> int:
    """Build a CBOT→EUR/t proxy for EMA when no real Euronext data is available.

    WARNING: This proxy is circular for any model using CBOT features as inputs.
    It should only be used for pipeline validation and replaced with real EMA data.
    Conversion: EMA_proxy_EUR_t = CBOT_USD_bu / eurusd_rate * 39.3679
    """
    from mais.paths import INTERIM_DIR, RAW_DIR

    db_path = INTERIM_DIR / "database.parquet"
    eurusd_path = RAW_DIR / "eu_cross_assets" / "eu_cross_assets.csv"

    if not db_path.exists() or not eurusd_path.exists():
        log.warning("ema_proxy_missing_inputs", db=str(db_path), eurusd=str(eurusd_path))
        return 0

    db = pd.read_parquet(db_path, columns=["Date", "corn_close"])
    eurusd = pd.read_csv(eurusd_path, parse_dates=["Date"])

    # Normalise
    db["Date"] = pd.to_datetime(db["Date"]).dt.tz_localize(None).dt.normalize()
    eurusd["Date"] = pd.to_datetime(eurusd["Date"]).dt.tz_localize(None).dt.normalize()

    close_col = "corn_close"
    merged = db[["Date", close_col]].merge(eurusd[["Date", "eurusd_rate"]], on="Date", how="inner")
    merged = merged.dropna()

    # corn_close is in US cents/bushel → /100 → USD/bu → /eurusd → EUR/bu → ×39.3679 → EUR/tonne
    bushel_to_tonne = 39.3679
    merged["ema_close"] = (merged[close_col] / 100) / merged["eurusd_rate"] * bushel_to_tonne
    merged["ema_open"] = merged["ema_close"]
    merged["ema_high"] = merged["ema_close"]
    merged["ema_low"] = merged["ema_close"]
    merged["ema_volume"] = 0
    merged["ema_is_proxy"] = True  # flag so notebooks can warn the user

    out_df = merged[["Date", "ema_open", "ema_high", "ema_low", "ema_close", "ema_volume", "ema_is_proxy"]]
    out_df = out_df.sort_values("Date").drop_duplicates("Date")
    out = out_dir / "euronext_ema.csv"
    out_df.to_csv(out, index=False)
    log.warning("ema_proxy_saved", rows=len(out_df), note="CBOT proxy — replace with real Euronext data")
    return len(out_df)

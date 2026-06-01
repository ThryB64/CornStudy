"""EU fundamentals data collector.

Covers:
  - EUR/USD spot rate (via yfinance EURUSD=X) — daily
  - TTF natural gas EU (via yfinance TTF=F) — daily
  - Baltic Dry Index BDI (via yfinance BDI proxy or manual) — daily
  - EC MARS bulletin crop monitoring — monthly stub
  - Euronext EMA spreads (Nov-Jan, Jan-Mar, Mar-Jun) — stub via yfinance specific contracts
  - Agreste France crop progress — weekly stub (no free API)

Each sub-collector is callable independently via src['name'].
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.eu_fundamentals")

# Cross-asset tickers via yfinance
_YF_TICKERS: dict[str, tuple[str, str]] = {
    "eurusd":   ("EURUSD=X",  "eurusd_rate"),
    "ttf_gas":  ("TTF=F",     "ttf_natgas_eur"),
    "bdi":      ("BDI",       "bdi_index"),       # may not exist on yfinance
    "eurusd_alt": ("EUR=X",   "eurusd_rate"),
}


def download(out_dir: Path, src: dict) -> str:
    name = src["name"]
    if name == "eu_cross_assets":
        return _download_cross_assets(out_dir)
    if name == "ec_mars_bulletin":
        return _stub_ec_mars(out_dir)
    if name == "agreste_france":
        return _stub_agreste(out_dir)
    if name == "franceagrimer":
        return _stub_franceagrimer(out_dir)
    if name == "euronext_ema_spreads":
        return _download_ema_spreads(out_dir, src)
    raise NotImplementedError(f"Unknown EU fundamentals source: {name}")


def _download_cross_assets(out_dir: Path) -> str:
    """Download EUR/USD, TTF gas, BDI — all via yfinance."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise NotImplementedError("yfinance not installed") from e

    results = {}
    frames = []

    # EUR/USD (critical for EU competitiveness signal)
    for ticker, col in [("EURUSD=X", "eurusd_rate"), ("EUR=X", "eurusd_rate")]:
        try:
            raw = yf.download(ticker, period="max", interval="1d",
                               auto_adjust=False, progress=False, threads=False)
            if raw is not None and not raw.empty:
                df = _yf_to_series(raw, col)
                frames.append(df)
                results["eurusd"] = f"{len(df)} rows"
                log.info("eurusd_ok", ticker=ticker, rows=len(df))
                break
        except Exception as exc:
            log.warning("eurusd_fail", ticker=ticker, error=str(exc))

    # TTF natural gas EU (proxy cost: drying + fertilizers)
    for ticker, col in [("TTF=F", "ttf_natgas_eur"), ("NG=F", "ttf_natgas_eur")]:
        try:
            raw = yf.download(ticker, period="max", interval="1d",
                               auto_adjust=False, progress=False, threads=False)
            if raw is not None and not raw.empty:
                df = _yf_to_series(raw, col)
                frames.append(df)
                results["ttf"] = f"{len(df)} rows"
                log.info("ttf_ok", ticker=ticker, rows=len(df))
                break
        except Exception as exc:
            log.warning("ttf_fail", ticker=ticker, error=str(exc))

    # BDI — Baltic Dry Index (grain freight proxy)
    # yfinance doesn't carry BDI natively; use manual fallback
    bdi_manual = out_dir / "bdi_manual.csv"
    if bdi_manual.exists():
        bdi_df = pd.read_csv(bdi_manual, parse_dates=["Date"])
        bdi_df = bdi_df.rename(columns={bdi_df.columns[1]: "bdi_index"})
        bdi_df["Date"] = pd.to_datetime(bdi_df["Date"]).dt.tz_localize(None).dt.normalize()
        frames.append(bdi_df.set_index("Date")[["bdi_index"]])
        results["bdi"] = f"{len(bdi_df)} rows (manual)"
        log.info("bdi_manual_ok", rows=len(bdi_df))
    else:
        log.warning("bdi_missing", note="Download from quandl/FRED DBDI or balticexchange.com")

    if not frames:
        raise RuntimeError("All EU cross-asset downloads failed")

    # Merge on daily index
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f, how="outer")
    merged = merged.sort_index().reset_index().rename(columns={"index": "Date"})
    merged["Date"] = pd.to_datetime(merged["Date"]).dt.tz_localize(None).dt.normalize()

    out = out_dir / "eu_cross_assets.csv"
    merged.to_csv(out, index=False)
    log.info("eu_cross_assets_saved", rows=len(merged), cols=list(merged.columns))
    return f"{len(merged)} rows ({results})"


def _yf_to_series(raw: pd.DataFrame, col: str) -> pd.DataFrame:
    """Convert yfinance OHLCV frame (possibly MultiIndex columns) to a single close series."""
    # yfinance ≥1.0 returns MultiIndex columns: (field, ticker) — flatten to field only
    if isinstance(raw.columns, pd.MultiIndex):
        raw = raw.copy()
        raw.columns = [str(c[0]).lower() for c in raw.columns]
    df = raw.reset_index()
    for date_col in ("date", "datetime", "Date", "Datetime"):
        if date_col in df.columns:
            df = df.rename(columns={date_col: "Date"})
            break
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    close_cols = [c for c in df.columns if c.lower() in ("close", "adj_close", "adj close")]
    if not close_cols:
        close_cols = [c for c in df.columns if c != "Date"]
    df = df.rename(columns={close_cols[0]: col})
    return df.set_index("Date")[[col]]


def _stub_ec_mars(out_dir: Path) -> str:
    """EC MARS bulletin — monthly crop monitoring, HTML scrape stub."""
    manual = out_dir / "ec_mars_manual.csv"
    if manual.exists():
        df = normalise_ec_mars(pd.read_csv(manual))
        out = out_dir / "ec_mars_bulletin.csv"
        df.to_csv(out, index=False)
        return f"{len(df)} rows (manual fallback)"
    raise NotImplementedError(
        "EC MARS bulletin collector not yet implemented.\n"
        "Source: https://agri4cast.jrc.ec.europa.eu/DataPortal/\n"
        "Data: monthly yield estimates, crop condition by country, soil moisture.\n"
        "Parsing: download PDF/Excel from MARS JRC data portal.\n"
        "Key output columns: Date, eu_yield_estimate_tha, eu_production_estimate_mt, "
        "eu_ending_stocks_surprise, eu_soil_moisture_anomaly, france_ge_pct\n"
        "Anti-leakage: publication ~15th of month → shift(1) month before use."
    )


def _stub_agreste(out_dir: Path) -> str:
    """Agreste France weekly crop progress — stub."""
    manual = out_dir / "agreste_france_manual.csv"
    if manual.exists():
        df = normalise_agreste_france(pd.read_csv(manual))
        out = out_dir / "agreste_france.csv"
        df.to_csv(out, index=False)
        return f"{len(df)} rows (manual fallback)"
    raise NotImplementedError(
        "Agreste France collector not yet implemented.\n"
        "Source: https://agreste.agriculture.gouv.fr/agreste-web/ > Conjoncture > Cultures\n"
        "Data: weekly crop condition G+E% for corn, sunflower, cereals during growing season.\n"
        "Key output columns: Date, france_ge_pct, france_corn_harvested_pct\n"
        "Anti-leakage: publication Monday → shift(1) week before use."
    )


def _stub_franceagrimer(out_dir: Path) -> str:
    """FranceAgriMer monthly supply/demand balance — stub."""
    manual = out_dir / "franceagrimer_manual.csv"
    if manual.exists():
        df = normalise_franceagrimer(pd.read_csv(manual))
        out = out_dir / "franceagrimer.csv"
        df.to_csv(out, index=False)
        return f"{len(df)} rows (manual fallback)"
    raise NotImplementedError(
        "FranceAgriMer collector not yet implemented.\n"
        "Source: https://www.franceagrimer.fr/filieres-vegetales/Cereales\n"
        "Data: monthly balance sheet — production, consumption, exports, ending stocks France.\n"
        "Key output columns: Date, france_ending_stocks_mt, france_export_pace_mt\n"
        "Anti-leakage: publication ~10th of month."
    )


def _download_ema_spreads(out_dir: Path, src: dict) -> str:
    """Download Euronext EMA contract spreads via yfinance specific months."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise NotImplementedError("yfinance not installed") from e

    # Euronext Matif corn specific contracts (format: EMAMonYY=F)
    # Example: EMAZ24=F (Nov 2024), EMAF25=F (Jan 2025), EMAH25=F (Mar 2025)
    # These tickers may not be available on yfinance — use manual if needed
    from datetime import datetime
    current_year = datetime.now().year
    contracts = {}
    for month_code, month_name in [("X", "Nov"), ("F", "Jan"), ("H", "Mar"), ("M", "Jun"), ("Q", "Aug")]:
        for yr in [current_year, current_year + 1]:
            ticker = f"EMA{month_code}{str(yr)[2:]}=F"
            try:
                raw = yf.download(ticker, period="6mo", interval="1d",
                                   auto_adjust=False, progress=False, threads=False)
                if raw is not None and not raw.empty:
                    contracts[f"ema_{month_name.lower()}_{yr}"] = len(raw)
            except Exception:
                pass

    if not contracts:
        raise NotImplementedError(
            "EMA contract spreads not available via yfinance.\n"
            "Download specific contract data from euronext.com or use Bloomberg/Refinitiv.\n"
            "Key spreads to compute: ema_nov_jan_spread, ema_jan_mar_spread, ema_contango_flag."
        )
    return f"contracts: {contracts}"


def normalise_ec_mars(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise EC MARS monthly crop monitoring exports."""
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "yield_estimate_tha": "eu_yield_estimate_tha",
            "production_estimate_mt": "eu_production_estimate_mt",
            "ending_stocks_surprise": "eu_ending_stocks_surprise",
            "soil_moisture_anomaly": "eu_soil_moisture_anomaly",
        },
    )
    keep = ["Date"] + [c for c in df.columns if c.startswith("eu_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_agreste_france(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise Agreste France seasonal crop condition exports."""
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "ge_pct": "france_ge_pct",
            "good_excellent_pct": "france_ge_pct",
            "corn_harvested_pct": "france_corn_harvested_pct",
        },
    )
    keep = ["Date"] + [c for c in df.columns if c.startswith("france_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_franceagrimer(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise FranceAgriMer monthly supply/demand balance."""
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "ending_stocks_mt": "france_ending_stocks_mt",
            "export_pace_mt": "france_export_pace_mt",
            "production_mt": "france_production_mt",
        },
    )
    keep = ["Date"] + [c for c in df.columns if c.startswith("france_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def build_eu_fundamental_features(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge EU source frames and add anti-leakage-friendly lag features."""
    if not frames:
        return pd.DataFrame()
    merged = frames[0].copy()
    merged["Date"] = pd.to_datetime(merged["Date"])
    for frame in frames[1:]:
        other = frame.copy()
        other["Date"] = pd.to_datetime(other["Date"])
        merged = merged.merge(other, on="Date", how="outer")
    merged = merged.sort_values("Date").reset_index(drop=True)
    for col in [c for c in merged.columns if c != "Date"]:
        merged[f"{col}_lag1"] = merged[col].shift(1)
    if "eu_production_estimate_mt" in merged.columns:
        merged["eu_production_revision_mt"] = merged["eu_production_estimate_mt"].diff().shift(1)
    if "france_ge_pct" in merged.columns:
        merged["france_ge_momentum_1w"] = merged["france_ge_pct"].diff().shift(1)
    return merged


def _with_date(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for date_col in ("Date", "date", "datetime", "Datetime"):
        if date_col in df.columns:
            df = df.rename(columns={date_col: "Date"})
            break
    if "Date" not in df.columns:
        raise ValueError("EU manual source requires a Date column")
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    return df


def _rename_known(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    lookup = {c.lower().strip(): c for c in df.columns}
    rename = {}
    for source, target in mapping.items():
        if source in lookup and target not in df.columns:
            rename[lookup[source]] = target
    return df.rename(columns=rename)

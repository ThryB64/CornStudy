"""World (non-US) corn data collector (Phase 1 NEW).

This module is a dispatcher: it reads ``src['name']`` and routes to the
right scraper. Each scraper is a stub for now; activation order:

1. CONAB Brazil (HTML scrape, monthly): https://www.conab.gov.br/info-agro/safras
2. Bolsa de Cereales Rosario Argentina (HTML, weekly): https://www.bolsadecereales.com/
3. UkrAgroConsult (subscription)
4. NOAA ENSO ONI (free, monthly): https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.world")


def download(out_dir: Path, src: dict) -> str:
    name = src["name"]
    if name == "noaa_oni":
        return _download_noaa_oni(out_dir, src)
    if name == "conab_brazil":
        return _download_manual(
            out_dir,
            "conab_brazil_manual.csv",
            "conab_brazil.csv",
            normalise_conab_brazil,
            "CONAB Brazil manual CSV required",
        )
    if name == "bcr_argentina":
        return _download_manual(
            out_dir,
            "bcr_argentina_manual.csv",
            "bcr_argentina.csv",
            normalise_argentina,
            "Bolsa de Cereales Argentina manual CSV required",
        )
    if name == "brazil_fob_prices":
        return _download_manual(
            out_dir,
            "brazil_fob_manual.csv",
            "brazil_fob_prices.csv",
            normalise_brazil_fob,
            "Brazil FOB manual CSV required",
        )
    if name == "brazil_export_inspections":
        return _download_manual(
            out_dir,
            "brazil_exports_manual.csv",
            "brazil_export_inspections.csv",
            normalise_brazil_exports,
            "Brazil export inspections manual CSV required",
        )
    if name == "ukraine_exports":
        return _download_manual(
            out_dir,
            "ukraine_exports_manual.csv",
            "ukraine_exports.csv",
            normalise_ukraine_exports,
            "Ukraine exports manual CSV required",
        )
    if name == "asia_tenders":
        return _download_manual(
            out_dir,
            "asia_tenders_manual.csv",
            "asia_tenders.csv",
            normalise_asia_tenders,
            "Asia tenders manual CSV required",
        )
    if name == "ukragroconsult":
        raise NotImplementedError("UkrAgroConsult requires subscription.")
    raise NotImplementedError(f"Unknown world source: {name}")


def normalise_conab_brazil(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise CONAB Brazil corn production/export estimates."""
    df = _with_date(raw)
    mapping = {
        "production_mt": "brazil_conab_production_mt",
        "corn_production_mt": "brazil_conab_production_mt",
        "safrinha_production_mt": "brazil_safrinha_production_mt",
        "export_forecast_mt": "brazil_conab_export_forecast_mt",
        "harvest_progress_pct": "brazil_safrinha_progress_pct",
    }
    df = _rename_known(df, mapping)
    keep = ["Date"] + [c for c in df.columns if c.startswith("brazil_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_brazil_fob(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise Brazilian FOB price series."""
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "fob_paranagua_usd_t": "brazil_fob_paranagua_usd_t",
            "paranagua_usd_t": "brazil_fob_paranagua_usd_t",
            "us_fob_gulf_usd_t": "us_fob_gulf_usd_t",
        },
    )
    if "brazil_us_fob_spread" not in df.columns and {"brazil_fob_paranagua_usd_t", "us_fob_gulf_usd_t"}.issubset(df.columns):
        df["brazil_us_fob_spread"] = df["brazil_fob_paranagua_usd_t"] - df["us_fob_gulf_usd_t"]
    keep = ["Date"] + [c for c in df.columns if c.startswith("brazil_") or c == "us_fob_gulf_usd_t"]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_brazil_exports(raw: pd.DataFrame) -> pd.DataFrame:
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "exports_mt": "brazil_export_inspections_mt",
            "export_inspections_mt": "brazil_export_inspections_mt",
            "exports_ytd_mt": "brazil_exports_ytd_mt",
        },
    )
    keep = ["Date"] + [c for c in df.columns if c.startswith("brazil_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_argentina(raw: pd.DataFrame) -> pd.DataFrame:
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "harvest_progress_pct": "argentina_harvest_progress_pct",
            "production_mt": "argentina_bolsa_production_mt",
            "retenciones_pct": "argentina_retenciones_pct",
            "fob_rosario_usd_t": "argentina_fob_rosario_usd_t",
        },
    )
    keep = ["Date"] + [c for c in df.columns if c.startswith("argentina_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_ukraine_exports(raw: pd.DataFrame) -> pd.DataFrame:
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "exports_mt": "ukraine_export_pace_mt",
            "corridor_status": "ukraine_corridor_status",
            "harvest_progress_pct": "ukraine_harvest_progress_pct",
        },
    )
    if "ukraine_corridor_status" in df.columns:
        df["ukraine_corridor_status"] = df["ukraine_corridor_status"].astype(float).clip(0, 1)
    keep = ["Date"] + [c for c in df.columns if c.startswith("ukraine_")]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def normalise_asia_tenders(raw: pd.DataFrame) -> pd.DataFrame:
    df = _with_date(raw)
    df = _rename_known(
        df,
        {
            "japan_tenders_mt": "japan_corn_tenders_mt",
            "korea_tenders_mt": "korea_corn_tenders_mt",
            "taiwan_tenders_mt": "taiwan_corn_tenders_mt",
        },
    )
    tender_cols = [c for c in df.columns if c.endswith("_corn_tenders_mt")]
    if tender_cols:
        df["asia_importer_tenders_mt"] = df[tender_cols].sum(axis=1, min_count=1)
    keep = ["Date"] + [c for c in df.columns if c.endswith("_corn_tenders_mt") or c == "asia_importer_tenders_mt"]
    return df[keep].sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def brazil_safrinha_pressure_flag(dates: pd.Series, progress_pct: pd.Series) -> pd.Series:
    """Return +1 delayed harvest pressure, -1 completed harvest pressure, 0 otherwise."""
    dt = pd.to_datetime(dates)
    progress = pd.to_numeric(progress_pct, errors="coerce")
    in_harvest = dt.dt.month.isin([6, 7, 8])
    return pd.Series(
        np.select([in_harvest & (progress < 85), in_harvest & (progress >= 85)], [1, -1], default=0),
        index=dates.index,
        dtype=int,
    )


def build_world_signal_features(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge world source frames and derive explicit global corn signals."""
    if not frames:
        return pd.DataFrame()
    merged = frames[0].copy()
    merged["Date"] = pd.to_datetime(merged["Date"])
    for frame in frames[1:]:
        other = frame.copy()
        other["Date"] = pd.to_datetime(other["Date"])
        merged = merged.merge(other, on="Date", how="outer")
    merged = merged.sort_values("Date").reset_index(drop=True)
    if "brazil_safrinha_progress_pct" in merged.columns:
        merged["brazil_safrinha_pressure_flag"] = brazil_safrinha_pressure_flag(
            merged["Date"],
            merged["brazil_safrinha_progress_pct"],
        )
    if {"brazil_fob_paranagua_usd_t", "us_fob_gulf_usd_t"}.issubset(merged.columns):
        merged["brazil_us_fob_spread"] = merged["brazil_fob_paranagua_usd_t"] - merged["us_fob_gulf_usd_t"]
    if "ukraine_corridor_status" in merged.columns:
        merged["uncertain_ukraine_risk"] = (merged["ukraine_corridor_status"].fillna(1.0) < 0.5).astype(int)
    return merged


def _download_noaa_oni(out_dir: Path, src: dict) -> str:
    try:
        import pandas as pd
        import requests
    except ImportError as e:
        raise NotImplementedError("requests/pandas not installed") from e
    url = src.get("url", "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    lines = [ln.strip().split() for ln in r.text.splitlines() if ln.strip()]
    rows = []
    for ln in lines[1:]:  # skip header
        try:
            seas, yr, total, anom = ln[0], int(ln[1]), float(ln[2]), float(ln[3])
        except (ValueError, IndexError):
            continue
        # Use the central month of the season
        mid_month = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
                      "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}.get(seas)
        if not mid_month:
            continue
        rows.append({"Date": pd.Timestamp(year=yr, month=mid_month, day=15),
                      "oni_value": total, "oni_anom": anom})
    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    out = out_dir / "noaa_oni.csv"
    df.to_csv(out, index=False)
    return f"{len(df)} rows"


def _download_manual(out_dir: Path, input_name: str, output_name: str, normaliser, message: str) -> str:
    path = out_dir / input_name
    if not path.exists():
        raise NotImplementedError(f"{message}. Save manual file to {path}")
    raw = pd.read_csv(path)
    df = normaliser(raw)
    out = out_dir / output_name
    df.to_csv(out, index=False)
    return f"{len(df)} rows (manual fallback)"


def _with_date(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for date_col in ("Date", "date", "datetime", "Datetime"):
        if date_col in df.columns:
            df = df.rename(columns={date_col: "Date"})
            break
    if "Date" not in df.columns:
        raise ValueError("manual world source requires a Date column")
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    return df


def _rename_known(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    lookup = {c.lower().strip(): c for c in df.columns}
    rename = {}
    for source, target in mapping.items():
        if source in lookup and target not in df.columns:
            rename[lookup[source]] = target
    return df.rename(columns=rename)

"""Extend interim/database.parquet with fresh market rows from data/raw/ CSVs.

The legacy combined database stops where the legacy CSVs stop; the daily
collectors keep writing raw CSVs but nothing carried them into the anchor.
This module appends the missing dates (anchored on cbot_corn) with the raw
OHLCV columns mapped onto the legacy naming; legacy-only columns stay NaN.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import structlog

from mais.paths import INTERIM_DIR, RAW_DIR
from mais.utils.io import write_parquet

log = structlog.get_logger()

RAW_SOURCES: dict[str, tuple[str, str]] = {
    "cbot_corn": ("corn", "corn"),
    "cbot_wheat": ("wheat", "wheat"),
    "cbot_soy": ("soy", "soy"),
    "cbot_oats": ("oats", "oats"),
    "nymex_crude_wti": ("crude_wti", "oil"),
    "nymex_natgas": ("natgas", "gas"),
}
OHLCV = ["open", "high", "low", "close", "volume"]


def _load_raw(raw_dir: Path, source: str, raw_prefix: str, db_prefix: str) -> pd.DataFrame | None:
    path = raw_dir / source / f"{source}.csv"
    if not path.exists():
        log.warning("refresh_raw_missing", source=source, path=str(path))
        return None
    df = pd.read_csv(path, parse_dates=["Date"])
    cols = {f"{raw_prefix}_{f}": f"{db_prefix}_{f}" for f in OHLCV
            if f"{raw_prefix}_{f}" in df.columns}
    if f"{db_prefix}_close" not in cols.values():
        log.warning("refresh_no_close", source=source, columns=list(df.columns))
        return None
    out = df[["Date", *cols]].rename(columns=cols)
    out["Date"] = pd.to_datetime(out["Date"]).dt.normalize()
    return out.sort_values("Date").drop_duplicates("Date", keep="last")


def refresh_database(interim_dir: Path | str = INTERIM_DIR,
                     raw_dir: Path | str = RAW_DIR) -> dict:
    interim_dir, raw_dir = Path(interim_dir), Path(raw_dir)
    db_path = interim_dir / "database.parquet"
    if not db_path.exists():
        raise FileNotFoundError(f"{db_path} absent - lancer migrate-legacy d'abord")
    db = pd.read_parquet(db_path)
    db["Date"] = pd.to_datetime(db["Date"])
    last = db["Date"].max()

    frames = {}
    for source, (raw_prefix, db_prefix) in RAW_SOURCES.items():
        raw = _load_raw(raw_dir, source, raw_prefix, db_prefix)
        if raw is not None:
            frames[db_prefix] = raw

    if "corn" not in frames:
        raise RuntimeError("cbot_corn brut indisponible - refresh impossible")

    anchor = frames["corn"]
    new = anchor[anchor["Date"] > last][["Date"]].copy()
    if new.empty:
        log.info("refresh_database_up_to_date", last=str(last.date()))
        return {"appended": 0, "last": str(last.date())}

    for raw in frames.values():
        new = new.merge(raw, on="Date", how="left")

    combined = pd.concat([db, new], ignore_index=True)
    combined = combined.sort_values("Date").drop_duplicates("Date", keep="last")
    combined = combined.reset_index(drop=True)
    write_parquet(combined, db_path)
    log.info("refresh_database_done", appended=len(new),
             new_last=str(combined["Date"].max().date()), rows=len(combined))
    return {"appended": int(len(new)), "last": str(combined["Date"].max().date())}

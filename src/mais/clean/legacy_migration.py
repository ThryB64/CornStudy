"""One-shot migration of the legacy ``csv/corrige/*`` files into ``data/interim/*.parquet``.

Why this exists
---------------
The legacy pipeline (``script/corrige/database.py``) has 2 known bugs that we
fix here at read time:

A. ``csv/corrige/macro_fred_completed.csv`` is written with ``header=False``
   (cf. ``script/corrige/complete_fred_data.py`` line 164). When pandas reads
   it back with the default ``header=0``, the first row of data becomes the
   column names: ``5.98``, ``175.1``, ``0.6321...``, etc. We re-attach the
   correct headers from the original ``TARGET_ORDER`` list.

B. The merged ``database.csv`` contains duplicate columns suffixed with
   ``.1`` (e.g. ``corn_ret_1d.1``) because ``indicateurs_completed.csv`` and
   ``historique_marche_mais_completed.csv`` overlap on ~25 columns and
   ``database.py`` does not deduplicate before merging. We drop those.

This module reads the legacy files, applies both fixes, harmonises types,
writes one parquet per source under ``data/interim/`` and a clean joined
``database.parquet`` for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.paths import (
    INTERIM_DIR,
    LEGACY_CSV_CORRIGE,
    PROJECT_ROOT,
)
from mais.utils import dedupe_columns, get_logger, write_parquet

log = get_logger("mais.clean.migration")


# Correct header for macro_fred_completed.csv (extracted from
# script/corrige/complete_fred_data.py:23-35 - TARGET_ORDER).
_MACRO_FRED_HEADERS: tuple[str, ...] = (
    "Date",
    "fedfunds",
    "cpiaucns",
    "cpi_mom_pct",
    "cpi_yoy_pct",
    "cpi_z24",
    "fedfunds_chg_1m",
    "fedfunds_chg_3m",
    "fedfunds_ma_3",
    "fedfunds_z24",
    "real_fed_rate",
)


def _read_macro_fred_with_correct_header(path: Path) -> pd.DataFrame:
    """Read macro_fred_completed.csv applying the missing header."""
    df = pd.read_csv(path, header=None, names=list(_MACRO_FRED_HEADERS))
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").drop_duplicates(["Date"], keep="last")
    return df.reset_index(drop=True)


def _read_with_date(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Date" not in df.columns and "date" in df.columns:
        df = df.rename(columns={"date": "Date"})
    if "Date" not in df.columns:
        c0 = df.columns[0]
        if pd.to_datetime(df[c0], errors="coerce").notna().mean() > 0.5:
            df = df.rename(columns={c0: "Date"})
        else:
            raise ValueError(f"No Date column found in {path}")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    df = df.drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
    return df


def _normalise_legacy_names(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    """Rename columns that would collide on merge.
    For sources other than the anchor (market/indicateurs), prefix every
    non-Date column with ``suffix_``. This eliminates the ``.1`` doublons.
    """
    rename = {c: c if c == "Date" or c.startswith(f"{suffix}_") else f"{suffix}_{c}"
              for c in df.columns}
    return df.rename(columns=rename)


def migrate_legacy(legacy_dir: Path | str = LEGACY_CSV_CORRIGE,
                    interim_dir: Path | str = INTERIM_DIR,
                    write_combined: bool = True) -> dict[str, Path]:
    """Read legacy ``csv/corrige/`` files, apply bug fixes, write Parquet.

    Returns a dict ``{source_name: parquet_path}`` for everything written.
    """
    legacy_dir = Path(legacy_dir)
    interim_dir = Path(interim_dir)
    interim_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    files: dict[str, Path] = {
        "market":      legacy_dir / "historique_marche_mais_completed.csv",
        "indicateurs": legacy_dir / "indicateurs_completed.csv",
        "macro_fred":  legacy_dir / "macro_fred_completed.csv",
        "wasde":       legacy_dir / "wasde_completed.csv",
        "quickstats":  legacy_dir / "quickstats_completed.csv",
        "production":  legacy_dir / "production_state_completed.csv",
    }

    frames: dict[str, pd.DataFrame] = {}

    for name, path in files.items():
        if not path.exists():
            log.warning("legacy_file_missing", source=name, path=str(path))
            continue
        try:
            if name == "macro_fred":
                df = _read_macro_fred_with_correct_header(path)
            else:
                df = _read_with_date(path)
                df = dedupe_columns(df)
        except Exception as e:
            log.error("legacy_read_failed", source=name, error=str(e))
            continue

        out = interim_dir / f"{name}.parquet"
        write_parquet(df, out)
        written[name] = out
        frames[name] = df
        log.info("legacy_migrated", source=name, rows=len(df), cols=df.shape[1], out=str(out))

    # Météo (1 fichier par état)
    legacy_meteo_dir = legacy_dir / "meteo"
    if legacy_meteo_dir.is_dir():
        meteo_frames: list[pd.DataFrame] = []
        for f in sorted(legacy_meteo_dir.glob("*.csv")):
            try:
                df = _read_with_date(f)
                df = dedupe_columns(df)
                state = f.stem.replace("meteo_", "").lower()
                df = df.rename(columns={c: c if c == "Date" else f"wx_{state}_{c}"
                                         for c in df.columns})
                meteo_frames.append(df)
            except Exception as e:
                log.warning("meteo_read_failed", file=str(f), error=str(e))
        if meteo_frames:
            meteo = meteo_frames[0]
            for f in meteo_frames[1:]:
                meteo = meteo.merge(f, on="Date", how="outer")
            meteo = meteo.sort_values("Date").drop_duplicates(["Date"], keep="last")
            out = interim_dir / "meteo.parquet"
            write_parquet(meteo, out)
            written["meteo"] = out
            frames["meteo"] = meteo
            log.info("legacy_migrated", source="meteo", rows=len(meteo), cols=meteo.shape[1])

    if write_combined and frames:
        combined = _build_combined(frames)
        out = interim_dir / "database.parquet"
        write_parquet(combined, out)
        written["combined"] = out
        log.info("legacy_combined", rows=len(combined), cols=combined.shape[1], out=str(out))

    return written


def _build_combined(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge all frames cleanly using namespacing to avoid collisions.

    Anchor priority: indicateurs > market.
    Other sources are prefixed with their name (macro_fred_*, wasde_*, ...).
    """
    if "indicateurs" in frames:
        anchor = frames["indicateurs"].copy()
    elif "market" in frames:
        anchor = frames["market"].copy()
    else:
        anchor = next(iter(frames.values())).copy()

    db = anchor

    if "market" in frames and "indicateurs" in frames:
        # Add only market columns NOT already in indicateurs.
        market = frames["market"]
        new_cols = [c for c in market.columns if c not in db.columns or c == "Date"]
        if len(new_cols) > 1:
            db = db.merge(market[new_cols], on="Date", how="left")

    for name in ["macro_fred", "wasde", "quickstats", "production", "meteo"]:
        if name not in frames:
            continue
        df = frames[name]
        df = _normalise_legacy_names(df, suffix=name) if name != "meteo" else df
        new_cols = [c for c in df.columns if c == "Date" or c not in db.columns]
        db = db.merge(df[new_cols], on="Date", how="left")

    db = db.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
    db = dedupe_columns(db)
    return db

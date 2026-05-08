"""I/O helpers: read/write CSV or Parquet transparently."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def read_table(
    path: str | Path,
    parse_dates: Optional[Iterable[str]] = None,
    date_col: Optional[str] = None,
    **read_csv_kwargs,
) -> pd.DataFrame:
    """Read a CSV or Parquet file based on the extension.

    Parameters
    ----------
    path
        File path; ``.parquet``, ``.pq``, ``.csv`` or ``.csv.gz`` supported.
    parse_dates
        Columns to parse as dates (CSV only - parquet preserves dtype).
    date_col
        If provided, sort + drop duplicates on this column.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(p)
    elif suffix in {".csv", ".gz", ".csv.gz"} or p.name.endswith(".csv.gz"):
        df = pd.read_csv(p, parse_dates=list(parse_dates) if parse_dates else None,
                         **read_csv_kwargs)
    else:
        raise ValueError(f"Unsupported file extension: {p}")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)
        df = df.drop_duplicates(subset=[date_col], keep="last").reset_index(drop=True)
    return df


def write_parquet(df: pd.DataFrame, path: str | Path, partition_year: bool = False,
                   date_col: str = "Date") -> None:
    """Write a DataFrame to Parquet, optionally partitioning by year."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if partition_year and date_col in df.columns:
        df = df.copy()
        df["_year"] = pd.to_datetime(df[date_col]).dt.year
        df.to_parquet(p, partition_cols=["_year"], engine="pyarrow", index=False)
    else:
        df.to_parquet(p, engine="pyarrow", index=False)


def read_parquet(path: str | Path, columns: Optional[list[str]] = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_parquet(p, columns=columns)


def dedupe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop columns whose name ends in ``.1`` (pandas merge collision artefacts)
    and any columns whose name starts with a digit or '-' (numerical-header bug
    inherited from headerless CSV reads, e.g. ``5.98``, ``175.1``).
    """
    bad = []
    for c in df.columns:
        sc = str(c)
        if sc.endswith(".1"):
            bad.append(c)
        elif sc and (sc[0].isdigit() or (sc[0] == "-" and len(sc) > 1 and sc[1].isdigit())):
            bad.append(c)
    if bad:
        df = df.drop(columns=bad)
    return df

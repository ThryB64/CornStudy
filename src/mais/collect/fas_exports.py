"""R&D-04 USDA FAS Export Sales collector wrapper."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from mais.collect import fas_export_sales_collector
from mais.paths import INTERIM_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.collect.fas_exports")


def empty_fas_weekly() -> pd.DataFrame:
    """Return the stable empty schema used when credentials/source are absent."""
    return pd.DataFrame(
        {
            "Date": pd.Series(dtype="datetime64[ns]"),
            "export_sales_mt": pd.Series(dtype="float"),
            "export_sales_accumulated_mt": pd.Series(dtype="float"),
            "export_china_sales_mt": pd.Series(dtype="float"),
            "usda_export_forecast_mt": pd.Series(dtype="float"),
        }
    )


def download(out_dir: Path, src: dict) -> str:
    """Download FAS export sales or write an empty fallback without crashing."""
    api_key_env = src.get("api_key_env", "FAS_API_KEY")
    if not os.environ.get(api_key_env):
        out_dir.mkdir(parents=True, exist_ok=True)
        empty = empty_fas_weekly()
        empty.to_csv(out_dir / "fas_export_sales.csv", index=False)
        if src.get("write_interim", True):
            INTERIM_DIR.mkdir(parents=True, exist_ok=True)
            write_parquet(empty, INTERIM_DIR / "fas_export_sales.parquet")
        log.warning("fas_api_key_missing_empty_fallback", api_key_env=api_key_env)
        return "empty fallback: FAS_API_KEY missing"
    return fas_export_sales_collector.download(out_dir, src)

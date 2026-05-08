"""USDA WASDE collector.

The legacy code in ``script/wasde_*.py`` already does the PDF parsing - this
module is a thin wrapper that calls the legacy parser and writes a clean CSV.

Until those parsers are ported into ``src/mais/collect/``, this collector is
a stub that points to the legacy artefacts.
"""

from __future__ import annotations

from pathlib import Path

from mais.utils import get_logger

log = get_logger("mais.collect.wasde")


def download(out_dir: Path, src: dict) -> str:
    raise NotImplementedError(
        "WASDE collector: port script/wasde_downloader.py + script/wasde_parser.py "
        "into src/mais/collect/usda_wasde_collector.py. The pdfplumber tables to extract "
        "are: 'World corn supply and use', 'US corn supply and use'. Output CSV columns: "
        "Date, wasde_us_corn_production, wasde_us_corn_yield, wasde_us_corn_ending_stocks, "
        "wasde_us_corn_exports, wasde_world_corn_production, wasde_world_corn_ending_stocks, "
        "wasde_world_corn_use."
    )

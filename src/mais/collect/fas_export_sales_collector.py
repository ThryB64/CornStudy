"""USDA FAS Export Sales collector (Phase 1 NEW).

Weekly. Released Thursday 8:30 ET for the week ending Thursday previous.
Critical: lag = 7 days (declared in sources.yaml).

API
---
https://apps.fas.usda.gov/OpenData/api/esr/exports/commodityCode/0410?marketYearId=...
Free key: https://apps.fas.usda.gov/OpenData/
Set FAS_API_KEY environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path

from mais.utils import get_logger

log = get_logger("mais.collect.fas")


def download(out_dir: Path, src: dict) -> str:
    api_key = os.environ.get(src.get("api_key_env", "FAS_API_KEY"))
    if not api_key:
        raise NotImplementedError(
            "Set FAS_API_KEY (https://apps.fas.usda.gov/OpenData/). Then implement the "
            "ESR endpoint loop over marketYearId 2000..current. Output CSV columns: "
            "Date (week_ending), commodity, country, weeklyExports, accumulatedExports, "
            "outstandingSales, grossNewSales, currentMYNetSales, nextMYNetSales, "
            "currentMYTotalCommitment."
        )
    raise NotImplementedError("FAS Export Sales collector to wire up.")

"""US Drought Monitor weekly collector (Phase 1 NEW).

Public, no API key. The Drought Monitor publishes weekly classification:
  D0 (abnormally dry), D1 (moderate), D2 (severe), D3 (extreme), D4 (exceptional)

For corn-area-impacted statistics:
  https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx
Filter: AgArea -> Corn.

A simpler endpoint (USDM web service):
  https://usdmdataservices.unl.edu/api/AgriculturalStatistics/GetCropImpactStateCorn
"""

from __future__ import annotations

from pathlib import Path

from mais.utils import get_logger

log = get_logger("mais.collect.drought")


def download(out_dir: Path, src: dict) -> str:
    raise NotImplementedError(
        "Drought Monitor collector to wire: GET https://usdmdataservices.unl.edu/api/"
        "AgriculturalStatistics/GetCropImpactStateCorn?aoi=CONUS&endDate={today}&"
        "startDate=2000-01-01&statisticsType=1&format=json. "
        "Returns weekly D0..D4 corn area pct. Output CSV columns: Date, "
        "corn_area_d0, corn_area_d1, corn_area_d2, corn_area_d3, corn_area_d4."
    )

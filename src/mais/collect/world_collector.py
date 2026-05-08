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

from mais.utils import get_logger

log = get_logger("mais.collect.world")


def download(out_dir: Path, src: dict) -> str:
    name = src["name"]
    if name == "noaa_oni":
        return _download_noaa_oni(out_dir, src)
    if name == "conab_brazil":
        raise NotImplementedError(
            "CONAB scraper to wire: parse https://www.conab.gov.br/info-agro/safras/serie-historica-das-safras "
            "Excel files. Output Date, brazil_corn_production_total, brazil_safrinha_production, "
            "brazil_corn_planted_area, brazil_corn_harvested_area."
        )
    if name == "bcr_argentina":
        raise NotImplementedError(
            "Bolsa de Cereales Rosario scraper to wire. Output Date, argentina_corn_planted_pct, "
            "argentina_corn_harvested_pct, argentina_corn_condition_good_pct, "
            "argentina_corn_production_estimate."
        )
    if name == "ukragroconsult":
        raise NotImplementedError("UkrAgroConsult requires subscription.")
    raise NotImplementedError(f"Unknown world source: {name}")


def _download_noaa_oni(out_dir: Path, src: dict) -> str:
    try:
        import requests
        import pandas as pd
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

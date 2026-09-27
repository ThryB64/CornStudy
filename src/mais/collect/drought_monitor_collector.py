"""US Drought Monitor weekly collector (V3-06, endpoint réparé 2026-09-27).

Public, no API key. L'ancien endpoint maïs (AgriculturalStatistics/GetCropImpactStateCorn) renvoie 404 :
proxy Corn Belt = moyenne des stats d'État pondérée par la production de maïs.
Les pourcentages USDM sont CUMULATIFS (D0 inclut D1..D4) → convertis en catégories exclusives d0..d4.
Date = publication (jeudi, carte valide au mardi) : la carte n'est pas connue avant.
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.drought")

BASE_URL = (
    "https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent"
    "?aoi={fips}&startdate={start}&enddate={end}&statisticsType=1"
)
# FIPS -> poids ~ production maïs moyenne 2019-2023 (Mds bu)
CORN_BELT_WEIGHTS = {"19": 2.5, "17": 2.2, "31": 1.7, "27": 1.4, "18": 1.0,
                     "46": 0.75, "39": 0.55, "55": 0.55}
PUBLICATION_LAG_DAYS = 2


def _fetch_state(fips: str, start: str, end: str, timeout: int = 60) -> pd.DataFrame:
    url = BASE_URL.format(fips=fips, start=start, end=end)
    req = urllib.request.Request(url, headers={"Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return pd.read_csv(io.StringIO(raw))


def _parse_records(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Moyenne pondérée Corn Belt des % cumulatifs, puis catégories exclusives."""
    parts = []
    for fips, df in frames.items():
        if df is None or df.empty or "MapDate" not in df.columns:
            continue
        d = pd.DataFrame({"map_date": pd.to_datetime(df["MapDate"].astype(str), format="%Y%m%d")})
        for lvl in range(5):
            d[f"D{lvl}"] = pd.to_numeric(df[f"D{lvl}"], errors="coerce")
        d["w"] = CORN_BELT_WEIGHTS.get(fips, 0.0)
        parts.append(d)
    if not parts:
        return pd.DataFrame()
    allp = pd.concat(parts, ignore_index=True).dropna()
    cum = allp.groupby("map_date").apply(
        lambda g: pd.Series({f"D{i}": (g[f"D{i}"] * g["w"]).sum() / g["w"].sum() for i in range(5)}),
        include_groups=False,
    )
    out = pd.DataFrame(index=cum.index)
    for i in range(4):
        out[f"corn_area_d{i}"] = (cum[f"D{i}"] - cum[f"D{i + 1}"]).clip(lower=0)
    out["corn_area_d4"] = cum["D4"]
    out = out.reset_index()
    out["Date"] = out["map_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    cols = ["Date", "map_date"] + [f"corn_area_d{i}" for i in range(5)]
    return out[cols].sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)


def download(out_dir: Path, src: dict, *, start_year: int = 2000) -> str:
    """Download USDM Corn Belt drought data and save to out_dir/drought_monitor.parquet."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "drought_monitor.parquet"

    now = datetime.now(tz=timezone.utc)
    start, end = f"1/1/{start_year}", f"{now.month}/{now.day}/{now.year}"
    frames: dict[str, pd.DataFrame] = {}
    for fips in CORN_BELT_WEIGHTS:
        try:
            frames[fips] = _fetch_state(fips, start, end)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            log.warning("drought_state_failed", fips=fips, error=str(exc))
    df = _parse_records(frames)
    # couverture partielle (<75 % du poids) = biais de composition : on garde le cache
    covered = sum(CORN_BELT_WEIGHTS[f] for f, d in frames.items() if d is not None and not d.empty)
    if df.empty or covered < 0.75 * sum(CORN_BELT_WEIGHTS.values()):
        if out_path.exists():
            log.warning("drought_using_cached", path=str(out_path), covered=covered)
            return str(out_path)
        raise RuntimeError("USDM fetch failed and no cached file available")

    df = df[df["Date"] <= pd.Timestamp(now.date())]
    df.to_parquet(out_path, index=False)
    df.drop(columns=["map_date"]).to_parquet(INTERIM_DIR / "drought_monitor.parquet", index=False)
    log.info("drought_saved", path=str(out_path), rows=len(df), last=str(df["Date"].max().date()))
    return str(out_path)


def build_drought_features(drought_df: pd.DataFrame) -> pd.DataFrame:
    """Build granular drought features from raw D0-D4 area data.

    Produces:
    - drought_d2plus: weighted D2+D3+D4 pct (severity-weighted)
    - drought_change_4w: change in drought_d2plus over 4 weeks (~26 days)
    - drought_extreme_flag: 1 if D3+D4 > 10% of corn area
    """
    df = drought_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    for col in ("corn_area_d2", "corn_area_d3", "corn_area_d4"):
        if col not in df.columns:
            df[col] = 0.0

    df["drought_d2plus"] = (
        0.5 * pd.to_numeric(df["corn_area_d2"], errors="coerce").fillna(0)
        + 0.75 * pd.to_numeric(df["corn_area_d3"], errors="coerce").fillna(0)
        + 1.0 * pd.to_numeric(df["corn_area_d4"], errors="coerce").fillna(0)
    )
    df["drought_change_4w"] = df["drought_d2plus"].diff(4)
    d3 = pd.to_numeric(df.get("corn_area_d3", 0), errors="coerce").fillna(0)
    d4 = pd.to_numeric(df.get("corn_area_d4", 0), errors="coerce").fillna(0)
    df["drought_extreme_flag"] = ((d3 + d4) > 10.0).astype(float)

    return df[["Date", "drought_d2plus", "drought_change_4w", "drought_extreme_flag"]]

"""DATA-EU-02 — Collecteur météo Open-Meteo pour 6 zones maïs EU.

Calcule GDD (Growing Degree Days), stress thermique, déficit précipitations.
API gratuite, sans clé. Toutes les features sont shift(1) — anti-leakage.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

_RAW_DIR = Path(__file__).parents[3] / "data" / "raw" / "openmeteo_eu"
_AUDIT_OUTPUT = ARTEFACTS_DIR / "ema_study" / "openmeteo_eu_audit.json"
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

CORN_ZONES_EU = {
    "france_so": {"lat": 44.0, "lon": 0.5, "weight": 0.25},
    "france_co": {"lat": 46.5, "lon": 2.0, "weight": 0.10},
    "italy_north": {"lat": 45.0, "lon": 11.0, "weight": 0.20},
    "romania": {"lat": 44.5, "lon": 26.0, "weight": 0.20},
    "hungary": {"lat": 47.0, "lon": 19.0, "weight": 0.15},
    "ukraine_west": {"lat": 49.0, "lon": 27.0, "weight": 0.10},
}

_GDD_BASE = 10.0
_GDD_MAX = 30.0


def _fetch_zone(zone: str, lat: float, lon: float, start: str = "2010-01-01") -> pd.DataFrame | None:
    try:
        import requests
    except ImportError:
        return None
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": pd.Timestamp.now("UTC").normalize().strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Paris",
    }
    try:
        r = requests.get(_ARCHIVE_URL, params=params, timeout=120)
        r.raise_for_status()
        payload = r.json()
    except Exception:
        return None
    daily = payload.get("daily", {})
    if not daily or "time" not in daily:
        return None
    df = pd.DataFrame(daily)
    df = df.rename(columns={"time": "Date"})
    df["Date"] = pd.to_datetime(df["Date"])
    df["zone"] = zone
    return df


def _compute_agro_features(df: pd.DataFrame) -> pd.DataFrame:
    tmax = df["temperature_2m_max"]
    tmin = df["temperature_2m_min"]
    precip = df["precipitation_sum"]

    tmax_clip = tmax.clip(_GDD_BASE, _GDD_MAX)
    tmin_clip = tmin.clip(_GDD_BASE, _GDD_MAX)
    gdd_daily = ((tmax_clip + tmin_clip) / 2) - _GDD_BASE
    gdd_daily = gdd_daily.clip(lower=0)

    df = df.copy()
    df["gdd_daily"] = gdd_daily
    df["heat_stress_32"] = (tmax > 32).astype(float)
    df["heat_stress_35"] = (tmax > 35).astype(float)
    df["precip_sum"] = precip
    return df


def _build_eu_aggregate(zone_frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Weighted average across zones, then weekly and daily features."""
    if not zone_frames:
        return pd.DataFrame()

    weighted = []
    for z, df in zone_frames:
        w = CORN_ZONES_EU[z]["weight"]
        df = df.copy()
        for col in ["gdd_daily", "heat_stress_32", "heat_stress_35", "precip_sum"]:
            if col in df.columns:
                df[col] = df[col] * w
        weighted.append(df)

    combined = pd.concat(weighted, ignore_index=True)
    agg = combined.groupby("Date")[["gdd_daily", "heat_stress_32", "heat_stress_35", "precip_sum"]].sum()
    agg = agg.reset_index().sort_values("Date").reset_index(drop=True)

    # GDD cumulative depuis 1er mai de chaque année
    agg["doy"] = agg["Date"].dt.dayofyear
    agg["year"] = agg["Date"].dt.year
    agg["month"] = agg["Date"].dt.month
    may1_doy = pd.Timestamp("2000-05-01").dayofyear

    gdd_cumul = []
    for _, grp in agg.groupby("year"):
        cumul = 0.0
        vals = []
        for _, row in grp.iterrows():
            if row["month"] < 5:
                cumul = 0.0
            elif row["month"] >= 5 and row["doy"] >= may1_doy:
                cumul += row["gdd_daily"]
            vals.append(cumul)
        gdd_cumul.extend(vals)
    agg["eu_gdd_cumul"] = gdd_cumul

    # Rolling metrics (28 jours = 4 semaines)
    agg["eu_heat_stress_days_4w"] = agg["heat_stress_32"].rolling(28, min_periods=14).sum()
    agg["eu_precip_deficit_30d"] = (
        agg["precip_sum"].rolling(30, min_periods=20).sum()
        - agg["precip_sum"].rolling(365, min_periods=180).mean() * 30 / 365
    )

    # GDD anomalie vs 10 ans glissants
    mu_gdd = agg["eu_gdd_cumul"].rolling(3650, min_periods=730).mean().shift(1)
    agg["eu_gdd_anomaly"] = agg["eu_gdd_cumul"] - mu_gdd

    result = agg[["Date", "eu_gdd_cumul", "eu_gdd_anomaly", "eu_heat_stress_days_4w", "eu_precip_deficit_30d"]].copy()

    # Anti-leakage : shift(1) sur toutes les features
    for col in ["eu_gdd_cumul", "eu_gdd_anomaly", "eu_heat_stress_days_4w", "eu_precip_deficit_30d"]:
        result[col] = result[col].shift(1)

    return result


def build_openmeteo_eu_features(out_dir: Path | None = None, start: str = "2010-01-01") -> pd.DataFrame:
    raw_dir = out_dir or _RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    zone_frames = []
    for zone, cfg in CORN_ZONES_EU.items():
        df = _fetch_zone(zone, cfg["lat"], cfg["lon"], start=start)
        if df is not None and not df.empty:
            df = _compute_agro_features(df)
            df.to_parquet(raw_dir / f"zone_{zone}.parquet", index=False)
            zone_frames.append((zone, df))

    if not zone_frames:
        return pd.DataFrame(columns=["Date", "eu_gdd_cumul", "eu_gdd_anomaly",
                                      "eu_heat_stress_days_4w", "eu_precip_deficit_30d"])

    result = _build_eu_aggregate(zone_frames)
    return result


def build_audit(df: pd.DataFrame, n_zones: int = 6) -> dict:
    audit: dict = {"n_zones": n_zones, "features": {}}
    if df.empty:
        audit["error"] = "no_data_collected"
        return audit

    audit["n_rows"] = int(len(df))
    if "Date" in df.columns and len(df) > 0:
        audit["start"] = str(df["Date"].iloc[0].date())
        audit["end"] = str(df["Date"].iloc[-1].date())

    for col in ["eu_gdd_cumul", "eu_gdd_anomaly", "eu_heat_stress_days_4w", "eu_precip_deficit_30d"]:
        if col in df.columns:
            s = df[col]
            audit["features"][col] = {
                "n_valid": int(s.notna().sum()),
                "nan_pct": float(s.isna().mean()),
            }
    return audit


def save_openmeteo_eu(output_path: Path | None = None) -> Path:
    path = output_path or _AUDIT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)

    df = build_openmeteo_eu_features()
    if not df.empty:
        df.to_parquet(_RAW_DIR / "openmeteo_eu_daily.parquet", index=False)

    n_zones = sum(1 for z in CORN_ZONES_EU if (_RAW_DIR / f"zone_{z}.parquet").exists())
    audit = build_audit(df, n_zones=n_zones)
    audit["zones"] = list(CORN_ZONES_EU.keys())
    audit["note"] = "Open-Meteo gratuit, sans clé. Données depuis 2010. Anti-leakage shift(1)."

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(audit, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_openmeteo_eu()
    print(f"Open-Meteo EU audit saved → {out}")

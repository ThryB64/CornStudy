"""Utilitaires meteo partages (EXT001/EXT002/EXT020).

Source : data/interim/database.parquet, metriques quotidiennes brutes par Etat
(tmin_c, tmax_c, tavg_c, prcp_mm, gdd_base10) pour 20 Etats. On ne reutilise PAS
les colonnes d'anomalie internes (_anom_z, non auditees) : la climatologie est
recalculee en expandant (annees strictement anterieures uniquement).

Anti-fuite :
- meteo realisee du jour J disponible J+1 -> shift(1) applique en sortie ;
- ponderations de production FIGEES sur 2000-2007 (hors periode d'evaluation) ;
- climatologie par day-of-year n'utilise que les annees passees.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
DB = ROOT / "data" / "interim" / "database.parquet"

# Etats disposant d'une part de production (corn belt principal)
SHARE_STATES = ["iowa", "illinois", "nebraska", "minnesota", "indiana",
                "south_dakota", "kansas", "ohio", "wisconsin", "missouri"]
BASE_METRICS = ["tmin_c", "tmax_c", "tavg_c", "prcp_mm", "gdd_base10"]
WEIGHT_FREEZE_END = pd.Timestamp("2008-01-01")


def _load_db() -> pd.DataFrame:
    db = pd.read_parquet(DB)
    db["Date"] = pd.to_datetime(db["Date"])
    return db.sort_values("Date").set_index("Date")


def national_weather() -> pd.DataFrame:
    """Series quotidiennes nationales ponderees production (poids figes 2000-07).
    NB : valeurs realisees, decalees J+1 (shift) pour la disponibilite."""
    db = _load_db()
    weights = {}
    for s in SHARE_STATES:
        col = f"production_share_{s}"
        if col in db.columns:
            w = db.loc[db.index < WEIGHT_FREEZE_END, col].mean()
            if np.isfinite(w):
                weights[s] = w
    tot = sum(weights.values())
    weights = {k: v / tot for k, v in weights.items()}

    out = pd.DataFrame(index=db.index)
    for metric in BASE_METRICS:
        acc = np.zeros(len(db))
        wsum = np.zeros(len(db))
        for s, w in weights.items():
            col = f"wx_{s}_wx_{metric}"
            if col not in db.columns:
                continue
            v = db[col].to_numpy(float)
            ok = np.isfinite(v)
            acc[ok] += w * v[ok]
            wsum[ok] += w
        with np.errstate(invalid="ignore", divide="ignore"):
            out[metric] = np.where(wsum > 0, acc / wsum, np.nan)
    # disponibilite J+1
    out = out.shift(1)
    out.attrs["weights"] = weights
    return out


def doy_anomaly_z(x: pd.Series, min_years: int = 5) -> pd.Series:
    """Anomalie standardisee vs climatologie expandante par day-of-year.
    Climatologie = moyenne/ecart-type des ANNEES STRICTEMENT ANTERIEURES pour le
    meme day-of-year (anti-fuite)."""
    df = pd.DataFrame({"x": x.to_numpy(float)}, index=x.index)
    df["doy"] = df.index.dayofyear
    df["yr"] = df.index.year
    z = pd.Series(np.nan, index=x.index)
    for doy, g in df.groupby("doy"):
        g = g.sort_index()
        clim_mean = g["x"].expanding().mean().shift(1)
        clim_std = g["x"].expanding().std().shift(1)
        cnt = g["x"].expanding().count().shift(1)
        zz = (g["x"] - clim_mean) / clim_std
        zz = zz.where(cnt >= min_years)
        z.loc[g.index] = zz.to_numpy()
    return z


def crop_year(idx: pd.DatetimeIndex) -> np.ndarray:
    """Annee de campagne (reset au 1er janvier pour le mais US new-crop)."""
    return idx.year.to_numpy()


def season_to_date_sum(daily: pd.Series, months: list[int]) -> pd.Series:
    """Somme cumulee par campagne (annee civile) restreinte aux mois donnes,
    portee jusqu'a la fin d'annee (as-of). Anti-fuite : que du passe."""
    df = pd.DataFrame({"v": daily.to_numpy(float)}, index=daily.index)
    df["yr"] = df.index.year
    df["mon"] = df.index.month
    df["in_win"] = df["mon"].isin(months).astype(float)
    df["contrib"] = df["v"].fillna(0.0) * df["in_win"]
    out = df.groupby("yr")["contrib"].cumsum()
    return out

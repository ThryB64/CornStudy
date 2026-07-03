"""Helpers communs pour series hebdomadaires datees-disponibilite (EXT019/003/004)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def daily_ffill(df: pd.DataFrame, end="2025-12-31") -> pd.DataFrame:
    """df indexe par available_from -> serie quotidienne forward-fill complete."""
    full = pd.date_range(df.index.min(), pd.Timestamp(end), freq="D")
    return df.reindex(df.index.union(full)).sort_index().ffill().reindex(full)


def expanding_z(s: pd.Series, min_periods: int = 26) -> pd.Series:
    """z-score expandant (passe strict via shift) sur l'ordre temporel."""
    m = s.expanding(min_periods=min_periods).mean().shift(1)
    sd = s.expanding(min_periods=min_periods).std().shift(1)
    return (s - m) / sd


def weekofyear_anom(s: pd.Series, min_years: int = 4) -> pd.Series:
    """Anomalie z vs climatologie expandante par semaine de l'annee (annees passees)."""
    df = pd.DataFrame({"x": s.to_numpy(float)}, index=s.index)
    df["woy"] = df.index.isocalendar().week.to_numpy()
    out = pd.Series(np.nan, index=s.index)
    for woy, g in df.groupby("woy"):
        g = g.sort_index()
        mean = g["x"].expanding().mean().shift(1)
        std = g["x"].expanding().std().shift(1)
        cnt = g["x"].expanding().count().shift(1)
        z = ((g["x"] - mean) / std).where(cnt >= min_years)
        out.loc[g.index] = z.to_numpy()
    return out


def expanding_pctile(s: pd.Series, min_periods: int = 26) -> pd.Series:
    """Rang percentile expandant (0-1) de la valeur courante vs passe strict."""
    vals = s.to_numpy(float)
    out = np.full(len(vals), np.nan)
    for i in range(min_periods, len(vals)):
        past = vals[:i]
        past = past[np.isfinite(past)]
        if len(past) >= min_periods and np.isfinite(vals[i]):
            out[i] = (past < vals[i]).mean()
    return pd.Series(out, index=s.index)

"""Seasonality features: Fourier encoding + agronomic seasons."""

from __future__ import annotations

import numpy as np
import pandas as pd


PLANTING_MONTHS = {4, 5}        # April-May
SILKING_MONTHS = {7}            # July
HARVEST_MONTHS = {9, 10, 11}    # Sept-Nov


def build_seasonality_features(dates: pd.Series) -> pd.DataFrame:
    d = pd.to_datetime(dates).dt
    out = pd.DataFrame({"Date": pd.to_datetime(dates).values})
    out["dow"] = d.dayofweek.values
    out["month"] = d.month.values
    out["doy"] = d.dayofyear.values
    out["month_sin"] = np.sin(2 * np.pi * d.month.values / 12)
    out["month_cos"] = np.cos(2 * np.pi * d.month.values / 12)
    out["doy_sin"] = np.sin(2 * np.pi * d.dayofyear.values / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * d.dayofyear.values / 365.25)
    out["is_planting_season"] = d.month.isin(PLANTING_MONTHS).astype(int).values
    out["is_silking_season"] = d.month.isin(SILKING_MONTHS).astype(int).values
    out["is_harvest_season"] = d.month.isin(HARVEST_MONTHS).astype(int).values
    return out

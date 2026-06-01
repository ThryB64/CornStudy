"""Seasonality analysis — agronomic calendar and market structure."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.research.seasonality")

AGRONOMIC_CALENDAR = {
    3:  ("Intentions semis", "Prospective Plantings USDA"),
    4:  ("Plantations", "Début plantations Corn Belt"),
    5:  ("Plantations", "Plantations en cours, incertitude météo max"),
    6:  ("Croissance", "Végétation active, stress hydrique critique"),
    7:  ("Pollinisation", "CRITIQUE — chaleur/sécheresse = catastrophe"),
    8:  ("Remplissage grains", "Pluie nécessaire, stocks mondiaux révisés"),
    9:  ("Récolte", "Pression de vente, prix souvent bas"),
    10: ("Récolte", "Récolte intensive, export window s'ouvre"),
    11: ("Post-récolte", "Exports actifs, stockage décision"),
    12: ("Hiver", "Stocks USDA, bilan mondial"),
    1:  ("Hiver", "WASDE révisé, tendances monde sud"),
    2:  ("Pré-saison", "Premières estimations semis"),
}

MONTH_FR = {1:"Jan",2:"Fév",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
             7:"Jul",8:"Aoû",9:"Sep",10:"Oct",11:"Nov",12:"Déc"}


def compute_monthly_returns(
    df: pd.DataFrame,
    target_col: str = "y_logret_h20",
    period_col: str = "Date",
) -> pd.DataFrame:
    """Mean and std of target by month, with calendar annotations."""
    d = df.copy()
    d["month"] = pd.to_datetime(d[period_col]).dt.month
    d["year"]  = pd.to_datetime(d[period_col]).dt.year
    agg = d.groupby("month")[target_col].agg(["mean", "std", "sem", "count"]).reset_index()
    agg["month_name"] = agg["month"].map(MONTH_FR)
    agg["phase"] = agg["month"].map(lambda m: AGRONOMIC_CALENDAR.get(m, ("?", ""))[0])
    return agg


def compute_seasonal_by_period(
    df: pd.DataFrame,
    target_col: str = "y_logret_h20",
    period_col: str = "Date",
    year_splits: list[int] | None = None,
) -> pd.DataFrame:
    """Monthly returns split by sub-period for stability analysis."""
    d = df.copy()
    d["month"] = pd.to_datetime(d[period_col]).dt.month
    d["year"]  = pd.to_datetime(d[period_col]).dt.year

    if year_splits is None:
        year_splits = [2012, 2019]  # pre-COT, COT era, post-COVID

    labels = (
        [f"<{year_splits[0]}"] +
        [f"{year_splits[i]}-{year_splits[i+1]}" for i in range(len(year_splits)-1)] +
        [f">{year_splits[-1]}"]
    )
    cuts = [-np.inf] + [float(y) for y in year_splits] + [np.inf]

    d["period"] = pd.cut(d["year"], bins=cuts, labels=labels)
    return d.groupby(["period", "month"])[target_col].mean().reset_index()


def compute_heatmap_data(
    df: pd.DataFrame,
    target_col: str = "y_logret_h20",
    period_col: str = "Date",
) -> pd.DataFrame:
    """Year × Month pivot table for heatmap visualization."""
    d = df.copy()
    d["month"] = pd.to_datetime(d[period_col]).dt.month
    d["year"]  = pd.to_datetime(d[period_col]).dt.year
    pivot = d.pivot_table(index="year", columns="month", values=target_col, aggfunc="mean")
    pivot.columns = [MONTH_FR[m] for m in pivot.columns]
    return pivot


def compute_volatility_by_month(
    df: pd.DataFrame,
    target_col: str = "y_logret_h20",
    period_col: str = "Date",
) -> pd.Series:
    """Std of target by month (proxy for seasonal risk)."""
    d = df.copy()
    d["month"] = pd.to_datetime(d[period_col]).dt.month
    return d.groupby("month")[target_col].std().rename("volatility")


def compute_wasde_effect(
    df: pd.DataFrame,
    price_col: str = "corn_close",
    period_col: str = "Date",
    wasde_dom: int = 10,
    window: int = 3,
) -> dict[str, float]:
    """Compare daily return volatility near WASDE release vs. other days."""
    d = df.copy()
    d["Date"] = pd.to_datetime(d[period_col])
    d["dom"]  = d["Date"].dt.day
    if price_col not in d.columns:
        return {}
    d["ret_1d"] = d[price_col].pct_change(1) * 100
    near = d[d["dom"].between(wasde_dom - window, wasde_dom + window)]["ret_1d"].dropna()
    other = d[~d["dom"].between(wasde_dom - window, wasde_dom + window)]["ret_1d"].dropna()
    return {
        "vol_wasde_days": float(near.std()),
        "vol_other_days": float(other.std()),
        "ratio": float(near.std() / other.std()) if other.std() > 0 else float("nan"),
        "n_wasde": len(near),
        "n_other": len(other),
    }

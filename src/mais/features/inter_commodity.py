"""V7-17 — Relations inter-commodités : 6 spreads et ratios.

Quantifie les relations entre le maïs et les commodités concurrentes.
DESCRIPTIVE_ECONOMIC.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

SPREAD_DEFINITIONS = {
    "corn_soy_ratio": "Ratio maïs/soja (substitution alimentation animale)",
    "wheat_corn_spread": "Spread blé-maïs en EUR/t (compétition céréales)",
    "corn_ethanol_ratio": "Ratio maïs/éthanol (demande énergie)",
    "corn_barley_spread": "Spread maïs-orge (substitution fourrage)",
    "corn_oats_spread": "Spread maïs-avoine",
    "ema_cbot_basis": "Basis EMA-CBOT (prime européenne brute)",
}


def compute_inter_commodity_spreads(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les 6 spreads inter-commodités.

    Colonnes optionnelles attendues : cbot_corn, cbot_soy, cbot_wheat,
    ethanol_price, cbot_barley, cbot_oats, ema_close.
    """
    spreads = pd.DataFrame(index=df.index)

    c_corn = df.get("cbot_corn", df.get("cbot_close", pd.Series(np.nan, index=df.index)))
    c_soy = df.get("cbot_soy", pd.Series(np.nan, index=df.index))
    c_wheat = df.get("cbot_wheat", pd.Series(np.nan, index=df.index))
    c_eth = df.get("ethanol_price", pd.Series(np.nan, index=df.index))
    c_bar = df.get("cbot_barley", pd.Series(np.nan, index=df.index))
    c_oats = df.get("cbot_oats", pd.Series(np.nan, index=df.index))
    ema = df.get("ema_close", pd.Series(np.nan, index=df.index))

    spreads["corn_soy_ratio"] = c_corn / c_soy.replace(0, np.nan)
    spreads["wheat_corn_spread"] = c_wheat - c_corn
    spreads["corn_ethanol_ratio"] = c_corn / c_eth.replace(0, np.nan)
    spreads["corn_barley_spread"] = c_corn - c_bar
    spreads["corn_oats_spread"] = c_corn - c_oats
    spreads["ema_cbot_basis"] = ema - c_corn

    return spreads


def compute_rolling_correlation(
    spreads: pd.DataFrame,
    premium: pd.Series,
    window: int = 90,
) -> pd.DataFrame:
    """Corrélation mobile entre chaque spread et le premium."""
    corrs = pd.DataFrame(index=spreads.index)
    for col in spreads.columns:
        corrs[f"corr_{col}_vs_premium"] = spreads[col].rolling(window, min_periods=30).corr(premium)
    return corrs


def run_inter_commodity_analysis(
    df: pd.DataFrame,
    premium_col: str = "ema_cbot_basis",
    window: int = 90,
) -> dict[str, Any]:
    """Analyse complète des relations inter-commodités."""
    spreads = compute_inter_commodity_spreads(df)
    premium = spreads.get(premium_col, pd.Series(0.0, index=df.index))
    corrs = compute_rolling_correlation(spreads, premium, window)

    mean_corrs = {}
    for col in spreads.columns:
        if col == premium_col:
            continue
        corr_col = f"corr_{col}_vs_premium"
        if corr_col in corrs.columns:
            mean_corrs[col] = round(float(corrs[corr_col].mean(skipna=True)), 4)

    return {
        "version": "V7-17",
        "n_spreads": len(SPREAD_DEFINITIONS),
        "spreads_defined": list(SPREAD_DEFINITIONS.keys()),
        "mean_rolling_correlations": mean_corrs,
        "correlation_window": window,
        "columns_available": {k: not spreads[k].isna().all() for k in spreads.columns},
    }

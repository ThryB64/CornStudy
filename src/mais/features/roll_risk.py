"""V7-07 — Roll-aware premium model : score de risque roll [0,1]."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_roll_risk_score(
    df: pd.DataFrame,
    dte_col: str = "days_to_expiry",
    gap_col: str = "roll_gap",
    price_col: str = "ema_close",
    dte_window: int = 30,
) -> pd.Series:
    """Score roll-risk [0,1] : 0 = pas de risque, 1 = risque maximum.

    3 composantes pondérées :
    - Proximité du roll (DTE) : 40%
    - Percentile historique du gap : 40%
    - Ratio vol 20j/60j : 20%
    """
    # Composante 1 : DTE — score croît dans les 30 derniers jours avant roll
    if dte_col in df.columns:
        dte_score = np.clip(1.0 - df[dte_col] / dte_window, 0.0, 1.0)
    else:
        dte_score = pd.Series(0.0, index=df.index)

    # Composante 2 : percentile historique du gap de roll
    if gap_col in df.columns:
        gap_percentile = df[gap_col].expanding(min_periods=20).rank(pct=True).fillna(0.5)
    else:
        gap_percentile = pd.Series(0.5, index=df.index)

    # Composante 3 : ratio vol 20j/60j (vol récente vs historique)
    if price_col in df.columns:
        daily_ret = df[price_col].pct_change()
        vol_20 = daily_ret.rolling(20, min_periods=5).std()
        vol_60 = daily_ret.rolling(60, min_periods=20).std()
        vol_ratio = (vol_20 / vol_60.replace(0, np.nan)).clip(0, 3) / 3.0
        vol_ratio = vol_ratio.fillna(0.5)
    else:
        vol_ratio = pd.Series(0.5, index=df.index)

    roll_risk = 0.4 * dte_score + 0.4 * gap_percentile + 0.2 * vol_ratio
    return roll_risk.rename("roll_risk_score")


def apply_roll_veto(
    signals: pd.DataFrame,
    roll_risk: pd.Series,
    threshold: float = 0.7,
    fill_value: float = float("nan"),
) -> pd.DataFrame:
    """Neutralise les signaux les jours à roll-risk > threshold."""
    high_risk = roll_risk > threshold
    result = signals.copy()
    result.loc[high_risk] = fill_value
    return result


def compute_roll_aware_report(
    df: pd.DataFrame,
    dte_col: str = "days_to_expiry",
    gap_col: str = "roll_gap",
    veto_threshold: float = 0.7,
) -> dict:
    """Rapport roll-risk complet."""
    score = compute_roll_risk_score(df, dte_col, gap_col)
    n_veto = int((score > veto_threshold).sum())
    return {
        "mean_roll_risk": round(float(score.mean()), 4),
        "pct_high_risk": round(float((score > veto_threshold).mean()), 4),
        "n_veto_days": n_veto,
        "veto_threshold": veto_threshold,
        "dte_available": dte_col in df.columns,
        "gap_available": gap_col in df.columns,
    }

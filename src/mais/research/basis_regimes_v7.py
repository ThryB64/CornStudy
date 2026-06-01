"""V7-08 — Régimes de basis EMA/CBOT : 6 régimes économiques.

Schéma de sortie _build_regimes() : Date, corn_close, return_60d,
realized_vol_60d, regime_score, regime.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "basis_regimes.json"

REGIME_NAMES = frozenset({
    "NORMAL",
    "HIGH_STABLE",
    "HIGH_COMPRESSING",
    "HIGH_EXPANDING",
    "LOW_BASIS",
    "ROLL_DISTORTED",
})


def _classify_regime(basis_z: float, basis_trend: float, roll_risk: float) -> str:
    if roll_risk > 0.7:
        return "ROLL_DISTORTED"
    if basis_z > 1.5 and abs(basis_trend) < 0.5:
        return "HIGH_STABLE"
    if basis_z > 1.0 and basis_trend < -0.5:
        return "HIGH_COMPRESSING"
    if basis_z > 1.0 and basis_trend > 0.5:
        return "HIGH_EXPANDING"
    if basis_z < -1.0:
        return "LOW_BASIS"
    return "NORMAL"


def _build_regimes(df: pd.DataFrame) -> pd.DataFrame:
    """Schéma fixe : Date, corn_close, return_60d, realized_vol_60d, regime_score, regime.

    Requiert colonnes : ema_close (+ optionnel : cbot_close_eur, roll_risk_score).
    """
    if "ema_close" not in df.columns:
        raise ValueError("Colonne 'ema_close' manquante")

    price = df["ema_close"]

    if "cbot_close_eur" in df.columns:
        basis = price - df["cbot_close_eur"]
    else:
        basis = price - price.rolling(252, min_periods=60).mean()

    basis_mean = basis.expanding(min_periods=20).mean()
    basis_std = basis.expanding(min_periods=20).std().replace(0, np.nan)
    basis_z = ((basis - basis_mean) / basis_std).fillna(0.0)
    basis_trend = (basis.rolling(20, min_periods=5).mean() - basis.rolling(60, min_periods=20).mean()).fillna(0.0)

    roll_risk = df.get("roll_risk_score", pd.Series(0.0, index=df.index))

    tmp = pd.DataFrame({
        "basis_z": basis_z,
        "basis_trend": basis_trend,
        "roll_risk": roll_risk,
    })
    regime_col = tmp.apply(
        lambda row: _classify_regime(row["basis_z"], row["basis_trend"], row["roll_risk"]),
        axis=1,
    )

    result = pd.DataFrame(
        {
            "corn_close": price,
            "return_60d": price.pct_change(60),
            "realized_vol_60d": price.pct_change().rolling(60, min_periods=20).std() * np.sqrt(252),
            "regime_score": basis_z.clip(-3, 3) / 3.0,
            "regime": regime_col,
        },
        index=df.index,
    )
    result.index.name = "Date"
    return result


def compute_regime_stats(regimes_df: pd.DataFrame) -> dict[str, Any]:
    """Statistiques par régime : fréquence, durée moyenne, transitions."""
    regime_counts = regimes_df["regime"].value_counts()
    n_total = len(regimes_df)

    stats: dict[str, Any] = {}
    for regime in REGIME_NAMES:
        count = int(regime_counts.get(regime, 0))
        stats[regime] = {
            "n_days": count,
            "frequency": round(count / n_total, 4) if n_total > 0 else 0.0,
        }

    # Matrice de transition
    transitions: dict[str, dict[str, int]] = {r: dict.fromkeys(REGIME_NAMES, 0) for r in REGIME_NAMES}
    prev = None
    for curr in regimes_df["regime"]:
        if prev is not None and pd.notna(prev) and pd.notna(curr):
            transitions[prev][curr] += 1
        prev = curr

    return {"regime_stats": stats, "transition_matrix": transitions}


def run_basis_regimes(df: pd.DataFrame) -> dict[str, Any]:
    """Construit les régimes et calcule les statistiques."""
    regimes_df = _build_regimes(df)
    stats = compute_regime_stats(regimes_df)
    regime_dist = {r: s["frequency"] for r, s in stats["regime_stats"].items()}
    return {
        "version": "V7-08",
        "n_dates": len(regimes_df),
        "regime_distribution": regime_dist,
        "dominant_regime": max(regime_dist, key=lambda k: regime_dist[k]),
        **stats,
    }


def save_basis_regimes(df: pd.DataFrame) -> dict[str, Any]:
    result = run_basis_regimes(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-08",
        target="basis_regimes",
        horizon=0,
        model="rule_based_regime_classifier",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=["basis_z", "basis_trend", "roll_risk_score"],
        metrics={"n_regimes": len(REGIME_NAMES), "dominant_regime": result["dominant_regime"]},
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result

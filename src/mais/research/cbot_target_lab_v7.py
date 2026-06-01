"""V7-04 — CBOT Target Lab avancé : 8 nouvelles cibles.

Extension du target lab V6 avec cibles conditionnelles, asymétriques,
risk-adjusted et long horizon.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "cbot_target_lab.json"

TARGET_HORIZONS = {
    "y_cbot_up_h60_when_basis_high": 60,
    "y_cbot_strong_up_h60": 60,
    "y_cbot_risk_adj_h60": 60,
    "y_cbot_down_h60": 60,
    "y_cbot_up_h120": 120,
    "y_cbot_vol_spike_h40": 40,
    "y_cbot_up_h30": 30,
    "y_cbot_extreme_move_h60": 60,
}


def build_cbot_targets_v7(df: pd.DataFrame) -> pd.DataFrame:
    """Construit 8 cibles CBOT V7.

    Requiert colonnes : cbot_close, basis_eur_t (optionnel).
    Anti-leakage : shift(-H) appliqué, pas de données futures directes en feature.
    """
    if "cbot_close" not in df.columns:
        raise ValueError("Colonne 'cbot_close' manquante dans df")

    targets: dict[str, pd.Series] = {}
    c = df["cbot_close"]
    pct_60 = c.pct_change(60).shift(-60)
    pct_30 = c.pct_change(30).shift(-30)
    pct_120 = c.pct_change(120).shift(-120)

    # T1 : CBOT up conditionnel (quand basis EMA/CBOT élevé)
    if "basis_eur_t" in df.columns:
        basis_high = df["basis_eur_t"] > df["basis_eur_t"].rolling(252, min_periods=60).quantile(0.7)
    else:
        basis_high = pd.Series(True, index=df.index)
    targets["y_cbot_up_h60_when_basis_high"] = ((pct_60 > 0) & basis_high).astype(int)

    # T2 : CBOT forte hausse > +3%
    targets["y_cbot_strong_up_h60"] = (pct_60 > 0.03).astype(int)

    # T3 : CBOT risk-adjusted (return / vol > 0.5 annualisé)
    daily_ret = c.pct_change()
    rolling_vol = daily_ret.rolling(60, min_periods=20).std() * np.sqrt(252)
    sharpe_fwd = pct_60 / rolling_vol.shift(-60).replace(0, np.nan)
    targets["y_cbot_risk_adj_h60"] = (sharpe_fwd > 0.5).astype(int)

    # T4 : CBOT forte baisse > -2% (signal short / couverture)
    targets["y_cbot_down_h60"] = (pct_60 < -0.02).astype(int)

    # T5 : CBOT up H120 (horizon long)
    targets["y_cbot_up_h120"] = (pct_120 > 0).astype(int)

    # T6 : Spike de volatilité H40 (signal risk-off)
    vol_fwd = daily_ret.rolling(40, min_periods=10).std().shift(-40)
    vol_hist = daily_ret.rolling(120, min_periods=30).std()
    targets["y_cbot_vol_spike_h40"] = (vol_fwd > vol_hist * 1.5).astype(int)

    # T7 : CBOT up H30 (horizon court)
    targets["y_cbot_up_h30"] = (pct_30 > 0).astype(int)

    # T8 : Mouvement extrême H60 (up > +5% OU down < -5%)
    targets["y_cbot_extreme_move_h60"] = (pct_60.abs() > 0.05).astype(int)

    return pd.DataFrame(targets, index=df.index)


def compute_target_prevalences(targets_df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Calcule prévalences et statistiques de chaque cible."""
    stats = {}
    for col in targets_df.columns:
        s = targets_df[col].dropna()
        n_pos = int(s.sum())
        n_total = len(s)
        prev = float(n_pos / n_total) if n_total > 0 else float("nan")
        stats[col] = {
            "n_total": n_total,
            "n_positive": n_pos,
            "prevalence": round(prev, 4),
            "balanced": 0.25 <= prev <= 0.75,
            "horizon_days": TARGET_HORIZONS.get(col),
        }
    return stats


def run_target_lab(df: pd.DataFrame) -> dict[str, Any]:
    """Construit les cibles et calcule les statistiques."""
    targets_df = build_cbot_targets_v7(df)
    prevalences = compute_target_prevalences(targets_df)
    n_balanced = sum(1 for s in prevalences.values() if s["balanced"])
    return {
        "n_targets": len(targets_df.columns),
        "target_names": list(targets_df.columns),
        "prevalences": prevalences,
        "n_balanced_targets": n_balanced,
        "version": "V7-04",
    }


def save_target_lab(df: pd.DataFrame) -> dict[str, Any]:
    import json
    result = run_target_lab(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    register_experiment(
        experiment_id="V7-04",
        target="cbot_target_lab_v7",
        horizon=0,
        model="target_engineering",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=[],
        metrics={
            "n_targets": result["n_targets"],
            "n_balanced": result["n_balanced_targets"],
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result

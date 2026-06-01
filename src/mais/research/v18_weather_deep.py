"""V18-WEATHER-DEEP — La météo comme warning « basis justifié par stress » (théorie du stockage).

Hypothèse (théorie du stockage) : un basis élevé SOUTENU par un vrai stress de rendement (chaleur,
déficit de pluie, sécheresse, mauvaise condition de culture) reflète une tension physique DURABLE, donc
se compresse MOINS. Shorter une telle prime serait plus risqué.

Test : parmi les trades short basis-haut (entrée basis_z>1), les entrées en stress météo élevé
gagnent-elles moins / sont-elles plus souvent censurées que les entrées sans stress ?

Verdict : WEATHER_WARNING_USEFUL (justifie un warning UNCERTAIN_WEATHER) ou WEATHER_NEUTRAL.
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v17_research_indicator import build_trades_detailed

V18_DIR = ARTEFACTS_DIR / "v18"
V18_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
STRESS_HI = 0.5  # seuil de stress météo élevé (z composite)


def _expanding_z(s: pd.Series, min_periods: int = 250) -> pd.Series:
    mean = s.expanding(min_periods=min_periods).mean()
    std = s.expanding(min_periods=min_periods).std().replace(0, np.nan)
    return (s - mean) / std


def weather_stress_index(df: pd.DataFrame) -> pd.Series:
    """Composite de stress de rendement (z expandant) : chaleur + déficit pluie + sécheresse − condition."""
    idx = df.index
    comps = []
    if "wx_belt_heat_days_38c_30" in df.columns:
        comps.append(_expanding_z(df["wx_belt_heat_days_38c_30"]))
    if "wx_belt_rain_deficit_14d" in df.columns:
        comps.append(_expanding_z(df["wx_belt_rain_deficit_14d"]))
    if "drought_composite" in df.columns:
        comps.append(_expanding_z(df["drought_composite"]))
    if "condition_gd_ex_pct" in df.columns:
        comps.append(-_expanding_z(df["condition_gd_ex_pct"]))  # bonne condition = moins de stress
    if not comps:
        return pd.Series(np.nan, index=idx)
    mat = pd.concat(comps, axis=1)
    return mat.mean(axis=1, skipna=True)


def run_weather_on_trades(df: pd.DataFrame) -> dict[str, Any]:
    """Compare les trades short basis-haut selon le stress météo à l'entrée."""
    assert_no_holdout(df)
    tdf = build_trades_detailed(df)
    if len(tdf) < 12:
        return {"version": "V18-WEATHER-DEEP", "verdict": "TOO_FEW", "n": int(len(tdf))}
    stress = weather_stress_index(df)
    stress_by_date = {str(d.date()): float(v) for d, v in stress.items() if not pd.isna(v)}
    tdf = tdf.copy()
    tdf["weather_stress"] = tdf["entry_date"].map(stress_by_date)
    tdf = tdf.dropna(subset=["weather_stress"])
    if len(tdf) < 12:
        return {"version": "V18-WEATHER-DEEP", "verdict": "TOO_FEW_WITH_WX", "n": int(len(tdf))}

    hi = tdf[tdf["weather_stress"] > STRESS_HI]
    lo = tdf[tdf["weather_stress"] <= STRESS_HI]

    def _prof(sub):
        if len(sub) < 4:
            return {"n": int(len(sub))}
        return {"n": int(len(sub)),
                "win_rate": round(float(sub["win"].mean()), 4),
                "mean_pnl_z0": round(float(sub["pnl_z0_max90_sl20"].mean()), 2),
                "mean_pnl_z05": round(float(sub["pnl_z0.5"].dropna().mean()), 2) if sub["pnl_z0.5"].notna().any() else None,
                "share_censored_or_stopped": round(float(((sub["reverted"] == 0) | (sub["stopped"] == 1)).mean()), 4),
                "mean_mae": round(float(sub["mae"].mean()), 2)}

    p_hi, p_lo = _prof(hi), _prof(lo)
    useful = (
        p_hi.get("n", 0) >= 4 and p_lo.get("n", 0) >= 4
        and (p_hi.get("win_rate", 1) < p_lo.get("win_rate", 0) - 0.08
             or p_hi.get("mean_pnl_z0", 1) < p_lo.get("mean_pnl_z0", 0) - 3.0)
    )
    out = {
        "version": "V18-WEATHER-DEEP",
        "n_trades_with_weather": int(len(tdf)),
        "stress_threshold_z": STRESS_HI,
        "high_stress_entries": p_hi,
        "low_stress_entries": p_lo,
        "weather_warning_useful": bool(useful),
        "interpretation": (
            "Si les entrées en stress météo élevé gagnent moins / sont plus censurées, le basis y est "
            "'justifié' par une tension physique durable -> warning UNCERTAIN_WEATHER (préférer z->0.5, "
            "réduire la taille, ou s'abstenir). Sinon la météo reste explicative."
        ),
        "verdict": "WEATHER_WARNING_USEFUL" if useful else "WEATHER_NEUTRAL",
    }
    (V18_DIR / "weather_deep_trades.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_weather_basis_justification(df: pd.DataFrame) -> dict[str, Any]:
    """Le stress météo prédit-il qu'un basis haut NE se compresse PAS (corr stress vs basis_change) ?"""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V18-WEATHER-JUSTIFICATION", "verdict": "MISSING_BASIS"}
    stress = weather_stress_index(df)
    basis = df["ema_cbot_basis"]
    bz = df.get("ema_cbot_basis_zscore_52w")
    basis_change = basis.shift(-HORIZON) - basis
    hi = (bz > 1.0) & stress.notna() & basis_change.notna()
    n = int(hi.sum())
    if n < 30:
        return {"version": "V18-WEATHER-JUSTIFICATION", "verdict": "TOO_FEW", "n": n}
    s = stress[hi].values
    chg = basis_change[hi].values
    # corr positive = plus de stress -> basis monte/reste (moins de compression = justifié)
    corr = float(np.corrcoef(s, chg)[0, 1])
    # compression = chg<0 ; stress élevé devrait diminuer P(compression)
    comp_hi_stress = float((chg[s > STRESS_HI] < 0).mean()) if (s > STRESS_HI).sum() >= 5 else None
    comp_lo_stress = float((chg[s <= STRESS_HI] < 0).mean()) if (s <= STRESS_HI).sum() >= 5 else None
    out = {
        "version": "V18-WEATHER-JUSTIFICATION",
        "n_high_basis": n,
        "corr_stress_vs_basis_change": round(corr, 4),
        "compression_rate_high_stress": round(comp_hi_stress, 4) if comp_hi_stress is not None else None,
        "compression_rate_low_stress": round(comp_lo_stress, 4) if comp_lo_stress is not None else None,
        "interpretation": (
            "corr > 0 ou compression_rate plus faible en stress élevé => le stress 'justifie' le basis haut "
            "(tension durable, moins de compression). Confirme la théorie du stockage appliquée à la prime."
        ),
        "verdict": "WEATHER_JUSTIFICATION_DONE",
    }
    (V18_DIR / "weather_justification.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

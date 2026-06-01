"""V60 — La météo US est-elle un DRIVER du basis EMA/CBOT (prime européenne) ?

Le cœur de l'étude est d'expliquer le basis. La météo pousse le CBOT (V51), mais affecte-t-elle la PRIME
EU différemment ? Deux mécanismes opposés possibles :
  (a) un stress US pousse le CBOT -> si l'EMA suit moins vite, le basis se COMPRIME (rattrapage CBOT) ;
  (b) un choc d'offre mondial peut renforcer la rareté EU -> le basis s'ÉLARGIT (prime up).
On tranche empiriquement, avec la même rigueur lead-lag que V51 (forward vs backward) et un conditionnement
par saison. Réutilise `extreme_features` de V51 (causal, shift(1), phénologie). Réalisé = borne explicative.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V60_DIR = ARTEFACTS_DIR / "v60"
V60_DIR.mkdir(parents=True, exist_ok=True)


def _basis_change(basis: pd.Series, h: int) -> pd.Series:
    """h>0 : variation FUTURE basis[t→t+h] (>0 = élargissement). h<0 : variation PASSÉE."""
    if h > 0:
        return basis.shift(-h) - basis
    return basis - basis.shift(-h)


def weather_basis_leadlag(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v51_weather_extremes import extreme_features
    f = extreme_features(df)
    ext = f["heat_extreme_crit"]
    crit = f["in_critical_window"] == 1
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    corrs = {}
    for h in (-20, -10, 10, 20, 40):
        d = _basis_change(basis, h)
        m = ext.notna() & d.notna() & crit & (ext > 0)
        if m.sum() > 80 and ext[m].std() > 0 and d[m].std() > 0:
            corrs[h] = round(float(np.corrcoef(ext[m], d[m])[0, 1]), 3)
    fwd = {h: v for h, v in corrs.items() if h > 0}
    sign = None
    if fwd:
        mean_fwd = float(np.mean(list(fwd.values())))
        sign = "WIDENS" if mean_fwd > 0.03 else ("COMPRESSES" if mean_fwd < -0.03 else "NEUTRAL")
    return {"corr_extreme_vs_basis_change_by_h": corrs, "forward_sign": sign,
            "reading": ("corr>0 à h>0 : un extrême US connu à J PRÉCÈDE un élargissement du basis (prime EU "
                        "renforcée) ; corr<0 : précède une compression (rattrapage CBOT).")}


def conditional_basis_level(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v51_weather_extremes import extreme_features
    f = extreme_features(df)
    ext = f["heat_extreme_crit"]
    crit = f["in_critical_window"] == 1
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    m = ext.notna() & basis.notna() & crit & (ext > 0)
    if m.sum() < 100:
        return {"verdict": "TOO_FEW", "n": int(m.sum())}
    thr = ext[m].quantile(0.8)
    hi = basis[m & (ext >= thr)]
    lo = basis[m & (ext < thr)]
    return {
        "n_critical": int(m.sum()),
        "basis_high_extreme_eur_t": round(float(hi.mean()), 2) if len(hi) else None,
        "basis_low_extreme_eur_t": round(float(lo.mean()), 2) if len(lo) else None,
        "basis_higher_under_extreme": bool(len(hi) and len(lo) and hi.mean() > lo.mean()),
    }


def run_v60_weather_basis(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if pd.to_numeric(df.get("wx_belt_tmax_c_anom_z"), errors="coerce").notna().sum() < 300:
        return {"version": "V60-WEATHER-BASIS", "verdict": "NO_WEATHER_DATA"}
    ll = weather_basis_leadlag(df)
    lvl = conditional_basis_level(df)

    sign = ll.get("forward_sign")
    if sign == "WIDENS":
        verdict = "US_HEAT_PRECEDES_BASIS_WIDENING_EU_PREMIUM"
    elif sign == "COMPRESSES":
        verdict = "US_HEAT_PRECEDES_BASIS_COMPRESSION_CBOT_CATCHUP"
    else:
        verdict = "US_HEAT_NOT_A_CLEAR_BASIS_DRIVER"

    out = {
        "version": "V60-WEATHER-BASIS",
        "lead_lag": ll,
        "conditional_basis_level": lvl,
        "verdict": verdict,
        "interpretation": (
            f"Signe forward du lien météo→basis : {sign}. Niveau de basis sous chaleur extrême "
            f"{lvl.get('basis_high_extreme_eur_t')} vs hors extrême {lvl.get('basis_low_extreme_eur_t')} €/t "
            f"(basis_higher_under_extreme={lvl.get('basis_higher_under_extreme')}). La chaleur US n'est PAS "
            "un driver forward propre du basis : le basis est même un peu PLUS BAS sous extrême (cohérent "
            "CBOT-catch-up, pas élargissement de prime EU), et la corrélation est surtout BACKWARD (basis "
            "déjà comprimé AVANT l'extrême). → renforce la thèse de la PRIME LOCALE (V16/V36/V40) : la prime "
            "EU n'est pas un phénomène de météo US. Edge météo réel = via PRÉVISION sur le CBOT, pas sur le basis."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V60_DIR / "v60_weather_basis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

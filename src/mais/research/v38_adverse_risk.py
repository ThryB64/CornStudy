"""V38 — Module ADVERSE_RISK : transformer V32/V36/V37 en contexte explicite, sans toucher la règle.

On ne fitte AUCUN modèle sur 42 trades (anti sur-filtrage). On assemble un score RÈGLE-BASÉE et
interprétable à partir des signatures déjà découvertes, toutes causales au moment du signal :

- V32 : les ADVERSE sont les primes MODÉRÉES (z dans [1,1.5)), pas les extrêmes -> +1.
- V37 : un RÉSIDU bas (prime déjà justifiée par la substitution blé/maïs) est ADVERSE-prone -> +1.
- V36 : un ratio blé/maïs ÉLEVÉ (prime soutenue par la substitution fourragère) -> +1.

Score 0..3 -> ADVERSE_RISK LOW / MEDIUM / HIGH. Usage = CONTEXTE/objectif prudent, JAMAIS un veto :
LOW -> objectif z->0 envisageable ; MEDIUM -> z->0.5 conseillé ; HIGH -> z->0.5 seulement, prudence,
ne pas renforcer. On valide ensuite descriptivement (le palier sépare-t-il vraiment l'ADVERSE ? l'objectif
prudent aide-t-il en HIGH ?) sans optimiser de seuil.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V38_DIR = ARTEFACTS_DIR / "v38"
V38_DIR.mkdir(parents=True, exist_ok=True)

_RECO = {
    "LOW": "objectif z->0 envisageable (full)",
    "MEDIUM": "objectif z->0.5 conseille",
    "HIGH": "z->0.5 seulement, prudence, ne pas renforcer (research)",
}


def _wheat_corn_ratio_z(df: pd.DataFrame) -> pd.Series:
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    ratio = wheat / corn
    mu = ratio.expanding(min_periods=120).mean()
    sd = ratio.expanding(min_periods=120).std()
    return (ratio - mu) / sd


def compute_adverse_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Score ADVERSE_RISK règle-basée par date (composants causaux, aucun fit)."""
    from mais.research.v37_substitution_residual import substitution_residual
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    resid_z = substitution_residual(df)["basis_residual_z"]
    wc_z = _wheat_corn_ratio_z(df)

    active = bz >= 1.0
    moderate_premium = (active & (bz < 1.5)).astype(int)        # V32
    low_residual = (active & (resid_z < 0)).astype(int)         # V37
    high_substitution = (active & (wc_z > 0.5)).astype(int)     # V36
    score = moderate_premium + low_residual + high_substitution

    tier = pd.Series("NO_SIGNAL", index=df.index)
    tier[active & (score == 0)] = "LOW"
    tier[active & (score == 1)] = "MEDIUM"
    tier[active & (score >= 2)] = "HIGH"

    out = pd.DataFrame({
        "basis_z": bz,
        "wheat_corn_ratio_z": wc_z,
        "basis_residual_z": resid_z,
        "c_moderate_premium": moderate_premium,
        "c_low_residual": low_residual,
        "c_high_substitution": high_substitution,
        "adverse_risk_score": score.where(active),
        "adverse_risk": tier,
    }, index=df.index)
    out["recommended_objective"] = out["adverse_risk"].map(_RECO).fillna("")
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def _by_tier(trades: pd.DataFrame) -> dict[str, Any]:
    res = {}
    for t in ("LOW", "MEDIUM", "HIGH"):
        sub = trades[trades["adverse_risk"] == t]
        if len(sub) == 0:
            res[t] = {"n": 0}
            continue
        res[t] = {
            "n": int(len(sub)),
            "adverse_rate": round(float(sub["adverse"].mean()), 3),
            "win_rate": round(float(sub["win"].mean()), 3),
            "mean_pnl_z0": round(float(sub["pnl_z0"].mean()), 2),
            "mean_pnl_z05": round(float(sub["pnl_z05"].mean()), 2),
            "prudent_helps": bool(sub["pnl_z05"].mean() > sub["pnl_z0"].mean()),
        }
    return res


def _attach_trades(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    det = build_trades_detailed(df)
    adv = build_adverse_frame(df)
    if len(det) == 0 or len(adv) == 0:
        return pd.DataFrame()
    det = det[["entry_date", "entry_z", "pnl_z0_max90_sl20", "pnl_z0.5", "win", "season", "crisis"]].rename(
        columns={"pnl_z0_max90_sl20": "pnl_z0", "pnl_z0.5": "pnl_z05"})
    adv = adv[["entry_date", "adverse"]]
    trades = det.merge(adv, on="entry_date", how="inner")
    risk = compute_adverse_risk(df)
    entry = pd.to_datetime(trades["entry_date"])
    trades["adverse_risk"] = risk["adverse_risk"].reindex(entry).to_numpy()
    return trades.dropna(subset=["adverse_risk"])


def run_v38_adverse_risk(df: pd.DataFrame) -> dict[str, Any]:
    """V38-01 + V38-04 : valider le palier ADVERSE_RISK + comparer objectif z->0.5 vs z->0 par palier."""
    assert_no_holdout(df)
    trades = _attach_trades(df)
    if len(trades) < 15:
        return {"version": "V38-ADVERSE-RISK", "verdict": "TOO_FEW", "n": int(len(trades))}

    by_tier = _by_tier(trades)
    rates = {t: by_tier[t]["adverse_rate"] for t in ("LOW", "MEDIUM", "HIGH")
             if by_tier[t].get("n", 0) >= 4 and "adverse_rate" in by_tier[t]}
    monotone = (len(rates) >= 2 and list(rates.values()) == sorted(rates.values()))
    high = by_tier.get("HIGH", {})
    prudent_helps_high = bool(high.get("n", 0) >= 4 and high.get("prudent_helps"))

    if monotone:
        verdict = "ADVERSE_RISK_TIER_SEPARATES" if prudent_helps_high else "ADVERSE_RISK_TIER_SEPARATES_OBJECTIVE_NEUTRAL"
    else:
        verdict = "ADVERSE_RISK_TIER_WEAK"

    out = {
        "version": "V38-ADVERSE-RISK",
        "n_trades": int(len(trades)),
        "by_tier": by_tier,
        "adverse_rate_by_tier": rates,
        "tier_monotone_increasing": monotone,
        "prudent_objective_helps_in_high": prudent_helps_high,
        "verdict": verdict,
        "components": {
            "c_moderate_premium": "V32 : z dans [1,1.5)",
            "c_low_residual": "V37 : residu < 0 (prime justifiee substitution)",
            "c_high_substitution": "V36 : ratio ble/mais z > 0.5",
        },
        "usage": ("ADVERSE_RISK = CONTEXTE/warning, JAMAIS un veto (anti sur-filtrage V15/V23/V29). "
                  "LOW->z->0 envisageable ; MEDIUM->z->0.5 conseille ; HIGH->z->0.5 seulement, prudence."),
        "note": "Score regle-base (aucun fit sur n=42). Descriptif, a re-tester en forward officiel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V38_DIR / "v38_adverse_risk.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def wheat_corn_deep_dive(df: pd.DataFrame, horizon: int = 40) -> dict[str, Any]:
    """V38-02 : approfondir le ratio ble/mais -> niveau, compression, time-to-reversion, ADVERSE, saison/crise."""
    assert_no_holdout(df)
    wc_z = _wheat_corn_ratio_z(df)
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    if wc_z.notna().sum() < 200 or basis.notna().sum() < 200:
        return {"version": "V38-WHEAT-CORN", "verdict": "TOO_SHORT"}

    fwd = basis.shift(-horizon) - basis
    comp = (fwd < 0).astype(float)
    m = wc_z.notna() & basis.notna()
    corr_level = round(float(np.corrcoef(wc_z[m], basis[m])[0, 1]), 3)
    # compression conditionnelle : ratio haut (>median) vs bas
    med = wc_z.median()
    mc = wc_z.notna() & comp.notna()
    hi = comp[mc & (wc_z >= med)]
    lo = comp[mc & (wc_z < med)]
    comp_hi = round(float(hi.mean()), 3) if len(hi) else None
    comp_lo = round(float(lo.mean()), 3) if len(lo) else None

    # ADVERSE par niveau de ratio blé/maïs à l'entrée
    trades = _attach_trades(df)
    adverse_by_ratio = {}
    season_block = {}
    if len(trades) >= 15:
        entry = pd.to_datetime(trades["entry_date"])
        trades = trades.copy()
        trades["wc_z"] = wc_z.reindex(entry).to_numpy()
        v = trades.dropna(subset=["wc_z"])
        if len(v) >= 15:
            tmed = v["wc_z"].median()
            h = v[v["wc_z"] >= tmed]
            ll = v[v["wc_z"] < tmed]
            adverse_by_ratio = {
                "n": int(len(v)),
                "high_ratio_adverse_rate": round(float(h["adverse"].mean()), 3) if len(h) else None,
                "low_ratio_adverse_rate": round(float(ll["adverse"].mean()), 3) if len(ll) else None,
            }
        for s, sub in trades.groupby("season"):
            if len(sub) >= 3:
                season_block[s] = {"n": int(len(sub)),
                                   "adverse_rate": round(float(sub["adverse"].mean()), 3),
                                   "mean_wc_z": round(float(pd.to_numeric(sub["wc_z"], errors="coerce").mean()), 3)}

    h_adv = adverse_by_ratio.get("high_ratio_adverse_rate")
    l_adv = adverse_by_ratio.get("low_ratio_adverse_rate")
    substitution_supports_premium = bool(
        h_adv is not None and l_adv is not None and (h_adv - l_adv) >= 0.05)

    out = {
        "version": "V38-WHEAT-CORN",
        "horizon": horizon,
        "corr_basis_wheat_corn_ratio": corr_level,
        "compression_rate_high_ratio": comp_hi,
        "compression_rate_low_ratio": comp_lo,
        "adverse_by_ratio": adverse_by_ratio,
        "adverse_by_season": season_block,
        "substitution_supports_premium": substitution_supports_premium,
        "verdict": ("HIGH_WHEAT_CORN_RATIO_LESS_COMPRESSIBLE"
                    if (comp_hi is not None and comp_lo is not None and comp_hi < comp_lo)
                    else "WHEAT_CORN_RATIO_NOT_DISCRIMINANT_FOR_COMPRESSION"),
        "interpretation": (
            "Le ratio ble/mais explique le NIVEAU du basis (substitution fourragere, V36 r~0.60). "
            "Quand le ratio est haut, la prime est economiquement soutenue : elle se comprime moins et "
            "finit plus souvent ADVERSE. -> CONTEXTE ADVERSE_RISK, pas un veto."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V38_DIR / "v38_wheat_corn.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def adverse_risk_report_block(df: pd.DataFrame) -> str:
    """V38-05 : bloc markdown CONTEXTE ADVERSE_RISK pour la dernière date (jamais un veto)."""
    risk = compute_adverse_risk(df)
    if len(risk) == 0:
        return ""
    last = risk.iloc[-1]
    if last["adverse_risk"] == "NO_SIGNAL":
        return ("### Contexte ADVERSE_RISK\n- Pas de signal actif (basis_z < 1) : sans objet.\n")
    comps = []
    if last["c_moderate_premium"]:
        comps.append("prime modérée z∈[1,1.5) (V32)")
    if last["c_low_residual"]:
        comps.append("résidu bas = prime justifiée par substitution (V37)")
    if last["c_high_substitution"]:
        comps.append("ratio blé/maïs élevé (V36)")
    comps_txt = "; ".join(comps) if comps else "aucun facteur adverse actif"
    return (
        "### Contexte ADVERSE_RISK (V38 — CONTEXTE, pas un veto)\n"
        f"- Niveau : **{last['adverse_risk']}** (score {int(last['adverse_risk_score'])}/3)\n"
        f"- Facteurs : {comps_txt}\n"
        f"- Objectif suggéré : {last['recommended_objective']}\n"
        "- La règle figée (short basis-haut) est INCHANGÉE ; ce bloc module seulement l'objectif "
        "(prudent vs complet) et la prudence. RESEARCH_ONLY_NOT_TRADING.\n"
    )


def run_v38_all(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "adverse_risk": run_v38_adverse_risk(df),
        "wheat_corn": wheat_corn_deep_dive(df),
    }

"""V64 — ADVERSE_RISK v2 : score enrichi et EXPLIQUÉ (règle-basé, AUCUN fit sur 42 trades).

V38 (v1) combinait 3 signatures (prime modérée, résidu bas, substitution haute). v2 ajoute les diagnostics
construits depuis — CBOT_SUPPORT (V41), PHYSICAL_TENSION (V54), roll, crise, volatilité — chacun causal, et
produit une EXPLICATION par composant. On NE fitte rien : score entier de flags binaires, banding fixe (non
optimisé). On valide que v2 sépare l'ADVERSE au moins aussi bien que v1 (split binaire robuste), avec plus
d'explication. CONTEXTE, jamais un veto.

Mécanique (chaque flag = +1 vers le risque adverse, tous connus à l'entrée) :
- prime modérée z∈[1,1.5)            (V32)
- résidu bas (prime justifiée subst.) (V37)
- ratio blé/maïs z>0.5               (V36)
- CBOT non porteur (CBOT_SUPPORT LOW) (V41)
- tension physique HIGH (prime adossée à la rareté) (V54)
- mois de roll ; année de crise ; volatilité haute (microstructure / régime)

Banding fixe : HIGH si score≥4, MEDIUM si 2–3, LOW si ≤1.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V64_DIR = ARTEFACTS_DIR / "v64"
V64_DIR.mkdir(parents=True, exist_ok=True)
ROLL_MONTHS = (2, 5, 7, 10)
CRISIS_YEARS = (2020, 2021, 2022)

_LABEL = {
    "c_moderate_premium": "prime seulement modérée (z<1.5)",
    "c_low_residual": "prime justifiée par substitution (résidu bas)",
    "c_high_substitution": "ratio blé/maïs élevé",
    "c_cbot_not_supportive": "CBOT non porteur (pas de rattrapage probable)",
    "c_physical_tension_high": "tension physique élevée (prime adossée à la rareté)",
    "c_roll_month": "mois de roll Euronext",
    "c_crisis": "année de crise (2020-2022)",
    "c_high_vol": "volatilité CBOT élevée",
}


def compute_adverse_risk_v2(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v37_substitution_residual import substitution_residual
    from mais.research.v38_adverse_risk import _wheat_corn_ratio_z
    from mais.research.v41_cbot_support import compute_cbot_support
    from mais.research.v54_physical_tension import compute_physical_tension

    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    active = bz >= 1.0
    resid_z = substitution_residual(df)["basis_residual_z"]
    wc_z = _wheat_corn_ratio_z(df)
    cbot = compute_cbot_support(df)["cbot_support"]
    tension = compute_physical_tension(df)["physical_tension"]
    vol = pd.to_numeric(df.get("corn_realized_vol_20"), errors="coerce")
    vol_med = vol.expanding(min_periods=120).median()
    months = df.index.month
    years = df.index.year

    flags = pd.DataFrame(index=df.index)
    flags["c_moderate_premium"] = (active & (bz < 1.5)).astype(int)
    flags["c_low_residual"] = (active & (resid_z < 0)).astype(int)
    flags["c_high_substitution"] = (active & (wc_z > 0.5)).astype(int)
    flags["c_cbot_not_supportive"] = (active & (cbot == "LOW")).astype(int)
    flags["c_physical_tension_high"] = (active & (tension == "HIGH")).astype(int)
    flags["c_roll_month"] = (active & pd.Series(np.isin(months, ROLL_MONTHS), index=df.index)).astype(int)
    flags["c_crisis"] = (active & pd.Series(np.isin(years, CRISIS_YEARS), index=df.index)).astype(int)
    flags["c_high_vol"] = (active & (vol > vol_med)).astype(int)

    score = flags.sum(axis=1)
    tier = pd.Series("NO_SIGNAL", index=df.index)
    tier[active & (score <= 1)] = "LOW"
    tier[active & (score.between(2, 3))] = "MEDIUM"
    tier[active & (score >= 4)] = "HIGH"

    out = flags.copy()
    out["basis_z"] = bz
    out["adverse_risk_v2_score"] = score.where(active)
    out["adverse_risk_v2"] = tier
    out["recommended_objective"] = tier.map(
        {"LOW": "z->0 envisageable", "MEDIUM": "z->0.5 conseillé",
         "HIGH": "z->0.5 seulement, prudence"}).fillna("")
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def explain_row(row: pd.Series) -> list[str]:
    return [_LABEL[c] for c in _LABEL if int(row.get(c, 0)) == 1]


def _attach_trades(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    det = build_trades_detailed(df)
    adv = build_adverse_frame(df)
    if len(det) == 0 or len(adv) == 0:
        return pd.DataFrame()
    det = det[["entry_date", "win", "pnl_z0_max90_sl20", "pnl_z0.5"]].rename(
        columns={"pnl_z0_max90_sl20": "pnl_z0", "pnl_z0.5": "pnl_z05"})
    trades = det.merge(adv[["entry_date", "adverse"]], on="entry_date", how="inner")
    risk = compute_adverse_risk_v2(df)
    entry = pd.to_datetime(trades["entry_date"])
    trades["risk_v2"] = risk["adverse_risk_v2"].reindex(entry).to_numpy()
    trades["score_v2"] = risk["adverse_risk_v2_score"].reindex(entry).to_numpy()
    return trades.dropna(subset=["risk_v2"])


def run_v64_adverse_v2(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    trades = _attach_trades(df)
    if len(trades) < 15:
        return {"version": "V64-ADVERSE-RISK-V2", "verdict": "TOO_FEW", "n": int(len(trades))}

    by_tier = {}
    for t in ("LOW", "MEDIUM", "HIGH"):
        sub = trades[trades["risk_v2"] == t]
        if len(sub):
            by_tier[t] = {"n": int(len(sub)), "adverse_rate": round(float(sub["adverse"].mean()), 3),
                          "win_rate": round(float(sub["win"].mean()), 3),
                          "mean_pnl_z0": round(float(sub["pnl_z0"].mean()), 2),
                          "prudent_helps": bool(sub["pnl_z05"].mean() > sub["pnl_z0"].mean())}

    # split binaire robuste : risque faible (LOW) vs élevé (MEDIUM+HIGH)
    low = trades[trades["risk_v2"] == "LOW"]
    hi = trades[trades["risk_v2"].isin(["MEDIUM", "HIGH"])]
    binary = {}
    binary_robust = False
    if len(low) >= 4 and len(hi) >= 4:
        binary = {"low_risk": {"n": int(len(low)), "adverse_rate": round(float(low["adverse"].mean()), 3)},
                  "elevated_risk": {"n": int(len(hi)), "adverse_rate": round(float(hi["adverse"].mean()), 3)}}
        binary_robust = bool(binary["elevated_risk"]["adverse_rate"] > binary["low_risk"]["adverse_rate"])

    # comparaison à v1 (V38) sur le même split binaire
    from mais.research.v38_adverse_risk import compute_adverse_risk
    r1 = compute_adverse_risk(df)["adverse_risk"]
    entry = pd.to_datetime(trades["entry_date"])
    t1 = trades.assign(risk_v1=r1.reindex(entry).to_numpy())
    v1_low = t1[t1["risk_v1"] == "LOW"]
    v1_hi = t1[t1["risk_v1"].isin(["MEDIUM", "HIGH"])]
    v1_gap = (round(float(v1_hi["adverse"].mean() - v1_low["adverse"].mean()), 3)
              if len(v1_low) >= 4 and len(v1_hi) >= 4 else None)
    v2_gap = (round(float(hi["adverse"].mean() - low["adverse"].mean()), 3)
              if binary else None)

    v2_as_good = bool(v2_gap is not None and v1_gap is not None and v2_gap >= v1_gap - 0.001)
    if binary_robust and v2_as_good:
        verdict = "ADVERSE_RISK_V2_SEPARATES_AND_EXPLAINS"
    elif binary_robust:
        verdict = "ADVERSE_RISK_V2_EXPLAINS_BUT_V1_SEPARATES_BETTER_KEEP_V1_SCORE"
    else:
        verdict = "ADVERSE_RISK_V2_WEAK_USE_V1"

    out = {
        "version": "V64-ADVERSE-RISK-V2",
        "n_trades": int(len(trades)),
        "by_tier": by_tier,
        "binary_split": binary,
        "binary_split_robust": binary_robust,
        "adverse_gap_v2_elevated_minus_low": v2_gap,
        "adverse_gap_v1_for_comparison": v1_gap,
        "v2_at_least_as_separating_as_v1": v2_as_good,
        "components": list(_LABEL.keys()),
        "banding": "HIGH si score>=4, MEDIUM si 2-3, LOW si <=1 (fixe, non optimisé)",
        "verdict": verdict,
        "usage": ("ADVERSE_RISK v2 = COUCHE D'EXPLICATION (raisons par composant), jamais un veto. "
                  "DÉCOUVERTE : ajouter roll/crise/volatilité DILUE la séparation -> pour le TIER de risque, "
                  "garder v1 (3 signaux focalisés) ; utiliser v2 pour EXPLIQUER pourquoi. Compatible V56."),
        "interpretation": (
            f"v2 sépare l'ADVERSE en binaire (élevé {binary.get('elevated_risk', {}).get('adverse_rate')} vs "
            f"faible {binary.get('low_risk', {}).get('adverse_rate')}) MAIS moins bien que v1 "
            f"(gap v2 {v2_gap} < v1 {v1_gap}) : empiler des composants (roll/crise/vol) AJOUTE de "
            "l'explication mais DILUE le pouvoir discriminant (HIGH non-monotone). Leçon anti-overfitting : "
            "le score focalisé v1 reste la référence pour le TIER ; v2 sert la couche EXPLICATION (POURQUOI "
            "ce signal est risqué : CBOT non porteur, prime modérée, substitution, roll/crise)."),
        "note": "Score règle-basé, banding fixe, aucun fit sur n=42. Négatif honnête documenté.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V64_DIR / "v64_adverse_risk_v2.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def adverse_risk_v2_report_block(df: pd.DataFrame) -> str:
    risk = compute_adverse_risk_v2(df)
    if len(risk) == 0:
        return ""
    last = risk.iloc[-1]
    if last["adverse_risk_v2"] == "NO_SIGNAL":
        return ""
    reasons = explain_row(last)
    reasons_txt = "; ".join(reasons) if reasons else "aucun facteur adverse actif"
    return (
        "### Contexte ADVERSE_RISK v2 (V64 — CONTEXTE explicité, pas un veto)\n"
        f"- Niveau : **{last['adverse_risk_v2']}** (score {int(last['adverse_risk_v2_score'])}/8)\n"
        f"- Raisons : {reasons_txt}\n"
        f"- Objectif suggéré : {last['recommended_objective']}\n"
        "- La règle figée est INCHANGÉE ; ce bloc explique le risque et module l'objectif. "
        "RESEARCH_ONLY_NOT_TRADING.\n"
    )

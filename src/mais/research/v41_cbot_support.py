"""V41 — CBOT_SUPPORT_SCORE : le CBOT est-il dans un état favorable au rattrapage (donc à la compression) ?

V39 a montré que la compression de la prime est plus fiable quand le CBOT est porteur : entrer en uptrend
CBOT divise l'ADVERSE par ~2 (E4) et un positionnement managed-money net long va dans le même sens (E6).
On assemble un score CBOT_SUPPORT règle-basé (aucun fit), miroir de V38 ADVERSE_RISK :

- E4 : CBOT > SMA50 (uptrend) -> +1
- E4 : momentum CBOT 20j > 0 -> +1
- E6 : managed money net (causal) au-dessus de sa médiane expandante -> +1

Score 0..3 -> CBOT_SUPPORT LOW / MEDIUM / HIGH. Un support HAUT = compression plus fiable (ADVERSE rare).
C'est le pendant POSITIF d'ADVERSE_RISK : « short premium ≈ long CBOT relatif ». CONTEXTE, jamais un veto.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V41_DIR = ARTEFACTS_DIR / "v41"
V41_DIR.mkdir(parents=True, exist_ok=True)

_NOTE = {
    "HIGH": "CBOT porteur -> compression historiquement plus fiable (ADVERSE rare)",
    "MEDIUM": "CBOT moyennement porteur",
    "LOW": "CBOT peu porteur -> attention ADVERSE (rattrapage moins probable)",
}


def compute_cbot_support(df: pd.DataFrame) -> pd.DataFrame:
    """Score CBOT_SUPPORT règle-basé par date (composants causaux, aucun fit)."""
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    sma = pd.to_numeric(df.get("corn_sma_50"), errors="coerce")
    mom = pd.to_numeric(df.get("corn_logret_20d"), errors="coerce")
    mm = df.get("cot_mm_net_pct_oi_x")
    if mm is None:
        mm = df.get("cot_mm_net_pct_oi")
    mm = pd.to_numeric(mm, errors="coerce").shift(1) if mm is not None else pd.Series(np.nan, index=df.index)
    mm_med = mm.expanding(min_periods=120).median()

    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    active = bz >= 1.0

    c_uptrend = (corn > sma).astype("Int64")
    c_momentum = (mom > 0).astype("Int64")
    c_mm = (mm > mm_med).astype("Int64")
    score = c_uptrend.fillna(0) + c_momentum.fillna(0) + c_mm.fillna(0)

    tier = pd.Series("NO_SIGNAL", index=df.index)
    tier[active & (score <= 1)] = "LOW"
    tier[active & (score == 2)] = "MEDIUM"
    tier[active & (score >= 3)] = "HIGH"

    out = pd.DataFrame({
        "cbot_above_sma50": c_uptrend,
        "cbot_mom20_positive": c_momentum,
        "mm_net_favorable": c_mm,
        "cbot_support_score": pd.Series(score, index=df.index).where(active),
        "cbot_support": tier,
    }, index=df.index)
    out["note"] = out["cbot_support"].map(_NOTE).fillna("")
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def _trades_with_support(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    det = build_trades_detailed(df)
    adv = build_adverse_frame(df)
    if len(det) == 0 or len(adv) == 0:
        return pd.DataFrame()
    det = det.merge(adv[["entry_date", "adverse"]], on="entry_date", how="inner")
    sup = compute_cbot_support(df)
    entry = pd.to_datetime(det["entry_date"])
    det["cbot_support"] = sup["cbot_support"].reindex(entry).to_numpy()
    return det.dropna(subset=["cbot_support"])


def run_v41_cbot_support(df: pd.DataFrame) -> dict[str, Any]:
    """Valider le palier CBOT_SUPPORT : l'ADVERSE doit DÉCROÎTRE et le PnL CROÎTRE avec le support."""
    assert_no_holdout(df)
    t = _trades_with_support(df)
    if len(t) < 15:
        return {"version": "V41-CBOT-SUPPORT", "verdict": "TOO_FEW", "n": int(len(t))}

    by_tier = {}
    for tier in ("LOW", "MEDIUM", "HIGH"):
        sub = t[t["cbot_support"] == tier]
        if len(sub):
            by_tier[tier] = {
                "n": int(len(sub)),
                "adverse_rate": round(float(sub["adverse"].mean()), 3),
                "win_rate": round(float(sub["win"].mean()), 3),
                "mean_pnl_z0": round(float(sub["pnl_z0_max90_sl20"].mean()), 2),
            }
    rates = {k: by_tier[k]["adverse_rate"] for k in ("LOW", "MEDIUM", "HIGH")
             if by_tier.get(k, {}).get("n", 0) >= 4}
    # ADVERSE doit DÉCROÎTRE quand le support augmente (LOW>=MEDIUM>=HIGH)
    monotone_dec = (len(rates) >= 2 and list(rates.values()) == sorted(rates.values(), reverse=True))
    pnls = {k: by_tier[k]["mean_pnl_z0"] for k in ("LOW", "MEDIUM", "HIGH")
            if by_tier.get(k, {}).get("n", 0) >= 4}
    pnl_inc = (len(pnls) >= 2 and list(pnls.values()) == sorted(pnls.values()))

    # Split binaire robuste (le gradué 3-paliers est bruité en petit n) : LOW (support faible) vs reste.
    weak = t[t["cbot_support"] == "LOW"]
    supported = t[t["cbot_support"].isin(["MEDIUM", "HIGH"])]
    binary = {}
    if len(weak) >= 4 and len(supported) >= 4:
        binary = {
            "weak_support": {"n": int(len(weak)), "adverse_rate": round(float(weak["adverse"].mean()), 3),
                             "mean_pnl_z0": round(float(weak["pnl_z0_max90_sl20"].mean()), 2)},
            "supported": {"n": int(len(supported)), "adverse_rate": round(float(supported["adverse"].mean()), 3),
                          "mean_pnl_z0": round(float(supported["pnl_z0_max90_sl20"].mean()), 2)},
        }
    binary_robust = bool(binary and binary["supported"]["adverse_rate"] < binary["weak_support"]["adverse_rate"])

    if monotone_dec:
        verdict = "CBOT_SUPPORT_SEPARATES_ADVERSE"
    elif binary_robust:
        verdict = "CBOT_SUPPORT_BINARY_ROBUST_GRADED_NOISY"
    else:
        verdict = "CBOT_SUPPORT_WEAK"
    out = {
        "version": "V41-CBOT-SUPPORT",
        "n_trades": int(len(t)),
        "by_tier": by_tier,
        "adverse_rate_by_tier": rates,
        "adverse_monotone_decreasing": monotone_dec,
        "pnl_monotone_increasing": pnl_inc,
        "binary_split_low_vs_supported": binary,
        "binary_split_robust": binary_robust,
        "verdict": verdict,
        "components": {
            "cbot_above_sma50": "E4 : CBOT > SMA50",
            "cbot_mom20_positive": "E4 : momentum 20j > 0",
            "mm_net_favorable": "E6 : managed money net > médiane expandante",
        },
        "usage": ("CBOT_SUPPORT = CONTEXTE positif (pendant d'ADVERSE_RISK), JAMAIS un veto. "
                  "HIGH -> compression historiquement plus fiable ; LOW -> attention ADVERSE."),
        "note": "Score règle-basé (aucun fit sur n=42). Descriptif, à confirmer en forward officiel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V41_DIR / "v41_cbot_support.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def cbot_support_report_block(df: pd.DataFrame) -> str:
    """Bloc markdown CONTEXTE CBOT_SUPPORT pour la dernière date (jamais un veto)."""
    sup = compute_cbot_support(df)
    if len(sup) == 0:
        return ""
    last = sup.iloc[-1]
    if last["cbot_support"] == "NO_SIGNAL":
        return ""
    facts = []
    facts.append("CBOT>SMA50" if last["cbot_above_sma50"] == 1 else "CBOT<SMA50")
    facts.append("momentum 20j>0" if last["cbot_mom20_positive"] == 1 else "momentum 20j<0")
    facts.append("fonds nets favorables" if last["mm_net_favorable"] == 1 else "fonds nets non favorables")
    return (
        "### Contexte CBOT_SUPPORT (V41 — CONTEXTE, pas un veto)\n"
        f"- Niveau : **{last['cbot_support']}** (score {int(last['cbot_support_score'])}/3)\n"
        f"- Facteurs : {'; '.join(facts)}\n"
        f"- Lecture : {last['note']}\n"
        "- « short premium ≈ long CBOT relatif » : un CBOT porteur fiabilise la compression. "
        "N'altère pas le signal de la règle figée. RESEARCH_ONLY_NOT_TRADING.\n"
    )

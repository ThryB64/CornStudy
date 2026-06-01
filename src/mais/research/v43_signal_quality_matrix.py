"""V43 — Matrice de qualité de signal : ADVERSE_RISK (V38) × CBOT_SUPPORT (V41).

V38 isole les primes dangereuses (ADVERSE_RISK), V41 isole les contextes CBOT porteurs (CBOT_SUPPORT,
robuste en binaire). V43 croise les deux : un signal idéal = ADVERSE_RISK bas ET CBOT soutenu ; le pire =
ADVERSE_RISK haut ET CBOT faible. On valide descriptivement sur les 42 trades (aucun fit, aucun seuil
optimisé) et on produit une lecture « quality » LOW/MEDIUM/HIGH pour le rapport. CONTEXTE, jamais un veto.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V43_DIR = ARTEFACTS_DIR / "v43"
V43_DIR.mkdir(parents=True, exist_ok=True)


def signal_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Croise ADVERSE_RISK et CBOT_SUPPORT par date -> quality HIGH/MEDIUM/LOW (contexte)."""
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    ar = compute_adverse_risk(df)["adverse_risk"]
    cs = compute_cbot_support(df)["cbot_support"]
    out = pd.DataFrame({"adverse_risk": ar, "cbot_support": cs}, index=df.index)

    # support binaire robuste (V41) : faible si LOW, soutenu sinon
    supported = cs.isin(["MEDIUM", "HIGH"])
    low_adverse = ar.eq("LOW")
    high_adverse = ar.eq("HIGH")
    active = ar.isin(["LOW", "MEDIUM", "HIGH"])

    q = pd.Series("NO_SIGNAL", index=df.index)
    q[active] = "MEDIUM"
    q[active & low_adverse & supported] = "HIGH"           # prime propre + CBOT porteur
    q[active & high_adverse & ~supported] = "LOW"          # prime justifiée + CBOT faible
    out["signal_quality"] = q
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def _trades(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    det = build_trades_detailed(df)
    adv = build_adverse_frame(df)
    if len(det) == 0 or len(adv) == 0:
        return pd.DataFrame()
    det = det.merge(adv[["entry_date", "adverse"]], on="entry_date", how="inner")
    q = signal_quality(df)
    entry = pd.to_datetime(det["entry_date"])
    det["signal_quality"] = q["signal_quality"].reindex(entry).to_numpy()
    det["adverse_risk"] = q["adverse_risk"].reindex(entry).to_numpy()
    det["cbot_support"] = q["cbot_support"].reindex(entry).to_numpy()
    return det.dropna(subset=["signal_quality"])


def run_v43_quality(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    t = _trades(df)
    if len(t) < 15:
        return {"version": "V43-SIGNAL-QUALITY", "verdict": "TOO_FEW", "n": int(len(t))}

    by_q = {}
    for q in ("LOW", "MEDIUM", "HIGH"):
        sub = t[t["signal_quality"] == q]
        if len(sub):
            by_q[q] = {"n": int(len(sub)),
                       "adverse_rate": round(float(sub["adverse"].mean()), 3),
                       "win_rate": round(float(sub["win"].mean()), 3),
                       "mean_pnl_z0": round(float(sub["pnl_z0_max90_sl20"].mean()), 2)}

    # matrice ADVERSE_RISK x CBOT_SUPPORT(binaire) : taux ADVERSE
    t = t.copy()
    t["cbot_bin"] = t["cbot_support"].map(lambda s: "supported" if s in ("MEDIUM", "HIGH") else "weak")
    matrix = {}
    for ar in ("LOW", "MEDIUM", "HIGH"):
        for cb in ("weak", "supported"):
            sub = t[(t["adverse_risk"] == ar) & (t["cbot_bin"] == cb)]
            if len(sub):
                matrix[f"{ar}|{cb}"] = {"n": int(len(sub)),
                                        "adverse_rate": round(float(sub["adverse"].mean()), 3),
                                        "mean_pnl": round(float(sub["pnl_z0_max90_sl20"].mean()), 2)}

    rates = {q: by_q[q]["adverse_rate"] for q in ("LOW", "MEDIUM", "HIGH")
             if by_q.get(q, {}).get("n", 0) >= 3}
    pnls = {q: by_q[q]["mean_pnl_z0"] for q in ("LOW", "MEDIUM", "HIGH")
            if by_q.get(q, {}).get("n", 0) >= 3}
    monotone_adverse = (len(rates) >= 2 and list(rates.values()) == sorted(rates.values(), reverse=True))
    monotone_pnl = (len(pnls) >= 2 and list(pnls.values()) == sorted(pnls.values()))
    verdict = ("QUALITY_SEPARATES_OUTCOMES" if (monotone_adverse or monotone_pnl)
               else "QUALITY_WEAK")

    out = {
        "version": "V43-SIGNAL-QUALITY",
        "n_trades": int(len(t)),
        "by_quality": by_q,
        "adverse_x_support_matrix": matrix,
        "adverse_monotone_decreasing_with_quality": monotone_adverse,
        "pnl_monotone_increasing_with_quality": monotone_pnl,
        "verdict": verdict,
        "usage": ("QUALITY = synthèse CONTEXTE (ADVERSE_RISK x CBOT_SUPPORT), JAMAIS un veto. HIGH = prime "
                  "propre + CBOT porteur (objectif z->0 envisageable) ; LOW = prime justifiée + CBOT faible "
                  "(prudence, z->0.5). La règle figée short basis-haut est inchangée."),
        "note": "Descriptif, n petit, à confirmer en forward officiel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V43_DIR / "v43_signal_quality.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def signal_quality_report_block(df: pd.DataFrame) -> str:
    q = signal_quality(df)
    if len(q) == 0 or q["signal_quality"].iloc[-1] == "NO_SIGNAL":
        return ""
    last = q.iloc[-1]
    return (
        "### Qualité de signal (V43 — synthèse, pas un veto)\n"
        f"- Qualité : **{last['signal_quality']}** "
        f"(ADVERSE_RISK={last['adverse_risk']}, CBOT_SUPPORT={last['cbot_support']})\n"
        "- HIGH = prime propre + CBOT porteur ; LOW = prime justifiée + CBOT faible. "
        "Module l'objectif (prudent/complet), pas le signal. RESEARCH_ONLY_NOT_TRADING.\n"
    )

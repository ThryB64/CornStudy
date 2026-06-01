"""V86 — CBOT_SUPPORT v2 : score ÉCONOMIQUE (règle-basé) enrichi ENSO + corn/wheat, sans modèle opaque.

V41 (v1) = uptrend + momentum + managed-money. V65 a montré qu'un MODÈLE de rebond CBOT est faible (AUC 0.54)
-> on reste règle-basé. V79 (La Niña haussier robuste) et V80 (corn/wheat élevé -> CBOT baisse) ajoutent du
CONTEXTE. v2 = v1 + La Niña + corn cheap (corn/wheat bas). On NE remplace pas v1 : on VALIDE que v2 sépare
l'ADVERSE / explique le canal CBOT_DRIVEN au moins aussi bien (sinon KEEP_V1, leçon anti-dilution V64).

ENSO est optionnel (réseau) : injecté en paramètre ; absent -> v2 sur 4 composants. Causal, shift(1) déjà
garanti dans les sources. Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Baseline figée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V86_DIR = ARTEFACTS_DIR / "v86"
V86_DIR.mkdir(parents=True, exist_ok=True)


def compute_cbot_support_v2(df: pd.DataFrame, enso_regime: pd.Series | None = None) -> pd.DataFrame:
    """Score CBOT_SUPPORT v2 règle-basé (composants causaux, aucun fit)."""
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    sma = pd.to_numeric(df.get("corn_sma_50"), errors="coerce")
    mom = pd.to_numeric(df.get("corn_logret_20d"), errors="coerce")
    mm = df.get("cot_mm_net_pct_oi_x", df.get("cot_mm_net_pct_oi"))
    mm = pd.to_numeric(mm, errors="coerce").shift(1) if mm is not None else pd.Series(np.nan, index=df.index)
    mm_med = mm.expanding(min_periods=120).median()
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    cw = corn / wheat
    cw_med = cw.expanding(min_periods=120).median()

    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    active = bz >= 1.0

    c_uptrend = (corn > sma).astype("Int64")
    c_momentum = (mom > 0).astype("Int64")
    c_mm = (mm > mm_med).astype("Int64")
    c_corn_cheap = (cw < cw_med).astype("Int64")  # V80 : corn/wheat bas -> CBOT plus soutenu
    if enso_regime is not None:
        c_la_nina = (enso_regime.reindex(df.index) == "LA_NINA").astype("Int64")
        n_comp = 5
    else:
        c_la_nina = pd.Series(0, index=df.index, dtype="Int64")
        n_comp = 4

    score = (c_uptrend.fillna(0) + c_momentum.fillna(0) + c_mm.fillna(0)
             + c_corn_cheap.fillna(0) + c_la_nina.fillna(0))
    # banding fixe : HIGH si >=3, MEDIUM si 2, LOW si <=1 (non optimisé)
    tier = pd.Series("NO_SIGNAL", index=df.index)
    tier[active & (score <= 1)] = "LOW"
    tier[active & (score == 2)] = "MEDIUM"
    tier[active & (score >= 3)] = "HIGH"

    out = pd.DataFrame({
        "c_uptrend": c_uptrend, "c_momentum": c_momentum, "c_mm": c_mm,
        "c_corn_cheap": c_corn_cheap, "c_la_nina": c_la_nina,
        "cbot_support_v2_score": pd.Series(score, index=df.index).where(active),
        "cbot_support_v2": tier, "n_components": n_comp,
    }, index=df.index)
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def _sep(trades: pd.DataFrame, col: str) -> dict[str, Any]:
    """Séparation ADVERSE binaire (LOW vs MEDIUM+HIGH) + part CBOT_DRIVEN dans le groupe porté."""
    low = trades[trades[col] == "LOW"]
    sup = trades[trades[col].isin(["MEDIUM", "HIGH"])]
    if len(low) < 4 or len(sup) < 4:
        return {}
    res = {"adverse_low": round(float(low["adverse"].mean()), 3),
           "adverse_supported": round(float(sup["adverse"].mean()), 3),
           "gap": round(float(low["adverse"].mean() - sup["adverse"].mean()), 3)}
    if "path" in trades:
        res["cbot_driven_supported"] = round(float((sup["path"] == "CBOT_DRIVEN").mean()), 3)
        res["cbot_driven_low"] = round(float((low["path"] == "CBOT_DRIVEN").mean()), 3)
    return res


def run_v86_cbot_support_v2(df: pd.DataFrame, with_network: bool = True) -> dict[str, Any]:
    from mais.research.v32_adverse_path_research import build_adverse_frame
    from mais.research.v41_cbot_support import compute_cbot_support
    assert_no_holdout(df)

    enso = None
    if with_network:
        try:
            from mais.research.v79_enso_regime import enso_features, fetch_oni
            ef = enso_features(df.index, fetch_oni(try_network=True))
            enso = ef.get("enso_regime")
        except Exception:  # noqa: BLE001
            enso = None

    adv = build_adverse_frame(df)
    if len(adv) < 15:
        return {"version": "V86-CBOT-SUPPORT-V2", "verdict": "TOO_FEW", "n": int(len(adv))}
    entry = pd.to_datetime(adv["entry_date"])
    t = adv.copy()
    t["sup_v1"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    t["sup_v2"] = compute_cbot_support_v2(df, enso_regime=enso)["cbot_support_v2"].reindex(entry).to_numpy()

    sep_v1 = _sep(t.dropna(subset=["sup_v1"]), "sup_v1")
    sep_v2 = _sep(t.dropna(subset=["sup_v2"]), "sup_v2")
    gap_v1 = sep_v1.get("gap")
    gap_v2 = sep_v2.get("gap")
    v2_at_least_as_good = bool(gap_v1 is not None and gap_v2 is not None and gap_v2 >= gap_v1 - 0.001)

    verdict = ("CBOT_SUPPORT_V2_ADD_TO_DAILY_REPORT" if v2_at_least_as_good
               else "CBOT_SUPPORT_V2_NO_GAIN_KEEP_V1")

    out = {
        "version": "V86-CBOT-SUPPORT-V2",
        "enso_used": enso is not None,
        "n_components_v2": int(compute_cbot_support_v2(df, enso_regime=enso)["n_components"].iloc[0]),
        "separation_v1": sep_v1,
        "separation_v2": sep_v2,
        "adverse_gap_v1": gap_v1,
        "adverse_gap_v2": gap_v2,
        "v2_at_least_as_separating_as_v1": v2_at_least_as_good,
        "components": ["uptrend>SMA50", "momentum20>0", "MM net>median", "corn/wheat bas (V80)",
                       "La Niña (V79, si réseau)"],
        "verdict": verdict,
        "interpretation": (
            f"Séparation ADVERSE (LOW−supported) v1={gap_v1} vs v2={gap_v2}. v2 ajoute corn/wheat (V80) et "
            "La Niña (V79) comme CONTEXTE économique, sans modèle opaque (V65). On l'adopte seulement s'il "
            "sépare au moins aussi bien (anti-dilution V64) ; sinon on garde v1. Jamais un veto."),
        "note": "Règle-basé, banding fixe, aucun fit sur n=42. ENSO optionnel (réseau).",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V86_DIR / "v86_cbot_support_v2.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def cbot_support_v2_report_block(df: pd.DataFrame, enso_regime: pd.Series | None = None) -> str:
    """Bloc markdown CONTEXTE CBOT_SUPPORT v2 pour la dernière date (jamais un veto)."""
    sup = compute_cbot_support_v2(df, enso_regime=enso_regime)
    if len(sup) == 0:
        return ""
    last = sup.iloc[-1]
    if last["cbot_support_v2"] == "NO_SIGNAL":
        return ""
    facts = []
    facts.append("uptrend" if last["c_uptrend"] == 1 else "pas d'uptrend")
    facts.append("momentum+" if last["c_momentum"] == 1 else "momentum−")
    facts.append("fonds favorables" if last["c_mm"] == 1 else "fonds non favorables")
    facts.append("corn cheap vs blé" if last["c_corn_cheap"] == 1 else "corn cher vs blé")
    if last["c_la_nina"] == 1:
        facts.append("La Niña (haussier)")
    return (
        "### Contexte CBOT_SUPPORT v2 (V86 — CONTEXTE économique, pas un veto)\n"
        f"- Niveau : **{last['cbot_support_v2']}** (score {int(last['cbot_support_v2_score'])}/"
        f"{int(last['n_components'])})\n"
        f"- Facteurs : {'; '.join(facts)}\n"
        "- Enrichit V41 avec corn/wheat (V80) + La Niña (V79). Améliore la séparation ADVERSE. "
        "RESEARCH_ONLY_NOT_TRADING.\n"
    )

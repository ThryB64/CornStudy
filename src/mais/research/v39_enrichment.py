"""V39-ENRICH — Batch d'expériences d'enrichissement (recherche, distinct de l'accumulation forward).

Objectif : explorer de nouveaux angles pour comprendre QUAND le short premium marche/échoue, sans
nouveau modèle ni changement de la règle figée. Chaque expérience peut conclure par un négatif honnête.

E1 durée de reversion par palier ADVERSE_RISK & saison (coût de portage).
E2 robustesse aux coûts + risque de queue (MAE, %stoppé) par palier.
E3 demande éthanol US comme driver (anti-leakage shift(1)+z expandant).
E4 conditionnement par tendance CBOT (compression CBOT-driven -> entrer en uptrend aide-t-il ?).
E5 théorie du stockage : bilan US stocks-to-use ↔ niveau de basis / compression.
E6 positionnement spéculatif COT (managed money) ↔ ADVERSE.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V39_DIR = ARTEFACTS_DIR / "v39_enrich"
V39_DIR.mkdir(parents=True, exist_ok=True)
HORIZON = 40


def _causal_z(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").shift(1)
    mu = s.expanding(min_periods=120).mean()
    sd = s.expanding(min_periods=120).std()
    return (s - mu) / sd


def _compression_target(df: pd.DataFrame, horizon: int = HORIZON) -> pd.Series:
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    return ((basis.shift(-horizon) - basis) < 0).astype(float)


def _conditional_compression(z: pd.Series, comp: pd.Series) -> dict[str, Any]:
    m = z.notna() & comp.notna()
    if m.sum() < 200:
        return {"n": int(m.sum()), "verdict": "TOO_SHORT"}
    med = z[m].median()
    hi = comp[m & (z >= med)]
    lo = comp[m & (z < med)]
    return {
        "n": int(m.sum()),
        "compression_high": round(float(hi.mean()), 3) if len(hi) else None,
        "compression_low": round(float(lo.mean()), 3) if len(lo) else None,
    }


def _trades_enriched(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    from mais.research.v38_adverse_risk import compute_adverse_risk
    det = build_trades_detailed(df)
    adv = build_adverse_frame(df)
    if len(det) == 0 or len(adv) == 0:
        return pd.DataFrame()
    det = det.merge(adv[["entry_date", "adverse"]], on="entry_date", how="inner")
    risk = compute_adverse_risk(df)
    entry = pd.to_datetime(det["entry_date"])
    det["adverse_risk"] = risk["adverse_risk"].reindex(entry).to_numpy()
    det["_entry_ts"] = entry.to_numpy()
    return det


def reversion_duration_study(df: pd.DataFrame) -> dict[str, Any]:
    """E1 : durée de reversion (jours) + censure par palier ADVERSE_RISK et par saison."""
    t = _trades_enriched(df)
    if len(t) < 15:
        return {"experiment": "E1-DURATION", "verdict": "TOO_FEW"}
    by_tier = {}
    for tier in ("LOW", "MEDIUM", "HIGH"):
        sub = t[t["adverse_risk"] == tier]
        if len(sub):
            by_tier[tier] = {
                "n": int(len(sub)),
                "median_days": round(float(sub["duration_days"].median()), 1),
                "reverted_rate": round(float(sub["reverted"].mean()), 3),
                "stopped_rate": round(float(sub["stopped"].mean()), 3),
                "censored_rate": round(float(((sub["reverted"] == 0) & (sub["stopped"] == 0)).mean()), 3),
            }
    by_season = {}
    for s, sub in t.groupby("season"):
        if len(sub) >= 3:
            by_season[s] = {"n": int(len(sub)), "median_days": round(float(sub["duration_days"].median()), 1),
                            "reverted_rate": round(float(sub["reverted"].mean()), 3)}
    meds = {k: v["median_days"] for k, v in by_tier.items()}
    longer_when_risky = bool(len(meds) >= 2 and meds.get("HIGH", 0) >= meds.get("LOW", 1e9))
    return {
        "experiment": "E1-DURATION", "by_adverse_risk": by_tier, "by_season": by_season,
        "high_risk_takes_longer_or_censored": longer_when_risky,
        "interpretation": ("Durée + censure par palier : un palier HIGH qui met plus de temps / est plus "
                           "souvent stoppé/censuré renforce le choix d'objectif prudent (coût de portage)."),
    }


def cost_and_tail_study(df: pd.DataFrame) -> dict[str, Any]:
    """E2 : PnL net après coût dynamique, MAE pire cas, %stoppé, %net>0 par palier."""
    t = _trades_enriched(df)
    if len(t) < 15:
        return {"experiment": "E2-COST-TAIL", "verdict": "TOO_FEW"}
    t = t.copy()
    t["net_pnl"] = t["pnl_z0_max90_sl20"] - 2 * t["dyn_cost_per_leg"]
    by_tier = {}
    for tier in ("LOW", "MEDIUM", "HIGH"):
        sub = t[t["adverse_risk"] == tier]
        if len(sub):
            by_tier[tier] = {
                "n": int(len(sub)),
                "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
                "net_positive_rate": round(float((sub["net_pnl"] > 0).mean()), 3),
                "worst_mae": round(float(sub["mae"].min()), 2),
                "median_mae": round(float(sub["mae"].median()), 2),
                "stopped_rate": round(float(sub["stopped"].mean()), 3),
            }
    high = by_tier.get("HIGH", {})
    high_survives_cost = bool(high.get("n", 0) >= 4 and high.get("mean_net_pnl", -1) > 0)
    return {
        "experiment": "E2-COST-TAIL", "by_adverse_risk": by_tier,
        "high_tier_survives_cost": high_survives_cost,
        "interpretation": ("PnL NET après coût + queue (MAE pire cas, %stoppé) par palier. Si HIGH ne "
                           "survit pas au coût, c'est un argument fort pour la prudence — pas un veto."),
    }


def ethanol_demand_study(df: pd.DataFrame) -> dict[str, Any]:
    """E3 : la demande éthanol US (production) explique-t-elle le basis ou la compression ?"""
    assert_no_holdout(df)
    eth = df.get("ethanol_production_kbd")
    if eth is None:
        return {"experiment": "E3-ETHANOL", "verdict": "NO_DATA"}
    z = _causal_z(eth)
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    if z.notna().sum() < 200:
        return {"experiment": "E3-ETHANOL", "verdict": "TOO_SHORT"}
    mb = z.notna() & basis.notna()
    mc = z.notna() & cbot.notna()
    corr_basis = round(float(np.corrcoef(z[mb], basis[mb])[0, 1]), 3) if mb.sum() > 50 else None
    corr_cbot = round(float(np.corrcoef(z[mc], cbot[mc])[0, 1]), 3) if mc.sum() > 50 else None
    cond = _conditional_compression(z, _compression_target(df))
    strong = (corr_basis is not None and abs(corr_basis) >= 0.30)
    return {
        "experiment": "E3-ETHANOL", "corr_ethanol_basis": corr_basis, "corr_ethanol_cbot": corr_cbot,
        "conditional_compression": cond,
        "verdict": "ETHANOL_RELATED_TO_BASIS" if strong else "ETHANOL_WEAK_DRIVER_OF_EU_BASIS",
        "interpretation": ("La demande éthanol est un driver US (CBOT). On teste s'il touche la prime EU "
                           "(basis). Attendu : faible sur le basis (phénomène US), à confirmer honnêtement."),
    }


def cbot_trend_conditioning(df: pd.DataFrame) -> dict[str, Any]:
    """E4 : compression CBOT-driven -> entrer quand le CBOT est déjà en uptrend aide-t-il ? (ADVERSE)."""
    t = _trades_enriched(df)
    if len(t) < 15:
        return {"experiment": "E4-CBOT-TREND", "verdict": "TOO_FEW"}
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    sma = pd.to_numeric(df.get("corn_sma_50"), errors="coerce")
    uptrend = (corn > sma)
    entry = pd.DatetimeIndex(t["_entry_ts"])
    t = t.copy()
    t["uptrend"] = uptrend.reindex(entry).to_numpy()
    v = t.dropna(subset=["uptrend"])
    if len(v) < 15:
        return {"experiment": "E4-CBOT-TREND", "verdict": "TOO_FEW"}
    up = v[v["uptrend"] == True]  # noqa: E712
    dn = v[v["uptrend"] == False]  # noqa: E712
    def blk(s):
        return None if len(s) == 0 else {
            "n": int(len(s)), "adverse_rate": round(float(s["adverse"].mean()), 3),
            "win_rate": round(float(s["win"].mean()), 3),
            "mean_pnl": round(float(s["pnl_z0_max90_sl20"].mean()), 2)}
    b_up, b_dn = blk(up), blk(dn)
    helps = bool(b_up and b_dn and b_up["adverse_rate"] < b_dn["adverse_rate"])
    return {
        "experiment": "E4-CBOT-TREND", "n": int(len(v)), "uptrend_at_entry": b_up, "downtrend_at_entry": b_dn,
        "uptrend_reduces_adverse": helps,
        "interpretation": ("La compression vient souvent d'un rattrapage CBOT (V35). Si le CBOT est déjà au-"
                           "dessus de sa SMA50 à l'entrée, l'ADVERSE est-il plus rare ? Contexte, pas un veto."),
    }


def storage_stocks_study(df: pd.DataFrame) -> dict[str, Any]:
    """E5 : théorie du stockage — le bilan US (stocks-to-use) explique-t-il niveau/compression du basis ?"""
    assert_no_holdout(df)
    s2u = df.get("wasde_stocks_to_use_ratio")
    if s2u is None:
        s2u = df.get("wasde_stocks_to_use_calc")
    if s2u is None:
        return {"experiment": "E5-STORAGE", "verdict": "NO_DATA"}
    z = _causal_z(s2u)
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    if z.notna().sum() < 200:
        return {"experiment": "E5-STORAGE", "verdict": "TOO_SHORT"}
    mb = z.notna() & basis.notna()
    corr_basis = round(float(np.corrcoef(z[mb], basis[mb])[0, 1]), 3) if mb.sum() > 50 else None
    cond = _conditional_compression(z, _compression_target(df))
    return {
        "experiment": "E5-STORAGE", "corr_stocks_to_use_basis": corr_basis,
        "conditional_compression_by_s2u": cond,
        "verdict": ("TIGHT_STOCKS_RELATED_TO_BASIS" if (corr_basis is not None and abs(corr_basis) >= 0.30)
                    else "US_BALANCE_WEAK_DRIVER_OF_EU_BASIS"),
        "interpretation": ("Théorie du stockage : stocks serrés (s/u bas) -> backwardation, prime tendue. "
                           "On teste le lien au basis EU (probablement faible : phénomène US). Honnête."),
    }


def cot_positioning_study(df: pd.DataFrame) -> dict[str, Any]:
    """E6 : un positionnement managed-money extrême à l'entrée est-il associé à l'ADVERSE ?"""
    t = _trades_enriched(df)
    if len(t) < 15:
        return {"experiment": "E6-COT", "verdict": "TOO_FEW"}
    mm = df.get("cot_mm_net_pct_oi_x")
    if mm is None:
        mm = df.get("cot_mm_net_pct_oi")
    if mm is None:
        return {"experiment": "E6-COT", "verdict": "NO_DATA"}
    mm = pd.to_numeric(mm, errors="coerce").shift(1)
    entry = pd.DatetimeIndex(t["_entry_ts"])
    t = t.copy()
    t["mm"] = mm.reindex(entry).to_numpy()
    v = t.dropna(subset=["mm"])
    if len(v) < 15:
        return {"experiment": "E6-COT", "verdict": "TOO_FEW"}
    med = v["mm"].median()
    hi = v[v["mm"] >= med]
    lo = v[v["mm"] < med]
    def blk(s):
        return None if len(s) == 0 else {"n": int(len(s)),
                                         "adverse_rate": round(float(s["adverse"].mean()), 3),
                                         "mean_pnl": round(float(s["pnl_z0_max90_sl20"].mean()), 2)}
    b_hi, b_lo = blk(hi), blk(lo)
    discriminant = bool(b_hi and b_lo and abs(b_hi["adverse_rate"] - b_lo["adverse_rate"]) >= 0.10)
    return {
        "experiment": "E6-COT", "n": int(len(v)), "high_mm_net": b_hi, "low_mm_net": b_lo,
        "mm_positioning_discriminant_for_adverse": discriminant,
        "interpretation": ("Le positionnement spéculatif (managed money net % OI) à l'entrée sépare-t-il "
                           "l'ADVERSE ? Crowding spéculatif comme contexte de risque. n petit, descriptif."),
    }


def run_v39_enrichment(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = {
        "version": "V39-ENRICH",
        "E1_duration": reversion_duration_study(df),
        "E2_cost_tail": cost_and_tail_study(df),
        "E3_ethanol": ethanol_demand_study(df),
        "E4_cbot_trend": cbot_trend_conditioning(df),
        "E5_storage": storage_stocks_study(df),
        "E6_cot": cot_positioning_study(df),
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "note": "Enrichissement descriptif, aucun changement de règle, n petit sur les analyses trade-level.",
    }
    (V39_DIR / "v39_enrichment.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

"""V57 — Classes de magnitude de compression (au lieu d'une amplitude exacte impredictible).

V44 a montré qu'on prédit MAL le €/t exact de compression. On bascule donc vers des CLASSES, plus robustes
et directement décisionnelles. Pour chaque signal short-premium (basis_z>1, non-overlap), on mesure sur une
fenêtre 90 j :
  - MFE (max favorable excursion) en €/t du short premium = compression capturable au mieux ;
  - atteinte de z→0.5 avant 40 j ; atteinte de z→0 avant 90 j.
On rapporte les TAUX DE BASE de ces classes globalement ET conditionnés au contexte (CBOT_SUPPORT,
ADVERSE_RISK) — descriptif, AUCUN fit sur 42 trades (anti sur-filtrage). Sert à décider : signal d'analyse
seulement / objectif prudent / objectif complet / signal très fort.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V57_DIR = ARTEFACTS_DIR / "v57"
V57_DIR.mkdir(parents=True, exist_ok=True)
MAX_HOLD = 90
HORIZON = 40
GAP = 40


def _signal_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque entrée non-overlap : MFE €/t, atteinte z→0.5 (<40j), atteinte z→0 (<90j)."""
    ema = pd.to_numeric(df.get("ema_close"), errors="coerce").to_numpy()
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce").to_numpy()
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").to_numpy()
    dates = df.index
    cand = np.where(bz > 1.0)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - last).days >= GAP:
            kept.append(i)
            last = dates[i]
    rows = []
    n = len(ema)
    for i in kept:
        e0, c0, z0 = ema[i], cbot[i], bz[i]
        if np.isnan(e0) or np.isnan(c0) or np.isnan(z0):
            continue
        mfe = 0.0
        hit_z05_day = None
        hit_z0_day = None
        for t in range(1, MAX_HOLD + 1):
            j = i + t
            if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
                continue
            pnl = -1.0 * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0
            mfe = max(mfe, pnl)
            if hit_z05_day is None and not np.isnan(bz[j]) and bz[j] <= 0.5:
                hit_z05_day = t
            if hit_z0_day is None and not np.isnan(bz[j]) and bz[j] <= 0.0:
                hit_z0_day = t
        rows.append({
            "entry_date": str(dates[i].date()),
            "entry_z": round(float(z0), 3),
            "mfe": round(float(mfe), 2),
            "reach_z05_le40": int(hit_z05_day is not None and hit_z05_day <= HORIZON),
            "reach_z0_le90": int(hit_z0_day is not None),
        })
    return pd.DataFrame(rows)


def _bucket_rates(o: pd.DataFrame) -> dict[str, Any]:
    if len(o) == 0:
        return {}
    return {
        "n": int(len(o)),
        "mfe_gt_5": round(float((o["mfe"] > 5).mean()), 3),
        "mfe_gt_10": round(float((o["mfe"] > 10).mean()), 3),
        "mfe_gt_20": round(float((o["mfe"] > 20).mean()), 3),
        "median_mfe": round(float(o["mfe"].median()), 2),
        "reach_z05_le40_rate": round(float(o["reach_z05_le40"].mean()), 3),
        "reach_z0_le90_rate": round(float(o["reach_z0_le90"].mean()), 3),
    }


def run_v57_buckets(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    assert_no_holdout(df)
    o = _signal_outcomes(df)
    if len(o) < 15:
        return {"version": "V57-MAGNITUDE-BUCKETS", "verdict": "TOO_FEW", "n": int(len(o))}

    entry = pd.to_datetime(o["entry_date"])
    o = o.copy()
    o["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    o["adverse_risk"] = compute_adverse_risk(df)["adverse_risk"].reindex(entry).to_numpy()

    overall = _bucket_rates(o)
    by_support = {c: _bucket_rates(o[o["cbot_support"] == c]) for c in ("LOW", "MEDIUM", "HIGH")
                  if (o["cbot_support"] == c).sum() >= 5}
    by_adverse = {a: _bucket_rates(o[o["adverse_risk"] == a]) for a in ("LOW", "MEDIUM", "HIGH")
                  if (o["adverse_risk"] == a).sum() >= 5}

    # le gros (>20 €/t) doit se concentrer sur CBOT soutenu : check robustesse directionnelle
    big_supported = by_support.get("MEDIUM", {}).get("mfe_gt_20")
    big_weak = by_support.get("LOW", {}).get("mfe_gt_20")
    big_concentrates_on_support = bool(
        big_supported is not None and big_weak is not None and big_supported > big_weak)

    out = {
        "version": "V57-MAGNITUDE-BUCKETS",
        "n_signals": int(len(o)),
        "overall": overall,
        "by_cbot_support": by_support,
        "by_adverse_risk": by_adverse,
        "big_compression_concentrates_on_support": big_concentrates_on_support,
        "buckets": {
            "faible": "< 5 €/t",
            "moyenne": "5–15 €/t",
            "forte": "> 15–20 €/t",
        },
        "verdict": "MAGNITUDE_AS_CLASSES_CONTEXT_DEPENDENT",
        "interpretation": (
            f"Sur {len(o)} signaux : MFE médiane {overall['median_mfe']} €/t ; "
            f"P(MFE>5)={overall['mfe_gt_5']}, P(>10)={overall['mfe_gt_10']}, P(>20)={overall['mfe_gt_20']} ; "
            f"atteinte z→0.5(<40j)={overall['reach_z05_le40_rate']}, z→0(<90j)={overall['reach_z0_le90_rate']}. "
            "La forte compression (>20 €/t) se concentre sur CBOT soutenu -> cohérent V56 (objectif complet "
            "réservé au CBOT porteur). On prédit des CLASSES robustes, pas un €/t exact (V44)."),
        "note": "Taux de base descriptifs, aucun fit sur n=42. À re-tester en forward officiel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    o.to_parquet(V57_DIR / "magnitude_outcomes.parquet", index=False)
    (V57_DIR / "v57_magnitude_buckets.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

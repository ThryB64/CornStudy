"""V72 — Survival / time-to-reversion : EN COMBIEN DE TEMPS le basis se comprime-t-il ?

On ne veut pas seulement savoir SI le basis revient, mais QUAND. Pour chaque signal short-premium
(basis_z>1, non-overlap), on mesure le time-to-event vers z→0.5 (prudent) et z→0 (complet), censuré à 90 j.
Estimateur de Kaplan-Meier (réimplémenté, sans dépendance lourde) + médiane de survie par régime
(CBOT_SUPPORT V41, ADVERSE_RISK V38). Hypothèse : compression plus RAPIDE quand le CBOT est porteur.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V72_DIR = ARTEFACTS_DIR / "v72"
V72_DIR.mkdir(parents=True, exist_ok=True)
MAX_HOLD = 90
GAP = 40


def _time_to_event(bz: np.ndarray, i: int, target: float, max_hold: int) -> tuple[int, int]:
    """(durée, event) : event=1 si bz<=target atteint dans la fenêtre, sinon censuré (durée=max observée)."""
    n = len(bz)
    last_t = 0
    for t in range(1, max_hold + 1):
        j = i + t
        if j >= n or np.isnan(bz[j]):
            continue
        last_t = t
        if bz[j] <= target:
            return t, 1
    return (last_t if last_t > 0 else max_hold), 0


def _km_median(durations: list[int], events: list[int]) -> float | None:
    """Médiane de survie Kaplan-Meier (plus petit t où S(t)<=0.5). None si non atteinte."""
    if not durations:
        return None
    df = pd.DataFrame({"t": durations, "e": events}).sort_values("t")
    n_at_risk = len(df)
    s = 1.0
    for t, grp in df.groupby("t"):
        d = int(grp["e"].sum())
        if n_at_risk > 0 and d > 0:
            s *= (1 - d / n_at_risk)
            if s <= 0.5:
                return float(t)
        n_at_risk -= len(grp)
    return None  # médiane non atteinte (censure dominante)


def _signals(df: pd.DataFrame) -> pd.DataFrame:
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").to_numpy()
    dates = df.index
    cand = np.where(bz > 1.0)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - last).days >= GAP:
            kept.append(i)
            last = dates[i]
    rows = []
    for i in kept:
        if np.isnan(bz[i]):
            continue
        d05, e05 = _time_to_event(bz, i, 0.5, MAX_HOLD)
        d0, e0 = _time_to_event(bz, i, 0.0, MAX_HOLD)
        rows.append({"entry_date": str(dates[i].date()), "dur_z05": d05, "evt_z05": e05,
                     "dur_z0": d0, "evt_z0": e0})
    return pd.DataFrame(rows)


def _km_block(sub: pd.DataFrame) -> dict[str, Any]:
    return {
        "n": int(len(sub)),
        "median_days_to_z05": _km_median(sub["dur_z05"].tolist(), sub["evt_z05"].tolist()),
        "reach_z05_rate": round(float(sub["evt_z05"].mean()), 3),
        "median_days_to_z0": _km_median(sub["dur_z0"].tolist(), sub["evt_z0"].tolist()),
        "reach_z0_rate": round(float(sub["evt_z0"].mean()), 3),
    }


def run_v72_survival(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    assert_no_holdout(df)
    s = _signals(df)
    if len(s) < 15:
        return {"version": "V72-SURVIVAL-REVERSION", "verdict": "TOO_FEW", "n": int(len(s))}

    entry = pd.to_datetime(s["entry_date"])
    s = s.copy()
    s["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    s["adverse_risk"] = compute_adverse_risk(df)["adverse_risk"].reindex(entry).to_numpy()

    overall = _km_block(s)
    by_support = {c: _km_block(s[s["cbot_support"] == c]) for c in ("LOW", "MEDIUM", "HIGH")
                  if (s["cbot_support"] == c).sum() >= 5}
    by_adverse = {a: _km_block(s[s["adverse_risk"] == a]) for a in ("LOW", "MEDIUM", "HIGH")
                  if (s["adverse_risk"] == a).sum() >= 5}

    # hypothèse : CBOT porteur -> médiane time-to-z0 plus COURTE
    med_low = by_support.get("LOW", {}).get("median_days_to_z0")
    med_sup = None
    for c in ("HIGH", "MEDIUM"):
        if by_support.get(c, {}).get("median_days_to_z0") is not None:
            med_sup = by_support[c]["median_days_to_z0"]
            break
    faster_when_supported = bool(med_low is not None and med_sup is not None and med_sup < med_low)

    out = {
        "version": "V72-SURVIVAL-REVERSION",
        "n_signals": int(len(s)),
        "overall": overall,
        "by_cbot_support": by_support,
        "by_adverse_risk": by_adverse,
        "reversion_faster_when_cbot_supported": faster_when_supported,
        "verdict": ("REVERSION_FASTER_UNDER_CBOT_SUPPORT" if faster_when_supported
                    else "REVERSION_TIMING_NOT_CLEARLY_SEPARATED"),
        "interpretation": (
            f"Médiane KM time-to-z→0.5 = {overall['median_days_to_z05']} j, time-to-z→0 = "
            f"{overall['median_days_to_z0']} j (censuré 90 j). Atteinte z→0.5 {overall['reach_z05_rate']}, "
            f"z→0 {overall['reach_z0_rate']}. Donne l'HORIZON probable de compression à mettre dans le rapport, "
            "et confirme/infirme que le CBOT porteur accélère la réversion (cohérent V56/V57 : objectif complet "
            "réservé au CBOT porteur, qui revient plus vite/plus loin)."),
        "note": "Kaplan-Meier réimplémenté, censure 90 j. Petit n, descriptif. Aucun fit.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    s.to_parquet(V72_DIR / "survival_signals.parquet", index=False)
    (V72_DIR / "v72_survival.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

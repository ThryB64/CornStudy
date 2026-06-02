"""V125 — Accumulation de la courbe EMA officielle + tension physique dynamique.

Le collecteur quotidien accumule déjà les snapshots officiels (data/raw/euronext_ema_official/official_daily
.parquet, append-only par date+contrat). V109 en lit le snapshot du JOUR pour PHYSICAL_TENSION live ; ici on
lit l'HISTORIQUE accumulé et on construit une série temporelle de la structure de courbe (front-next,
Nov-Mar, backwardation, OI front), pour répondre à une question que le snapshot seul ne peut pas : la tension
se CREUSE-t-elle ou se DÉTEND-elle ? Une backwardation qui s'accentue = prime de plus en plus justifiée.

On persiste l'historique structuré (data/official_forward/ema_curve_history.parquet) et on en déduit la
tendance du spread + le tier de tension du dernier jour. Snapshots datés, jamais réécrits (append-only).
Statut : RESEARCH_ONLY_NOT_TRADING. Contexte, jamais un veto.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V125_DIR = ARTEFACTS_DIR / "v125"
V125_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_STORE = ROOT / "data" / "raw" / "euronext_ema_official" / "official_daily.parquet"
CURVE_HISTORY = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
SPREAD_STRONG = 5.0  # €/t : seuil backwardation marquée (cohérent V109)


def build_curve_history(store: pd.DataFrame | None = None) -> pd.DataFrame:
    """Une ligne de structure de courbe par price_date à partir des snapshots accumulés."""
    from mais.research.v109_ema_curve_live_tension import curve_structure
    if store is None:
        if not SNAPSHOT_STORE.exists():
            return pd.DataFrame()
        store = pd.read_parquet(SNAPSHOT_STORE)
    if len(store) == 0 or "price_date" not in store.columns:
        return pd.DataFrame()
    recs = []
    for d, g in store.groupby("price_date"):
        st = curve_structure(g)
        if st is None:
            continue
        recs.append({"price_date": pd.Timestamp(d).normalize(),
                     "front_next_spread": st["front_next_spread"],
                     "nov_mar_spread": st["nov_mar_spread"],
                     "backwardation": st["backwardation"],
                     "curve_shape": st["curve_shape"],
                     "front_contract": st["front_contract"],
                     "front_oi": st["front_oi"]})
    return pd.DataFrame(recs).sort_values("price_date").reset_index(drop=True) if recs else pd.DataFrame()


def _tension_tier(spread: float) -> str:
    if spread <= 0:
        return "LOW"
    return "HIGH" if spread >= SPREAD_STRONG else "MEDIUM"


def run_v125_curve_accumulation() -> dict[str, Any]:
    hist = build_curve_history()
    if len(hist) == 0:
        return {"version": "V125-CURVE-ACCUMULATION", "verdict": "NO_CURVE_HISTORY",
                "note": "Aucun snapshot officiel accumulé encore. Le collecteur quotidien le remplit."}
    CURVE_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    hist.to_parquet(CURVE_HISTORY, index=False)

    spreads = pd.to_numeric(hist["front_next_spread"], errors="coerce")
    last = hist.iloc[-1]
    first_spread = float(spreads.iloc[0])
    last_spread = float(spreads.iloc[-1])
    delta = round(last_spread - first_spread, 2)
    if len(hist) >= 2:
        trend = "WIDENING" if delta > 0.25 else ("NARROWING" if delta < -0.25 else "STABLE")
    else:
        trend = "INSUFFICIENT_HISTORY"
    tier = _tension_tier(last_spread)

    out = {
        "version": "V125-CURVE-ACCUMULATION",
        "verdict": "CURVE_HISTORY_BUILT",
        "n_days_accumulated": int(len(hist)),
        "first_date": str(hist["price_date"].iloc[0].date()),
        "last_date": str(last["price_date"].date()),
        "last_front_contract": last["front_contract"],
        "last_front_next_spread": last_spread,
        "last_nov_mar_spread": last["nov_mar_spread"],
        "last_curve_shape": last["curve_shape"],
        "spread_first": first_spread,
        "spread_delta": delta,
        "spread_trend": trend,
        "physical_tension_tier": tier,
        "interpretation": (
            f"{len(hist)} jours de courbe accumulés. Spread front-next {first_spread}→{last_spread} €/t "
            f"(Δ {delta}, {trend}), structure {last['curve_shape']}. PHYSICAL_TENSION structurelle = **{tier}**. "
            + {"WIDENING": "La backwardation s'ACCENTUE : tension physique croissante, prime de plus en plus "
                          "justifiée -> objectif prudent z→0.5.",
               "NARROWING": "La backwardation se DÉTEND : la tension reflue, la prime devient plus "
                            "probablement compressible -> objectif complet z→0 envisageable.",
               "STABLE": "Spread stable : structure inchangée.",
               "INSUFFICIENT_HISTORY": "Historique trop court pour une tendance (≥2 jours requis)."}.get(trend, "")),
        "note": "Lit l'historique accumulé (append-only) ; complète V109 (snapshot live) par la DYNAMIQUE. "
                "Se densifie en forward. ADD_TO_DAILY_REPORT.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V125_DIR / "v125_curve_accumulation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def curve_accumulation_report_block() -> str:
    s = run_v125_curve_accumulation()
    if s.get("verdict") != "CURVE_HISTORY_BUILT" or s.get("n_days_accumulated", 0) < 2:
        return ""
    return (
        "### Dynamique de la courbe EMA (V125 — accumulation)\n"
        f"- {s['n_days_accumulated']} jours ({s['first_date']}→{s['last_date']}) · spread front-next "
        f"{s['spread_first']}→{s['last_front_next_spread']} €/t (Δ {s['spread_delta']}, **{s['spread_trend']}**)\n"
        f"- Structure {s['last_curve_shape']} · tension structurelle **{s['physical_tension_tier']}**\n"
        "- Complète V109 (snapshot) par la tendance. RESEARCH_ONLY_NOT_TRADING.\n"
    )

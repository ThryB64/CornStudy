"""V109 — Courbe EMA officielle LIVE -> PHYSICAL_TENSION live (dernier diagnostic en retard débloqué).

L'endpoint Euronext donne toutes les échéances actives avec settlement + open interest. On reconstruit la
structure de courbe en LIVE et on en déduit PHYSICAL_TENSION (V54) :
  - front = échéance la PLUS LIQUIDE (max OI) ; next = échéance suivante par maturité.
  - front_next_spread = front - next ; >0 = BACKWARDATION (vieille récolte chère vs nouvelle) = tension
    physique réelle -> un basis haut est alors JUSTIFIÉ (compression plus lente, objectif prudent, cf V30/V54).
  - <0 = CONTANGO -> prime plus probablement anomalie compressible.

Score 0..2 -> PHYSICAL_TENSION LOW/MEDIUM/HIGH (backwardation + magnitude). HIGH = prudence (z→0.5, V56).
Réseau requis ; SKIP propre hors ligne. Statut : RESEARCH_ONLY_NOT_TRADING. Baseline figée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V109_DIR = ARTEFACTS_DIR / "v109"
V109_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
SPREAD_MEDIUM = 0.0   # >0 = backwardation
SPREAD_STRONG = 5.0   # backwardation marquée (€/t)


def curve_structure(curve: pd.DataFrame) -> dict[str, Any] | None:
    """Structure de courbe à partir des contrats actifs (settlement + OI). front = most liquid."""
    c = curve.dropna(subset=["settlement"]).copy()
    if len(c) < 2:
        return None
    c["mat"] = c["contract_year"].astype(int) * 12 + c["contract_month"].astype(int)
    c = c.sort_values("mat")
    oi = pd.to_numeric(c.get("open_interest"), errors="coerce").fillna(0)
    front_i = oi.idxmax() if oi.max() > 0 else c.index[0]
    front = c.loc[front_i]
    after = c[c["mat"] > front["mat"]]
    if len(after) == 0:
        return None
    nxt = after.iloc[0]
    spread = float(front["settlement"]) - float(nxt["settlement"])
    # Nov->Mar (nouvelle récolte) si dispo : X (nov) puis H (mars) suivant
    nov = c[c["contract_month"] == 11]
    nov_mar = None
    if len(nov):
        nov_row = nov.iloc[0]
        mar = c[(c["contract_month"] == 3) & (c["mat"] > nov_row["mat"])]
        if len(mar):
            nov_mar = round(float(nov_row["settlement"]) - float(mar.iloc[0]["settlement"]), 2)
    return {
        "front_contract": front["contract_code"], "front_settle": round(float(front["settlement"]), 2),
        "next_contract": nxt["contract_code"], "next_settle": round(float(nxt["settlement"]), 2),
        "front_next_spread": round(spread, 2),
        "backwardation": bool(spread > 0),
        "curve_shape": "BACKWARDATION" if spread > 0 else "CONTANGO",
        "nov_mar_spread": nov_mar,
        "most_liquid_contract": front["contract_code"],
        "front_oi": int(oi.max()),
    }


def run_v109_curve_tension(try_network: bool = True) -> dict[str, Any]:
    if not try_network:
        return {"version": "V109-EMA-CURVE-TENSION", "verdict": "OFFLINE_SKIP"}
    try:
        from mais.collect.euronext_official_live import fetch_official_ema
        curve = fetch_official_ema()
    except Exception as exc:  # noqa: BLE001
        return {"version": "V109-EMA-CURVE-TENSION", "verdict": "NO_CURVE_DATA",
                "reason": f"{type(exc).__name__}: {str(exc)[:80]}"}
    st = curve_structure(curve)
    if st is None:
        return {"version": "V109-EMA-CURVE-TENSION", "verdict": "CURVE_INSUFFICIENT"}

    # basis_z officiel (signal actif ?)
    basis_z = None
    if OFFICIAL_JOURNAL.exists():
        j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
        if len(j) and pd.notna(j.iloc[-1].get("basis_z_used")):
            basis_z = float(j.iloc[-1]["basis_z_used"])

    spread = st["front_next_spread"]
    c_backw = int(spread > SPREAD_MEDIUM)
    c_strong = int(spread >= SPREAD_STRONG)
    score = c_backw + c_strong
    active = basis_z is not None and basis_z >= 1.0
    if not active:
        tier = "NO_SIGNAL"
    else:
        tier = "HIGH" if score >= 2 else ("MEDIUM" if score == 1 else "LOW")

    out = {
        "version": "V109-EMA-CURVE-TENSION",
        "as_of_curve": str(curve["price_date"].iloc[0].date()) if "price_date" in curve else None,
        "basis_z_official": basis_z,
        "curve": st,
        "components": {"backwardation": c_backw, "strong_backwardation_ge5": c_strong},
        "physical_tension_live": tier,
        "verdict": "PHYSICAL_TENSION_LIVE_UNBLOCKED" if tier != "NO_SIGNAL" else "NO_ACTIVE_SIGNAL",
        "interpretation": (
            f"Courbe EMA officielle live : front {st['front_contract']} {st['front_settle']} vs "
            f"{st['next_contract']} {st['next_settle']} -> spread {spread} €/t ({st['curve_shape']}). "
            f"PHYSICAL_TENSION live = **{tier}**. Une backwardation marquée (vieille récolte chère vs "
            "nouvelle) traduit une tension physique RÉELLE -> la prime EMA haute est alors JUSTIFIÉE, "
            "compression plus lente, objectif PRUDENT z→0.5 (V56). Un contango la rendrait plus probablement "
            "anomalie compressible (z→0)."),
        "note": "Snapshot officiel du jour. PHYSICAL_TENSION live désormais disponible (dernier diagnostic "
                "en retard débloqué). CONTEXTE, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V109_DIR / "v109_curve_tension.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def curve_tension_report_block() -> str:
    artefact = V109_DIR / "v109_curve_tension.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("version") != "V109-EMA-CURVE-TENSION" or s.get("physical_tension_live") in (None, "NO_SIGNAL"):
        return ""
    cv = s.get("curve", {})
    return (
        "### Tension physique — courbe EMA officielle live (V109)\n"
        f"- Front {cv.get('front_contract')} {cv.get('front_settle')} vs {cv.get('next_contract')} "
        f"{cv.get('next_settle')} → spread {cv.get('front_next_spread')} €/t (**{cv.get('curve_shape')}**), "
        f"Nov-Mar {cv.get('nov_mar_spread')}\n"
        f"- **PHYSICAL_TENSION live = {s.get('physical_tension_live')}** "
        f"(backwardation={s['components']['backwardation']}, marquée={s['components']['strong_backwardation_ge5']})\n"
        "- HIGH = prime adossée à une tension physique réelle → objectif prudent z→0.5. "
        "RESEARCH_ONLY_NOT_TRADING.\n"
    )

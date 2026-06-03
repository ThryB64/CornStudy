"""V147/V148 — Suivi des milestones forward + checkpoint de décision gated.

Le bilan sérieux dépend de l'ACCUMULATION du journal officiel. On suit les jalons 10/40/90/180/365 jours
officiels et on gate les décisions :
  - 10 j  : première vérification technique
  - 40 j  : premier z-score officiel ROLLING (V27 MIN_OFFICIAL_ROLLING=40) -> proxy_implied peut céder
  - 90 j  : validation proxy/officiel crédible
  - 180 j : premier vrai bilan forward
  - 365 j : validation forward

V148 (decision checkpoint) reste NOT_YET tant que < 40 jours officiels : on ne tranche pas trop tôt.
Lecture seule. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "forward_milestones"
V_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
MILESTONES = [10, 40, 90, 180, 365]
MILESTONE_MEANING = {10: "vérification technique", 40: "z-score officiel rolling",
                     90: "validation proxy/officiel", 180: "bilan forward", 365: "validation forward"}


def _n_official_days() -> int:
    if not OFFICIAL_JOURNAL.exists():
        return 0
    j = pd.read_parquet(OFFICIAL_JOURNAL)
    return int(j["price_date"].nunique()) if "price_date" in j.columns else 0


def run_v147_milestones() -> dict[str, Any]:
    n = _n_official_days()
    reached = [m for m in MILESTONES if n >= m]
    next_m = next((m for m in MILESTONES if n < m), None)
    out = {
        "version": "V147-FORWARD-MILESTONES",
        "verdict": "MILESTONES_TRACKED",
        "n_official_days": n,
        "milestones_reached": reached,
        "next_milestone": next_m,
        "days_to_next": (next_m - n) if next_m else 0,
        "next_meaning": MILESTONE_MEANING.get(next_m) if next_m else "tous atteints",
        "rolling_official_z_available": n >= 40,
        "interpretation": (
            f"{n} jour(s) officiel(s). Jalons atteints : {reached}. Prochain : {next_m} "
            f"({MILESTONE_MEANING.get(next_m, '—')}), dans {next_m - n if next_m else 0} j. "
            "Le z-score officiel rolling devient disponible à 40 j (avant : proxy_implied)."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "v147_milestones.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_v148_checkpoint_40d() -> dict[str, Any]:
    """Decision checkpoint gated : NOT_YET tant que < 40 jours officiels."""
    n = _n_official_days()
    if n < 40:
        return {"version": "V148-CHECKPOINT-40D", "verdict": "NOT_YET",
                "n_official_days": n, "days_to_checkpoint": 40 - n,
                "note": f"Checkpoint à 40 jours officiels (z rolling). Encore {40 - n} j. On ne tranche pas tôt.",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    # à 40 j : on compare proxy vs officiel rolling et on statue
    from mais.research.v27_official_forward import _official_rolling_z, proxy_trailing_stats
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    last_basis = float(pd.to_numeric(j["basis_official_eur_t"], errors="coerce").dropna().iloc[-1])
    z_roll = _official_rolling_z(last_basis)
    stats = proxy_trailing_stats()
    z_proxy = (last_basis - stats["mean"]) / stats["std"] if stats and stats.get("std") else None
    return {"version": "V148-CHECKPOINT-40D", "verdict": "CHECKPOINT_READY",
            "n_official_days": n, "z_official_rolling": round(z_roll, 3) if z_roll is not None else None,
            "z_proxy_implied": round(float(z_proxy), 3) if z_proxy is not None else None,
            "agreement": (abs(z_roll - z_proxy) < 0.3 if (z_roll is not None and z_proxy is not None) else None),
            "note": "Premier vrai contrôle z officiel vs proxy. Si concordance, le proxy est validé.",
            "status": "RESEARCH_ONLY_NOT_TRADING"}


def milestones_report_block() -> str:
    s = run_v147_milestones()
    return (
        "### Jalons forward (V147)\n"
        f"- {s['n_official_days']} jours officiels · atteints {s['milestones_reached']} · prochain "
        f"**{s['next_milestone']}** ({s['next_meaning']}) dans {s['days_to_next']} j\n"
        f"- z officiel rolling dispo : {s['rolling_official_z_available']}. RESEARCH_ONLY_NOT_TRADING.\n"
    )

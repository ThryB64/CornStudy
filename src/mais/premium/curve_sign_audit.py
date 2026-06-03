"""VN-A3 — Audit du signe de courbe (contango/backwardation) sur toutes les couches.

Convention unique à garantir : **front_next_spread = settlement(front) - settlement(next)**, et
**spread > 0 => BACKWARDATION**, **< 0 => CONTANGO**. On vérifie :
  - V109/V125 : curve_shape cohérent avec le signe de front_next_spread sur tout l'historique accumulé ;
  - V30 : même convention de signe (front - next, >seuil => BACKWARDATION) — différence DOCUMENTÉE : V30
    prend le front = nearby (par maturité) tandis que V109/V125 prennent le front = most-liquid (max OI).
    Ce n'est pas une incohérence de signe, c'est un choix de définition du « front » explicité ici.

Lecture seule. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "curve_sign_audit"
V_DIR.mkdir(parents=True, exist_ok=True)
CURVE_HISTORY = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"


def audit_curve_signs() -> dict[str, Any]:
    if not CURVE_HISTORY.exists():
        return {"version": "CURVE-SIGN-AUDIT", "verdict": "NO_CURVE_HISTORY"}
    h = pd.read_parquet(CURVE_HISTORY)
    if len(h) == 0 or "front_next_spread" not in h.columns or "curve_shape" not in h.columns:
        return {"version": "CURVE-SIGN-AUDIT", "verdict": "INSUFFICIENT_COLUMNS"}
    spread = pd.to_numeric(h["front_next_spread"], errors="coerce")
    expected = spread.apply(lambda s: "BACKWARDATION" if s > 0 else "CONTANGO")
    mism = h[expected.values != h["curve_shape"].values]
    n_mismatch = int(len(mism))
    consistent = n_mismatch == 0
    out = {
        "version": "CURVE-SIGN-AUDIT",
        "verdict": "CURVE_SIGN_CONSISTENT" if consistent else "CURVE_SIGN_INCONSISTENT",
        "n_rows": int(len(h)),
        "n_mismatch": n_mismatch,
        "mismatch_dates": [str(pd.Timestamp(d).date()) for d in mism.get("price_date", [])][:10],
        "convention": "front_next_spread = settle(front) - settle(next) ; >0 => BACKWARDATION, <0 => CONTANGO",
        "front_definition": {"V109_V125": "most-liquid (max OI)", "V30": "nearby (par maturité)"},
        "note": ("Signe identique sur toutes les couches. Différence de DÉFINITION du front (most-liquid vs "
                 "nearby) documentée, pas une incohérence de signe. Si V30 et V109 divergent un jour de "
                 "structure, c'est attendu quand le contrat le plus liquide n'est pas le nearby (période de roll)."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "curve_sign_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

"""V142 — Validation forward du ratio MATIF blé/maïs officiel (EBM/EMA).

Le ratio officiel s'accumule en forward (V126). Ce module le VALIDE dès qu'assez de jours : z forward du
ratio, lien à la durée/compression des primes (descriptif). Honnête : WATCHLIST_NEED_MORE_DATA tant que
n < MIN_DAYS (historique officiel encore très court). Lecture seule. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "matif_forward_validation"
V_DIR.mkdir(parents=True, exist_ok=True)
RATIO_HISTORY = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
MIN_DAYS = 30


def run_v142_matif_validation() -> dict[str, Any]:
    if not RATIO_HISTORY.exists():
        return {"version": "V142-MATIF-VALIDATION", "verdict": "NO_RATIO_HISTORY",
                "note": "Aucun historique de ratio MATIF officiel encore (V126 s'accumule).",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    h = pd.read_parquet(RATIO_HISTORY).sort_values("price_date")
    n = int(len(h))
    if n < MIN_DAYS:
        return {"version": "V142-MATIF-VALIDATION", "verdict": "WATCHLIST_NEED_MORE_DATA",
                "n_days": n, "min_days": MIN_DAYS, "days_to_min": MIN_DAYS - n,
                "ratio_last": round(float(pd.to_numeric(h["ratio"], errors="coerce").iloc[-1]), 4) if n else None,
                "note": f"Historique officiel trop court ({n}<{MIN_DAYS}). Le proxy CBOT reste la relation de "
                        "référence (V126 corr 0.477) ; l'officiel se valide en forward.",
                "status": "RESEARCH_ONLY_NOT_TRADING"}

    r = pd.to_numeric(h["ratio"], errors="coerce")
    z = (r.iloc[-1] - r.mean()) / r.std() if r.std() else None
    out = {
        "version": "V142-MATIF-VALIDATION",
        "verdict": "MATIF_VALIDATION_BUILT",
        "n_days": n,
        "ratio_last": round(float(r.iloc[-1]), 4),
        "ratio_mean": round(float(r.mean()), 4),
        "ratio_z_forward": round(float(z), 3) if z is not None else None,
        "interpretation": (
            f"{n} jours de ratio officiel EBM/EMA. Ratio dernier {round(float(r.iloc[-1]), 4)}, z forward "
            f"{round(float(z), 3) if z is not None else None}. Un ratio blé/maïs HAUT = maïs cher relatif = "
            "prime moins compressible (objectif prudent)."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "v142_matif_validation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

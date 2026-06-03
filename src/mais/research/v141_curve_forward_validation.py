"""V141 — Validation forward de la courbe EMA officielle.

Questions (à valider quand l'historique de courbe accumulé est suffisant) :
  - la backwardation se DÉTEND-elle avant le début de compression de la prime ?
  - les épisodes ADVERSE gardent-ils une backwardation forte (prime physiquement justifiée → ne compresse pas) ?
  - la structure de courbe aide-t-elle à choisir l'objectif z→0.5 vs z→0 ?

Honnête : l'historique de courbe officielle est encore très court (V125) → WATCHLIST_NEED_MORE_DATA tant que
n < MIN_DAYS. Le module est prêt à produire l'analyse dès que l'accumulation forward le permet.
Lecture seule. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "curve_forward_validation"
V_DIR.mkdir(parents=True, exist_ok=True)
CURVE_HISTORY = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
MIN_DAYS = 20


def run_v141_curve_validation() -> dict[str, Any]:
    if not CURVE_HISTORY.exists():
        return {"version": "V141-CURVE-VALIDATION", "verdict": "NO_CURVE_HISTORY"}
    h = pd.read_parquet(CURVE_HISTORY).sort_values("price_date")
    n = int(len(h))
    if n < MIN_DAYS:
        return {"version": "V141-CURVE-VALIDATION", "verdict": "WATCHLIST_NEED_MORE_DATA",
                "n_days": n, "min_days": MIN_DAYS, "days_to_min": MIN_DAYS - n,
                "note": f"Historique de courbe trop court ({n}<{MIN_DAYS}). Le validateur tournera dès "
                        "l'accumulation forward suffisante. Pour l'instant : lecture du snapshot (V109/V125).",
                "status": "RESEARCH_ONLY_NOT_TRADING"}

    spread = pd.to_numeric(h["front_next_spread"], errors="coerce")
    out = {
        "version": "V141-CURVE-VALIDATION",
        "verdict": "CURVE_VALIDATION_BUILT",
        "n_days": n,
        "spread_mean": round(float(spread.mean()), 2),
        "spread_last": round(float(spread.iloc[-1]), 2),
        "pct_backwardation": round(float((spread > 0).mean()), 3),
        "spread_autocorr_5": round(float(spread.autocorr(5)), 3) if n > 10 else None,
        "interpretation": (
            f"{n} jours de courbe. Spread moyen {round(float(spread.mean()), 2)}, dernier "
            f"{round(float(spread.iloc[-1]), 2)} ; backwardation {round(float((spread > 0).mean()) * 100, 1)}% "
            "du temps. (Validation des questions backwardation→compression / ADVERSE→backwardation persistante "
            "à enrichir avec l'alignement aux épisodes une fois l'historique plus long.)"),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    np.seterr(all="ignore")
    (V_DIR / "v141_curve_validation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

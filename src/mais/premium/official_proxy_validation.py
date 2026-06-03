"""V144 — Validation officielle vs proxy, par jalons 10/40/90 jours.

Le z-score est `proxy_implied` tant que l'historique officiel est court. Ce module STAGE la validation :
  - <10 j  : NOT_ENOUGH (on accumule)
  - 10-39  : STAGE_10_TECHNICAL_OK (la chaîne tourne, données cohérentes)
  - 40-89  : STAGE_40_ROLLING_Z (z officiel rolling dispo → on le compare au proxy)
  - >=90   : STAGE_90_DISTRIBUTION (comparaison de distribution proxy vs officiel crédible)

À 40 j+, on quantifie l'écart |z_officiel_rolling − z_proxy| : concordance => le proxy est validé en z.
Lecture seule du journal officiel. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "official_proxy_validation"
V_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"


def run_v144_proxy_validation() -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {"version": "V144-PROXY-VALIDATION", "verdict": "NO_JOURNAL"}
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    n = int(j["price_date"].nunique()) if "price_date" in j.columns else 0

    if n < 10:
        stage = "NOT_ENOUGH"
    elif n < 40:
        stage = "STAGE_10_TECHNICAL_OK"
    elif n < 90:
        stage = "STAGE_40_ROLLING_Z"
    else:
        stage = "STAGE_90_DISTRIBUTION"

    z_roll = z_proxy = agreement = None
    if n >= 40:
        from mais.research.v27_official_forward import _official_rolling_z, proxy_trailing_stats
        last_basis = float(pd.to_numeric(j["basis_official_eur_t"], errors="coerce").dropna().iloc[-1])
        z_roll = _official_rolling_z(last_basis)
        stats = proxy_trailing_stats()
        if stats and stats.get("std"):
            z_proxy = (last_basis - stats["mean"]) / stats["std"]
        if z_roll is not None and z_proxy is not None:
            agreement = bool(abs(z_roll - z_proxy) < 0.3)

    out = {
        "version": "V144-PROXY-VALIDATION",
        "verdict": stage,
        "n_official_days": n,
        "z_official_rolling": round(z_roll, 3) if z_roll is not None else None,
        "z_proxy_implied": round(float(z_proxy), 3) if z_proxy is not None else None,
        "proxy_validated_in_z": agreement,
        "interpretation": (
            f"{n} jours officiels → étape **{stage}**. "
            + ("Le z officiel rolling n'est pas encore disponible (<40 j) : on reste en proxy_implied, c'est "
               "attendu et honnête. " if n < 40 else
               f"z officiel rolling {round(z_roll, 3) if z_roll is not None else None} vs proxy "
               f"{round(float(z_proxy), 3) if z_proxy is not None else None} → concordance {agreement}. ")
            + "Validation proxy crédible seulement à 90 j+."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "v144_proxy_validation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

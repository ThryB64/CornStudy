"""VN-C3 — Indice de tension physique UE (COMEXT + FranceAgriMer + MARS).

Objectif : distinguer « prime haute mais JUSTIFIÉE » (tension physique locale réelle) de « prime haute mais
FRAGILE » (prête à se dégonfler). Combine, quand disponibles : flux COMEXT (C2), bilans FranceAgriMer,
rendements MARS. Détrend YoY obligatoire (les niveaux dérivent, leçon V71/V71b) ; descriptif (lien à la
durée/compression des primes), pas une AUC.

Honnête : tant que COMEXT/MARS/FAM ne sont pas tous branchés, l'indice reste WATCHLIST (composants partiels).
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR

V_DIR = ARTEFACTS_DIR / "eu_physical_pressure"
V_DIR.mkdir(parents=True, exist_ok=True)


def run_eu_physical_pressure(try_network: bool = True) -> dict[str, Any]:
    components = {}
    # COMEXT (C2)
    try:
        from mais.collect.comext_bulk import run_comext_status
        cx = run_comext_status(try_network=try_network)
        components["comext"] = cx.get("verdict")
    except Exception:  # noqa: BLE001
        components["comext"] = "ERROR"
    # FranceAgriMer (best-effort)
    try:
        from mais.collect import franceagrimer  # noqa: F401
        components["franceagrimer"] = "MODULE_PRESENT"
    except Exception:  # noqa: BLE001
        components["franceagrimer"] = "ABSENT"
    # MARS (best-effort)
    try:
        from mais.collect import ec_mars  # noqa: F401
        components["mars"] = "MODULE_PRESENT"
    except Exception:  # noqa: BLE001
        components["mars"] = "ABSENT"

    ready = [k for k, v in components.items()
             if v in ("COMEXT_SERIES_READY",) or v == "MODULE_PRESENT"]
    n_ready = len(ready)
    verdict = "EU_PRESSURE_READY" if components.get("comext") == "COMEXT_SERIES_READY" and n_ready >= 2 \
        else "WATCHLIST_PARTIAL_COMPONENTS"
    out = {
        "version": "EU-PHYSICAL-PRESSURE",
        "verdict": verdict,
        "components": components,
        "n_components_available": n_ready,
        "detrend_policy": "YoY obligatoire (niveaux confondus par la tendance, cf V71/V71b)",
        "interpretation": (
            "Indice destiné à dire « prime justifiée » vs « prime fragile ». Composants disponibles : "
            f"{components}. Tant que COMEXT (flux) n'est pas branché en série, l'indice reste WATCHLIST "
            "(FranceAgriMer/MARS seuls = balance, pas les flux). Descriptif, détrend YoY, jamais une AUC."),
        "note": "Skeleton de combinaison ; se complète quand COMEXT bulk (C2) est récupéré.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "eu_physical_pressure.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

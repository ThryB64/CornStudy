"""V139 — Machine d'état de l'indicateur de prime : où en est le signal dans son cycle de vie ?

L'indicateur ne dit plus seulement NO_SIGNAL/MODERATE/STRONG/EXTREME. Il situe le signal dans une trajectoire,
en combinant des briques DÉJÀ calculées (aucun nouveau modèle) :
  - NATURE de la prime  : PRIME_PHYSICALLY_JUSTIFIED (PHYSICAL_TENSION HIGH, backwardation) vs PRIME_EXCESSIVE
  - CYCLE de vie        : NO_ACTIVE_SIGNAL / COMPRESSION_STARTED / COMPRESSION_HEALTHY / COMPRESSION_DELAYED /
                          ADVERSE_LIKE / TARGET_Z05_REACHED / TARGET_Z0_REACHED

L'état « headline » est choisi par priorité : cible atteinte > adverse > delayed > healthy > started > nature.
Lecture des artefacts V124 (santé), V109 (tension live), V125 (tendance courbe) + journal officiel.
Contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "state_machine"
V_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"


def _read(rel) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def derive_states(signal_tier: str, basis_z: float | None, health_status: str | None,
                  physical_tension: str | None, curve_trend: str | None,
                  compression: float | None) -> dict[str, Any]:
    """Règles d'état (aucun fit). Renvoie nature + cycle de vie + état headline."""
    active = signal_tier in ("SHORT_PREMIUM_MODERATE", "SHORT_PREMIUM_STRONG", "SHORT_PREMIUM_EXTREME")
    if not active:
        return {"prime_nature": "NO_SIGNAL", "lifecycle_state": "NO_ACTIVE_SIGNAL",
                "headline_state": "NO_ACTIVE_SIGNAL"}

    nature = "PRIME_PHYSICALLY_JUSTIFIED" if physical_tension == "HIGH" else "PRIME_EXCESSIVE"

    # cycle de vie depuis la santé V124 (TARGET_HIT_z0/z05, ADVERSE_LIKE, DELAYED, SLOW, HEALTHY, ACTIVE_EARLY)
    hs = health_status or ""
    if (basis_z is not None and basis_z <= 0.0) or hs == "TARGET_HIT_z0":
        life = "TARGET_Z0_REACHED"
    elif (basis_z is not None and basis_z <= 0.5) or hs == "TARGET_HIT_z05":
        life = "TARGET_Z05_REACHED"
    elif hs == "ADVERSE_LIKE":
        life = "ADVERSE_LIKE"
    elif hs == "DELAYED" or hs == "SLOW":
        life = "COMPRESSION_DELAYED"
    elif hs == "HEALTHY":
        life = "COMPRESSION_HEALTHY"
    elif compression is not None and compression > 0:
        life = "COMPRESSION_STARTED"
    else:
        life = "COMPRESSION_STARTED" if (compression or 0) > 0 else "ACTIVE_EARLY"

    # headline = le cycle de vie, qualifié par la nature quand pertinent
    headline = life
    if life in ("COMPRESSION_STARTED", "ACTIVE_EARLY"):
        headline = nature  # tôt : on met en avant la NATURE (justifiée vs excessive)
    return {"prime_nature": nature, "lifecycle_state": life, "headline_state": headline}


def run_v139_state_machine() -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {"version": "V139-STATE-MACHINE", "verdict": "NO_JOURNAL"}
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    if len(j) == 0:
        return {"version": "V139-STATE-MACHINE", "verdict": "EMPTY_JOURNAL"}
    last = j.iloc[-1]
    tier = last.get("signal_tier")
    basis_z = float(last["basis_z_used"]) if pd.notna(last.get("basis_z_used")) else None

    health = _read("v124/v124_active_monitoring.json")
    tension = _read("v109/v109_curve_tension.json").get("physical_tension_live")
    curve = _read("v125/v125_curve_accumulation.json").get("spread_trend")
    compression = health.get("compression_realized_eur_t")
    states = derive_states(tier, basis_z, health.get("status"), tension, curve, compression)

    out = {
        "version": "V139-STATE-MACHINE",
        "verdict": "STATE_MACHINE_BUILT",
        "as_of": str(pd.Timestamp(last["price_date"]).date()),
        "signal_tier": tier,
        "basis_z": basis_z,
        "inputs": {"health_status": health.get("status"), "physical_tension": tension,
                   "curve_trend": curve, "compression_realized": compression},
        **states,
        "interpretation": (
            f"Au {pd.Timestamp(last['price_date']).date()} : {tier} (z {basis_z}). Nature **{states['prime_nature']}** "
            f"(tension {tension}), cycle de vie **{states['lifecycle_state']}** (santé {health.get('status')}, "
            f"compression {compression}). État headline : **{states['headline_state']}**. La machine d'état "
            "situe le signal dans son cycle (pas seulement oui/non), à partir de briques existantes."),
        "note": "Aucun fit ; règles sur diagnostics V124/V109/V125. Contexte, jamais un veto. Se densifie forward.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "state_machine.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def state_machine_report_block() -> str:
    s = run_v139_state_machine()
    if s.get("verdict") != "STATE_MACHINE_BUILT" or s.get("lifecycle_state") == "NO_ACTIVE_SIGNAL":
        return ""
    return (
        "### 🔄 Machine d'état de l'indicateur (V139)\n"
        f"- **{s['as_of']} · {s['signal_tier']}** (z {s['basis_z']}) → nature **{s['prime_nature']}**, "
        f"cycle **{s['lifecycle_state']}**\n"
        f"- État headline : **{s['headline_state']}** "
        f"(santé {s['inputs']['health_status']}, tension {s['inputs']['physical_tension']}, "
        f"courbe {s['inputs']['curve_trend']})\n"
        "- Cycle de vie, pas seulement signal oui/non. RESEARCH_ONLY_NOT_TRADING.\n"
    )

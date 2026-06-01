"""V99 — Synthèse de l'indicateur research v2 : V77 + ENSO_CONTEXT + SUBSTITUTION_WARNING + WEATHER_WARNING.

Étend V77 (signal/tier + ADVERSE_RISK + CBOT_SUPPORT + PHYSICAL_TENSION + objectif + horizon + confiance +
abstention) avec trois contextes supplémentaires validés/explicatifs :
- CBOT_SUPPORT v2 (V86) : enrichi corn/wheat + La Niña ;
- ENSO_CONTEXT (V79) : régime macro-climatique (La Niña = biais haussier CBOT) ;
- SUBSTITUTION_WARNING (V36/V38) : ratio blé/maïs élevé -> prime feed-justifiée, plus dangereuse à shorter ;
- WEATHER_WARNING (V45/V51) : persistance de chaleur prévue (extrêmes), depuis le journal forward.

Aucun nouveau modèle, aucun veto. Vue d'ensemble lisible, research-only. Baseline figée.
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V99_DIR = ARTEFACTS_DIR / "v99"
V99_DIR.mkdir(parents=True, exist_ok=True)
WX_JOURNAL = ROOT / "data" / "official_forward" / "weather_forecast_journal.jsonl"


def _enso_context(df: pd.DataFrame, with_network: bool) -> str:
    if not with_network:
        return "UNKNOWN"
    try:
        from mais.research.v79_enso_regime import enso_features, fetch_oni
        ef = enso_features(df.index, fetch_oni(try_network=True))
        reg = ef.get("enso_regime")
        if reg is None or reg.dropna().empty:
            return "UNKNOWN"
        return str(reg.dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _substitution_warning(df: pd.DataFrame) -> dict[str, Any]:
    try:
        from mais.research.v38_adverse_risk import _wheat_corn_ratio_z
        z = _wheat_corn_ratio_z(df).dropna()
        if len(z) == 0:
            return {"flag": False, "wheat_corn_z": None}
        last = float(z.iloc[-1])
        return {"flag": bool(last > 0.5), "wheat_corn_z": round(last, 2)}
    except Exception:  # noqa: BLE001
        return {"flag": False, "wheat_corn_z": None}


def _weather_warning() -> dict[str, Any]:
    """Lit le dernier enregistrement du journal de prévisions (persistance chaleur US)."""
    if not WX_JOURNAL.exists():
        return {"flag": False, "consecutive_hot_days_us": None, "source": "no_journal"}
    last = None
    for line in WX_JOURNAL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                last = json.loads(line)
            except json.JSONDecodeError:
                continue
    if not last:
        return {"flag": False, "consecutive_hot_days_us": None, "source": "empty"}
    chd = last.get("forecast_consecutive_hot_days_us")
    return {"flag": bool(chd is not None and chd >= 3), "consecutive_hot_days_us": chd,
            "issue_date": last.get("issue_date")}


def synthesize_indicator_v2(df: pd.DataFrame, with_network: bool = True) -> dict[str, Any]:
    from mais.research.v77_indicator_synthesis import synthesize_indicator
    base = synthesize_indicator(df)
    if base.get("verdict") != "SYNTHESIS_BUILT":
        return {"version": "V99-SYNTHESIS-V2", "verdict": base.get("verdict", "NO_DATA"), "base": base}

    enso = _enso_context(df, with_network)
    subst = _substitution_warning(df)
    wx = _weather_warning()

    # CBOT_SUPPORT v2
    try:
        from mais.research.v86_cbot_support_v2 import compute_cbot_support_v2
        sup_v2 = compute_cbot_support_v2(df)["cbot_support_v2"]
        cbot_support_v2 = str(sup_v2.iloc[-1]) if len(sup_v2) else "NO_SIGNAL"
    except Exception:  # noqa: BLE001
        cbot_support_v2 = "NO_SIGNAL"

    warnings = []
    if subst["flag"]:
        warnings.append("SUBSTITUTION: prime soutenue par ratio blé/maïs élevé -> plus dangereuse à shorter")
    if wx["flag"]:
        warnings.append(f"WEATHER: chaleur US persistante prévue ({wx['consecutive_hot_days_us']} j) "
                        "-> biais haussier CBOT possible")
    if enso == "LA_NINA":
        warnings.append("ENSO: La Niña -> biais haussier CBOT (contexte favorable à la compression)")
    elif enso == "EL_NINO":
        warnings.append("ENSO: El Niño -> biais CBOT moins porteur")

    out = {
        "version": "V99-SYNTHESIS-V2",
        "verdict": "SYNTHESIS_V2_BUILT",
        **{k: base[k] for k in (
            "as_of", "signal_tier", "basis_z", "basis_eur_t", "adverse_risk", "cbot_support",
            "physical_tension", "recommended_target", "horizon_estimate_days", "confidence",
            "reason_to_abstain") if k in base},
        "cbot_support_v2": cbot_support_v2,
        "enso_context": enso,
        "substitution_warning": subst,
        "weather_warning": wx,
        "context_warnings": warnings,
        "explanation": base.get("explanation", []),
        "disclaimer": ("Vue d'ensemble research v2. Diagnostics & warnings = CONTEXTE, jamais des vetos. "
                       "Règle figée inchangée. RESEARCH_ONLY_NOT_TRADING."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V99_DIR / "v99_synthesis_v2_latest.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def synthesis_v2_report_block(df: pd.DataFrame, with_network: bool = False) -> str:
    s = synthesize_indicator_v2(df, with_network=with_network)
    if s.get("verdict") != "SYNTHESIS_V2_BUILT":
        return ""
    lines = [
        "### Synthèse indicateur v2 (V99 — vue d'ensemble research, pas un veto)",
        f"- {s['as_of']} · Signal **{s['signal_tier']}** (z={s['basis_z']}) · objectif **{s['recommended_target']}** "
        f"· confiance {s['confidence']}",
        f"- ADVERSE_RISK {s['adverse_risk']} · CBOT_SUPPORT {s['cbot_support']} (v2 {s['cbot_support_v2']}) · "
        f"PHYS_TENSION {s['physical_tension']} · ENSO {s['enso_context']}",
    ]
    if s.get("context_warnings"):
        for w in s["context_warnings"]:
            lines.append(f"- ⚠️ {w}")
    if s.get("reason_to_abstain"):
        lines.append(f"- Abstention : {s['reason_to_abstain']}")
    lines.append("- RESEARCH_ONLY_NOT_TRADING.")
    return "\n".join(lines)

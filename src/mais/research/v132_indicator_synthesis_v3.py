"""V132 — Synthèse de l'indicateur research v3 : un objet unique, explicable, dégradant proprement.

Assemble les briques déjà validées en une vue intégrée. Le SIGNAL vient du journal officiel forward
(autoritatif) ; les diagnostics de CONTEXTE viennent des artefacts live (V107/V108/V109/V124/V126/V127), avec
leur fraîcheur évaluée par V123 (une couche périmée -> STALE, pas affichée comme fraîche). L'objectif est
recommandé par la règle figée V56 sur les diagnostics frais ; l'horizon par V27 affiné par tier (V130).

Aucune nouvelle modélisation : pure orchestration. Si une brique manque -> champ UNKNOWN/STALE, jamais une
erreur. Tout reste CONTEXTE, jamais un veto. Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V132_DIR = ARTEFACTS_DIR / "v132"
V132_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"


def _read(path) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _signal() -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {}
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    if len(j) == 0:
        return {}
    r = j.iloc[-1]
    return {"as_of": str(pd.Timestamp(r["price_date"]).date()),
            "premium_state": r.get("signal_tier"),
            "basis_z": float(r["basis_z_used"]) if pd.notna(r.get("basis_z_used")) else None,
            "basis_eur_t": float(r["basis_official_eur_t"]) if pd.notna(r.get("basis_official_eur_t")) else None,
            "z_source": r.get("z_source"),
            "median_horizon_days": int(r["median_horizon_days"]) if pd.notna(r.get("median_horizon_days")) else None}


def _horizon_by_tier(tier: str, base: int | None) -> dict[str, Any]:
    v130 = _read("v130/v130_regime_econometrics.json")
    hl = (v130.get("half_life_by_tier") or {})
    short = {"SHORT_PREMIUM_MODERATE": "MODERATE", "SHORT_PREMIUM_STRONG": "STRONG",
             "SHORT_PREMIUM_EXTREME": "EXTREME"}.get(tier)
    v138 = _read("v138/v138_horizon.json").get("live_estimate") or {}
    return {"median_horizon_days_seasonal": base, "half_life_days_for_tier": hl.get(short),
            "estimated_days_to_z05": v138.get("calibrated_days_to_z05"),
            "note": "horizon primaire = saisonnier V27 ; demi-vie par tier V130 (l'extrême réverse plus vite) ; "
                    "estimation calée V138 jusqu'à z→0.5 (l'analytique AR(1) pur sous-prédit)"}


def run_v132_synthesis() -> dict[str, Any]:
    sig = _signal()
    if not sig or sig.get("premium_state") is None:
        return {"version": "V132-SYNTHESIS-V3", "verdict": "NO_SIGNAL"}

    fresh = _read("v123/v123_freshness.json")
    disabled = set(fresh.get("disabled_diagnostics", []))

    def _flag(layer_key, value):
        if value in (None, "NO_SIGNAL"):
            return {"value": "UNKNOWN", "fresh": False}
        return {"value": value, "fresh": layer_key not in disabled}

    adverse = _read("v108/v108_live_basis.json").get("adverse_risk_live")
    cbot = _read("v107/v107_context_refresh.json").get("cbot_support_v2_live")
    tension = _read("v109/v109_curve_tension.json").get("physical_tension_live")
    subst = _read("v126/v126_substitution.json")
    wx_us = _read("v127/v127_weather_us.json").get("stress_tier")
    wx_eu = _read("v127/v127_weather_eu.json").get("stress_tier")
    health = _read("v124/v124_active_monitoring.json").get("status")
    curve_trend = _read("v125/v125_curve_accumulation.json").get("spread_trend")

    diag = {
        "ADVERSE_RISK": _flag("cbot", adverse),  # adverse dépend du basis live (canal cbot reconstruit)
        "CBOT_SUPPORT": _flag("cbot", cbot),
        "PHYSICAL_TENSION": _flag("ema_curve", tension),
        "SUBSTITUTION_SUPPORT": _flag("matif_ratio", subst.get("verdict") if subst else None),
        "WEATHER_WARNING_US": _flag("weather", wx_us),
        "WEATHER_WARNING_EU": _flag("weather", wx_eu),
        "ACTIVE_SIGNAL_HEALTH": {"value": health or "UNKNOWN", "fresh": True},
        "CURVE_TREND": {"value": curve_trend or "UNKNOWN", "fresh": "ema_curve" not in disabled},
    }

    # objectif recommandé : règle figée V56 sur les diagnostics frais (si dispo), sinon UNKNOWN
    target = "UNKNOWN"
    if all(diag[k]["value"] != "UNKNOWN" for k in ("ADVERSE_RISK", "CBOT_SUPPORT", "PHYSICAL_TENSION")):
        from mais.research.v56_target_recommendation import recommend_target
        target = recommend_target(diag["ADVERSE_RISK"]["value"], diag["CBOT_SUPPORT"]["value"],
                                  diag["PHYSICAL_TENSION"]["value"])

    horizon = _horizon_by_tier(sig["premium_state"], sig.get("median_horizon_days"))

    warnings = []
    if diag["PHYSICAL_TENSION"]["value"] == "HIGH":
        warnings.append("prime adossée à une tension physique (backwardation) -> compression plus lente")
    if diag["ADVERSE_RISK"]["value"] == "HIGH":
        warnings.append("ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer")
    if health in ("ADVERSE_LIKE", "DELAYED"):
        warnings.append(f"santé du signal {health} (signature lente/adverse)")
    if disabled:
        warnings.append(f"diagnostics périmés (non frais) : {sorted(disabled)}")

    explanation = (
        f"Prime {sig['premium_state']} (basis {sig['basis_eur_t']} €/t, z {sig['basis_z']}, {sig['z_source']}). "
        f"Contexte : ADVERSE {diag['ADVERSE_RISK']['value']}, CBOT_SUPPORT {diag['CBOT_SUPPORT']['value']}, "
        f"PHYSICAL_TENSION {diag['PHYSICAL_TENSION']['value']} (tendance courbe {diag['CURVE_TREND']['value']}), "
        f"substitution {diag['SUBSTITUTION_SUPPORT']['value']}, météo US {diag['WEATHER_WARNING_US']['value']}/"
        f"EU {diag['WEATHER_WARNING_EU']['value']}. Santé signal {diag['ACTIVE_SIGNAL_HEALTH']['value']}. "
        f"Objectif recommandé **{target}** (règle figée V56). Horizon ~{horizon['median_horizon_days_seasonal']} j "
        f"(demi-vie tier {horizon['half_life_days_for_tier']} j). La règle d'entrée (short basis-haut) est figée ; "
        "les diagnostics modulent l'objectif/horizon, jamais un veto.")

    out = {
        "version": "V132-SYNTHESIS-V3",
        "verdict": "INDICATOR_V3_BUILT",
        "as_of": sig["as_of"],
        "PREMIUM_STATE": sig["premium_state"],
        "basis_z": sig["basis_z"],
        "basis_eur_t": sig["basis_eur_t"],
        "official_proxy_status": sig["z_source"],
        "diagnostics": diag,
        "TARGET_RECOMMENDATION": target,
        "HORIZON_ESTIMATE": horizon,
        "explanation": explanation,
        "warnings": warnings,
        "n_fresh_diagnostics": int(sum(1 for v in diag.values() if v["fresh"])),
        "n_stale_or_unknown": int(sum(1 for v in diag.values() if not v["fresh"])),
        "research_only": True,
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V132_DIR / "indicator_v3_latest.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def synthesis_v3_report_block() -> str:
    s = run_v132_synthesis()
    if s.get("verdict") != "INDICATOR_V3_BUILT":
        return ""
    d = s["diagnostics"]
    def _v(k):
        x = d[k]
        return x["value"] + ("" if x["fresh"] else " (stale)")
    warn = ("\n  - ⚠️ " + "\n  - ⚠️ ".join(s["warnings"])) if s["warnings"] else ""
    return (
        "### 🎯 Indicateur research v3 — synthèse intégrée (V132)\n"
        f"- **{s['as_of']} · {s['PREMIUM_STATE']}** · basis {s['basis_eur_t']} €/t (z {s['basis_z']}, "
        f"{s['official_proxy_status']})\n"
        f"- ADVERSE {_v('ADVERSE_RISK')} · CBOT_SUPPORT {_v('CBOT_SUPPORT')} · PHYSICAL_TENSION "
        f"{_v('PHYSICAL_TENSION')} · courbe {_v('CURVE_TREND')}\n"
        f"- Substitution {_v('SUBSTITUTION_SUPPORT')} · météo US {_v('WEATHER_WARNING_US')}/EU "
        f"{_v('WEATHER_WARNING_EU')} · santé {_v('ACTIVE_SIGNAL_HEALTH')}\n"
        f"- **Objectif recommandé : {s['TARGET_RECOMMENDATION']}** · horizon ~"
        f"{s['HORIZON_ESTIMATE']['median_horizon_days_seasonal']} j "
        f"(demi-vie tier {s['HORIZON_ESTIMATE']['half_life_days_for_tier']} j)"
        f"{warn}\n"
        "- Diagnostics = contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.\n"
    )

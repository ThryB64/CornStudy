"""VN-A1 — Single source of truth premium : `premium_daily_head.json`.

Un seul artefact autoritatif pour « le dernier état premium ». Il consolide le SIGNAL (journal officiel),
la SYNTHÈSE de contexte (V132), la COHÉRENCE (V122) et la FRAÎCHEUR (V123), en flaggant chaque couche
auxiliaire AUTHORITATIVE / REPORTING_ONLY / LEGACY. Le head ne contient JAMAIS de décision farmer/SELL_NOW
(périmètre legacy, cf. docs/PREMIUM_SCOPE.md).

Lecture seule des artefacts déjà produits. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from mais.paths import ARTEFACTS_DIR, DATA_DIR

PREMIUM_DIR = DATA_DIR / "premium"
PREMIUM_DIR.mkdir(parents=True, exist_ok=True)
HEAD_PATH = PREMIUM_DIR / "premium_daily_head.json"

# couches et leur rôle vis-à-vis du head
LAYER_ROLES = {
    "v132/indicator_v3_latest.json": "AUTHORITATIVE_SYNTHESIS",
    "v122/v122_consistency.json": "AUTHORITATIVE_CONSISTENCY",
    "v123/v123_freshness.json": "AUTHORITATIVE_FRESHNESS",
    "v101/official_synthesis_fix.json": "REPORTING_ONLY",
    "v99/v99_synthesis_v2_latest.json": "REPORTING_ONLY",
}
LEGACY_OUT_OF_SCOPE = ["ops/daily.py (farmer pipeline)", "decision/ (SELL_NOW rules)",
                       "farmer_backtest.py", "asymmetric_module.py"]


def _read(rel) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def build_premium_head() -> dict[str, Any]:
    v132 = _read("v132/indicator_v3_latest.json")
    if v132.get("verdict") != "INDICATOR_V3_BUILT":
        return {"version": "PREMIUM-HEAD", "verdict": "NO_PREMIUM_STATE",
                "note": "Synthèse V132 indisponible ; lancer le pipeline premium."}
    cons = _read("v122/v122_consistency.json")
    fresh = _read("v123/v123_freshness.json")

    head = {
        "version": "PREMIUM-HEAD",
        "verdict": "PREMIUM_HEAD_BUILT",
        "scope": "PREMIUM_ONLY",
        "as_of": v132.get("as_of"),
        "PREMIUM_STATE": v132.get("PREMIUM_STATE"),
        "basis_z": v132.get("basis_z"),
        "basis_eur_t": v132.get("basis_eur_t"),
        "official_proxy_status": v132.get("official_proxy_status"),
        "TARGET_RECOMMENDATION": v132.get("TARGET_RECOMMENDATION"),
        "HORIZON_ESTIMATE": v132.get("HORIZON_ESTIMATE"),
        "diagnostics": v132.get("diagnostics"),
        "warnings": v132.get("warnings"),
        "consistency": {"verdict": cons.get("verdict"), "reference_date": cons.get("reference_date"),
                        "stale_layers": [s.get("layer") for s in cons.get("stale_layers", [])]},
        "freshness": {"verdict": fresh.get("verdict"), "context_lag_days": fresh.get("context_lag_days"),
                      "disabled": fresh.get("disabled_diagnostics", [])},
        "layer_roles": LAYER_ROLES,
        "legacy_out_of_scope": LEGACY_OUT_OF_SCOPE,
        "explanation": v132.get("explanation"),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    # garde-fou périmètre : aucune trace farmer/SELL_NOW dans le CONTENU d'état (hors champs méta documentant
    # justement le legacy exclu).
    content = json.dumps({k: head[k] for k in ("PREMIUM_STATE", "TARGET_RECOMMENDATION", "diagnostics",
                                               "warnings", "explanation")}).upper()
    head["scope_clean"] = not any(tok in content for tok in ("SELL_NOW", "FARMER", "VENDRE", "STOCKER"))
    HEAD_PATH.write_text(json.dumps(head, indent=2, default=str), encoding="utf-8")
    return head


def premium_head_report_block() -> str:
    h = build_premium_head()
    if h.get("verdict") != "PREMIUM_HEAD_BUILT":
        return ""
    he = h.get("HORIZON_ESTIMATE") or {}
    return (
        "### ⭐ Premium head — source unique (VN-A1)\n"
        f"- **{h['as_of']} · {h['PREMIUM_STATE']}** · basis {h['basis_eur_t']} €/t (z {h['basis_z']}, "
        f"{h['official_proxy_status']}) · objectif **{h['TARGET_RECOMMENDATION']}** · horizon ~"
        f"{he.get('estimated_days_to_z05') or he.get('median_horizon_days_seasonal')} j\n"
        f"- Cohérence {h['consistency']['verdict']} · fraîcheur {h['freshness']['verdict']} · périmètre "
        f"PREMIUM_ONLY (clean={h['scope_clean']})\n"
        "- Couches auxiliaires : REPORTING_ONLY/LEGACY explicitées. RESEARCH_ONLY_NOT_TRADING.\n"
    )

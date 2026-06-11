"""V146 — Dashboard indicateur v4 : vue consolidée premium en un markdown unique.

Assemble le head (VN-A1) + machine d'état (V139) + jalons (V147) + cycle de vie (V145) en un tableau de bord
lisible. Source unique = premium head. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mais.paths import DATA_DIR

REPORTS_DIR = DATA_DIR / "premium"


def run_v146_dashboard() -> dict[str, Any]:
    from mais.premium.forward_milestones import run_v147_milestones
    from mais.premium.head import build_premium_head
    head = build_premium_head()
    if head.get("verdict") != "PREMIUM_HEAD_BUILT":
        return {"version": "V146-DASHBOARD-V4", "verdict": "NO_PREMIUM_STATE"}
    ms = run_v147_milestones()
    he = head.get("HORIZON_ESTIMATE") or {}
    diags = head.get("diagnostics") or {}

    def _d(k):
        v = diags.get(k, {})
        return f"{v.get('value', '?')}" + ("" if v.get("fresh", True) else " (stale)")

    md = [
        f"# 📊 Dashboard indicateur premium v4 — {head['as_of']}",
        f"_Généré {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} · RESEARCH_ONLY_NOT_TRADING_", "",
        "## Signal",
        f"- **{head['PREMIUM_STATE']}** · basis {head['basis_eur_t']} €/t · z {head['basis_z']} "
        f"({head['official_proxy_status']})",
        f"- État : **{head.get('HEADLINE_STATE')}** (nature {head.get('PRIME_NATURE')}, "
        f"cycle {head.get('LIFECYCLE_STATE')})",
        f"- Objectif : **{head['TARGET_RECOMMENDATION']}** · horizon ~"
        f"{he.get('estimated_days_to_z05') or he.get('median_horizon_days_seasonal')} j",
        f"- Qualité : **{head.get('SIGNAL_QUALITY') or 'NONE'}**"
        + (f" · score composite **{head.get('COMPOSITE_SCORE')}/5** (V176, qualifie sans remplacer la "
           f"baseline z>1)" if head.get("COMPOSITE_SCORE") is not None else ""),
        "", "## Contexte",
        f"- ADVERSE_RISK {_d('ADVERSE_RISK')} · CBOT_SUPPORT {_d('CBOT_SUPPORT')} · "
        f"PHYSICAL_TENSION {_d('PHYSICAL_TENSION')}",
        f"- Substitution {_d('SUBSTITUTION_SUPPORT')} · courbe {_d('CURVE_TREND')} · santé {_d('ACTIVE_SIGNAL_HEALTH')}",
        "", "## Qualité & jalons",
        f"- Cohérence {head['consistency']['verdict']} · fraîcheur {head['freshness']['verdict']} · "
        f"scope_clean {head.get('scope_clean')}",
        f"- Diagnostics bloqués (stale) : {head['freshness'].get('disabled') or 'aucun'} · couches "
        f"reporting-only en retard : {head['consistency'].get('stale_reporting_only_layers') or 'aucune'}",
        f"- Jours officiels {ms['n_official_days']} · prochain jalon {ms['next_milestone']} "
        f"({ms['next_meaning']}) · z rolling officiel {ms['rolling_official_z_available']}",
        "", f"_Warnings : {head.get('warnings')}_", "",
        "Source unique : data/premium/premium_daily_head.json. RESEARCH_ONLY_NOT_TRADING.",
    ]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "dashboard_v4.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    out = {"version": "V146-DASHBOARD-V4", "verdict": "DASHBOARD_V4_BUILT", "as_of": head["as_of"],
           "headline_state": head.get("HEADLINE_STATE"), "path": str(REPORTS_DIR / "dashboard_v4.md"),
           "status": "RESEARCH_ONLY_NOT_TRADING"}
    return out

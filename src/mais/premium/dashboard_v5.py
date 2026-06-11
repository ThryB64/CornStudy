"""V180 — Dashboard indicateur v5 : la vue consolidée de la phase forward.

Étend la v4 (intacte) avec ce que la phase de validation forward doit montrer chaque jour :
compression réalisée du signal actif (V124), baseline z>1 vs signal confirmé z>=1.2 (V131),
ratio MATIF blé/maïs, météo US/EU, état de la validation proxy↔officiel (V178), re-runs
data-gated (V177) et jalons 40/90 j (V147). Source unique = premium head ; tout le reste est
lu en LECTURE SEULE depuis les artefacts des couches. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR, DATA_DIR
from mais.paths import PROJECT_ROOT as ROOT

REPORTS_DIR = DATA_DIR / "premium"
MATIF_HISTORY = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
CURVE_HISTORY = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
V178_ARTEFACT = ARTEFACTS_DIR / "v178" / "v178_official_validation.json"
V177_ARTEFACT = ARTEFACTS_DIR / "v177" / "data_gated_status.json"
V124_ARTEFACT = ARTEFACTS_DIR / "v124" / "v124_active_monitoring.json"

CONFIRMED_Z = 1.2  # V131 — seuil de CONFIRMATION, jamais un remplacement de la baseline z>1


def _read_json(path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _latest_parquet_value(path, col: str):
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if col not in df.columns or df.empty:
        return None
    return df.sort_values("price_date")[col].iloc[-1]


def baseline_vs_confirmed(z: float | None) -> str:
    if z is None:
        return "z indisponible"
    base = "BASELINE z>1 ACTIVE" if z >= 1.0 else "sous baseline"
    conf = "CONFIRMÉ z≥1.2" if z >= CONFIRMED_Z else "non confirmé (<1.2)"
    return f"{base} · {conf}"


def run_v180_dashboard() -> dict[str, Any]:
    from mais.premium.forward_milestones import run_v147_milestones
    from mais.premium.head import build_premium_head
    head = build_premium_head()
    if head.get("verdict") != "PREMIUM_HEAD_BUILT":
        return {"version": "V180-DASHBOARD-V5", "verdict": "NO_PREMIUM_STATE"}
    ms = run_v147_milestones()
    diags = head.get("diagnostics") or {}
    he = head.get("HORIZON_ESTIMATE") or {}
    mon = _read_json(V124_ARTEFACT)
    v178 = _read_json(V178_ARTEFACT)
    v177 = _read_json(V177_ARTEFACT)

    def _d(k):
        v = diags.get(k, {})
        return f"{v.get('value', '?')}" + ("" if v.get("fresh", True) else " (stale)")

    z = head.get("basis_z")
    matif = _latest_parquet_value(MATIF_HISTORY, "ratio")
    spread = _latest_parquet_value(CURVE_HISTORY, "front_next_spread")
    shape = _latest_parquet_value(CURVE_HISTORY, "curve_shape")
    gates = {g.get("rerun"): f"{g.get('status')} {g.get('n')}/{g.get('gate')}"
             for g in v177.get("gates", [])}

    md = [
        f"# 📊 Dashboard indicateur premium v5 — {head['as_of']}",
        f"_Généré {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} · "
        "RESEARCH_ONLY_NOT_TRADING_", "",
        "## Signal",
        f"- **{head['PREMIUM_STATE']}** · basis {head['basis_eur_t']} €/t · z {z} "
        f"({head['official_proxy_status']})",
        f"- Baseline vs confirmé : **{baseline_vs_confirmed(z)}** · qualité "
        f"**{head.get('SIGNAL_QUALITY') or 'NONE'}** · score composite "
        f"**{head.get('COMPOSITE_SCORE')}/5** (V176, qualifie sans remplacer la baseline)",
        f"- Machine d'état : **{head.get('HEADLINE_STATE')}** · nature "
        f"**{head.get('PRIME_NATURE')}** · cycle **{head.get('LIFECYCLE_STATE')}**",
        f"- Objectif **{head['TARGET_RECOMMENDATION']}** · horizon ~"
        f"{he.get('estimated_days_to_z05') or he.get('median_horizon_days_seasonal')} j", "",
        "## Signal actif (V124/V179)",
        f"- Entrée {mon.get('entry_date')} (z {mon.get('entry_z')}) · {mon.get('days_since_entry')} j · "
        f"statut **{mon.get('status')}**",
        f"- Compression réalisée **{mon.get('compression_realized_eur_t')} €/t** · MFE "
        f"{mon.get('mfe_eur_t')} · MAE {mon.get('mae_eur_t')} · distance z→0.5 : "
        f"{mon.get('distance_to_z05')}", "",
        "## Contexte marché",
        f"- Courbe EMA : {_d('CURVE_TREND')} (spread front-next {spread} €/t, {shape})",
        f"- MATIF blé/maïs : {round(float(matif), 3) if matif is not None else 'n/a'} · "
        f"substitution {_d('SUBSTITUTION_SUPPORT')}",
        f"- CBOT_SUPPORT {_d('CBOT_SUPPORT')} · ADVERSE_RISK {_d('ADVERSE_RISK')} · "
        f"PHYSICAL_TENSION {_d('PHYSICAL_TENSION')}",
        f"- Météo US {_d('WEATHER_WARNING_US')} · Météo EU {_d('WEATHER_WARNING_EU')}", "",
        "## Officiel / proxy & jalons",
        f"- Jours officiels **{ms['n_official_days']}** · prochain jalon **{ms['next_milestone']}** "
        f"({ms['next_meaning']}) · z rolling officiel {ms['rolling_official_z_available']}",
        f"- Validation V178 (40 j) : **{v178.get('verdict', 'n/a')}** · paires proxy↔officiel "
        f"{v178.get('n_pairs', 0)}",
        f"- Re-runs data-gated (V177) : {gates or 'n/a'}", "",
        "## Santé du système",
        f"- Cohérence {head['consistency']['verdict']} · fraîcheur {head['freshness']['verdict']} · "
        f"scope_clean {head.get('scope_clean')}",
        f"- Diagnostics bloqués : {head['freshness'].get('disabled') or 'aucun'}",
        f"- Warnings : {head.get('warnings') or 'aucun'}", "",
        "Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. "
        "RESEARCH_ONLY_NOT_TRADING.",
    ]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "dashboard_v5.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"version": "V180-DASHBOARD-V5", "verdict": "DASHBOARD_V5_BUILT",
            "as_of": head["as_of"], "headline_state": head.get("HEADLINE_STATE"),
            "active_status": mon.get("status"), "path": str(REPORTS_DIR / "dashboard_v5.md"),
            "status": "RESEARCH_ONLY_NOT_TRADING"}

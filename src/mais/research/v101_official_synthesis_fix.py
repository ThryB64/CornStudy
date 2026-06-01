"""V101 — Fix de la source de synthèse LIVE : utiliser le journal officiel forward, pas la fin du master.

Bug constaté : `v99_synthesis_v2_latest.json` affichait `as_of=2025-07-25 / UNCERTAIN_ROLL` (dernière date du
MASTER de features) alors que le journal officiel forward (V27) a déjà 2026-06-01 / SHORT_PREMIUM_EXTREME.
Cause : la synthèse calculait tout depuis le master, dont les features (corn/COT/météo) s'arrêtent mi-2025.

Correctif : la synthèse LIVE prend le SIGNAL du dernier jour du journal officiel (autoritatif, récent) et
calcule les diagnostics de CONTEXTE à la dernière date de features disponible, en FLAGGANT explicitement le
décalage (context_as_of, lag). On n'affiche plus l'ancien UNCERTAIN_ROLL comme état live. Si aucun journal
officiel, on retombe proprement sur la synthèse master (proxy) avec warning.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Baseline figée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V101_DIR = ARTEFACTS_DIR / "v101"
V101_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
V99_LATEST = ARTEFACTS_DIR / "v99" / "v99_synthesis_v2_latest.json"


def _latest_official() -> dict[str, Any] | None:
    if not OFFICIAL_JOURNAL.exists():
        return None
    j = pd.read_parquet(OFFICIAL_JOURNAL)
    if len(j) == 0 or "price_date" not in j.columns:
        return None
    j = j.sort_values("price_date")
    row = j.iloc[-1]
    return {
        "price_date": str(pd.Timestamp(row["price_date"]).date()),
        "signal_tier": row.get("signal_tier"),
        "basis_official_eur_t": float(row["basis_official_eur_t"]) if pd.notna(row.get("basis_official_eur_t")) else None,
        "basis_z_used": float(row["basis_z_used"]) if pd.notna(row.get("basis_z_used")) else None,
        "z_source": row.get("z_source"),
        "cbot_eur_t": float(row["cbot_eur_t"]) if pd.notna(row.get("cbot_eur_t")) else None,
        "eurusd": float(row["eurusd"]) if pd.notna(row.get("eurusd")) else None,
        "objective_prudent": row.get("objective_prudent"),
        "objective_full": row.get("objective_full"),
        "median_horizon_days": int(row["median_horizon_days"]) if pd.notna(row.get("median_horizon_days")) else None,
        "curve_shape": row.get("curve_shape"),
        "warnings": row.get("warnings"),
    }


def _context_at_last_feature_date(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v54_physical_tension import compute_physical_tension
    from mais.research.v56_target_recommendation import recommend_target
    from mais.research.v86_cbot_support_v2 import compute_cbot_support_v2
    ar = compute_adverse_risk(df)["adverse_risk"]
    pt = compute_physical_tension(df)["physical_tension"]
    cs2 = compute_cbot_support_v2(df)["cbot_support_v2"]
    ctx_date = df.index[-1]
    a = str(ar.iloc[-1]) if len(ar) else "NO_SIGNAL"
    c = str(cs2.iloc[-1]) if len(cs2) else "NO_SIGNAL"
    p = str(pt.iloc[-1]) if len(pt) else "NO_SIGNAL"
    return {"context_as_of": str(ctx_date.date()), "adverse_risk": a,
            "cbot_support_v2": c, "physical_tension": p,
            "recommended_target_ctx": recommend_target(a, c, p)}


def run_v101_official_synthesis(df: pd.DataFrame, write_v99_latest: bool = True) -> dict[str, Any]:
    assert_no_holdout(df)
    official = _latest_official()
    ctx = _context_at_last_feature_date(df)

    if official is None:
        out = {"version": "V101-OFFICIAL-SYNTHESIS", "verdict": "NO_OFFICIAL_JOURNAL_FALLBACK_PROXY",
               "note": "Aucun journal officiel ; utiliser la synthèse master/proxy (V99) avec warning.",
               "context": ctx, "status": "RESEARCH_ONLY_NOT_TRADING"}
        (V101_DIR / "official_synthesis_fix.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out

    lag_days = (pd.Timestamp(official["price_date"]) - pd.Timestamp(ctx["context_as_of"])).days
    out = {
        "version": "V101-OFFICIAL-SYNTHESIS",
        "verdict": "OFFICIAL_SYNTHESIS_FIXED",
        "as_of": official["price_date"],
        "source": "official_forward_journal",
        "signal_tier": official["signal_tier"],
        "basis_official_eur_t": official["basis_official_eur_t"],
        "basis_z_used": official["basis_z_used"],
        "z_source": official["z_source"],
        "cbot_eur_t": official["cbot_eur_t"],
        "eurusd": official["eurusd"],
        "objective_prudent": official["objective_prudent"],
        "objective_full": official["objective_full"],
        "median_horizon_days": official["median_horizon_days"],
        "curve_shape": official["curve_shape"],
        "official_warnings": official["warnings"],
        # contexte (diagnostics) calculé à la dernière date de FEATURES, flaggé
        "context_as_of": ctx["context_as_of"],
        "context_lag_days": int(lag_days),
        "context_is_stale": bool(lag_days > 10),
        "adverse_risk_ctx": ctx["adverse_risk"],
        "cbot_support_v2_ctx": ctx["cbot_support_v2"],
        "physical_tension_ctx": ctx["physical_tension"],
        "recommended_target_ctx": ctx["recommended_target_ctx"],
        "data_lag_warning": (
            f"Signal officiel à {official['price_date']} mais features (CBOT/COT/météo) arrêtées à "
            f"{ctx['context_as_of']} ({lag_days} j de retard) -> diagnostics de CONTEXTE indicatifs, à "
            "rafraîchir quand le master sera ré-collecté. Le SIGNAL (tier/basis_z) vient de l'officiel."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V101_DIR / "official_synthesis_fix.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    # corrige l'artefact v99 stale : on y écrit l'état live officiel
    if write_v99_latest:
        V99_LATEST.parent.mkdir(parents=True, exist_ok=True)
        fixed = {"version": "V99-SYNTHESIS-V2", "verdict": "SYNTHESIS_V2_BUILT_OFFICIAL_LIVE",
                 "as_of": official["price_date"], "source": "official_forward_journal",
                 "signal_tier": official["signal_tier"], "basis_z": official["basis_z_used"],
                 "basis_eur_t": official["basis_official_eur_t"],
                 "adverse_risk": ctx["adverse_risk"], "cbot_support_v2": ctx["cbot_support_v2"],
                 "physical_tension": ctx["physical_tension"],
                 "recommended_target": ctx["recommended_target_ctx"],
                 "context_as_of": ctx["context_as_of"], "context_lag_days": int(lag_days),
                 "data_lag_warning": out["data_lag_warning"],
                 "status": "RESEARCH_ONLY_NOT_TRADING"}
        V99_LATEST.write_text(json.dumps(fixed, indent=2, default=str), encoding="utf-8")
    return out


def official_live_report_block(df: pd.DataFrame) -> str:
    s = run_v101_official_synthesis(df, write_v99_latest=False)
    if s.get("verdict") != "OFFICIAL_SYNTHESIS_FIXED":
        return ""
    return (
        "### État LIVE officiel (V101 — source = journal officiel forward)\n"
        f"- **{s['as_of']}** · Signal **{s['signal_tier']}** · basis officiel {s['basis_official_eur_t']} €/t "
        f"(z={s['basis_z_used']}, {s['z_source']})\n"
        f"- Objectif : prudent {s['objective_prudent']} / complet {s['objective_full']} · horizon médian "
        f"{s['median_horizon_days']} j · courbe {s['curve_shape']}\n"
        f"- Contexte (au {s['context_as_of']}, retard {s['context_lag_days']} j) : ADVERSE_RISK "
        f"{s['adverse_risk_ctx']} · CBOT_SUPPORT v2 {s['cbot_support_v2_ctx']} · PHYS_TENSION "
        f"{s['physical_tension_ctx']} → objectif suggéré {s['recommended_target_ctx']}\n"
        f"- ⚠️ {s['data_lag_warning']}\n"
        "- RESEARCH_ONLY_NOT_TRADING.\n"
    )

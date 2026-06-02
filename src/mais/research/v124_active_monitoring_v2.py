"""V124 — Suivi du signal actif v2 : santé du signal vivant avec paliers 10/20/30 j.

Étend V102 (qu'on RÉUTILISE pour isoler l'épisode courant) en explicitant des statuts plus fins, calibrés
sur la signature ADVERSE de V82 (MFE faible + durée longue) et sur la demi-vie ≈17 j (V120/V121), PAS
optimisés sur le PnL :

  - TARGET_HIT      : objectif atteint (z ≤ 0.5 prudent, ou z ≤ 0 complet)
  - HEALTHY         : compression nette en cours, dans les temps
  - SLOW            : ≥10 j, pas encore de compression nette (en retard sur la demi-vie)
  - DELAYED         : ≥30 j sans compression (au-delà de l'horizon médian saisonnier)
  - ADVERSE_LIKE    : ≥20 j avec MFE < 5 €/t (signature ADVERSE V82) -> prudence, ne pas renforcer
  - ACTIVE_EARLY    : <10 j, trop tôt pour juger

Lecture seule du journal officiel (révisé V122). Descriptif, contexte, jamais un veto.
Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V124_DIR = ARTEFACTS_DIR / "v124"
V124_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
MFE_ADVERSE_THRESHOLD = 5.0   # €/t : MFE en deçà = signature ADVERSE (V82)
DAY_EARLY, DAY_SLOW, DAY_ADVERSE, DAY_DELAYED = 10, 10, 20, 30


def _classify(days: int, compression: float, mfe: float, cur_z: float) -> str:
    if cur_z <= 0.0:
        return "TARGET_HIT_z0"
    if cur_z <= 0.5:
        return "TARGET_HIT_z05"
    if days >= DAY_DELAYED and compression <= 0:
        return "DELAYED"
    if days >= DAY_ADVERSE and mfe < MFE_ADVERSE_THRESHOLD:
        return "ADVERSE_LIKE"
    if days >= DAY_SLOW and compression <= 0:
        return "SLOW"
    if compression > 0:
        return "HEALTHY"
    return "ACTIVE_EARLY"


def monitor_active_signal_v2() -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {"version": "V124-MONITORING-V2", "verdict": "NO_OFFICIAL_JOURNAL"}
    from mais.research.v102_active_signal_monitoring import _current_episode
    j = pd.read_parquet(OFFICIAL_JOURNAL)
    if len(j) == 0 or "signal_tier" not in j.columns:
        return {"version": "V124-MONITORING-V2", "verdict": "EMPTY_JOURNAL"}
    ep = _current_episode(j)
    if len(ep) == 0:
        return {"version": "V124-MONITORING-V2", "verdict": "NO_ACTIVE_SIGNAL"}

    basis = pd.to_numeric(ep["basis_official_eur_t"], errors="coerce")
    z = pd.to_numeric(ep["basis_z_used"], errors="coerce")
    entry_basis, cur_basis = float(basis.iloc[0]), float(basis.iloc[-1])
    entry_z, cur_z = float(z.iloc[0]), float(z.iloc[-1])
    entry_date = pd.Timestamp(ep["price_date"].iloc[0])
    cur_date = pd.Timestamp(ep["price_date"].iloc[-1])
    days = int((cur_date - entry_date).days)

    compression = round(entry_basis - cur_basis, 2)
    mfe = round(entry_basis - float(basis.min()), 2)
    mae = round(float(basis.max()) - entry_basis, 2)
    dist_z05 = round(cur_z - 0.5, 3)
    dist_z0 = round(cur_z - 0.0, 3)
    horizon = int(ep["median_horizon_days"].iloc[-1]) if "median_horizon_days" in ep.columns and pd.notna(
        ep["median_horizon_days"].iloc[-1]) else None
    status = _classify(days, compression, mfe, cur_z)

    out = {
        "version": "V124-MONITORING-V2",
        "verdict": "ACTIVE_MONITORING_READY",
        "entry_date": str(entry_date.date()),
        "current_date": str(cur_date.date()),
        "days_since_entry": days,
        "n_official_days_in_episode": int(len(ep)),
        "entry_tier": ep["signal_tier"].iloc[0],
        "current_tier": ep["signal_tier"].iloc[-1],
        "entry_z": round(entry_z, 3),
        "current_z": round(cur_z, 3),
        "entry_basis_eur_t": round(entry_basis, 2),
        "current_basis_eur_t": round(cur_basis, 2),
        "compression_realized_eur_t": compression,
        "mfe_eur_t": mfe,
        "mae_eur_t": mae,
        "distance_to_z05": dist_z05,
        "distance_to_z0": dist_z0,
        "median_horizon_days": horizon,
        "status": status,
        "thresholds": {"early_lt": DAY_EARLY, "slow_ge": DAY_SLOW, "adverse_ge": DAY_ADVERSE,
                       "delayed_ge": DAY_DELAYED, "mfe_adverse_lt": MFE_ADVERSE_THRESHOLD},
        "interpretation": (
            f"Signal actif {days} j ({len(ep)} jours officiels). Compression {compression} €/t, MFE {mfe}, "
            f"MAE {mae}, z {round(entry_z,3)}→{round(cur_z,3)}. Statut **{status}** "
            f"(horizon médian saisonnier {horizon} j). "
            + {"DELAYED": "Au-delà de 30 j sans compression : la prime ne réagit pas, prudence (objectif z→0.5).",
               "ADVERSE_LIKE": "Signature ADVERSE V82 (≥20 j, MFE<5) : ne pas renforcer, viser z→0.5.",
               "SLOW": "≥10 j sans compression nette : en retard sur la demi-vie ≈17 j, surveiller.",
               "HEALTHY": "Compression en cours, dans les temps.",
               "TARGET_HIT_z05": "Objectif prudent z→0.5 atteint.",
               "TARGET_HIT_z0": "Objectif complet z→0 atteint.",
               "ACTIVE_EARLY": "Trop tôt (<10 j) pour juger."}.get(status, "")),
        "note": "Réutilise l'isolement d'épisode V102. Paliers calibrés sur V82/V120, pas sur le PnL. "
                "Descriptif, jamais un veto. Se densifie avec le forward.",
        "status_research": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V124_DIR / "v124_active_monitoring.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def active_monitoring_v2_report_block() -> str:
    s = monitor_active_signal_v2()
    if s.get("verdict") != "ACTIVE_MONITORING_READY":
        return ""
    return (
        "### Santé du signal actif v2 (V124 — paliers 10/20/30 j)\n"
        f"- Entrée {s['entry_date']} ({s['entry_tier']}) → {s['current_date']} : **{s['days_since_entry']} j** "
        f"(horizon médian {s['median_horizon_days']} j)\n"
        f"- z {s['entry_z']}→{s['current_z']} · compression {s['compression_realized_eur_t']} · "
        f"MFE {s['mfe_eur_t']} · MAE {s['mae_eur_t']} · dist z→0.5 {s['distance_to_z05']}\n"
        f"- Statut **{s['status']}**. {s['interpretation'].split('. ', 2)[-1]}\n"
        "- Contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.\n"
    )

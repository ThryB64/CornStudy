"""V102 — Suivi dynamique d'un signal ACTIF : ne pas seulement signaler à l'entrée, suivre sa vie.

V82 a montré que les ADVERSE ont une signature post-entrée : MFE faible et durée longue. Donc, pour un signal
ouvert (journal officiel forward), on suit son évolution : jours depuis l'entrée, compression réalisée,
MFE/MAE, distance à z→0.5 / z→0, et un STATUT de santé (healthy / slow / warning / adverse-like / objectif
atteint). But : dire « le signal est actif mais ne se comporte pas comme les gagnants historiques ».

Lecture seule du journal officiel. Descriptif, baseline figée, jamais un veto.
Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V102_DIR = ARTEFACTS_DIR / "v102"
V102_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
SIGNAL_TIERS = ("SHORT_PREMIUM_MODERATE", "SHORT_PREMIUM_STRONG", "SHORT_PREMIUM_EXTREME")


def _current_episode(j: pd.DataFrame) -> pd.DataFrame:
    """Dernier RUN consécutif de jours avec un signal actif (tier SHORT_PREMIUM_*)."""
    j = j.sort_values("price_date").reset_index(drop=True)
    j["is_signal"] = j["signal_tier"].isin(SIGNAL_TIERS)
    if not j["is_signal"].iloc[-1]:
        return j.iloc[0:0]
    # remonter tant que c'est un signal
    start = len(j) - 1
    while start - 1 >= 0 and bool(j["is_signal"].iloc[start - 1]):
        start -= 1
    return j.iloc[start:]


def monitor_active_signal() -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {"verdict": "NO_OFFICIAL_JOURNAL"}
    j = pd.read_parquet(OFFICIAL_JOURNAL)
    if len(j) == 0 or "signal_tier" not in j.columns:
        return {"verdict": "EMPTY_JOURNAL"}
    ep = _current_episode(j)
    if len(ep) == 0:
        return {"verdict": "NO_ACTIVE_SIGNAL", "last_date": str(pd.Timestamp(
            j.sort_values("price_date")["price_date"].iloc[-1]).date())}

    basis = pd.to_numeric(ep["basis_official_eur_t"], errors="coerce")
    z = pd.to_numeric(ep["basis_z_used"], errors="coerce")
    entry_basis, cur_basis = float(basis.iloc[0]), float(basis.iloc[-1])
    entry_z, cur_z = float(z.iloc[0]), float(z.iloc[-1])
    entry_date = pd.Timestamp(ep["price_date"].iloc[0])
    cur_date = pd.Timestamp(ep["price_date"].iloc[-1])
    days = int((cur_date - entry_date).days)

    compression = round(entry_basis - cur_basis, 2)          # >0 = la prime se comprime (favorable au short)
    mfe = round(entry_basis - float(basis.min()), 2)         # meilleure compression atteinte
    mae = round(float(basis.max()) - entry_basis, 2)         # pire écartement (adverse)
    dist_z05 = round(cur_z - 0.5, 3)
    dist_z0 = round(cur_z - 0.0, 3)

    if cur_z <= 0.0:
        status = "OBJECTIVE_FULL_REACHED_z0"
    elif cur_z <= 0.5:
        status = "OBJECTIVE_PRUDENT_REACHED_z05"
    elif days >= 30 and compression <= 0:
        status = "WARNING_COMPRESSION_DELAYED"
    elif days >= 20 and mfe < 5:
        status = "ADVERSE_LIKE_LOW_MFE_LONG"          # signature ADVERSE V82
    elif compression > 0:
        status = "HEALTHY_COMPRESSING"
    else:
        status = "ACTIVE_EARLY_MONITORING"

    out = {
        "version": "V102-ACTIVE-MONITORING",
        "verdict": "ACTIVE_SIGNAL_MONITORED",
        "entry_date": str(entry_date.date()),
        "current_date": str(cur_date.date()),
        "days_since_entry": days,
        "n_official_days_in_episode": int(len(ep)),
        "entry_tier": ep["signal_tier"].iloc[0],
        "current_tier": ep["signal_tier"].iloc[-1],
        "entry_basis_eur_t": round(entry_basis, 2),
        "current_basis_eur_t": round(cur_basis, 2),
        "entry_z": round(entry_z, 3),
        "current_z": round(cur_z, 3),
        "compression_realized_eur_t": compression,
        "mfe_eur_t": mfe,
        "mae_eur_t": mae,
        "distance_to_z05": dist_z05,
        "distance_to_z0": dist_z0,
        "status": status,
        "interpretation": (
            f"Signal actif depuis {days} j ({len(ep)} jours officiels). Compression réalisée "
            f"{compression} €/t, MFE {mfe}, MAE {mae}. Distance z→0.5 {dist_z05}, z→0 {dist_z0}. Statut "
            f"**{status}**. Rappel V82 : un ADVERSE traîne (>20j) avec MFE faible (<5) -> si le statut passe "
            "ADVERSE_LIKE, prudence (objectif z→0.5), ne pas renforcer. Jamais un veto."),
        "note": "Lecture seule du journal officiel ; se densifie avec l'accumulation forward.",
        "status_research": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V102_DIR / "v102_active_signal.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def active_signal_report_block() -> str:
    s = monitor_active_signal()
    if s.get("verdict") != "ACTIVE_SIGNAL_MONITORED":
        return ""
    return (
        "### Suivi du signal ACTIF (V102 — monitoring dynamique)\n"
        f"- Entrée {s['entry_date']} ({s['entry_tier']}) → {s['current_date']} : **{s['days_since_entry']} j**, "
        f"{s['n_official_days_in_episode']} jours officiels\n"
        f"- basis {s['entry_basis_eur_t']} → {s['current_basis_eur_t']} €/t · z {s['entry_z']} → {s['current_z']} · "
        f"compression {s['compression_realized_eur_t']} · MFE {s['mfe_eur_t']} · MAE {s['mae_eur_t']}\n"
        f"- Distance z→0.5 {s['distance_to_z05']} · z→0 {s['distance_to_z0']} · statut **{s['status']}**\n"
        "- RESEARCH_ONLY_NOT_TRADING.\n"
    )

"""V103 — Dashboard proxy vs officiel (validation continue de la source EMA).

Combine (1) la validation HISTORIQUE proxy↔officiel (corr ~0.94, MAE ~37 €/t, verdict PROXY_FORBIDDEN sur le
NIVEAU mais z-score utilisable), (2) la trajectoire du journal officiel forward (V27), (3) un tracker de
milestones (10/40/90 j) pour le passage research→paper. Honnête : la comparaison forward proxy↔officiel sur
les MÊMES dates est PENDING tant que le master de features n'atteint pas les dates forward (il s'arrête mi-2025).

Lecture seule. Descriptif, `RESEARCH_ONLY_NOT_TRADING`.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V103_DIR = ARTEFACTS_DIR / "v103"
V103_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
PROXY_AUDIT = ARTEFACTS_DIR / "proxy_vs_real_ema_report.json"
DASHBOARD_MD = ROOT / "docs" / "PROXY_OFFICIAL_DASHBOARD.md"
MILESTONES = (10, 40, 90, 180, 365)


def _historical() -> dict[str, Any]:
    if not PROXY_AUDIT.exists():
        return {}
    d = json.loads(PROXY_AUDIT.read_text(encoding="utf-8"))
    return {k: d.get(k) for k in ("correlation", "mae_eur_t", "rmse_eur_t", "verdict")}


def run_v103_dashboard() -> dict[str, Any]:
    hist = _historical()
    if not OFFICIAL_JOURNAL.exists():
        fwd = {"n_days": 0}
    else:
        j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
        sig = j[j["signal_tier"].astype(str).str.startswith("SHORT_PREMIUM")]
        fwd = {
            "n_days": int(len(j)),
            "date_range": [str(pd.Timestamp(j["price_date"].iloc[0]).date()),
                           str(pd.Timestamp(j["price_date"].iloc[-1]).date())] if len(j) else None,
            "n_signal_days": int(len(sig)),
            "basis_official_range": [round(float(j["basis_official_eur_t"].min()), 1),
                                     round(float(j["basis_official_eur_t"].max()), 1)] if len(j) else None,
            "z_used_range": [round(float(j["basis_z_used"].min()), 2),
                             round(float(j["basis_z_used"].max()), 2)] if len(j) else None,
            "z_source_modes": j["z_source"].value_counts().to_dict() if "z_source" in j else {},
        }

    n = fwd["n_days"]
    next_ms = next((m for m in MILESTONES if n < m), None)
    milestones = {str(m): ("reached" if n >= m else "pending") for m in MILESTONES}

    out = {
        "version": "V103-PROXY-OFFICIAL-DASHBOARD",
        "historical_proxy_vs_official": hist,
        "historical_reading": (
            "corr proxy↔officiel ~0.94 mais MAE ~37 €/t -> le NIVEAU proxy est interdit en absolu "
            "(PROXY_FORBIDDEN) ; en revanche le z-score (relatif, trailing) reste exploitable, d'où "
            "z_source=proxy_implied dans le journal officiel."),
        "forward_official": fwd,
        "forward_overlap_status": "FORWARD_OVERLAP_PENDING (master features s'arrête mi-2025, "
                                  "pas de proxy parallèle sur les dates forward 2026)",
        "milestones": milestones,
        "days_accumulated": n,
        "next_milestone": next_ms,
        "verdict": "PROXY_RESEARCH_ONLY",
        "interpretation": (
            f"{n} jours officiels accumulés ; prochain palier {next_ms} j. La validation forward "
            "proxy↔officiel sur dates communes attend soit la ré-collecte du master jusqu'en 2026, soit "
            "l'accumulation parallèle d'un proxy live. D'ici là : niveau = officiel uniquement, z = "
            "proxy_implied (acceptable). Statut PROXY_RESEARCH_ONLY."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }

    lines = ["# Dashboard proxy vs officiel (V103)", "",
             "Validation continue de la source EMA. `RESEARCH_ONLY_NOT_TRADING`.", "",
             "## Historique (proxy Barchart vs EMA officiel, overlap 2010-2022)",
             f"- corrélation {hist.get('correlation')} · MAE {hist.get('mae_eur_t')} €/t · "
             f"verdict **{hist.get('verdict')}**",
             "- Lecture : niveau proxy interdit en absolu ; z-score relatif utilisable.", "",
             "## Forward officiel (journal V27)",
             f"- jours : **{n}** · plage {fwd.get('date_range')} · signaux {fwd.get('n_signal_days')}",
             f"- basis officiel {fwd.get('basis_official_range')} €/t · z {fwd.get('z_used_range')} · "
             f"source z {fwd.get('z_source_modes')}", "",
             "## Milestones research→paper",
             *[f"- {m} j : {st}" for m, st in milestones.items()],
             "", f"Prochain palier : **{next_ms} j**. Statut : **PROXY_RESEARCH_ONLY**.",
             "", "## Limite", "Comparaison forward proxy↔officiel sur dates communes = PENDING "
             "(master features arrêté mi-2025). À activer dès ré-collecte ou proxy live parallèle."]
    DASHBOARD_MD.write_text("\n".join(lines), encoding="utf-8")
    (V103_DIR / "v103_dashboard.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

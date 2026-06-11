"""V174 — Audit de la règle FX : eurusd journalisé (yfinance) vs taux de référence BCE horodaté.

Pour chaque jour FINAL/REVISED du journal officiel, on reconstruit cbot_eur_t avec :
  (a) l'eurusd journalisé (règle actuelle) ;
  (b) le taux BCE du même jour (publié 14:15 CET, donc connu avant le DSP 18:30 CET — pas de fuite).
On compare aux cbot_eur_t écrits dans le journal et l'écart (a)-(b). GO si la règle BCE est documentable
avec un écart borné ; la BCE devient alors la règle de référence horodatée recommandée.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.audit.data_truth import BU_PER_TONNE
from mais.collect.ecb_fx_collector import load_ecb_eurusd
from mais.paths import ARTEFACTS_DIR
from mais.research import v27_official_forward as v27

AUDIT_DIR = ARTEFACTS_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def reconstruct_cbot_eur_t(cents_bu: float, eurusd: float) -> float:
    """cents/bu -> EUR/t : (cents/100) USD/bu * bu/t / (USD par EUR)."""
    return (cents_bu / 100.0) * BU_PER_TONNE / eurusd


def run_fx_bce_audit() -> dict[str, Any]:
    if not v27.JOURNAL_JSONL.exists():
        return {"audit": "fx_bce", "verdict": "SKIP", "reason": "journal absent"}
    j = v27.load_forward_journal(final_only=True)
    ecb = load_ecb_eurusd()
    if j.empty or ecb.empty:
        return {"audit": "fx_bce", "verdict": "SKIP",
                "reason": "journal vide ou archive BCE absente (fetch_ecb_eurusd)"}
    j = j.copy()
    j["price_date"] = j["price_date"].astype(str)
    m = j.merge(ecb.rename(columns={"Date": "price_date"}), on="price_date", how="inner")
    if m.empty:
        return {"audit": "fx_bce", "verdict": "SKIP", "reason": "aucun jour commun journal/BCE"}

    rows = []
    for _, r in m.iterrows():
        cents = float(r["cbot_cents_bu"])
        rec_journal = reconstruct_cbot_eur_t(cents, float(r["eurusd"]))
        rec_ecb = reconstruct_cbot_eur_t(cents, float(r["eurusd_ecb"]))
        written = float(r["cbot_eur_t"])
        rows.append({
            "price_date": r["price_date"],
            "eurusd_journal": round(float(r["eurusd"]), 4),
            "eurusd_ecb": round(float(r["eurusd_ecb"]), 4),
            "abs_err_journal_rule": round(abs(rec_journal - written), 4),
            "abs_err_ecb_rule": round(abs(rec_ecb - written), 4),
            "ecb_vs_journal_eur_t": round(rec_ecb - rec_journal, 4),
        })
    df = pd.DataFrame(rows)
    max_dev = float(df["ecb_vs_journal_eur_t"].abs().max())
    out = {
        "audit": "fx_bce",
        "verdict": "PASS" if max_dev <= 1.0 else "WARN",
        "n_days_compared": int(len(df)),
        "max_abs_err_journal_rule_eur_t": float(df["abs_err_journal_rule"].max()),
        "mean_abs_dev_ecb_vs_journal_eur_t": round(float(df["ecb_vs_journal_eur_t"].abs().mean()), 4),
        "max_abs_dev_ecb_vs_journal_eur_t": round(max_dev, 4),
        "rule": ("Taux BCE D (14:15 CET) utilisable pour le settlement D (DSP 18:30 CET) sans fuite ; "
                 "recommandé comme règle horodatée de référence, l'eurusd yfinance reste le fallback."),
        "per_day": rows,
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (AUDIT_DIR / "fx_bce_report.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

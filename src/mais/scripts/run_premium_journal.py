"""V14-03 — Journal paper-trading opérationnel (cron-ready, append-only, sans exécution réelle).

Usage cron (jours ouvrés) :
    venv/bin/python -m mais.scripts.run_premium_journal

Étapes : append des nouveaux signaux short-only, évaluation des lignes arrivées à maturité, rapport.
Aucune position réelle. Statut RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from mais.research.v14_short_indicator import (  # noqa: E402
    _backtest_short,
    assemble_short_indicator,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

JOURNAL = ROOT / "data" / "reports" / "premium_journal.parquet"


def update_journal() -> dict:
    df = filter_out_holdout(load_master_dataset())
    sig = assemble_short_indicator(df)
    actionable = sig[sig["signal"] == "SHORT_PREMIUM"].copy()
    actionable = actionable.reset_index().rename(columns={"index": "date", actionable.index.name or "index": "date"})
    if "date" not in actionable.columns:
        actionable.insert(0, "date", sig[sig["signal"] == "SHORT_PREMIUM"].index)
    actionable["data_source_flag"] = "barchart_proxy_exploratory"
    actionable["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    actionable["exit_rule"] = "z0_max90"

    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    if JOURNAL.exists():
        existing = pd.read_parquet(JOURNAL)
        known = set(pd.to_datetime(existing["date"]))
        fresh = actionable[~pd.to_datetime(actionable["date"]).isin(known)]
        combined = pd.concat([existing, fresh], ignore_index=True)
        n_added = int(len(fresh))
    else:
        combined = actionable
        n_added = int(len(actionable))
    combined.to_parquet(JOURNAL, index=False)

    # évaluation des trades mûrs (sortie z0_max90)
    trades = _backtest_short(df, sig)
    eval_summary = {}
    if len(trades) >= 5:
        g = trades["pnl"].values
        eval_summary = {"n_matured": int(len(trades)), "hit_rate": round(float((g > 0).mean()), 4),
                        "net_cost1": round(float((g - 2).sum()), 1),
                        "net_cost3": round(float((g - 6).sum()), 1),
                        "net_cost5": round(float((g - 10).sum()), 1)}
    return {"n_added": n_added, "n_total": int(len(combined)),
            "path": str(JOURNAL), "evaluation": eval_summary}


if __name__ == "__main__":
    r = update_journal()
    print(json.dumps(r, indent=2, default=str))

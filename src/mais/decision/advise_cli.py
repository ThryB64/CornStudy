"""``mais advise`` - print the current recommendation."""

from __future__ import annotations

import json

from mais.paths import ARTEFACTS_DIR

DECISION_SNAPSHOT_JSON = ARTEFACTS_DIR / "professional_study" / "decision_snapshot.json"


def advise_today(horizon: int = 20, farmer_state: str = "iowa") -> str:
    """Return the latest study recommendation, falling back to a clear message."""
    if not DECISION_SNAPSHOT_JSON.exists():
        return (
            f"=== Mais Decision Advisor (state={farmer_state}, horizon=H{horizon}) ===\n"
            f"No decision snapshot found. Run `mais study` first."
        )
    decision = json.loads(DECISION_SNAPSHOT_JSON.read_text(encoding="utf-8"))
    if decision.get("status") != "ok":
        return (
            f"=== Mais Decision Advisor (state={farmer_state}, horizon=H{horizon}) ===\n"
            f"Decision unavailable: {decision.get('status', 'unknown')}"
        )
    rec = decision.get("recommendation", {})
    return (
        f"=== Mais Decision Advisor (state={farmer_state}, horizon=H{horizon}) ===\n"
        f"As of       : {decision.get('as_of')}\n"
        f"Action      : {rec.get('action')}\n"
        f"Sell %      : {float(rec.get('sell_fraction', 0.0)):.0%}\n"
        f"Rule fired  : {rec.get('rule_id')}\n"
        f"Regime      : {decision.get('regime')}\n"
        f"Cash price  : {decision.get('cash_price_usd_per_bu', 0.0):.2f} USD/bu\n"
        f"Q10/Q50/Q90 : {decision.get('predicted_cash_q10_h20', 0.0):.2f} / "
        f"{decision.get('predicted_cash_q50_h20', 0.0):.2f} / "
        f"{decision.get('predicted_cash_q90_h20', 0.0):.2f} USD/bu\n"
        f"Rationale   : {rec.get('rationale', '')}"
    )

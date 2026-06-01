"""``mais advise`` - print today's recommendation."""

from __future__ import annotations

from .rules import advise, load_rules


def advise_today(horizon: int = 20, farmer_state: str = "iowa") -> str:
    """Toy implementation - returns a SAMPLE recommendation since the real
    meta-predictions table doesn't exist yet. Wire this to
    ``data/processed/meta_predictions.parquet`` (stacking output) once
    Phase 3 is complete."""
    rules, profile = load_rules()
    profile["location_state"] = farmer_state
    h = horizon
    sample_preds = {
        f"p_up_strong_h{h}":   0.55,
        f"p_down_strong_h{h}": 0.15,
        f"q10_h{h}":           0.97,
        f"q50_h{h}":           1.02,
        f"q90_h{h}":           1.08,
        "regime":              "bull",
        "p_t":                 1.0,
    }
    rec = advise(sample_preds, profile, rules)
    return (
        f"=== Mais Decision Advisor (state={farmer_state}, horizon=H{h}) ===\n"
        f"Action      : {rec.action.value}\n"
        f"Sell %      : {int(rec.sell_fraction * 100)}%\n"
        f"Rule fired  : {rec.rule_id}\n"
        f"Rationale   : {rec.rationale}\n"
        f"\n[NOTE] This used SAMPLE predictions. Run `mais train` then `mais stack`\n"
        f"to wire real model outputs."
    )

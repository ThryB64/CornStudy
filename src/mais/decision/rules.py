"""Decision rules engine.

Reads ``config/decision.yaml`` and evaluates the rules in priority order
against a dictionary of model predictions + farmer profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mais.utils import get_logger, load_decision

log = get_logger("mais.decision.rules")


class Action(str, Enum):
    SELL_NOW = "SELL_NOW"
    SELL_THIRDS = "SELL_THIRDS"
    SELL_THIRDS_OVER_60_DAYS = "SELL_THIRDS_OVER_60_DAYS"
    STORE = "STORE"
    WAIT = "WAIT"


@dataclass
class Recommendation:
    action: Action
    sell_fraction: float
    rule_id: str
    rationale: str
    inputs: dict[str, float] = field(default_factory=dict)
    profile: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "sell_fraction": self.sell_fraction,
            "rule_id": self.rule_id,
            "rationale": self.rationale,
            "inputs": self.inputs,
            "profile": self.profile,
        }


def load_rules() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cfg = load_decision()
    rules = sorted(cfg.get("decision_rules", []), key=lambda r: r.get("priority", 999))
    profile = cfg.get("farmer_profile", {}).get("default", {})
    return rules, profile


_OPERATOR_NORMALISATIONS = (
    (" AND ", " and "),
    (" OR ", " or "),
    (" NOT ", " not "),
    (" or  not ", " or not "),
)


def _safe_eval(condition: str, inputs: dict[str, Any]) -> bool:
    """Evaluate a *very restricted* boolean expression.

    Allowed names: keys of ``inputs`` plus ``regime`` strings, ``True``/``False``,
    arithmetic and comparison operators. NO function calls, attribute access,
    imports, etc. We use ``eval`` with an empty ``__builtins__`` namespace.

    Accepts SQL-like operators ``AND``/``OR``/``NOT`` for human-friendly YAML rules.
    """
    norm = " " + condition.strip() + " "
    for old, new in _OPERATOR_NORMALISATIONS:
        norm = norm.replace(old, new)
    try:
        return bool(eval(norm.strip(), {"__builtins__": {}}, dict(inputs)))
    except Exception as e:
        log.warning("rule_eval_failed", condition=condition, error=str(e))
        return False


def advise(
    predictions: dict[str, float | str],
    profile: dict[str, Any] | None = None,
    rules: list[dict[str, Any]] | None = None,
) -> Recommendation:
    """Apply rules in priority order; return the first matching recommendation.

    Parameters
    ----------
    predictions
        Dict of variables available in rules (e.g. p_up_strong_h20, q10_h20,
        q90_h20, q50_h20, regime, p_t).
    profile
        Farmer profile dict (uses default from yaml if None).
    rules
        Rules list (loaded from yaml if None).
    """
    if rules is None or profile is None:
        loaded_rules, default_profile = load_rules()
        rules = rules if rules is not None else loaded_rules
        profile = profile if profile is not None else default_profile

    inputs: dict[str, Any] = dict(predictions)
    inputs["farmer_profile"] = profile
    # Flatten profile keys to top-level so rules can reference e.g.
    #   farmer_profile.cash_flow_constraint  (qualified)  OR
    #   storage_cost_usd_per_bu_per_month     (top-level)
    for k, v in (profile or {}).items():
        inputs.setdefault(k, v)

    # Custom helper: profile.* attribute-like access via dotted keys
    inputs.update({"true": True, "false": False, "True": True, "False": False})

    for rule in rules:
        cond = rule.get("condition", "false")
        cond_norm = cond.replace("farmer_profile.", "")
        if _safe_eval(cond_norm, inputs):
            return Recommendation(
                action=Action(rule.get("action", "WAIT")),
                sell_fraction=float(rule.get("sell_fraction", 0.0)),
                rule_id=str(rule.get("id", "unknown")),
                rationale=rule.get("rationale", ""),
                inputs={k: v for k, v in predictions.items() if not isinstance(v, dict)},
                profile=profile or {},
            )

    return Recommendation(
        action=Action.WAIT,
        sell_fraction=0.0,
        rule_id="no_match",
        rationale="No rule matched - default to WAIT.",
        inputs={k: v for k, v in predictions.items() if not isinstance(v, dict)},
        profile=profile or {},
    )

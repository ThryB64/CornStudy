"""Phase 2 - Farmer decision support layer.

Transforms probabilistic model outputs into actionable advice
(SELL_NOW / SELL_THIRDS / STORE / WAIT) given a farmer profile.

Public API
----------
``advise(predictions, profile, rules) -> Recommendation``
    Apply rules in priority order to current predictions.
``run_backtest(horizon, farmer_state) -> dict``
    Backtest decisions over the historical period vs baseline strategies.
``advise_today(horizon, farmer_state) -> str``
    Helper used by the CLI.
"""

from .rules import Action, Recommendation, advise, load_rules
from .backtest import run_backtest
from .advise_cli import advise_today

__all__ = [
    "Action",
    "Recommendation",
    "advise",
    "load_rules",
    "run_backtest",
    "advise_today",
]

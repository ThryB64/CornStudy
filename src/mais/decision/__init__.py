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
from .advise_cli import advise_today


def run_backtest(*args, **kwargs):
    """Lazy wrapper to avoid importing study artefacts during study generation."""
    from .backtest import run_backtest as _run_backtest

    return _run_backtest(*args, **kwargs)

__all__ = [
    "Action",
    "Recommendation",
    "advise",
    "load_rules",
    "run_backtest",
    "advise_today",
]

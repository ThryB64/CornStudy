"""Walk-forward validation engine.

The legacy ``Models/base/wf_core.py`` (866 lines) contains a working but
monolithic walk-forward implementation. This module ships a CLEAN, focused
walk-forward that is easier to test and extend, with a clear interface for
both training and producing the meta-database of out-of-fold predictions.
"""

from .splits import WalkForwardSplitter, generate_walk_forward_splits
from .runner import walk_forward_run

__all__ = [
    "WalkForwardSplitter",
    "generate_walk_forward_splits",
    "walk_forward_run",
]

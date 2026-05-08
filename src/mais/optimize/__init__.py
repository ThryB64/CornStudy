"""Optimisation orchestration (Optuna over walk-forward).

The legacy 3286-line ``Models/optimize.py`` is being broken up here into:

  * ``profiler.py``   - auto-detect dataset structure (TS vs tabular, target type)
  * ``feature_select.py`` - the universal/medoid/topk selection (extracted from optimize.py)
  * ``optuna_loop.py``    - the actual Optuna study runner
  * ``runner.py``         - thin orchestrator called by `mais train`
"""

from .runner import run_training
from .profiler import profile_dataset

__all__ = ["run_training", "profile_dataset"]

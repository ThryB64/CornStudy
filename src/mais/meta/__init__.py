"""Meta-database + stacking.

The legacy ``Models/models/stacking_reg.py`` was a 64-line file that did
``raise NotImplementedError("Stacking à implémenter")``. This module
implements it properly:

  1. ``build_meta_database()`` - aggregates OOF predictions of all base
     models from ``artefacts/predictions/<target>/<model>.parquet`` into a
     single wide parquet ``artefacts/meta_database.parquet``.
  2. ``run_stacking()`` - fits a meta-model (Ridge/Lasso/LightGBM) on the
     meta-features. Walk-forward to avoid leakage from base models into the
     meta-model.
  3. ``conformal_prediction()`` - cheap conformal calibration to produce
     90%-coverage prediction intervals.
"""

from .meta_database import build_meta_database
from .stacking import run_stacking
from .conformal import calibrate_conformal_intervals

__all__ = [
    "build_meta_database",
    "run_stacking",
    "calibrate_conformal_intervals",
]

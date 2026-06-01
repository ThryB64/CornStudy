"""End-to-end smoke test: build features, targets, train, stack, advise."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.decision import Action, advise
from mais.meta import calibrate_conformal_intervals
from mais.models import ModelRegistry, ModelTask, ModelRequirement
from mais.targets import TargetSpec, build_targets
from mais.walkforward import walk_forward_run


pytestmark = pytest.mark.integration


def test_full_pipeline_synthetic(synthetic_prices, synthetic_features):
    spec = TargetSpec(horizons=(5, 10, 20))
    targets = build_targets(synthetic_prices, spec)

    # 1) Train a small model
    adapter = ModelRegistry.get("ridge_reg")
    run = walk_forward_run(
        adapter, synthetic_features, targets,
        target_col="y_logret_h10", horizon=10,
        initial_train_years=2, step_days=21,
    )
    assert not run.predictions.empty
    assert "y_pred" in run.predictions.columns

    # 2) Conformal intervals on the predictions
    intervals = calibrate_conformal_intervals(
        run.predictions["y_true"], run.predictions["y_pred"], alpha=0.1,
    )
    coverage = float(((run.predictions["y_true"] >= intervals["lo"]) &
                       (run.predictions["y_true"] <= intervals["hi"])).mean())
    assert coverage >= 0.7  # rough lower bound (small sample)

    # 3) Decision rules
    rec = advise({
        "p_up_strong_h20": 0.7, "p_down_strong_h10": 0.1,
        "q10_h20": 0.95, "q50_h20": 1.05, "q90_h20": 1.10,
        "regime": "bull", "p_t": 1.0,
    })
    assert rec.action in {Action.STORE, Action.SELL_NOW, Action.SELL_THIRDS,
                           Action.SELL_THIRDS_OVER_60_DAYS, Action.WAIT}


def test_registry_lists_all_50_models():
    names = ModelRegistry.list()
    assert len(names) >= 50, f"Expected 50+ models, got {len(names)}"
    # A handful of ports must be present
    for name in ["naive_last", "ridge_reg", "rf_reg", "xgboost_reg",
                 "lgbm_reg", "ar1_baseline", "ema_baseline", "stacking_reg"]:
        assert name in names, f"Missing model in registry: {name}"


def test_compatible_models_filtering():
    # Many features available, time index, regression -> we expect tens of models
    compat = ModelRegistry.compatible(
        ModelTask.REGRESSION,
        {ModelRequirement.EXOGENOUS, ModelRequirement.TIME_INDEX},
        n_samples=1500,
    )
    assert len(compat) >= 20
    # Quantile-only model not in REGRESSION list
    compat_quant = ModelRegistry.compatible(
        ModelTask.QUANTILE,
        {ModelRequirement.EXOGENOUS},
        n_samples=1500,
    )
    assert "xgboost_quantile" in compat_quant

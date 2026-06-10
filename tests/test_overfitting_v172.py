"""V172 — anti-overfitting : PSR/DSR/PBO."""
from __future__ import annotations

import numpy as np

from mais.audit import overfitting as ov


def test_psr_increases_with_sharpe():
    lo = ov.probabilistic_sharpe_ratio(0.05, 200, 0.0, 3.0)
    hi = ov.probabilistic_sharpe_ratio(0.20, 200, 0.0, 3.0)
    assert 0.0 <= lo <= hi <= 1.0


def test_expected_max_sharpe_grows_with_trials():
    a = ov.expected_max_sharpe(0.01, 5)
    b = ov.expected_max_sharpe(0.01, 500)
    assert b > a > 0


def test_dsr_penalizes_many_trials():
    rng = np.random.default_rng(0)
    rets = rng.normal(0.08, 1.0, 250)  # Sharpe/obs ~0.08
    few = ov.deflated_sharpe_ratio(rets, n_trials=1)
    many = ov.deflated_sharpe_ratio(rets, n_trials=1000)
    assert many["deflated_sharpe_ratio"] <= few["deflated_sharpe_ratio"]
    assert many["expected_max_sharpe"] > few["expected_max_sharpe"]


def test_pbo_random_strategies_near_half():
    """N stratégies de pur bruit -> PBO doit être élevé (pas de skill réel)."""
    rng = np.random.default_rng(1)
    M = rng.normal(0, 1, size=(400, 12))
    out = ov.pbo_cscv(M, n_splits=8)
    assert out["verdict"] in ("OVERFIT_LIKELY", "ROBUST")
    assert 0.0 <= out["pbo"] <= 1.0


def test_pbo_one_genuinely_good_strategy_is_robust():
    """Une stratégie à edge réel + bruit autour -> best-IS reste bon OOS -> PBO bas."""
    rng = np.random.default_rng(2)
    M = rng.normal(0, 1, size=(400, 10))
    M[:, 0] += 0.45  # stratégie 0 a un vrai edge constant
    out = ov.pbo_cscv(M, n_splits=8)
    assert out["pbo"] < 0.5
    assert out["verdict"] == "ROBUST"


def test_spa_random_not_significant():
    rng = np.random.default_rng(10)
    M = rng.normal(0, 1, size=(40, 8))  # pur bruit -> pas de stratégie significative
    out = ov.reality_check_spa(M, n_boot=500)
    assert out["p_spa_hansen"] > 0.05
    assert out["verdict"] == "NOT_SIGNIFICANT_AFTER_SNOOPING"


def test_spa_strong_strategy_significant():
    rng = np.random.default_rng(11)
    M = rng.normal(0, 1, size=(60, 6))
    M[:, 2] += 1.2  # une stratégie nettement supérieure
    out = ov.reality_check_spa(M, n_boot=500)
    assert out["p_spa_hansen"] <= 0.05
    assert out["best_strategy_index"] == 2


def test_run_pack_overall():
    rng = np.random.default_rng(3)
    rets = rng.normal(0.1, 1.0, 200)
    M = rng.normal(0, 1, size=(200, 8)); M[:, 0] += 0.4
    out = ov.run_overfitting_pack(rets, n_trials=50, perf_matrix=M)
    assert out["overall"] in ("SURVIVES", "REQUALIFY_EXPLORATORY")
    assert "deflated_sharpe" in out and "pbo" in out

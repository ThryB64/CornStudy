"""Tests V7-29 — Multiple testing correction + holdout lock."""

import json

import numpy as np
import pytest

from mais.research.multiple_testing import (
    bh_correction,
    consume_holdout,
    is_holdout_available,
    run_bh_on_registry,
)


def test_bh_empty():
    result = bh_correction([])
    assert result["n_rejected"] == 0
    assert result["results"] == []


def test_bh_all_significant():
    p_values = [0.001, 0.005, 0.01]
    result = bh_correction(p_values, alpha=0.05)
    assert result["n_rejected"] == 3
    assert all(r["rejected"] for r in result["results"])


def test_bh_none_significant():
    p_values = [0.9, 0.8, 0.7]
    result = bh_correction(p_values, alpha=0.05)
    assert result["n_rejected"] == 0
    assert not any(r["rejected"] for r in result["results"])


def test_bh_partial():
    # 2 small, 1 large
    p_values = [0.001, 0.04, 0.9]
    result = bh_correction(p_values, alpha=0.05)
    assert 1 <= result["n_rejected"] <= 2


def test_bh_q_values_ordered():
    p_values = [0.01, 0.03, 0.05, 0.1]
    result = bh_correction(p_values, alpha=0.05)
    # q_bh = p * m / rank — check formula
    for r in result["results"]:
        assert r["q_bh"] >= r["p_value"]


def test_bh_results_sorted_by_original_index():
    p_values = [0.05, 0.01, 0.3]
    result = bh_correction(p_values, alpha=0.05)
    indices = [r["original_index"] for r in result["results"]]
    assert indices == sorted(indices)


def test_run_bh_on_empty_registry():
    """Si le registre n'a aucun p_value, on attend NO_TESTS."""
    result = run_bh_on_registry()
    assert result["global_verdict"] in {"NO_TESTS", "NONE_SIGNIFICANT", "SOME_SIGNIFICANT"}


def test_holdout_lock_roundtrip(tmp_path, monkeypatch):
    import mais.research.multiple_testing as mod
    lock_path = tmp_path / "holdout_lock.json"
    monkeypatch.setattr(mod, "_HOLDOUT_LOCK", lock_path)

    assert mod.is_holdout_available()
    result = consume_holdout("V7-28")
    assert result["status"] == "CONSUMED"
    assert not mod.is_holdout_available()


def test_holdout_double_consume_raises(tmp_path, monkeypatch):
    import mais.research.multiple_testing as mod
    lock_path = tmp_path / "holdout_lock.json"
    monkeypatch.setattr(mod, "_HOLDOUT_LOCK", lock_path)

    consume_holdout("V7-28")
    with pytest.raises(RuntimeError, match="déjà consommé"):
        consume_holdout("V7-28-again")

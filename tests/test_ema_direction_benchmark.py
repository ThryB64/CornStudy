"""Tests pour NB-EMA-08 — Benchmark directionnel EMA."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_direction_benchmark import build_direction_benchmark, save_direction_benchmark


def test_build_returns_dict():
    data = build_direction_benchmark()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_direction_benchmark()
    for key in ["n_combinations", "feature_sets", "targets", "results", "summary"]:
        assert key in data, f"Clé manquante : {key}"


def test_multiple_feature_sets_tested():
    data = build_direction_benchmark()
    assert len(data["feature_sets"]) >= 3, "Moins de 3 feature sets testés"


def test_results_have_verdict():
    data = build_direction_benchmark()
    for r in data["results"]:
        if "error" not in r:
            assert "verdict_go_minimal" in r, f"Verdict manquant : {r}"


def test_results_have_ci():
    data = build_direction_benchmark()
    valid = [r for r in data["results"] if "da_mean" in r]
    assert len(valid) > 0
    for r in valid:
        assert "da_ci_lo" in r and "da_ci_hi" in r
        assert r["da_ci_lo"] <= r["da_mean"] <= r["da_ci_hi"]


def test_bh_correction_applied():
    data = build_direction_benchmark()
    has_bh = [r for r in data["results"] if "bh_significant" in r]
    assert len(has_bh) > 0, "Correction BH non appliquée"


def test_summary_has_overall_verdict():
    data = build_direction_benchmark()
    s = data["summary"]
    assert "overall_verdict" in s
    assert s["overall_verdict"] in ("GO_SIGNAL", "NO_GO")


def test_basis_reversion_is_best_signal():
    data = build_direction_benchmark()
    valid = [r for r in data["results"] if "da_mean" in r and "basis_reversion" in r["target"]]
    if not valid:
        pytest.skip("Cible basis_reversion non présente")
    das = [r["da_mean"] for r in valid]
    assert max(das) >= 0.60, f"Meilleur DA basis_reversion trop faible : {max(das):.3f}"


def test_save_creates_json(tmp_path):
    out = save_direction_benchmark(tmp_path / "test_bench.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "results" in data
    assert "summary" in data

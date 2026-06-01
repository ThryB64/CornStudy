"""Tests pour NB-EMA-13 — Benchmark hebdomadaire EMA."""

from __future__ import annotations

import json

from mais.research.ema_weekly_benchmark import build_weekly_benchmark, save_weekly_benchmark


def test_build_returns_dict():
    data = build_weekly_benchmark()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_weekly_benchmark()
    for key in [
        "n_weeks",
        "weekly_return_stats",
        "da_naive_trend_H4w",
        "basis_signal_H4w",
        "generalised_weekly_results",
        "key_findings",
    ]:
        assert key in data, f"Clé manquante : {key}"


def test_n_weeks_sufficient():
    data = build_weekly_benchmark()
    assert data["n_weeks"] >= 100, f"Trop peu de semaines : {data['n_weeks']}"


def test_da_naive_reasonable():
    data = build_weekly_benchmark()
    da = data["da_naive_trend_H4w"]["da_naive_trend"]
    assert 0.3 <= da <= 0.7, f"DA naive hors plage : {da}"


def test_basis_signal_has_da():
    data = build_weekly_benchmark()
    bs = data["basis_signal_H4w"]
    if "error" not in bs:
        assert "hit_rate" in bs
        assert 0 <= bs["hit_rate"] <= 1


def test_generalised_weekly_results_cover_expected_labels():
    data = build_weekly_benchmark()
    labels = {row["label"] for row in data["generalised_weekly_results"]}
    assert "ema_direct_momentum" in labels
    assert "relative_ema_outperformance_basis_z" in labels
    assert "basis_reversion" in labels
    assert "ema_vol_high_persistence" in labels


def test_generalised_weekly_results_cover_horizons():
    data = build_weekly_benchmark()
    horizons = {row["horizon_weeks"] for row in data["generalised_weekly_results"]}
    assert {4, 8, 12}.issubset(horizons)


def test_pct_up_weeks_near_half():
    data = build_weekly_benchmark()
    pct = data["weekly_return_stats"]["pct_up_weeks"]
    assert 0.3 <= pct <= 0.7, f"% semaines haussières hors plage : {pct}"


def test_key_findings_note():
    data = build_weekly_benchmark()
    note = data["key_findings"].get("note", "")
    assert len(note) > 0
    assert "best_weekly_label" in data["key_findings"]


def test_save_creates_json(tmp_path):
    out = save_weekly_benchmark(tmp_path / "test_weekly.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "key_findings" in data

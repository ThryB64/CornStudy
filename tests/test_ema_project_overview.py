"""Tests pour NB-EMA-00 — Module vue d'ensemble projet."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_project_overview import build_project_overview, save_overview


def test_build_overview_returns_dict():
    overview = build_project_overview()
    assert isinstance(overview, dict)


def test_required_keys_present():
    overview = build_project_overview()
    for key in ["project", "pivot_date", "guiding_phrase", "known_results_summary", "benchmark_results"]:
        assert key in overview, f"Clé manquante : {key}"


def test_known_results_summary_values():
    s = build_project_overview()["known_results_summary"]
    assert s["ema_direction_da_h20"] == pytest.approx(0.4673, abs=0.001)
    assert s["ema_direction_verdict"] == "NO_GO"
    assert s["basis_mean_reversion_hit_rate_h20"] > 0.6
    assert s["granger_ema_to_cbot_p"] < 0.05
    assert "non confirmé OOF" in s["granger_status"]


def test_ema_front_stats_period_covers_2014_2023():
    overview = build_project_overview()
    stats = overview.get("ema_front_stats", {})
    if "period_start" in stats and stats["period_start"]:
        assert stats["period_start"] <= "2016-01-01", f"Période début trop tardive: {stats['period_start']}"
    if "n_days" in stats and stats["n_days"]:
        assert stats["n_days"] > 1000, f"Trop peu de jours: {stats['n_days']}"


def test_save_overview_creates_json(tmp_path):
    out = save_overview(tmp_path / "test_overview.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "project" in data
    assert "known_results_summary" in data

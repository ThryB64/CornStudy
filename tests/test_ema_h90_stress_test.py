from __future__ import annotations

import json

from mais.research.ema_h90_stress_test import build_h90_stress_test, save_h90_stress_test


def test_h90_stress_required_keys():
    data = build_h90_stress_test()
    assert "scenario_results" in data
    assert "h90_cost_stress" in data
    assert "key_findings" in data


def test_h90_stress_has_required_scenarios():
    scenarios = {row["scenario"] for row in build_h90_stress_test()["scenario_results"]}
    assert "all_oof" in scenarios
    assert "strict_non_overlap" in scenarios
    assert "no_crisis_2020_2022" in scenarios


def test_h90_stress_has_verdict():
    status = build_h90_stress_test()["status"]
    assert status in {"H90_MAIN_GO_RESEARCH_ONLY", "H90_RESEARCH_ONLY", "H90_REJECTED_OVERLAP"}


def test_h90_stress_keeps_no_production():
    assert build_h90_stress_test()["production_verdict"] == "NO_PRODUCTION_BACKTEST"


def test_save_h90_stress_test(tmp_path):
    out = save_h90_stress_test(tmp_path / "h90.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["target"] == "relative_ema_outperformance_h90"

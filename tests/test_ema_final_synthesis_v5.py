from __future__ import annotations

import json

from mais.research.ema_final_synthesis_v5 import build_final_synthesis_v5, save_final_synthesis_v5


def test_final_synthesis_v5_required_keys():
    data = build_final_synthesis_v5()
    assert "central_conclusion" in data
    assert "v5_target_lab" in data
    assert "v5_cross_data" in data
    assert "v5_hierarchical" in data


def test_final_synthesis_v5_keeps_research_only():
    data = build_final_synthesis_v5()
    assert data["production_verdict"] == "NO_PRODUCTION_BACKTEST"
    assert data["verdict_data"] == "NO_RELIABLE_PERIOD_ML"


def test_final_synthesis_v5_keeps_relative_signal_central():
    conclusion = build_final_synthesis_v5()["central_conclusion"]
    assert conclusion["ema_absolute_direction"] == "NO_GO_AS_MAIN_TARGET"
    assert conclusion["ema_relative_cbot_h40"] == "PRIMARY_RESEARCH_SIGNAL"


def test_final_synthesis_v5_mentions_v5_experiments():
    data = build_final_synthesis_v5()
    assert data["v5_target_lab"]["n_targets_tested"] >= 18
    assert "Cross-data" in data["v5_cross_data"]["interpretation"] or "cross-data" in data["v5_cross_data"]["interpretation"]


def test_save_final_synthesis_v5(tmp_path):
    out = save_final_synthesis_v5(tmp_path / "synthesis.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["guiding_equation"].startswith("EMA = CBOT")

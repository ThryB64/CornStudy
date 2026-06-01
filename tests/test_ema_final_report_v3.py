from __future__ import annotations

import json

from mais.research.ema_final_report_v3 import build_final_report_v3, save_final_report_v3


def test_final_report_v3_required_keys():
    data = build_final_report_v3()
    for key in ["source_quality", "verdict_data", "primary_result", "basis_centrality"]:
        assert key in data


def test_final_report_v3_promotes_relative_not_absolute():
    data = build_final_report_v3()
    assert data["primary_result"]["target"] == "relative_ema_outperformance_h40"
    assert data["scientific_pivot"]["old_question_verdict"] == "REJECTED_AS_MAIN_TARGET"
    assert data["scientific_pivot"]["new_question_verdict"] == "GO_RESEARCH_EXPLORATORY"


def test_final_report_v3_marks_h90_as_candidate():
    data = build_final_report_v3()
    assert data["h90_candidate"]["status"] == "PROMISING_BUT_NEEDS_STRESS_TEST"
    assert "strict_non_overlapping" in data["h90_candidate"]["required_checks"]


def test_final_report_v3_keeps_backtest_research_only():
    data = build_final_report_v3()
    assert data["relative_backtest"]["status"] == "RESEARCH_ONLY_NOT_TRADING"
    assert data["relative_backtest"]["production_verdict"] == "NO_PRODUCTION_BACKTEST"


def test_final_report_v3_lists_no_go_results():
    items = {row["item"] for row in build_final_report_v3()["no_go_results"]}
    assert "EMA direction absolue" in items
    assert "CQR prix absolu EMA" in items


def test_save_final_report_v3(tmp_path):
    out = save_final_report_v3(tmp_path / "final_v3.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["verdict_data"] == "NO_RELIABLE_PERIOD_ML"

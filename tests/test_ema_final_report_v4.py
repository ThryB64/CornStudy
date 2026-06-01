from __future__ import annotations

import json

from mais.research.ema_final_report_v4 import build_final_report_v4, save_final_report_v4


def test_final_report_v4_required_keys():
    data = build_final_report_v4()
    for key in ["official_v4_conclusion", "h40_main_signal", "h90_candidate", "basis_evidence"]:
        assert key in data


def test_final_report_v4_keeps_absolute_ema_no_go():
    conclusion = build_final_report_v4()["official_v4_conclusion"]
    assert conclusion["ema_absolute_direction"] == "NO_GO_AS_MAIN_TARGET"


def test_final_report_v4_marks_h40_primary_and_h90_candidate():
    data = build_final_report_v4()
    assert data["h40_main_signal"]["status"] == "PRIMARY_PRUDENT_HORIZON"
    assert data["h90_candidate"]["status"] == "PROMISING_NOT_FINAL"
    assert data["h90_candidate"]["required_ticket"] == "EMA-H90-01"


def test_final_report_v4_keeps_backtest_research_only():
    data = build_final_report_v4()
    assert data["production_verdict"] == "NO_PRODUCTION_BACKTEST"
    assert data["backtest_research_only"]["production_verdict"] == "NO_PRODUCTION_BACKTEST"


def test_final_report_v4_has_roadmap():
    roadmap = build_final_report_v4()["v4_roadmap"]
    assert any("EMA-H90-01" in item for item in roadmap)
    assert any("notebooks/" in item for item in roadmap)


def test_save_final_report_v4(tmp_path):
    out = save_final_report_v4(tmp_path / "final_v4.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["verdict_data"] == "NO_RELIABLE_PERIOD_ML"

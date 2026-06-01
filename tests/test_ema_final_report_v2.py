from __future__ import annotations

import json

from mais.research.ema_final_report_v2 import build_final_report_v2, save_final_report_v2


def test_final_report_v2_required_keys():
    data = build_final_report_v2()
    for key in ["source_quality", "verdict_data", "implementation_status", "main_conclusion"]:
        assert key in data


def test_final_report_v2_source_warning():
    data = build_final_report_v2()
    assert data["verdict_data"] == "NO_RELIABLE_PERIOD_ML"


def test_final_report_v2_status_table_contains_granger():
    table = build_final_report_v2()["implementation_status"]
    assert any("Granger EMA" in row["item"] for row in table)


def test_final_report_v2_promotes_relative_h40():
    data = build_final_report_v2()
    table = data["implementation_status"]
    relative = next(row for row in table if row["item"] == "Direction EMA relative vs CBOT")
    assert "MEILLEUR SIGNAL EMA ROBUSTE" in relative["status"]
    assert "relative_ema_outperformance_h40" in relative["evidence"]
    assert any("relative_ema_outperformance_h40" in item for item in data["main_conclusion"])


def test_final_report_v2_rejects_vol_high_as_best_signal():
    table = build_final_report_v2()["implementation_status"]
    vol = next(row for row in table if row["item"] == "Faux bon signal volatilité EMA")
    assert "REJETÉ" in vol["status"]
    assert "ema_vol_high_h20" in vol["evidence"]


def test_save_final_report_v2(tmp_path):
    out = save_final_report_v2(tmp_path / "final_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "guiding_equation" in data

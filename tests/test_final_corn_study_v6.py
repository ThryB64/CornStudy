from __future__ import annotations

import json

from mais.research.final_corn_study_v6 import build_final_corn_study_v6, save_final_corn_study_v6


def test_final_corn_study_v6_has_summary_and_review():
    data = build_final_corn_study_v6()

    assert data["version"] == "V6"
    assert data["summary"]["ema_premium_status"] == "PRIMARY_RESEARCH_SIGNAL"
    assert data["review"]["manual_review_verdict"] in {"PASS_WITH_RESEARCH_ONLY_CAVEATS", "NEEDS_FIX"}


def test_final_review_checks_are_complete():
    data = build_final_corn_study_v6()
    checks = data["review"]["checks"]

    assert "required_json_present" in checks
    assert "meta_best_robust_support_ok" in checks
    assert "backtest_research_only" in checks
    assert checks["notebook_v6_blocked_by_agents_rule"] is True


def test_final_report_keeps_research_only_caveat():
    data = build_final_corn_study_v6()

    assert data["summary"]["production_verdict"] == "RESEARCH_ONLY_NOT_TRADING"
    assert "proxy" in data["source_quality"].lower()


def test_save_final_corn_study_v6_writes_json(tmp_path):
    out = save_final_corn_study_v6(tmp_path / "final_corn_study_v6.json")
    data = json.loads(out.read_text(encoding="utf-8"))

    assert out.exists()
    assert data["recommended_next_research"]

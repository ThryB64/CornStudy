from __future__ import annotations

import json

from mais.research.ema_relative_error_analysis import (
    build_relative_error_analysis,
    save_relative_error_analysis,
)


def test_relative_error_analysis_required_keys():
    data = build_relative_error_analysis()
    assert "top_correct" in data
    assert "worst_errors" in data
    assert "failed_top20" in data
    assert "summaries" in data


def test_relative_error_analysis_has_oof_rows():
    data = build_relative_error_analysis()
    assert data["n_oof"] > 100
    assert data["n_errors"] > 0


def test_relative_error_records_have_tags():
    data = build_relative_error_analysis()
    assert data["worst_errors"]
    assert "tags" in data["worst_errors"][0]


def test_relative_error_failed_top20_limited():
    data = build_relative_error_analysis()
    assert len(data["failed_top20"]) <= 50


def test_save_relative_error_analysis(tmp_path):
    out = save_relative_error_analysis(tmp_path / "relative_errors.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["target"] == "relative_ema_outperformance_h40"

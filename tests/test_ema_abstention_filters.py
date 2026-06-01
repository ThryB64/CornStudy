from __future__ import annotations

import json

from mais.research.ema_abstention_filters import build_abstention_filters, save_abstention_filters


def test_abstention_filters_required_keys():
    data = build_abstention_filters()
    assert "filters" in data
    assert "key_findings" in data


def test_abstention_filters_include_baseline():
    rows = build_abstention_filters()["filters"]
    assert any(row["filter"] == "all_signals" for row in rows)


def test_abstention_filters_include_top20():
    rows = build_abstention_filters()["filters"]
    assert any(row["filter"] == "top20_confidence" for row in rows)


def test_abstention_filters_have_coverage():
    rows = build_abstention_filters()["filters"]
    ok = [row for row in rows if row.get("status") == "OK"]
    assert ok
    assert all("coverage" in row for row in ok)


def test_save_abstention_filters(tmp_path):
    out = save_abstention_filters(tmp_path / "abstention.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["target"] == "relative_ema_outperformance_h40"

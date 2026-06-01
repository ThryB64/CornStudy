from __future__ import annotations

import json

from mais.research.ema_relative_error_archaeology_v2 import (
    build_relative_error_archaeology_v2,
    save_relative_error_archaeology_v2,
)


def test_error_archaeology_required_keys():
    data = build_relative_error_archaeology_v2()
    assert "catalogues" in data
    assert "key_findings" in data


def test_error_archaeology_has_h40_h90():
    horizons = {row["horizon"] for row in build_relative_error_archaeology_v2()["catalogues"]}
    assert {40, 90}.issubset(horizons)


def test_error_archaeology_has_records():
    catalogues = build_relative_error_archaeology_v2()["catalogues"]
    assert all(cat["worst_errors"] for cat in catalogues)
    assert all(cat["top_correct"] for cat in catalogues)


def test_error_archaeology_has_tag_summaries():
    catalogues = build_relative_error_archaeology_v2()["catalogues"]
    assert all(cat["worst_error_tag_summary"] for cat in catalogues)


def test_save_error_archaeology(tmp_path):
    out = save_relative_error_archaeology_v2(tmp_path / "errors.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("Error archaeology")

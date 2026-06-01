from __future__ import annotations

import json

from mais.research.ema_cqr_v2 import build_cqr_v2, save_cqr_v2


def test_cqr_v2_required_keys():
    data = build_cqr_v2()
    assert "results" in data
    assert "key_findings" in data


def test_cqr_v2_targets_present():
    targets = {row["target"] for row in build_cqr_v2()["results"]}
    assert "return_ema_h20" in targets
    assert "relative_return_h20" in targets


def test_cqr_v2_has_coverage():
    row = build_cqr_v2()["results"][0]
    assert "coverage_overall" in row
    assert 0 <= row["coverage_overall"] <= 1


def test_save_cqr_v2(tmp_path):
    out = save_cqr_v2(tmp_path / "cqr_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "overall_verdict" in data["key_findings"]

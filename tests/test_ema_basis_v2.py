from __future__ import annotations

import json

from mais.research.ema_basis_v2 import build_basis_v2, save_basis_v2


def test_basis_v2_required_keys():
    data = build_basis_v2()
    for key in ["basis_stats", "stationarity", "ar1", "regime_stats", "walk_forward_oof"]:
        assert key in data


def test_basis_v2_source_quality_present():
    assert build_basis_v2()["source_quality"] == "exploratoire_barchart_proxy"


def test_basis_v2_has_positive_basis_rate():
    pct = build_basis_v2()["basis_stats"]["pct_positive"]
    assert 0.90 <= pct <= 1.0


def test_basis_v2_has_oof_rows():
    rows = build_basis_v2()["walk_forward_oof"]
    assert any("hit_rate" in row for row in rows)


def test_basis_v2_weekly_validation_present():
    data = build_basis_v2()
    assert len(data["weekly_validation"]) > 0


def test_basis_v2_period_stability_present():
    stability = build_basis_v2()["period_stability"]
    assert "2020_2022" in stability


def test_basis_v2_anti_confusion_wording():
    text = build_basis_v2()["anti_confusion"]
    assert "basis_reversion ≠ EMA up" in text


def test_save_basis_v2(tmp_path):
    out = save_basis_v2(tmp_path / "basis_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data

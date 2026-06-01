from __future__ import annotations

import json

from mais.research.ema_smart_baselines import build_smart_baselines, save_smart_baselines


def test_smart_baselines_required_keys():
    data = build_smart_baselines()
    assert "results" in data
    assert "key_findings" in data


def test_smart_baselines_targets_present():
    results = build_smart_baselines()["results"]
    assert "relative_ema_outperformance_h40" in results
    assert "ema_direction_absolute_h40" in results


def test_smart_baselines_include_expected_rules():
    rel = build_smart_baselines()["results"]["relative_ema_outperformance_h40"]
    names = {row["baseline"] for row in rel["baselines"]}
    assert "walk_forward_majority" in names
    assert "basis_z_rule" in names
    assert "seasonal_month_rule" in names
    assert "random_50_50" in names


def test_smart_baselines_model_reference_present():
    rel = build_smart_baselines()["results"]["relative_ema_outperformance_h40"]
    assert rel["model_reference"]["status"] == "OK"


def test_save_smart_baselines(tmp_path):
    out = save_smart_baselines(tmp_path / "smart_baselines.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "source_quality" in data

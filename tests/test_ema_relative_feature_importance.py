from __future__ import annotations

import json

from mais.research.ema_relative_feature_importance import (
    build_relative_feature_importance,
    save_relative_feature_importance,
)


def test_relative_feature_importance_required_keys():
    data = build_relative_feature_importance()
    assert "results" in data
    assert "key_findings" in data


def test_relative_feature_importance_has_h40_h90():
    horizons = {row["horizon"] for row in build_relative_feature_importance()["results"]}
    assert {40, 90}.issubset(horizons)


def test_relative_feature_importance_has_permutation_rows():
    rows = build_relative_feature_importance()["results"]
    assert all(row["permutation_importance"] for row in rows)
    assert all("delta_auc" in row["permutation_importance"][0] for row in rows)


def test_relative_feature_importance_has_family_ablation():
    rows = build_relative_feature_importance()["results"]
    families = {item["family"] for row in rows for item in row["family_ablation"]}
    assert "basis" in families
    assert "cbot_technical" in families


def test_save_relative_feature_importance(tmp_path):
    out = save_relative_feature_importance(tmp_path / "importance.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["target_family"] == "relative_ema_outperformance"

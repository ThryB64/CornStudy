from __future__ import annotations

import json

from mais.research.meta_model_premium_v6 import (
    build_meta_model_frame,
    build_meta_model_premium_v6,
    save_meta_model_premium_v6,
)


def test_meta_model_frame_contains_targets_and_oof_meta_features():
    frame = build_meta_model_frame()

    assert "y_rel_outperform_h40" in frame.columns
    assert "meta_mean_rel_signal" in frame.columns
    assert any(col.startswith("pred_") and "y_rel_outperform_h40" in col for col in frame.columns)
    assert len(frame) > 500


def test_meta_model_premium_has_required_sections():
    data = build_meta_model_premium_v6()

    assert data["source_quality"] == "exploratoire_barchart_proxy"
    assert data["results"]
    assert data["abstention_on_best"]
    assert data["key_findings"]["best_target"]


def test_meta_model_compares_expected_feature_sets():
    data = build_meta_model_premium_v6()
    feature_sets = {row["feature_set"] for row in data["results"]}

    assert {"classic", "meta_only", "classic_plus_meta", "meta_plus_basis", "full_stack"} <= feature_sets


def test_meta_model_delta_vs_classic_reported_for_ok_rows():
    data = build_meta_model_premium_v6()
    rows = [row for row in data["results"] if row["status"] == "OK" and row["feature_set"] != "classic"]

    assert rows
    assert all("delta_auc_vs_classic" in row for row in rows)
    assert all("delta_top20_vs_classic" in row for row in rows)


def test_meta_model_abstention_policies_include_confidence_filters():
    data = build_meta_model_premium_v6()
    policies = {row["policy"] for row in data["abstention_on_best"]}

    assert {"all", "top40_confidence", "top20_confidence", "avoid_roll_proxy_months"} <= policies


def test_save_meta_model_premium_v6_writes_json(tmp_path):
    out = save_meta_model_premium_v6(tmp_path / "meta_model_premium_v6.json")
    data = json.loads(out.read_text(encoding="utf-8"))

    assert out.exists()
    assert data["key_findings"]["best_feature_set"]

from __future__ import annotations

import json

from mais.research.ema_cross_data_interactions_v5 import (
    build_cross_data_interactions_v5,
    build_interaction_frame,
    save_cross_data_interactions_v5,
)


def test_interaction_frame_has_core_crosses():
    frame = build_interaction_frame()
    expected = {
        "x_basis_cbot_momentum",
        "x_basis_cbot_vol",
        "x_basis_ema_vol",
        "x_basis_month_sin",
        "x_basis_month_cos",
    }
    assert expected.issubset(frame.columns)


def test_cross_data_interactions_required_keys():
    data = build_cross_data_interactions_v5()
    assert "feature_sets" in data
    assert "results" in data
    assert "key_findings" in data


def test_cross_data_interactions_compare_base_and_cross():
    data = build_cross_data_interactions_v5()
    sets = {row["feature_set"] for row in data["results"]}
    assert "base" in sets
    assert "all_cross" in sets
    assert data["key_findings"]["n_ok"] > 0


def test_cross_data_interactions_have_deltas():
    rows = [
        row
        for row in build_cross_data_interactions_v5()["results"]
        if row.get("status") == "OK" and row["feature_set"] != "base"
    ]
    assert rows
    assert any("delta_auc_vs_base" in row for row in rows)


def test_save_cross_data_interactions_v5(tmp_path):
    out = save_cross_data_interactions_v5(tmp_path / "cross.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("Cross-data")

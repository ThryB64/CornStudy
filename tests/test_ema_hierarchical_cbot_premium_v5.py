from __future__ import annotations

import json

from mais.research.ema_hierarchical_cbot_premium_v5 import (
    build_hierarchical_cbot_premium_v5,
    build_hierarchical_frame,
    save_hierarchical_cbot_premium_v5,
)


def test_hierarchical_frame_has_component_targets():
    frame = build_hierarchical_frame()
    for horizon in [40, 90]:
        assert f"y_ema_up_h{horizon}" in frame.columns
        assert f"y_cbot_up_h{horizon}" in frame.columns
        assert f"y_rel_outperform_h{horizon}" in frame.columns


def test_hierarchical_required_keys():
    data = build_hierarchical_cbot_premium_v5()
    assert "results" in data
    assert "train_weight_summary" in data
    assert "key_findings" in data


def test_hierarchical_compares_models():
    data = build_hierarchical_cbot_premium_v5()
    models = {row["model"] for row in data["results"]}
    assert {"direct_ema", "cbot_only", "premium_only", "hierarchical_fixed", "hierarchical_train_weighted"}.issubset(models)


def test_hierarchical_has_delta_vs_direct():
    rows = [
        row
        for row in build_hierarchical_cbot_premium_v5()["results"]
        if row.get("status") == "OK" and row["model"] != "direct_ema"
    ]
    assert rows
    assert any("delta_auc_vs_direct" in row for row in rows)


def test_save_hierarchical_cbot_premium_v5(tmp_path):
    out = save_hierarchical_cbot_premium_v5(tmp_path / "hierarchical.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("Hierarchical EMA")

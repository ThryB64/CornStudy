from __future__ import annotations

import json

from mais.research.ema_feature_importance_v2 import (
    build_feature_importance_v2,
    save_feature_importance_v2,
)


def test_feature_importance_v2_required_keys():
    data = build_feature_importance_v2()
    for key in ["mi_spearman", "permutation_oof", "fedfunds_audit", "family_ablation_oof"]:
        assert key in data


def test_feature_importance_v2_uses_features():
    assert build_feature_importance_v2()["key_findings"]["n_features"] > 0


def test_feature_importance_v2_fedfunds_suspect():
    assert build_feature_importance_v2()["fedfunds_audit"]["status"] == "suspect_temporal_proxy"


def test_save_feature_importance_v2(tmp_path):
    out = save_feature_importance_v2(tmp_path / "fi_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data

from __future__ import annotations

import json

from mais.research.cross_target_oof_v6 import (
    build_cross_target_oof_v6,
    build_meta_features_v6,
    build_oof_predictions_v6,
    save_cross_target_oof_v6,
)


def test_oof_predictions_are_oof_and_time_ordered():
    pred = build_oof_predictions_v6()
    assert not pred.empty
    assert pred["is_oof"].all()
    assert (pred["train_end"] < pred["test_start"]).all()


def test_oof_predictions_have_manifest_columns():
    pred = build_oof_predictions_v6()
    required = {"Date", "target_name", "model_name", "pred_proba", "fold", "train_start", "test_start"}
    assert required.issubset(pred.columns)


def test_meta_features_v6_builds_aggregates():
    meta = build_meta_features_v6(build_oof_predictions_v6())
    assert not meta.empty
    assert "meta_mean_rel_signal" in meta.columns
    assert "meta_signal_entropy" in meta.columns


def test_cross_target_oof_v6_required_keys():
    data = build_cross_target_oof_v6()
    assert data["prediction_rows"] > 0
    assert data["meta_rows"] > 0
    assert "metrics" in data


def test_save_cross_target_oof_v6(tmp_path):
    out = save_cross_target_oof_v6(tmp_path / "manifest.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("OOF prediction")

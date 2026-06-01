from __future__ import annotations

import json

from mais.research.ema_relative_study import (
    build_relative_frame,
    build_relative_study,
    oof_relative_predictions,
    save_relative_study,
)


def test_relative_frame_has_multi_horizon_targets():
    frame = build_relative_frame()
    for horizon in [10, 20, 40, 60, 90]:
        assert f"relative_return_h{horizon}" in frame.columns
        assert f"y_ema_outperforms_cbot_h{horizon}" in frame.columns


def test_relative_targets_keep_tail_nan():
    frame = build_relative_frame()
    for horizon in [10, 20, 40, 60, 90]:
        assert frame[f"y_ema_outperforms_cbot_h{horizon}"].tail(horizon).isna().all()


def test_oof_relative_predictions_h40():
    pred = oof_relative_predictions(horizon=40)
    assert not pred.empty
    assert {"Date", "y_true", "y_pred", "prob", "confidence"}.issubset(pred.columns)


def test_relative_study_required_keys():
    data = build_relative_study()
    assert "daily_results" in data
    assert "weekly_results" in data
    assert "key_findings" in data


def test_relative_study_h40_present():
    data = build_relative_study()
    horizons = {row["horizon"] for row in data["daily_results"] if row.get("status") == "OK"}
    assert 40 in horizons


def test_save_relative_study(tmp_path):
    out = save_relative_study(tmp_path / "relative_study.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("EMA relative")

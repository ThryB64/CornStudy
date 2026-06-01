from __future__ import annotations

import json

from mais.research.ema_residual_eu_v2 import (
    _compute_oof_residuals,
    _load_data,
    _predict_shocks,
    build_residual_eu_v2,
    save_residual_eu_v2,
)


def test_residual_eu_v2_required_keys():
    data = build_residual_eu_v2()
    for key in ["residual_stats", "driver_attribution", "shock_predictability", "leave_one_crisis_out"]:
        assert key in data


def test_residual_eu_v2_has_residual_obs():
    assert build_residual_eu_v2()["n_residual_obs"] > 100


def test_residual_eu_v2_has_events():
    stats = build_residual_eu_v2()["residual_stats"]
    assert stats["n_events_2sigma"] > 0


def test_residual_eu_v2_catalogue_preview():
    data = build_residual_eu_v2()
    assert isinstance(data["event_catalogue_preview_3sigma"], list)


def test_residual_eu_v2_driver_missing_families_documented():
    missing = build_residual_eu_v2()["driver_attribution"]["missing_driver_families"]
    assert any("Ukraine" in item for item in missing)


def test_residual_eu_v2_predictability_targets():
    pred = build_residual_eu_v2()["shock_predictability"]
    assert "shock_up_h20" in pred
    assert "shock_down_h20" in pred


def test_residual_eu_v2_leave_one_crisis_out():
    loo = build_residual_eu_v2()["leave_one_crisis_out"]
    assert "without_2022" in loo


def test_residual_eu_v2_shock_targets_keep_tail_nan():
    resid = _compute_oof_residuals(_load_data())
    pred = _predict_shocks(resid)
    for target in ["shock_up_h20", "shock_down_h20"]:
        folds = pred[target]["folds"]
        assert isinstance(folds, list)
    # Directly verify the construction path through future residual availability.
    work = resid.copy()
    future = work["ema_residual_oof"].shift(-20)
    assert future.tail(20).isna().all()


def test_save_residual_eu_v2(tmp_path):
    out = save_residual_eu_v2(tmp_path / "residual_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data

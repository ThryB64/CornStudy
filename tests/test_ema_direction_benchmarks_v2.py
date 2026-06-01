from __future__ import annotations

import json

from mais.research.ema_direction_benchmarks_v2 import (
    _load_dataset,
    build_direction_benchmarks_v2,
    save_direction_benchmarks_v2,
)


def test_direction_benchmarks_v2_required_keys():
    data = build_direction_benchmarks_v2()
    for key in ["daily_results", "weekly_results", "leave_one_2022_out", "key_findings"]:
        assert key in data


def test_direction_benchmarks_v2_has_targets():
    assert "basis_reversion_h20" in build_direction_benchmarks_v2()["targets"]


def test_direction_benchmarks_v2_daily_metrics():
    rows = [r for r in build_direction_benchmarks_v2()["daily_results"] if "da" in r]
    assert rows
    assert "balanced_accuracy" in rows[0]
    assert "majority_baseline_da" in rows[0]
    assert "lift_vs_majority" in rows[0]
    assert "mcc" in rows[0]


def test_direction_benchmarks_v2_weekly_metrics():
    rows = build_direction_benchmarks_v2()["weekly_results"]
    assert rows


def test_direction_benchmarks_v2_bh_present():
    rows = [r for r in build_direction_benchmarks_v2()["daily_results"] if "da" in r]
    assert "bh_q_value" in rows[0]


def test_direction_benchmarks_v2_loco_2022():
    data = build_direction_benchmarks_v2()
    assert "basis_reversion_h20" in data["leave_one_2022_out"]


def test_direction_benchmarks_v2_future_targets_keep_tail_nan():
    df = _load_dataset()
    targets = {
        "y_up_h20_ema_raw": 20,
        "y_up_h40_ema_raw": 40,
        "y_ema_outperforms_cbot_h20": 20,
        "y_ema_outperforms_cbot_h40": 40,
        "basis_reversion_h20": 20,
        "ema_vol_high_h20": 20,
        "eu_residual_shock_up_h20": 20,
        "eu_residual_shock_down_h20": 20,
    }
    for target, horizon in targets.items():
        assert df[target].tail(horizon).isna().all(), target


def test_direction_benchmarks_v2_key_findings():
    findings = build_direction_benchmarks_v2()["key_findings"]
    assert "overall_verdict" in findings
    assert "best_by_da_label" in findings
    assert "robust_best_signal_label" in findings


def test_direction_benchmarks_v2_robust_selection_present():
    data = build_direction_benchmarks_v2()
    selection = data["robust_signal_selection"]
    assert selection["selection_rule"].startswith("Sort by AUC")
    assert selection["ranked_signals"]
    assert selection["robust_best_signal"]["robust_rank"] == 1


def test_save_direction_benchmarks_v2(tmp_path):
    out = save_direction_benchmarks_v2(tmp_path / "direction_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "daily_results" in data

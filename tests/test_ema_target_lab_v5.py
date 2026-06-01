from __future__ import annotations

import json

from mais.research.ema_target_lab_v5 import (
    build_target_frame,
    build_target_lab_v5,
    save_target_lab_v5,
)


def test_target_frame_has_new_targets():
    frame = build_target_frame((20,))
    expected = {
        "y_rel_outperform_h20",
        "y_rel_large_outperform_h20",
        "y_rel_large_underperform_h20",
        "y_basis_compress_h20",
        "y_basis_reverts_to_normal_h20",
        "y_basis_widens_h20",
        "y_rel_outperform_after_cbot_weak_h20",
        "y_rel_outperform_when_basis_extreme_h20",
    }
    assert expected.issubset(frame.columns)


def test_target_frame_keeps_tail_nan():
    frame = build_target_frame((40,))
    assert frame["y_rel_outperform_h40"].tail(40).isna().all()
    assert frame["y_rel_large_outperform_h40"].tail(40).isna().all()


def test_target_lab_required_keys():
    data = build_target_lab_v5()
    assert "results" in data
    assert "target_catalog" in data
    assert "family_summary" in data
    assert "key_findings" in data


def test_target_lab_tests_many_targets():
    data = build_target_lab_v5()
    assert data["key_findings"]["n_targets_tested"] >= 18
    assert data["key_findings"]["n_ok"] > 0


def test_target_lab_has_verdicts():
    verdicts = {row["verdict"] for row in build_target_lab_v5()["results"]}
    assert verdicts
    assert verdicts.issubset({"PROMISING_TARGET", "WATCHLIST_TARGET", "NO_GO_TARGET", "SKIPPED"})


def test_save_target_lab_v5(tmp_path):
    out = save_target_lab_v5(tmp_path / "target_lab.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("Exploratory EMA target")

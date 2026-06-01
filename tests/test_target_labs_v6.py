from __future__ import annotations

import json

from mais.research.target_labs_v6 import (
    build_target_frames_v6,
    build_target_labs_v6,
    save_target_labs_v6,
)


def test_target_frames_v6_have_ema_and_cbot_targets():
    frames = build_target_frames_v6()
    assert "ema" in frames
    assert "cbot" in frames
    assert "y_rel_outperform_h40" in frames["ema"].columns
    assert "y_cbot_up_h60" in frames["cbot"].columns


def test_target_frames_v6_keep_tail_nan():
    frames = build_target_frames_v6()
    assert frames["ema"]["y_rel_outperform_h120"].tail(120).isna().all()
    assert frames["cbot"]["y_cbot_up_h90"].tail(90).isna().all()


def test_target_labs_v6_required_keys():
    data = build_target_labs_v6()
    assert "support" in data
    assert "results" in data
    assert "key_findings" in data


def test_target_labs_v6_evaluates_both_markets():
    markets = {row["market"] for row in build_target_labs_v6()["results"]}
    assert {"ema", "cbot"}.issubset(markets)


def test_target_labs_v6_flags_rare_targets():
    data = build_target_labs_v6()
    assert all("rare" in row for row in data["results"])
    assert data["key_findings"]["n_targets"] >= 20


def test_save_target_labs_v6(tmp_path):
    out = save_target_labs_v6(tmp_path / "target_labs.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("Expanded V6")

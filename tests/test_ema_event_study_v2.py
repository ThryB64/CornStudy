from __future__ import annotations

import json

from mais.research.ema_event_study_v2 import build_event_study_v2, save_event_study_v2


def test_event_study_v2_required_keys():
    data = build_event_study_v2()
    assert "threshold_event_study" in data
    assert "named_event_windows" in data


def test_event_study_v2_thresholds():
    events = build_event_study_v2()["threshold_event_study"]
    assert "abs_ret_gt_3pct" in events
    assert "abs_ret_gt_5pct" in events


def test_event_study_v2_named_windows():
    named = build_event_study_v2()["named_event_windows"]
    assert "mars_publication_window_proxy" in named


def test_save_event_study_v2(tmp_path):
    out = save_event_study_v2(tmp_path / "event_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data

from __future__ import annotations

import json

from mais.research.ema_data_quality_split import build_data_quality_split, save_data_quality_split


def test_data_quality_split_required_keys():
    data = build_data_quality_split()
    assert "splits" in data
    assert "key_findings" in data


def test_data_quality_split_has_core_splits():
    splits = build_data_quality_split()["splits"]
    assert "all_data" in splits
    assert "proxy_dominant" in splits
    assert "official_recent" in splits


def test_data_quality_split_has_targets():
    split = build_data_quality_split()["splits"]["all_data"]
    assert "relative_ema_outperformance_h40" in split["targets"]
    assert "ema_direction_absolute_h40" in split["targets"]
    assert "basis_reversion_h20" in split["targets"]


def test_official_recent_can_be_too_short():
    official = build_data_quality_split()["splits"]["official_recent"]
    assert official["summary"]["n_rows"] >= 0
    assert "relative_ema_outperformance_h40" in official["targets"]


def test_save_data_quality_split(tmp_path):
    out = save_data_quality_split(tmp_path / "quality_split.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "source_quality" in data

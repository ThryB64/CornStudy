from __future__ import annotations

import json

from mais.research.ema_premium_indicator import build_premium_indicator, save_premium_indicator


def test_premium_indicator_required_keys():
    data = build_premium_indicator()
    assert "latest_snapshot" in data
    assert "historical_reversion_stats" in data
    assert "key_findings" in data


def test_premium_indicator_snapshot_fields():
    snap = build_premium_indicator()["latest_snapshot"]
    assert "basis_eur_t" in snap
    assert "basis_zscore_52w" in snap
    assert "premium_zone" in snap
    assert "relative_signal" in snap


def test_premium_indicator_reversion_stats_cover_horizons():
    stats = build_premium_indicator()["historical_reversion_stats"]
    horizons = {row["horizon_days"] for row in stats}
    assert {20, 40, 60}.issubset(horizons)


def test_premium_indicator_scope_is_relative():
    data = build_premium_indicator()
    assert "not absolute EMA up/down" in data["scope"]


def test_save_premium_indicator(tmp_path):
    out = save_premium_indicator(tmp_path / "premium_indicator.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "source_quality" in data

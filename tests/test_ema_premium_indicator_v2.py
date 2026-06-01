from __future__ import annotations

import json

from mais.research.ema_premium_indicator_v2 import (
    build_premium_indicator_v2,
    save_premium_indicator_v2,
)


def test_premium_indicator_v2_required_keys():
    data = build_premium_indicator_v2()
    assert "snapshot" in data
    assert "history_summary" in data
    assert data["source_quality"] == "exploratoire_barchart_proxy"


def test_premium_indicator_v2_signal_is_known():
    signal = build_premium_indicator_v2()["snapshot"]["premium_signal"]
    assert signal in {"EU_PREMIUM_BULLISH", "EU_PREMIUM_BEARISH", "NEUTRAL", "UNCERTAIN"}


def test_premium_indicator_v2_scope_is_relative():
    data = build_premium_indicator_v2()
    assert "not an absolute EMA up/down signal" in data["scope"]


def test_premium_indicator_v2_has_history_accuracy():
    hist = build_premium_indicator_v2()["history_summary"]
    assert hist["n"] > 0
    assert 0 <= hist["medium_high_coverage"] <= 1


def test_save_premium_indicator_v2(tmp_path):
    out = save_premium_indicator_v2(tmp_path / "premium_indicator_v2.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "premium_score" in data["snapshot"]

from __future__ import annotations

import json

from mais.research.ema_seasonal_premium_regimes import (
    build_seasonal_premium_regimes,
    save_seasonal_premium_regimes,
)


def test_seasonal_premium_regimes_required_keys():
    data = build_seasonal_premium_regimes()
    assert "regimes" in data
    assert "key_findings" in data


def test_seasonal_premium_regimes_have_actions():
    actions = {row["recommended_action"] for row in build_seasonal_premium_regimes()["regimes"]}
    assert actions
    assert actions <= {"TRADE_ALLOWED_RESEARCH", "CAUTION", "ABSTAIN"}


def test_seasonal_premium_regimes_have_horizons():
    horizons = {row["recommended_horizon"] for row in build_seasonal_premium_regimes()["regimes"]}
    assert horizons <= {40, 90}


def test_seasonal_premium_regimes_best_season():
    findings = build_seasonal_premium_regimes()["key_findings"]
    assert findings["best_overall_season"]
    assert findings["best_overall_horizon"] in {40, 90}


def test_save_seasonal_premium_regimes(tmp_path):
    out = save_seasonal_premium_regimes(tmp_path / "seasonal_regimes.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["scope"].startswith("Seasonal confidence")

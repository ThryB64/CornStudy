from __future__ import annotations

import json

from mais.research.ema_relative_seasonality import (
    build_relative_seasonality,
    save_relative_seasonality,
)


def test_relative_seasonality_required_keys():
    data = build_relative_seasonality()
    assert "results" in data
    assert "key_findings" in data
    assert "season_definitions" in data


def test_relative_seasonality_has_h40_h90():
    horizons = {row["horizon"] for row in build_relative_seasonality()["results"]}
    assert {40, 90}.issubset(horizons)


def test_relative_seasonality_has_ok_seasons():
    rows = [item for result in build_relative_seasonality()["results"] for item in result["seasonal_results"]]
    assert any(row.get("status") == "OK" for row in rows)


def test_relative_seasonality_reports_best_season():
    data = build_relative_seasonality()
    assert data["key_findings"]["h40_best_season"]
    assert data["key_findings"]["h90_best_season"]


def test_save_relative_seasonality(tmp_path):
    out = save_relative_seasonality(tmp_path / "seasonality.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["target_family"] == "relative_ema_outperformance"

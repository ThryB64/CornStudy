"""Tests V28 — étude météo prévue anti-leakage (offline-safe, archive synthétique)."""
from __future__ import annotations

import pandas as pd
import pytest

import mais.research.v28_forecast_weather_study as v28
from mais.features.weather_forecast import (
    ForecastLeakageError,
    assert_forecast_no_leakage,
    build_forecast_features,
    make_synthetic_forecast_archive,
)


def test_anti_leakage_guard_catches_future_run():
    fc = make_synthetic_forecast_archive(n_days=30)
    assert_forecast_no_leakage(fc)  # cohérent
    bad = fc.copy()
    bad.loc[bad.index[0], "lead_time_days"] = -1
    with pytest.raises(ForecastLeakageError):
        assert_forecast_no_leakage(bad)


def test_features_indexed_by_issue_date():
    fc = make_synthetic_forecast_archive(n_days=60)
    feats = build_forecast_features(fc, region="us")
    assert not feats.empty
    assert feats.index.name == "forecast_issue_date"
    assert any(c.startswith("fc_") for c in feats.columns)


def test_run_v28_synthetic_is_labeled_demo(monkeypatch, tmp_path):
    monkeypatch.setattr(v28, "V28_DIR", tmp_path)
    monkeypatch.setattr(v28, "load_real_archive", lambda region="us": None)
    out = v28.run_v28_all(try_network=False)
    assert out["archive_status"] == "SYNTHETIC_DEMO_ONLY"
    assert out["is_demo_synthetic"] is True
    assert out["verdict"] == "METHODOLOGY_DEMO_SYNTHETIC"
    # le pipeline tourne sans crash (AUC peut être None sur synthétique court)
    assert out["forecast_cbot"]["version"] == "V28-FORECAST-CBOT"


def test_cbot_join_runs_offline():
    fc = make_synthetic_forecast_archive(n_days=200)
    out = v28.run_forecast_cbot_study(fc, horizon=20)
    assert out["version"] == "V28-FORECAST-CBOT"
    assert out["verdict"] in {"FORECAST_CBOT_TESTED", "TOO_SHORT", "NO_FEATURES"}
    if out["verdict"] == "FORECAST_CBOT_TESTED":
        assert isinstance(out["n_features"], int)
        assert not pd.Series([out["n"]]).isna().any()

"""Tests V136 — archive météo historique (offline, fetch mocké)."""
from __future__ import annotations

import pandas as pd

import mais.collect.openmeteo_forecast_collector as collector
import mais.research.v136_weather_revision_archive as v136


def _hist(hot=True):
    rows = []
    tmax = 36.0 if hot else 22.0
    for d in pd.date_range("2026-07-01", periods=20, freq="D"):
        for zone in ("iowa", "illinois"):
            rows.append({"forecast_issue_date": d - pd.Timedelta(days=1), "forecast_valid_date": d,
                         "lead_time_days": 1, "zone": zone, "variable": "tmax", "value": tmax})
            rows.append({"forecast_issue_date": d - pd.Timedelta(days=1), "forecast_valid_date": d,
                         "lead_time_days": 1, "zone": zone, "variable": "precip", "value": 0.1})
    return pd.DataFrame(rows)


def test_offline():
    out = v136.run_v136_weather_archive(try_network=False)
    assert out["verdict"] == "OFFLINE_SKIP"
    assert out["revisions_status"] == "FORWARD_ONLY_VIA_V127"


def test_archive_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(v136, "V136_DIR", tmp_path)
    monkeypatch.setattr(v136, "ARCHIVE", tmp_path / "arch.parquet")
    monkeypatch.setattr(collector, "fetch_historical_forecast", lambda s, e, region="us": _hist(True))
    out = v136.run_v136_weather_archive(try_network=True)
    assert out["verdict"] == "WEATHER_ARCHIVE_READY"
    assert out["n_months_archived"] >= 1
    assert out["lead_available"] == 1
    assert (tmp_path / "arch.parquet").exists()


def test_data_blocked_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(v136, "V136_DIR", tmp_path)
    def _boom(s, e, region="us"):
        raise NotImplementedError("timeout")
    monkeypatch.setattr(collector, "fetch_historical_forecast", _boom)
    out = v136.run_v136_weather_archive(try_network=True)
    assert out["verdict"] == "DATA_BLOCKED"
    assert out["revisions_status"] == "FORWARD_ONLY_VIA_V127"


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v136, "V136_DIR", tmp_path)
    monkeypatch.setattr(v136, "ARCHIVE", tmp_path / "arch.parquet")
    monkeypatch.setattr(collector, "fetch_historical_forecast", lambda s, e, region="us": _hist(True))
    v136.run_v136_weather_archive(try_network=True)
    block = v136.weather_archive_report_block()
    assert "V136" in block

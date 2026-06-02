"""Tests V127 — météo forecast extrême + révisions (offline, fetch mocké)."""
from __future__ import annotations

import pandas as pd

import mais.collect.openmeteo_forecast_collector as collector
import mais.research.v127_weather_forecast_extremes as v127


def _forecast(issue="2026-07-01", hot=True):
    rows = []
    tmax = 36.0 if hot else 24.0
    precip = 0.2 if hot else 5.0
    for lead in range(1, 17):
        valid = pd.Timestamp(issue) + pd.Timedelta(days=lead)
        for zone in ("iowa", "illinois"):
            rows.append({"forecast_issue_date": pd.Timestamp(issue), "forecast_valid_date": valid,
                         "lead_time_days": lead, "zone": zone, "variable": "tmax", "value": tmax})
            rows.append({"forecast_issue_date": pd.Timestamp(issue), "forecast_valid_date": valid,
                         "lead_time_days": lead, "zone": zone, "variable": "precip", "value": precip})
    return pd.DataFrame(rows)


def test_extreme_metrics_hot():
    m = v127.extreme_metrics(_forecast(hot=True), issue_month=7)
    assert m["heat_days_gt32"] == 16
    assert m["heat_days_gt35"] == 16
    assert m["dry_deficit"] == 1
    assert m["stress_tier"] == "HIGH"


def test_extreme_metrics_mild():
    m = v127.extreme_metrics(_forecast(hot=False), issue_month=7)
    assert m["heat_days_gt32"] == 0
    assert m["dry_deficit"] == 0
    assert m["stress_tier"] == "LOW"


def test_run_and_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(v127, "V127_DIR", tmp_path)
    monkeypatch.setattr(v127, "JOURNAL", tmp_path / "wx.jsonl")
    monkeypatch.setattr(collector, "fetch_forecast", lambda region="us", issue=None: _forecast(hot=True))
    out = v127.run_v127_weather(try_network=True, region="us")
    assert out["verdict"] == "WEATHER_WARNING_READY"
    assert out["stress_tier"] == "HIGH"
    assert out["channel"] == "CBOT_SUPPORT"
    assert out["journal_appended"] is True
    assert out["revision_status"] == "NO_PREVIOUS_ISSUE"


def test_revision_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(v127, "V127_DIR", tmp_path)
    monkeypatch.setattr(v127, "JOURNAL", tmp_path / "wx.jsonl")
    # première émission douce, puis émission chaude -> révision positive
    monkeypatch.setattr(collector, "fetch_forecast", lambda region="us", issue=None: _forecast("2026-06-28", hot=False))
    v127.run_v127_weather(try_network=True, region="us")
    monkeypatch.setattr(collector, "fetch_forecast", lambda region="us", issue=None: _forecast("2026-07-01", hot=True))
    out = v127.run_v127_weather(try_network=True, region="us")
    assert out["revision_status"] == "OK"
    assert out["revision_vs_prev"]["d_score"] > 0


def test_offline():
    assert v127.run_v127_weather(try_network=False)["verdict"] == "OFFLINE_SKIP"

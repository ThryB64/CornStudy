"""Tests VN-E1 — capture du soir (offline + mock)."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

import mais.collect.euronext_evening_snapshots as ev


def _curve():
    return pd.DataFrame({
        "price_date": [pd.Timestamp("2026-06-11")] * 3,
        "contract_month": [8, 11, 3], "contract_year": [2026, 2026, 2027],
        "contract_code": ["EMA_Q2026", "EMA_X2026", "EMA_H2027"],
        "settlement": [224.25, 212.5, 216.0], "open_interest": [15091.0, 12379.0, 2056.0]})


def test_offline():
    assert ev.capture_evening_snapshot("18:35", try_network=False)["verdict"] == "OFFLINE_SKIP"


def test_snapshot_logged_final(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVENING_JOURNAL", tmp_path / "evening.jsonl")
    out = ev.capture_evening_snapshot(
        "19:00", event_label="WASDE", try_network=True,
        fetch_curve=lambda: _curve(), fetch_cbot=lambda: 441.25,
        collected_at_utc=datetime(2026, 6, 11, 17, 0, tzinfo=timezone.utc))  # 19:00 Paris -> FINAL
    assert out["verdict"] == "SNAPSHOT_LOGGED"
    assert out["record_status"] == "FINAL"
    assert out["curve_shape"] == "BACKWARDATION"
    j = ev.load_evening_journal()
    assert len(j) == 1 and j[0]["event_label"] == "WASDE" and j[0]["cbot_last"] == 441.25


def test_snapshot_provisional_before_cutoff(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVENING_JOURNAL", tmp_path / "evening.jsonl")
    out = ev.capture_evening_snapshot(
        "17:55", try_network=True, fetch_curve=lambda: _curve(), fetch_cbot=lambda: 441.0,
        collected_at_utc=datetime(2026, 6, 11, 15, 55, tzinfo=timezone.utc))  # 17:55 Paris -> PROVISIONAL
    assert out["record_status"] == "PROVISIONAL"


def test_no_curve(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVENING_JOURNAL", tmp_path / "evening.jsonl")
    def _boom():
        raise NotImplementedError("network")
    out = ev.capture_evening_snapshot("18:35", try_network=True, fetch_curve=_boom)
    assert out["verdict"] == "NO_CURVE"

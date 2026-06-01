"""Tests V42 — automation officielle (calendrier + sessions + proxy/officiel)."""
from __future__ import annotations

import pandas as pd

import mais.ops.official_automation as auto
from mais.research.data_freshness import compute_freshness


def test_update_market_sessions_append_only(tmp_path, monkeypatch):
    monkeypatch.setattr(auto, "MARKET_SESSIONS_PARQUET", tmp_path / "ms.parquet")
    monkeypatch.setattr(auto, "MARKET_SESSIONS_CSV", tmp_path / "ms.csv")
    r1 = auto.update_market_sessions(as_of="2026-06-01", lookback_days=10)
    r2 = auto.update_market_sessions(as_of="2026-06-08", lookback_days=10)
    assert r2["n_days"] >= r1["n_days"]  # append, pas d'écrasement
    assert r2["no_session_days"] >= 2


def test_run_v42_weekend_is_not_a_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(auto, "V42_DIR", tmp_path)
    monkeypatch.setattr(auto, "MARKET_SESSIONS_PARQUET", tmp_path / "ms.parquet")
    monkeypatch.setattr(auto, "MARKET_SESSIONS_CSV", tmp_path / "ms.csv")
    out = auto.run_v42_automation(master_df=None, as_of="2026-05-31")  # dimanche
    assert out["session_today"] == "NO_SESSION_WEEKEND"
    assert out["collect_expected_today"] is False
    assert out["monitoring_status"] == "OK_NO_SESSION"


def test_freshness_weekend_is_ok_via_calendar():
    df = pd.DataFrame(
        {"cbot_eur_t": [1], "ema_close": [1], "eurusd": [1], "ema_cbot_basis_zscore_52w": [1]},
        index=[pd.Timestamp("2026-05-29")])
    r = compute_freshness(df, as_of=pd.Timestamp("2026-05-31"))
    assert r["staleness_days"] == 0
    assert r["freshness_verdict"] == "OK"
    assert r["calendar"]["missing_explained_by_calendar"] is True
    assert len(r["calendar"]["non_session_days_since_last_data"]) == 2


def test_proxy_stats_fallback_to_snapshot_when_parquet_absent(tmp_path, monkeypatch):
    """CI : sans le parquet lourd, proxy_trailing_stats lit le snapshot committé."""
    import json

    import mais.research.v27_official_forward as v27

    monkeypatch.setattr(v27, "ROOT", tmp_path)  # data/processed/... n'existe pas ici
    snap = tmp_path / "proxy_trailing_stats.json"
    snap.write_text(json.dumps({"mean": 50.0, "std": 12.0, "n": 260,
                                "full_mean": 37.0, "full_std": 15.0}), encoding="utf-8")
    monkeypatch.setattr(v27, "PROXY_STATS_SNAPSHOT", snap)
    stats = v27.proxy_trailing_stats()
    assert stats is not None and stats["mean"] == 50.0 and stats["n"] == 260

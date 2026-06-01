from __future__ import annotations

import json

from mais.research.cbot_cross_market_v6 import build_cbot_cross_market_v6, save_cbot_cross_market_v6


def test_cbot_cross_market_has_required_sections():
    data = build_cbot_cross_market_v6()

    assert "cbot_cross_market" in data
    assert "ema_cbot_meta_impact" in data
    assert "ema_decomposition" in data
    assert "event_study" in data
    assert data["key_findings"]["interpretation"]


def test_cbot_cross_market_compares_base_and_cross_market_sets():
    data = build_cbot_cross_market_v6()
    feature_sets = {row["feature_set"] for row in data["cbot_cross_market"]}

    assert "cbot_base" in feature_sets
    assert "cbot_plus_ema_premium" in feature_sets
    assert "cbot_full_cross_market" in feature_sets


def test_cbot_cross_market_reports_deltas_for_ok_rows():
    data = build_cbot_cross_market_v6()
    rows = [row for row in data["cbot_cross_market"] if row["status"] == "OK" and row["feature_set"] != "cbot_base"]

    assert rows
    assert all("delta_auc_vs_cbot_base" in row for row in rows)


def test_decomposition_contains_h40_and_h90():
    data = build_cbot_cross_market_v6()

    assert "h40_all" in data["ema_decomposition"]
    assert "h90_all" in data["ema_decomposition"]


def test_event_study_contains_basis_and_wasde_events():
    data = build_cbot_cross_market_v6()
    events = {row["event"] for row in data["event_study"]}

    assert "basis_extreme_abs_z2" in events
    assert "wasde_day" in events


def test_save_cbot_cross_market_v6_writes_json(tmp_path):
    out = save_cbot_cross_market_v6(tmp_path / "cbot_cross_market_v6.json")
    data = json.loads(out.read_text(encoding="utf-8"))

    assert out.exists()
    assert data["key_findings"]["best_cbot_cross_market"]

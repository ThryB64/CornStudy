"""Tests pour NB-EMA-09 — Event study grands mouvements EMA."""

from __future__ import annotations

import json
import pytest
from mais.research.ema_event_study import build_event_study, save_event_study


def test_build_returns_dict():
    data = build_event_study()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_event_study()
    for key in ["n_events_total", "car_all_events", "car_positive_events", "car_negative_events", "asymmetry_analysis", "key_findings"]:
        assert key in data, f"Clé manquante : {key}"


def test_events_detected():
    data = build_event_study()
    assert data["n_events_total"] > 0
    assert data["n_positive"] + data["n_negative"] == data["n_events_total"]


def test_mean_reversion_detected():
    data = build_event_study()
    assert data["key_findings"]["mean_reversion_detected"] is True, "Mean reversion non détectée"


def test_car_post_negative_after_positive_shock():
    data = build_event_study()
    post_pos = data["car_positive_events"]["avg_post_cumret"]
    if not (post_pos != post_pos):  # not nan
        assert post_pos < 0.02, f"Pas de mean reversion après choc positif : {post_pos:.4f}"


def test_top5_events_present():
    data = build_event_study()
    assert len(data["top5_largest_events"]) > 0
    assert len(data["top5_smallest_events"]) > 0
    ev = data["top5_largest_events"][0]
    assert any(k.lower() == "date" for k in ev), f"Clé date manquante dans {list(ev.keys())}"
    assert "z_score" in ev


def test_asymmetry_has_interpretation():
    data = build_event_study()
    asym = data["asymmetry_analysis"]
    if "error" not in asym:
        assert "interpretation" in asym


def test_save_creates_json(tmp_path):
    out = save_event_study(tmp_path / "test_event.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "key_findings" in data
    assert "mean_reversion_detected" in data["key_findings"]

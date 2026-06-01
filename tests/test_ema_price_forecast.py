"""Tests pour NB-EMA-12 — Prévision prix EMA expérimental."""

from __future__ import annotations

import json
import pytest
from mais.research.ema_price_forecast import build_price_forecast, save_price_forecast


def test_build_returns_dict():
    data = build_price_forecast()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_price_forecast()
    for key in ["horizons", "models", "key_findings"]:
        assert key in data, f"Clé manquante : {key}"


def test_all_horizons_present():
    data = build_price_forecast()
    for H in [5, 20, 60]:
        assert f"H{H}" in data["models"], f"Horizon H{H} manquant"


def test_naive_benchmark_present():
    data = build_price_forecast()
    for H in [5, 20, 60]:
        naive = data["models"][f"H{H}"]["naive"]
        assert "rmse" in naive
        assert naive["rmse"] > 0


def test_basis_mr_has_note():
    data = build_price_forecast()
    bmr = data["models"]["H5"]["basis_mean_reversion"]
    if "error" not in bmr:
        assert "note" in bmr, "Note de mise en garde manquante"


def test_key_findings_experimental_note():
    data = build_price_forecast()
    note = data["key_findings"].get("note", "")
    assert len(note) > 0


def test_save_creates_json(tmp_path):
    out = save_price_forecast(tmp_path / "test_forecast.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "models" in data
    assert "key_findings" in data

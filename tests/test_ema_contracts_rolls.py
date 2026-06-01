"""Tests pour NB-EMA-02 — Contrats EMA et rolls."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_contracts_rolls import build_contracts_rolls, save_contracts_rolls


def test_build_contracts_rolls_returns_dict():
    data = build_contracts_rolls()
    assert isinstance(data, dict)


def test_required_keys_present():
    data = build_contracts_rolls()
    for key in [
        "contract_lifecycle_by_crop_year",
        "roll_stats",
        "pct_windows_crossing_roll",
        "raw_vs_adjusted",
        "active_contracts_per_day",
        "key_findings",
    ]:
        assert key in data, f"Clé manquante : {key}"


def test_roll_stats_keys():
    data = build_contracts_rolls()
    rs = data["roll_stats"]
    for k in ["n_rolls", "mean_abs_gap", "median_abs_gap", "max_abs_gap", "pct_gaps_gt_5", "pct_gaps_gt_15"]:
        assert k in rs, f"Clé manquante dans roll_stats : {k}"


def test_n_rolls_positive():
    data = build_contracts_rolls()
    assert data["roll_stats"]["n_rolls"] > 0


def test_avg_roll_gap_range():
    data = build_contracts_rolls()
    avg = data["roll_stats"]["mean_abs_gap"]
    assert 5.0 <= avg <= 20.0, f"avg_roll_gap inattendu : {avg:.2f}"


def test_max_roll_gap_known():
    data = build_contracts_rolls()
    max_gap = data["roll_stats"]["max_abs_gap"]
    assert 50.0 <= max_gap <= 60.0, f"max_roll_gap inattendu : {max_gap:.2f} (attendu ~54.25)"


def test_pct_crossing_horizons():
    data = build_contracts_rolls()
    pc = data["pct_windows_crossing_roll"]
    assert "H20" in pc and "H40" in pc and "H60" in pc
    assert pc["H20"] < pc["H40"] < pc["H60"], "Les pourcentages doivent croître avec l'horizon"
    assert pc["H60"] >= 0.95, f"H60 devrait être ~99% : {pc['H60']:.3f}"


def test_active_contracts_pct_2plus():
    data = build_contracts_rolls()
    pct = data["active_contracts_per_day"]["pct_2plus"]
    assert 0.10 <= pct <= 0.20, f"pct_2plus inattendu : {pct:.3f} (attendu ~14.9%)"


def test_lifecycle_has_month_codes():
    data = build_contracts_rolls()
    lifecycle = data["contract_lifecycle_by_crop_year"]
    assert len(lifecycle) > 0
    first_cy = next(iter(lifecycle.values()))
    assert len(first_cy) > 0


def test_raw_vs_adjusted_keys():
    data = build_contracts_rolls()
    rva = data["raw_vs_adjusted"]
    assert "corr_returns" in rva or "error" in rva


def test_save_contracts_rolls_creates_json(tmp_path):
    out = save_contracts_rolls(tmp_path / "test_contracts_rolls.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "roll_stats" in data
    assert "pct_windows_crossing_roll" in data

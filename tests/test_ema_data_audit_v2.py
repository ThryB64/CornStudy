"""Tests pour NB-EMA-01 — Audit données EMA v2."""

from __future__ import annotations

import json

from mais.research.ema_data_audit_v2 import build_data_audit_v2, save_audit_v2


def test_build_audit_v2_returns_dict():
    data = build_data_audit_v2()
    assert isinstance(data, dict)


def test_required_keys_present():
    data = build_data_audit_v2()
    for key in ["total_rows", "coverage_matrix", "coverage_verdicts", "verdict_period_ml", "gaps", "oi_stats"]:
        assert key in data, f"Clé manquante : {key}"


def test_total_rows():
    data = build_data_audit_v2()
    assert data["total_rows"] > 0


def test_coverage_matrix_has_month_codes():
    data = build_data_audit_v2()
    matrix = data["coverage_matrix"]
    assert len(matrix) > 0
    first_year = next(iter(matrix.values()))
    for mc in ["H", "M", "Q", "X"]:
        assert mc in first_year, f"Mois {mc} manquant dans la matrice"


def test_verdict_period_ml_is_string():
    data = build_data_audit_v2()
    verd = data["verdict_period_ml"]
    assert isinstance(verd, str)
    assert len(verd) > 0


def test_gaps_is_list():
    data = build_data_audit_v2()
    assert isinstance(data["gaps"], list)


def test_active_contracts_pct_2plus_matches_known():
    data = build_data_audit_v2()
    pct = data["active_contracts_per_day"]["pct_2plus"]
    assert 0.10 <= pct <= 0.25, f"pct_2plus inattendu: {pct:.3f} (attendu ~14.9%)"


def test_save_audit_v2_creates_json(tmp_path):
    out = save_audit_v2(tmp_path / "test_audit_v2.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "verdict_period_ml" in data
    assert "coverage_matrix" in data

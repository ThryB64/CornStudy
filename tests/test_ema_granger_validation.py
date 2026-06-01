"""Tests pour VALID-GRANGER-01 — Validation Granger EMA→CBOT (5 tests)."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_granger_validation import build_granger_validation, save_granger_validation


def test_build_returns_dict():
    data = build_granger_validation()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_granger_validation()
    for key in [
        "n_obs_total",
        "test1_temporal_robustness",
        "test2_lag_robustness",
        "test3_eur_usd_neutralization",
        "test4_oof_validation",
        "test5_exclude_2022",
        "summary",
    ]:
        assert key in data, f"Clé manquante : {key}"


def test_summary_structure():
    data = build_granger_validation()
    s = data["summary"]
    assert "verdicts" in s
    assert "n_robust_or_confirmed" in s
    assert "overall_verdict" in s
    assert s["overall_verdict"] in ("CONFIRMED", "PARTIAL", "REJECTED")
    assert len(s["verdicts"]) == 5


def test_all_five_tests_present():
    data = build_granger_validation()
    s = data["summary"]
    for t in ["t1", "t2", "t3", "t4", "t5"]:
        assert t in s["verdicts"], f"Test {t} manquant"


def test_oof_test4_has_verdict():
    data = build_granger_validation()
    t4 = data["test4_oof_validation"]
    assert "verdict" in t4
    assert t4["verdict"] in ("OOF_CONFIRMED", "TRAIN_ONLY", "NOT_SIGNIFICANT")


def test_test5_exclude_2022_has_verdict():
    data = build_granger_validation()
    t5 = data["test5_exclude_2022"]
    assert "verdict" in t5
    assert t5["verdict"] in ("ROBUST", "2022_DRIVEN", "NOT_SIGNIFICANT")


def test_granger_results_have_p_values():
    data = build_granger_validation()
    for tkey in ["test1_temporal_robustness", "test2_lag_robustness"]:
        t = data[tkey]
        assert "verdict" in t


def test_n_obs_sufficient():
    data = build_granger_validation()
    assert data["n_obs_total"] >= 2000, f"Trop peu d'observations : {data['n_obs_total']}"


def test_overall_verdict_matches_count():
    data = build_granger_validation()
    s = data["summary"]
    n = s["n_robust_or_confirmed"]
    ov = s["overall_verdict"]
    if n >= 4:
        assert ov == "CONFIRMED"
    elif n >= 2:
        assert ov == "PARTIAL"
    else:
        assert ov == "REJECTED"


def test_save_creates_json(tmp_path):
    out = save_granger_validation(tmp_path / "test_granger.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "summary" in data
    assert "overall_verdict" in data["summary"]

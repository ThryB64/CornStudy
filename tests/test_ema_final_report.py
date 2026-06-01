"""Tests pour NB-EMA-14 — Rapport de synthèse final."""

from __future__ import annotations

import json
import pytest
from mais.research.ema_final_report import build_final_report, save_final_report


def test_build_returns_dict():
    data = build_final_report()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_final_report()
    for key in ["key_metrics", "verdict_table", "main_conclusions", "guiding_phrase", "data_caveat"]:
        assert key in data, f"Clé manquante : {key}"


def test_all_artefacts_loaded():
    data = build_final_report()
    assert data["artefacts_loaded"] >= 10, f"Moins de 10 artefacts chargés : {data['artefacts_loaded']}"
    assert len(data["artefacts_missing"]) == 0, f"Artefacts manquants : {data['artefacts_missing']}"


def test_verdict_table_has_entries():
    data = build_final_report()
    assert len(data["verdict_table"]) >= 5
    for v in data["verdict_table"]:
        assert "finding" in v
        assert "verdict" in v


def test_cointegration_confirmed():
    data = build_final_report()
    coint_verdict = next((v for v in data["verdict_table"] if "Cointégration" in v["finding"]), None)
    assert coint_verdict is not None
    assert coint_verdict["verdict"] == "CONFIRMÉ"


def test_granger_oof_rejected():
    data = build_final_report()
    granger_oof = next((v for v in data["verdict_table"] if "OOF" in v["finding"]), None)
    assert granger_oof is not None
    assert granger_oof["verdict"] == "REJECTED"


def test_guiding_phrase_present():
    data = build_final_report()
    assert "CBOT" in data["guiding_phrase"]
    assert "basis" in data["guiding_phrase"]


def test_save_creates_json(tmp_path):
    out = save_final_report(tmp_path / "test_final.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "verdict_table" in data
    assert "main_conclusions" in data

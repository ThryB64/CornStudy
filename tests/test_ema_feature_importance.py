"""Tests pour NB-EMA-10 — Importance des features EMA."""

from __future__ import annotations

import json
import pytest
from mais.research.ema_feature_importance import build_feature_importance, save_feature_importance


def test_build_returns_dict():
    data = build_feature_importance()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_feature_importance()
    for key in ["candidate_features", "mutual_info_importance", "spearman_correlation_with_y_up_h20", "top5_features", "key_findings"]:
        assert key in data, f"Clé manquante : {key}"


def test_candidate_features_found():
    data = build_feature_importance()
    assert len(data["candidate_features"]) >= 5


def test_mi_importance_has_values():
    data = build_feature_importance()
    mi = data["mutual_info_importance"]
    n_valid = sum(1 for v in mi.values() if not (v.get("importance") != v.get("importance")))
    assert n_valid >= 3, f"Trop peu de features avec MI valide : {n_valid}"


def test_top5_features_present():
    data = build_feature_importance()
    assert len(data["top5_features"]) >= 3
    assert "feature" in data["top5_features"][0]
    assert "importance" in data["top5_features"][0]


def test_top_feature_has_positive_mi():
    data = build_feature_importance()
    top = data["top5_features"][0]
    imp = top.get("importance")
    if imp is not None and imp == imp:  # not nan
        assert imp >= 0, f"MI doit être non-négatif : {imp}"


def test_key_findings_structure():
    data = build_feature_importance()
    kf = data["key_findings"]
    assert "top_feature" in kf
    assert "n_features_positive_importance" in kf
    assert kf["n_features_positive_importance"] >= 0


def test_save_creates_json(tmp_path):
    out = save_feature_importance(tmp_path / "test_fi.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "top5_features" in data

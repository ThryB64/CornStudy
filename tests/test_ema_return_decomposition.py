"""Tests pour NB-EMA-05 — Décomposition retour EMA."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_return_decomposition import build_return_decomposition, save_return_decomposition


def test_build_returns_dict():
    data = build_return_decomposition()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_return_decomposition()
    for key in ["n_obs", "global_ols", "rolling_ols_260d", "by_regime", "key_findings"]:
        assert key in data, f"Clé manquante : {key}"


def test_global_ols_keys():
    data = build_return_decomposition()
    go = data["global_ols"]
    for k in ["model_cbot_only", "model_cbot_basis", "incremental_r2_basis", "corr_regressors_cbot_basis"]:
        assert k in go, f"global_ols: clé manquante {k}"


def test_r2_cbot_basis_high():
    data = build_return_decomposition()
    r2 = data["global_ols"]["model_cbot_basis"]["r2"]
    assert r2 >= 0.85, f"R² CBOT+basis trop faible : {r2:.3f} (attendu ≥0.85)"


def test_incremental_r2_basis_positive():
    data = build_return_decomposition()
    incr = data["global_ols"]["incremental_r2_basis"]
    assert incr > 0, f"R² incrémental basis négatif : {incr:.4f}"
    r2_cbot = data["global_ols"]["model_cbot_only"]["r2"]
    r2_full = data["global_ols"]["model_cbot_basis"]["r2"]
    assert abs(incr - (r2_full - r2_cbot)) < 1e-6, "R² incrémental incohérent"


def test_corr_regressors_reported():
    data = build_return_decomposition()
    corr = data["global_ols"]["corr_regressors_cbot_basis"]
    assert -1.0 <= corr <= 1.0, f"Corrélation régresseurs hors [-1,1] : {corr}"


def test_rolling_ols_keys():
    data = build_return_decomposition()
    ro = data["rolling_ols_260d"]
    for k in ["window_days", "n_windows", "mean_r2", "min_r2", "max_r2"]:
        assert k in ro, f"rolling_ols: clé manquante {k}"
    assert ro["window_days"] == 260


def test_regime_results_present():
    data = build_return_decomposition()
    br = data["by_regime"]
    assert len(br) >= 2, "Moins de 2 régimes trouvés"
    for regime, vals in br.items():
        if "error" not in vals:
            assert "r2" in vals
            assert "n" in vals


def test_decomposition_note_in_findings():
    data = build_return_decomposition()
    note = data["key_findings"].get("decomposition_note", "")
    assert len(note) > 0, "Note décomposition manquante"


def test_save_creates_json(tmp_path):
    out = save_return_decomposition(tmp_path / "test_decomp.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "global_ols" in data
    assert "key_findings" in data

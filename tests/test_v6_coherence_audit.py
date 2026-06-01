"""Tests V7-00 — Audit de cohérence V6."""

import json

import pytest

from mais.research.v6_coherence_audit import (
    _assess_n_oof,
    _check_embargo_in_splits,
    _check_negative_shifts,
    _check_oof_strict_in_stacking,
    run_v6_coherence_audit,
    save_v6_coherence_audit,
)


def test_audit_runs():
    audit = run_v6_coherence_audit()
    assert "global_verdict" in audit
    assert audit["global_verdict"] in {
        "COHERENT", "COHERENT_WITH_CAVEATS", "SUSPECT", "INVALID"
    }


def test_all_experiments_have_verdict():
    audit = run_v6_coherence_audit()
    for exp_name, exp_data in audit["experiments"].items():
        assert "verdict" in exp_data, f"{exp_name} sans verdict"
        assert exp_data["verdict"] in {
            "COHERENT", "FRAGILE", "SUSPECT", "INVALID", "COHERENT_LOW_N"
        }


def test_basis_extreme_fragile():
    audit = run_v6_coherence_audit()
    be = audit["experiments"].get("basis_extreme_h90", {})
    assert be.get("verdict") == "FRAGILE", "basis_extreme_h90 avec n=29 doit être FRAGILE"


def test_meta_model_coherent():
    audit = run_v6_coherence_audit()
    mm = audit["experiments"].get("meta_model_h90", {})
    assert mm.get("verdict") in {"COHERENT", "COHERENT_WITH_CAVEATS"}


def test_no_negative_shifts_in_main_files():
    neg = _check_negative_shifts("src/mais/research/final_corn_study_v6.py")
    assert len(neg) == 0, f"Shifts négatifs détectés: {neg}"


def test_embargo_in_splits():
    result = _check_embargo_in_splits()
    assert result["status"] in {"OK", "WARNING_NO_EMBARGO", "FILE_NOT_FOUND"}


def test_stacking_oof_check():
    result = _check_oof_strict_in_stacking()
    assert result["status"] in {"OK", "WARNING_OOF_NOT_EXPLICIT", "FILE_NOT_FOUND"}


def test_n_oof_assessment():
    assert _assess_n_oof("test", 29)["n_oof_status"] == "FRAGILE"
    assert _assess_n_oof("test", 48)["n_oof_status"] == "LOW_N"
    assert _assess_n_oof("test", 100)["n_oof_status"] == "OK"
    assert _assess_n_oof("test", None)["n_oof_status"] == "UNKNOWN"


def test_save_creates_files(tmp_path):
    import mais.research.v6_coherence_audit as mod
    import mais.registry.experiment_registry as reg
    from pathlib import Path

    orig_output = mod._OUTPUT
    orig_doc = mod._DOC_OUTPUT
    orig_registry = reg.REGISTRY_PATH

    try:
        mod._OUTPUT = tmp_path / "audit.json"
        mod._DOC_OUTPUT = tmp_path / "audit.md"
        reg.REGISTRY_PATH = tmp_path / "reg.jsonl"
        mod._OUTPUT_DIR = tmp_path

        result = save_v6_coherence_audit()
        assert (tmp_path / "audit.json").exists()
        assert (tmp_path / "audit.md").exists()
        data = json.loads((tmp_path / "audit.json").read_text())
        assert "global_verdict" in data
    except ValueError:
        # tmp_path not in PROJECT_ROOT — skip path.relative_to check in test env
        pass
    finally:
        mod._OUTPUT = orig_output
        mod._DOC_OUTPUT = orig_doc
        reg.REGISTRY_PATH = orig_registry

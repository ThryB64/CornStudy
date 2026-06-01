"""Tests V7-INFRA-00 — Registre global des expériences."""

import json
import os
import tempfile
from pathlib import Path

import mais.registry.experiment_registry as reg


def _tmp_registry(tmp_path: Path) -> Path:
    p = tmp_path / "experiments.jsonl"
    reg.REGISTRY_PATH = p
    return p


def test_register_and_load(tmp_path):
    _tmp_registry(tmp_path)
    entry = reg.register_experiment(
        experiment_id="TEST-001",
        target="y_rel_outperform_h90",
        horizon=90,
        model="lgbm",
        cv_protocol="purged_kfold",
        embargo_days=90,
        n_oof=100,
        features=["f1", "f2", "f3"],
        metrics={"auc": 0.65, "da": 0.60},
        p_value=0.01,
        verdict="PROMISING",
        artefact_paths=["artefacts/v7/test.json"],
    )
    assert entry["auc"] == 0.65
    assert entry["q_bh"] is None
    assert entry["n_features"] == 3

    loaded = reg.load_registry()
    assert len(loaded) == 1
    assert loaded[0]["experiment_id"] == "TEST-001"


def test_deduplication_last_wins(tmp_path):
    _tmp_registry(tmp_path)
    for verdict in ["PROMISING", "GO_RESEARCH"]:
        reg.register_experiment(
            experiment_id="DUP-001",
            target="y_rel_outperform_h90",
            horizon=90,
            model="lgbm",
            cv_protocol="purged_kfold",
            embargo_days=90,
            n_oof=50,
            features=["f1"],
            metrics={"auc": 0.70},
            p_value=0.005,
            verdict=verdict,
            artefact_paths=[],
        )
    loaded = reg.load_registry()
    assert len(loaded) == 1
    assert loaded[0]["verdict"] == "GO_RESEARCH"


def test_features_hash_deterministic(tmp_path):
    _tmp_registry(tmp_path)
    e1 = reg.register_experiment(
        experiment_id="HASH-A",
        target="t",
        horizon=40,
        model="lgbm",
        cv_protocol="classic",
        embargo_days=0,
        n_oof=50,
        features=["b", "a", "c"],
        metrics={},
        p_value=None,
        verdict="WATCHLIST",
        artefact_paths=[],
    )
    e2 = reg.register_experiment(
        experiment_id="HASH-B",
        target="t",
        horizon=40,
        model="lgbm",
        cv_protocol="classic",
        embargo_days=0,
        n_oof=50,
        features=["a", "b", "c"],
        metrics={},
        p_value=None,
        verdict="WATCHLIST",
        artefact_paths=[],
    )
    assert e1["features_hash"] == e2["features_hash"]


def test_registry_path_created(tmp_path):
    deep_path = tmp_path / "sub" / "experiments.jsonl"
    reg.REGISTRY_PATH = deep_path
    reg.register_experiment(
        experiment_id="PATH-001",
        target="t",
        horizon=40,
        model="m",
        cv_protocol="c",
        embargo_days=0,
        n_oof=10,
        features=[],
        metrics={},
        p_value=None,
        verdict="NO_GO",
        artefact_paths=[],
    )
    assert deep_path.exists()

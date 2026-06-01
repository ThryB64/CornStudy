from __future__ import annotations

from mais.research.experiment_registry_v6 import (
    build_experiment_registry_v6,
    make_record,
    records_to_frame,
    save_registry,
    seed_registry,
)


def test_make_record_has_required_fields():
    record = make_record(
        experiment_id="TEST",
        feature_set="features",
        target="target",
        horizon=40,
        model="model",
        cv_protocol="crop_year_oof",
        metrics={"auc": 0.7},
        verdict="GO",
    )
    assert record.experiment_id == "TEST"
    assert record.config_hash
    assert record.metrics["auc"] == 0.7


def test_records_to_frame_flattens_metrics():
    frame = records_to_frame(seed_registry())
    assert "metric_n_required_fields" in frame.columns
    assert "verdict" in frame.columns
    assert len(frame) >= 3


def test_save_registry_outputs_csv_and_parquet(tmp_path):
    result = save_registry(
        seed_registry(),
        csv_path=tmp_path / "registry.csv",
        parquet_path=tmp_path / "registry.parquet",
    )
    assert result["n_records"] >= 3
    assert (tmp_path / "registry.csv").exists()
    assert (tmp_path / "registry.parquet").exists()


def test_build_experiment_registry_v6_required_fields():
    data = build_experiment_registry_v6()
    assert data["status"] == "OK"
    assert "experiment_id" in data["required_fields"]
    assert data["registry"]["n_records"] >= 3

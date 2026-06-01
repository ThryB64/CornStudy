from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.storage_benchmark_ema import run_storage_benchmark_ema, storage_baselines


def _fixture(seed: int = 17) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    ema_signal = rng.normal(size=n)
    cbot_signal = rng.normal(size=n)
    storage_value = 4.0 * ema_signal + rng.normal(scale=0.5, size=n)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": cbot_signal,
            "ema_cbot_basis": ema_signal,
            "cbot_eur_t": ema_signal * 0.2,
            "ema_data_availability_score": 1.0,
        }
    )
    targets = pd.DataFrame(
        {
            "Date": dates,
            "y_storage_value_3m": storage_value,
            "y_storage_profit_3m": (storage_value > 0).astype(float),
        }
    )
    selected = ["corn_signal", "ema_cbot_basis", "cbot_eur_t"]
    return features, targets, selected


def test_storage_baselines_compute_gain_and_da() -> None:
    features, targets, _ = _fixture()
    frame = features.merge(targets, on="Date")

    baselines = storage_baselines(frame)

    assert set(baselines) == {"always_store", "never_store", "oracle_store_if_profitable"}
    assert baselines["oracle_store_if_profitable"]["avg_gain_eur_t"] >= baselines["always_store"]["avg_gain_eur_t"]
    assert baselines["always_store"]["da"] + baselines["never_store"]["da"] == 1.0


def test_run_storage_benchmark_writes_json(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "storage_benchmark_ema.json"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    report = run_storage_benchmark_ema(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        n_bootstrap=10,
    )

    assert output_path.exists()
    assert report["best_model"]["da"] is not None
    assert report["verdict"] in {"STORAGE_USEFUL", "DA_OK_ECONOMICS_WEAK", "STORAGE_NO_GO", "NO_VALID_MODEL"}


def test_storage_benchmark_reports_economics(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "storage_benchmark_ema.json"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    report = run_storage_benchmark_ema(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        n_bootstrap=10,
    )

    assert all("avg_gain_eur_t" in row for row in report["models"])
    assert "always_store" in report["baselines"]

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.ema_storage_economic_study import (
    build_storage_frame,
    decide_storage_economic_value,
    evaluate_storage_strategy,
    run_ema_storage_economic_study,
    storage_strategy_baselines,
    walk_forward_storage_value,
)


def _fixture(seed: int = 23) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    signal = rng.normal(size=n)
    value = 4.0 * signal + rng.normal(scale=0.8, size=n)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": rng.normal(size=n),
            "ema_cbot_basis": signal,
            "cbot_eur_t": signal * 0.2,
            "ema_data_availability_score": 1.0,
        }
    )
    targets = pd.DataFrame(
        {
            "Date": dates,
            "y_storage_value_1m_raw": value * 0.4,
            "y_storage_value_3m_raw": value,
            "y_storage_value_6m_raw": value * 1.2,
        }
    )
    selected = ["corn_signal", "ema_cbot_basis", "cbot_eur_t"]
    return features, targets, selected


def test_storage_strategy_baselines_include_annual_metrics() -> None:
    features, targets, _selected = _fixture()
    frame = build_storage_frame(features, targets, max_date="2022-12-31")

    baselines = storage_strategy_baselines(frame)

    assert {"never_store", "always_store_3m", "oracle_store_3m"}.issubset(baselines)
    assert baselines["oracle_store_3m"]["avg_gain_eur_t"] >= baselines["always_store_3m"]["avg_gain_eur_t"]
    assert "avg_regret_vs_oracle_eur_t" in baselines["never_store"]
    assert baselines["always_store_3m"]["years_total"] > 0


def test_evaluate_storage_strategy_respects_decision() -> None:
    dates = pd.bdate_range("2024-01-01", periods=4)
    frame = pd.DataFrame({"Date": dates, "value": [5.0, -3.0, 2.0, -1.0]})

    result = evaluate_storage_strategy(
        frame,
        value_col="value",
        strategy_name="positive_only",
        decision=frame["value"].gt(0),
    )

    assert result["avg_gain_eur_t"] == 1.75
    assert result["pct_store"] == 0.5
    assert result["avg_regret_vs_oracle_eur_t"] == 0.0


def test_walk_forward_storage_value_outputs_predictions() -> None:
    features, targets, _selected = _fixture()
    frame = build_storage_frame(features, targets, max_date="2022-12-31")

    predictions = walk_forward_storage_value(
        frame,
        columns=["ema_cbot_basis", "cbot_eur_t"],
        value_col="y_storage_value_3m_raw",
        n_splits=3,
    )

    assert not predictions.empty
    assert "predicted_storage_value" in predictions.columns
    assert predictions["validation_year"].nunique() <= 3


def test_run_storage_economic_study_writes_outputs(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_json = tmp_path / "storage.json"
    output_md = tmp_path / "storage.md"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    payload = run_ema_storage_economic_study(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_json_path=output_json,
        output_markdown_path=output_md,
        margins_eur_t=(0.0, 3.0),
    )

    assert output_json.exists()
    assert output_md.exists()
    assert payload["best_model_strategy"] is not None
    assert payload["decision"]["verdict"] in {
        "STORAGE_ECONOMIC_PROMISING",
        "STORAGE_ECONOMIC_PARTIAL",
        "STORAGE_ECONOMIC_NO_GO",
        "NO_VALID_STORAGE_MODEL",
    }


def test_decide_storage_economic_value() -> None:
    best = {
        "strategy": "model",
        "avg_gain_eur_t": 2.0,
        "pct_years_positive": 0.75,
        "avg_regret_vs_oracle_eur_t": 1.0,
    }
    baselines = {
        "never_store": {"avg_gain_eur_t": 0.0},
        "always_store_3m": {"avg_gain_eur_t": -1.0, "avg_regret_vs_oracle_eur_t": 3.0},
    }

    decision = decide_storage_economic_value(best, baselines)

    assert decision["verdict"] == "STORAGE_ECONOMIC_PROMISING"

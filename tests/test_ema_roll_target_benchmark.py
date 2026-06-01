from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.ema_roll_target_benchmark import (
    ROLL_TARGET_VARIANTS,
    decide_roll_target,
    run_ema_roll_target_benchmark,
)


def _fixture(seed: int = 12) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    signal = rng.normal(size=n)
    noise = rng.normal(scale=1.0, size=n)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": signal * 0.3 + rng.normal(scale=0.6, size=n),
            "ema_signal": signal,
            "cbot_eur_t": signal * 0.4 + rng.normal(scale=0.5, size=n),
            "ema_data_availability_score": 1.0,
        }
    )
    adjusted = (signal > 0).astype(float)
    raw = (signal + noise > 0).astype(float)
    no_roll = adjusted.copy()
    no_roll[:150] = np.nan
    ema_targets = pd.DataFrame(
        {
            "Date": dates,
            "y_up_h20_ema_raw": raw,
            "y_up_h20_ema_adjusted": adjusted,
            "y_up_h20_ema_no_roll": no_roll,
            "y_up_h40_ema_raw": raw,
            "y_up_h40_ema_adjusted": adjusted,
            "y_up_h40_ema_no_roll": no_roll,
            "y_up_h60_ema_raw": raw,
            "y_up_h60_ema_adjusted": adjusted,
            "y_up_h60_ema_no_roll": np.nan,
        }
    )
    selected = ["corn_signal", "ema_signal", "cbot_eur_t"]
    return features, ema_targets, selected


def test_roll_target_report_writes_json_and_csv(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "roll_target.json"
    table_path = tmp_path / "roll_target.csv"
    doc_path = tmp_path / "roll_target.md"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    table, decision = run_ema_roll_target_benchmark(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        table_output_path=table_path,
        doc_output_path=doc_path,
        n_bootstrap=10,
    )

    assert set(table["target_variant"]) == set(ROLL_TARGET_VARIANTS)
    assert "bh_q_value" in table.columns
    assert output_path.exists()
    assert table_path.exists()
    assert doc_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert "target_tail_integrity" in payload
    assert decision["verdict"] in {
        "ROLL_TARGET_FIX_VALIDATED",
        "ROLL_TARGET_FIX_PROMISING",
        "ROLL_TARGET_NOT_EXPLAINED",
    }


def test_no_roll_can_be_skipped_when_target_has_no_rows(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    table, _decision = run_ema_roll_target_benchmark(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_path=tmp_path / "roll_target.json",
        table_output_path=tmp_path / "roll_target.csv",
        doc_output_path=tmp_path / "roll_target.md",
        n_bootstrap=5,
    )

    skipped = table[
        table["target_col"].eq("y_up_h60_ema_no_roll")
        & table["feature_set"].eq("cbot_ema_combined")
    ].iloc[0]
    assert skipped["status"] == "SKIPPED"
    assert skipped["target_non_null_rows"] == 0


def test_roll_target_tail_integrity_is_reported(tmp_path) -> None:
    features, targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "roll_target.json"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    run_ema_roll_target_benchmark(
        features_path=features_path,
        ema_targets_path=targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        table_output_path=tmp_path / "roll_target.csv",
        doc_output_path=tmp_path / "roll_target.md",
        n_bootstrap=5,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    audit = payload["target_tail_integrity"]
    assert audit
    assert all("tail_integrity_ok" in row for row in audit)


def test_decide_roll_target_promotes_large_adjusted_improvement() -> None:
    results = pd.DataFrame(
        {
            "horizon": [20, 20, 20],
            "target_variant": ["raw", "adjusted", "no_roll"],
            "target_col": ["raw", "adjusted", "no_roll"],
            "feature_set": ["cbot_ema_combined"] * 3,
            "status": ["OK", "OK", "SKIPPED"],
            "n_oof": [1000, 1000, 0],
            "n_features": [3, 3, 3],
            "target_non_null_rows": [1200, 1200, 0],
            "da": [0.50, 0.57, np.nan],
            "da_ci95_lo": [0.47, 0.52, np.nan],
            "da_ci95_hi": [0.53, 0.60, np.nan],
            "auc": [0.50, 0.58, np.nan],
            "auc_ci95_lo": [0.47, 0.53, np.nan],
            "auc_ci95_hi": [0.53, 0.62, np.nan],
            "top20_da": [0.52, 0.64, np.nan],
            "annual_stability": [0.4, 0.8, np.nan],
        }
    )

    decision = decide_roll_target(results)

    assert decision["verdict"] == "ROLL_TARGET_FIX_VALIDATED"
    assert decision["best_alternative"]["target_variant"] == "adjusted"

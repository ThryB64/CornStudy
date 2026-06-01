from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from mais.research.ema_benchmark import (
    TARGETS,
    apply_benjamini_hochberg,
    build_feature_sets,
    decide_pivot,
    run_ema_benchmark,
    walk_forward_da,
)


def _benchmark_fixture(seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    corn_signal = rng.normal(size=n)
    ema_signal = 0.7 * corn_signal + rng.normal(scale=0.7, size=n)
    wasde_signal = rng.normal(size=n)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": corn_signal,
            "wheat_signal": corn_signal * 0.4 + rng.normal(scale=0.4, size=n),
            "ema_signal": ema_signal,
            "cbot_eur_t": ema_signal * 0.2 + rng.normal(scale=0.2, size=n),
            "wasde_signal": wasde_signal,
            "ema_data_availability_score": 1.0,
        }
    )
    cbot_targets = pd.DataFrame({"Date": dates, "y_up_h20": (corn_signal > 0).astype(float)})
    ema_targets = pd.DataFrame(
        {
            "Date": dates,
            "y_up_h20_ema": (ema_signal > 0).astype(float),
            "y_up_h20_ema_harvest": (ema_signal + wasde_signal * 0.1 > 0).astype(float),
        }
    )
    selected = ["corn_signal", "wheat_signal", "ema_signal", "cbot_eur_t", "wasde_signal"]
    return features, cbot_targets, ema_targets, selected


def test_ic95_bootstrap_1000_draws_and_annual_stability() -> None:
    features, cbot_targets, _, _ = _benchmark_fixture()
    result = walk_forward_da(
        features[["corn_signal", "wheat_signal"]],
        cbot_targets["y_up_h20"],
        features["Date"],
        n_bootstrap=1000,
    )

    assert result["status"] == "OK"
    assert result["bootstrap_n"] == 1000
    assert result["da_ci95_lo"] <= result["da"] <= result["da_ci95_hi"]
    assert result["annual_stability"] is not None
    assert result["split_das"]


def test_benjamini_hochberg_applied() -> None:
    results = pd.DataFrame(
        {
            "target_col": ["y_up_h20", "y_up_h20", "y_up_h20"],
            "feature_set": ["cbot_full", "ema_curve_only", "cbot_ema_combined"],
            "da": [0.55, 0.60, 0.61],
            "n_oof": [1000, 1000, 1000],
        }
    )

    corrected = apply_benjamini_hochberg(results)

    assert "p_value_vs_baseline" in corrected.columns
    assert "bh_q_value" in corrected.columns
    assert "bh_reject_0_05" in corrected.columns


def test_verdict_json_produced(tmp_path) -> None:
    features, cbot_targets, ema_targets, selected = _benchmark_fixture()
    features_path = tmp_path / "features.parquet"
    cbot_targets_path = tmp_path / "targets.parquet"
    ema_targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    benchmark_path = tmp_path / "benchmark_full.json"
    decision_path = tmp_path / "pivot_decision.json"
    table_path = tmp_path / "benchmark_full.csv"
    features.to_parquet(features_path, index=False)
    cbot_targets.to_parquet(cbot_targets_path, index=False)
    ema_targets.to_parquet(ema_targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    table, decision = run_ema_benchmark(
        features_path=features_path,
        cbot_targets_path=cbot_targets_path,
        ema_targets_path=ema_targets_path,
        selection_report_path=selection_path,
        benchmark_output_path=benchmark_path,
        decision_output_path=decision_path,
        table_output_path=table_path,
        n_bootstrap=10,
    )

    assert set(table["target_col"]) == set(TARGETS)
    assert benchmark_path.exists()
    assert decision_path.exists()
    assert table_path.exists()
    assert decision["verdict"] in {"PIVOT_VALIDÉ", "PIVOT_UTILE", "CBOT_MOTEUR", "NO_GO"}


def test_no_proxy_in_benchmark(tmp_path) -> None:
    features, cbot_targets, ema_targets, selected = _benchmark_fixture()
    features["is_proxy"] = False
    features.loc[0, "is_proxy"] = True
    features_path = tmp_path / "features.parquet"
    cbot_targets_path = tmp_path / "targets.parquet"
    ema_targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    features.to_parquet(features_path, index=False)
    cbot_targets.to_parquet(cbot_targets_path, index=False)
    ema_targets.to_parquet(ema_targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    with pytest.raises(ValueError, match="Proxy EMA rows are forbidden"):
        run_ema_benchmark(
            features_path=features_path,
            cbot_targets_path=cbot_targets_path,
            ema_targets_path=ema_targets_path,
            selection_report_path=selection_path,
            benchmark_output_path=tmp_path / "benchmark.json",
            decision_output_path=tmp_path / "decision.json",
            table_output_path=tmp_path / "table.csv",
            n_bootstrap=5,
        )


def test_feature_sets_non_overlapping() -> None:
    features = ["corn_signal", "wheat_signal", "ema_signal", "cbot_eur_t", "wasde_signal"]

    sets = build_feature_sets(features)

    assert set(sets["cbot_only"]).isdisjoint(sets["ema_curve_only"])
    assert set(sets["cbot_ema_combined"]) == set(sets["cbot_only"]) | set(sets["ema_curve_only"])
    assert "ema_signal" not in sets["cbot_full"]


def test_decide_pivot_minimal_go_logic() -> None:
    results = pd.DataFrame(
        {
            "target_col": ["y_up_h20", "y_up_h20_ema"],
            "feature_set": ["cbot_full", "cbot_ema_combined"],
            "status": ["OK", "OK"],
            "n_oof": [1000, 1000],
            "n_features": [10, 12],
            "da": [0.56, 0.58],
            "da_ci95_lo": [0.52, 0.53],
            "da_ci95_hi": [0.59, 0.61],
            "auc": [0.56, 0.57],
            "auc_ci95_lo": [0.52, 0.52],
            "auc_ci95_hi": [0.60, 0.61],
            "top20_da": [0.63, 0.64],
            "annual_stability": [0.8, 0.9],
        }
    )

    decision = decide_pivot(results)

    assert decision["minimal_go"] is True
    assert decision["verdict"] == "PIVOT_VALIDÉ"

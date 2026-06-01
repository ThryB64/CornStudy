from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.ema_true_curve_benchmark import (
    FORBIDDEN_SPARSE_CURVE_TOKENS,
    build_true_curve_feature_groups,
    decide_true_curve_signal,
    run_ema_true_curve_benchmark,
)


def _fixture(seed: int = 31) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-01", "2022-12-30")
    n = len(dates)
    pure = rng.normal(size=n)
    basis = rng.normal(size=n)
    cbot = rng.normal(size=n)
    y = (0.9 * pure + 0.2 * basis > 0).astype(float)
    features = pd.DataFrame(
        {
            "Date": dates,
            "corn_signal": cbot,
            "ema_front_price_lag1": pure,
            "ema_liquid_price_lag1": pure * 0.5 + rng.normal(scale=0.2, size=n),
            "ema_harvest_nov_price_lag1": pure * 0.3 + rng.normal(scale=0.4, size=n),
            "ema_oi_total": rng.normal(size=n),
            "ema_volume_total": rng.normal(size=n),
            "ema_front_return_5d_adjusted": pure * 0.4 + rng.normal(scale=0.2, size=n),
            "ema_front_vol_20d_adjusted": np.abs(rng.normal(size=n)),
            "ema_cbot_basis": basis,
            "ema_cbot_basis_zscore_52w": basis * 0.5 + rng.normal(scale=0.2, size=n),
            "cbot_eur_t": cbot * 0.2 + rng.normal(scale=0.6, size=n),
            "ema_spread_f0_f1": rng.normal(size=n),
            "ema_curve_slope_3": rng.normal(size=n),
            "ema_data_availability_score": 1.0,
        }
    )
    cbot_targets = pd.DataFrame({"Date": dates, "y_up_h20": y})
    ema_targets = pd.DataFrame({"Date": dates, "y_up_h20_ema_raw": y})
    selected = ["corn_signal", "ema_spread_f0_f1", "ema_curve_slope_3", "ema_cbot_basis", "cbot_eur_t"]
    return features, cbot_targets, ema_targets, selected


def test_true_curve_groups_exclude_sparse_curve_tokens() -> None:
    features, _cbot_targets, _ema_targets, selected = _fixture()
    groups = build_true_curve_feature_groups(selected, available_columns=set(features.columns))

    reliable = groups["reliable_ema_with_basis"]
    selected_ema = groups["selected_ema_curve_only"]

    assert "ema_front_price_lag1" in reliable
    assert "ema_cbot_basis" in reliable
    assert "cbot_eur_t" not in reliable
    assert all(not any(token in col for token in FORBIDDEN_SPARSE_CURVE_TOKENS) for col in selected_ema)


def test_run_true_curve_benchmark_writes_outputs(tmp_path) -> None:
    features, cbot_targets, ema_targets, selected = _fixture()
    features_path = tmp_path / "features.parquet"
    cbot_targets_path = tmp_path / "targets.parquet"
    ema_targets_path = tmp_path / "ema_targets.parquet"
    selection_path = tmp_path / "selection.json"
    output_path = tmp_path / "true_curve.json"
    table_path = tmp_path / "true_curve.csv"
    features.to_parquet(features_path, index=False)
    cbot_targets.to_parquet(cbot_targets_path, index=False)
    ema_targets.to_parquet(ema_targets_path, index=False)
    selection_path.write_text(json.dumps({"selected_features": selected}), encoding="utf-8")

    table, decision = run_ema_true_curve_benchmark(
        features_path=features_path,
        cbot_targets_path=cbot_targets_path,
        ema_targets_path=ema_targets_path,
        selection_report_path=selection_path,
        output_path=output_path,
        table_output_path=table_path,
        n_bootstrap=10,
    )

    assert output_path.exists()
    assert table_path.exists()
    assert {"reliable_ema_no_basis", "basis_only", "cbot_eur_t_only"}.issubset(set(table["feature_set"]))
    assert "bh_q_value" in table.columns
    assert decision["verdict"] in {
        "PURE_EMA_SIGNAL_CONFIRMED",
        "BASIS_DRIVEN_SIGNAL",
        "CBOT_TRANSLATION_DRIVEN",
        "NO_RELIABLE_CURVE_SIGNAL",
    }


def test_decide_true_curve_signal_identifies_pure_ema_signal() -> None:
    results = pd.DataFrame(
        {
            "target_col": ["y_up_h20", "y_up_h20", "y_up_h20"],
            "feature_set": ["cbot_only", "reliable_ema_no_basis", "reliable_ema_with_basis"],
            "status": ["OK", "OK", "OK"],
            "n_oof": [1000, 1000, 1000],
            "n_features": [1, 5, 7],
            "da": [0.51, 0.58, 0.59],
            "da_ci95_lo": [0.48, 0.53, 0.54],
            "da_ci95_hi": [0.54, 0.61, 0.62],
            "auc": [0.50, 0.57, 0.58],
            "auc_ci95_lo": [0.47, 0.52, 0.53],
            "auc_ci95_hi": [0.53, 0.61, 0.62],
            "top20_da": [0.50, 0.64, 0.65],
            "annual_stability": [0.4, 0.8, 0.8],
            "bh_q_value": [1.0, 0.01, 0.01],
        }
    )

    decision = decide_true_curve_signal(results)

    assert decision["verdict"] == "PURE_EMA_SIGNAL_CONFIRMED"

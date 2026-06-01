from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.research.ema_feature_selector import (
    run_ema_feature_selection,
    select_ema_features,
)


def _frame(n: int = 160) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2018-01-01", periods=n)
    signal = rng.normal(size=n)
    return pd.DataFrame({
        "Date": dates,
        "ema_signal": signal,
        "ema_signal_clone": signal + rng.normal(0, 0.001, n),
        "corn_signal": rng.normal(size=n),
        "wasde_signal": rng.normal(size=n),
        "mostly_nan": [np.nan] * 130 + list(rng.normal(size=n - 130)),
        "constant": 1.0,
        "y_up_h20": (signal > 0).astype(int),
    })


def test_select_drops_high_nan_and_constant() -> None:
    selected, report = select_ema_features(_frame(), "y_up_h20", shap_top_n=5)

    assert "mostly_nan" not in selected
    assert "constant" not in selected
    assert "mostly_nan" in report["dropped_high_nan"]
    assert "constant" in report["dropped_constant"]


def test_select_drops_correlated_clone() -> None:
    selected, report = select_ema_features(_frame(), "y_up_h20", shap_top_n=5)
    correlated = {row["dropped"] for row in report["dropped_correlated"]}

    assert len({"ema_signal", "ema_signal_clone"} & set(selected)) == 1
    assert {"ema_signal", "ema_signal_clone"} & correlated


def test_select_limits_top_n_and_reports_family_counts() -> None:
    selected, report = select_ema_features(_frame(), "y_up_h20", shap_top_n=2)

    assert len(selected) <= 2
    assert report["n_selected"] == len(selected)
    assert "selected_by_family" in report
    assert report["max_selected_nan_rate"] is not None


def test_run_ema_feature_selection_writes_report(tmp_path) -> None:
    features = _frame().drop(columns=["y_up_h20"])
    targets = _frame()[["Date", "y_up_h20"]]
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "targets.parquet"
    output_path = tmp_path / "ema_feature_selection.json"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)

    selected, report = run_ema_feature_selection(
        features_path=features_path,
        targets_path=targets_path,
        output_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert selected == report["selected_features"]
    assert payload["n_selected"] == len(selected)
    assert payload["target_col"] == "y_up_h20"

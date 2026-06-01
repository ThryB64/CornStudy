from __future__ import annotations

import json

import numpy as np
import pandas as pd

from mais.indicator.module_a_context import SIGNAL_DEFINITIONS, compute_context_timeseries
from mais.indicator.module_a_data_status import (
    classify_signal_data_status,
    evaluate_signal_da,
    run_module_a_data_status,
)


def _features(n: int = 120) -> pd.DataFrame:
    dates = pd.bdate_range("2018-01-01", periods=n)
    x = np.sin(np.arange(n) / 8)
    return pd.DataFrame(
        {
            "Date": dates,
            "wasde_stocks_to_use_calc_z": -x,
            "ema_cbot_basis_zscore_52w": x,
            "crop_ge_zscore_seasonal": -x,
            "soy_close": 10 + x,
            "drought_composite": x,
            "export_china_pct_total": np.nan,
            "wasde_exports_surprise_vs_5y": x,
            "wasde_ending_stocks_surprise_vs_5y": -x,
            "cot_mm_pct_oi_percentile": np.where(x > 0, 25, 75),
            "ema_backwardation_flag": np.where(x > 0, 1.0, np.nan),
            "ema_contango_flag": np.where(x < 0, 1.0, np.nan),
            "cbot_eur_t": 190 + x,
        }
    )


def test_classify_signal_data_status_handles_real_proxy_missing_manual() -> None:
    features = _features()

    real = classify_signal_data_status("bilan_mondial", SIGNAL_DEFINITIONS["bilan_mondial"], features)
    proxy = classify_signal_data_status("bilan_stocks_eu", SIGNAL_DEFINITIONS["bilan_stocks_eu"], features)
    manual = classify_signal_data_status("ukraine_corridor", SIGNAL_DEFINITIONS["ukraine_corridor"], features)
    missing = classify_signal_data_status("export_pace_eu", SIGNAL_DEFINITIONS["export_pace_eu"], features)

    assert real["data_status"] == "real"
    assert proxy["data_status"] == "proxy"
    assert manual["data_status"] == "manual"
    assert missing["data_status"] == "missing"
    assert proxy["coverage"] == 1.0


def test_classify_uses_active_column_not_shadowed_fallback() -> None:
    features = _features()
    status = classify_signal_data_status("china_demand", SIGNAL_DEFINITIONS["china_demand"], features)

    assert status["active_column"] == "export_china_pct_total"
    assert status["coverage"] == 0.0
    assert status["candidate_coverage"] > 0.0
    assert status["data_status"] == "missing"


def test_evaluate_signal_da_returns_weekly_accuracy() -> None:
    features = _features()
    context = compute_context_timeseries(features)
    targets = pd.DataFrame(
        {
            "Date": features["Date"],
            "y_up_h20_ema": context["signal_bilan_mondial"].gt(0).astype(float),
        }
    )

    report = evaluate_signal_da(context, targets, "bilan_mondial")

    assert report["n_weekly"] > 0
    assert report["da_weekly"] == 1.0
    assert 0.0 <= report["positive_signal_rate"] <= 1.0


def test_run_module_a_data_status_writes_json_and_markdown(tmp_path) -> None:
    features = _features(180)
    context = compute_context_timeseries(features)
    targets = pd.DataFrame(
        {
            "Date": features["Date"],
            "y_up_h20_ema": context["context_score"].gt(0).astype(float),
        }
    )
    calibration = {
        "final_weights": {
            "bilan_mondial": 0.2,
            "bilan_stocks_eu": 0.1,
            "ukraine_corridor": 0.05,
        }
    }
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "targets.parquet"
    calibration_path = tmp_path / "module_a_calibration.json"
    output_json = tmp_path / "module_a_data_status.json"
    output_md = tmp_path / "MODULE_A_DATA_STATUS.md"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)
    calibration_path.write_text(json.dumps(calibration), encoding="utf-8")

    payload = run_module_a_data_status(
        features_path=features_path,
        targets_path=targets_path,
        calibration_path=calibration_path,
        output_json_path=output_json,
        output_markdown_path=output_md,
    )

    saved = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert output_json.exists()
    assert output_md.exists()
    assert payload["n_signals"] == len(SIGNAL_DEFINITIONS)
    assert payload["n_coverage_features"] <= payload["n_features"]
    assert saved["status_counts"]["manual"] == 1
    assert "Module A" in markdown
    assert "REMPLACER" in markdown


def test_decisions_include_keep_and_replace(tmp_path) -> None:
    features = _features(100)
    targets = pd.DataFrame({"Date": features["Date"], "y_up_h20_ema": np.ones(len(features))})
    features_path = tmp_path / "features.parquet"
    targets_path = tmp_path / "targets.parquet"
    features.to_parquet(features_path, index=False)
    targets.to_parquet(targets_path, index=False)

    payload = run_module_a_data_status(
        features_path=features_path,
        targets_path=targets_path,
        calibration_path=tmp_path / "missing.json",
        output_json_path=tmp_path / "out.json",
        output_markdown_path=tmp_path / "out.md",
    )

    decisions = {row["decision"] for row in payload["signals"]}
    assert "REMPLACER" in decisions
    assert {"GARDER", "GARDER_COMME_PROXY", "GARDER_PRIORITAIRE"} & decisions

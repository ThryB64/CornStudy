from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from typer.testing import CliRunner

import mais.cli as cli
from mais.cli import app

runner = CliRunner()


def test_ema_cli_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "build-ema-dataset" in result.output
    assert "predict-ema" in result.output
    assert "data-quality" in result.output


def test_report_cli_help_lists_daily_and_weekly() -> None:
    result = runner.invoke(app, ["report", "--help"])

    assert result.exit_code == 0
    assert "daily" in result.output
    assert "weekly" in result.output


def test_build_ema_dataset_calls_pipeline(monkeypatch) -> None:
    import mais.features as features_mod
    import mais.features.ema_targets as targets_mod
    import mais.features.euronext_continuous as continuous_mod
    import mais.features.euronext_curve as curve_mod

    calls: list[str] = []

    def fake_continuous() -> dict[str, int]:
        calls.append("continuous")
        return {"ema_front_continuous_raw.parquet": 2}

    def fake_curve() -> pd.DataFrame:
        calls.append("curve")
        return pd.DataFrame({"Date": pd.date_range("2026-01-01", periods=2)})

    def fake_targets() -> pd.DataFrame:
        calls.append("targets")
        return pd.DataFrame({"Date": pd.date_range("2026-01-01", periods=2)})

    def fake_features() -> pd.DataFrame:
        calls.append("features")
        return pd.DataFrame({"Date": pd.date_range("2026-01-01", periods=2), "ema_x": [1.0, 2.0]})

    monkeypatch.setattr(continuous_mod, "build_and_save_continuous_series", fake_continuous)
    monkeypatch.setattr(curve_mod, "build_and_save_curve_features", fake_curve)
    monkeypatch.setattr(targets_mod, "build_and_save_ema_targets", fake_targets)
    monkeypatch.setattr(features_mod, "build_features", fake_features)

    result = runner.invoke(app, ["build-ema-dataset"])

    assert result.exit_code == 0
    assert calls == ["continuous", "curve", "targets", "features"]
    assert "EMA dataset OK" in result.output


def test_predict_ema_writes_signal_json(monkeypatch, tmp_path: Path) -> None:
    features_path = tmp_path / "features.parquet"
    predictions_dir = tmp_path / "predictions"
    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    pd.DataFrame(
        {
            "Date": dates,
            "ema_cbot_basis_zscore_52w": np.linspace(-1.0, 1.0, len(dates)),
            "ema_cbot_basis": np.linspace(20.0, 25.0, len(dates)),
        }
    ).to_parquet(features_path, index=False)
    monkeypatch.setattr(cli, "FEATURES_PARQUET", features_path)
    monkeypatch.setattr(cli, "PREDICTIONS_DAILY_DIR", predictions_dir)

    result = runner.invoke(app, ["predict-ema", "--date", "2026-02-12"])

    assert result.exit_code == 0
    out_path = predictions_dir / "2026-02-11_ema_signal.json"
    assert out_path.exists()
    payload = pd.read_json(out_path, typ="series")
    assert payload["model_status"] == "module_a_context_rule_until_ema_models_are_validated"


def test_data_quality_command_uses_requested_date(monkeypatch) -> None:
    import mais.collect.data_quality as quality_mod

    seen: list[date] = []

    def fake_quality(report_date: date) -> Path:
        seen.append(report_date)
        return Path("quality.json")

    monkeypatch.setattr(quality_mod, "generate_quality_report", fake_quality)

    result = runner.invoke(app, ["data-quality", "--date", "2026-05-20"])

    assert result.exit_code == 0
    assert seen == [date(2026, 5, 20)]
    assert "quality.json" in result.output

"""Tests DATA-PATHS-01 — chemins EMA dans paths.py."""

from mais.paths import (
    EMA_BACKFILL_DIR,
    EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT,
    EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS,
    EMA_BARCHART_PROBE_REPORT,
    EMA_BARCHART_PROBE_RESULTS,
    EMA_BENCHMARK_DIR,
    EMA_CONSTANT_30D,
    EMA_CONSTANT_60D,
    EMA_CONSTANT_120D,
    EMA_CONTINUOUS_PROBE_REPORT,
    EMA_CONTINUOUS_PROBE_RESULTS,
    EMA_CONTRACT_DAILY,
    EMA_CONTRACT_REFERENCE,
    EMA_CONTRACTS_RAW_DIR,
    EMA_CURVE_DAILY,
    EMA_CURVE_FEATURES,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    EMA_LIQUID_ADJUSTED,
    EMA_LIQUID_RAW,
    EMA_MOST_LIQUID,
    EMA_PROCESSED_DIR,
    EMA_ROLL_AUDIT,
    PREDICTIONS_DAILY_DIR,
    PREDICTIONS_WEEKLY_DIR,
    REPORTS_QUALITY_DIR,
    REPORTS_WEEKLY_EMA_DIR,
)


def test_ema_paths_importable() -> None:
    """Tous les chemins EMA sont importables et de type Path."""
    from pathlib import Path

    for p in [
        EMA_CONTRACTS_RAW_DIR, EMA_BACKFILL_DIR, EMA_PROCESSED_DIR,
        EMA_CONTRACT_REFERENCE, EMA_CONTRACT_DAILY, EMA_CURVE_DAILY,
        EMA_FRONT_RAW, EMA_FRONT_ADJUSTED,
        EMA_LIQUID_RAW, EMA_LIQUID_ADJUSTED, EMA_MOST_LIQUID, EMA_HARVEST_NOV,
        EMA_CONSTANT_30D, EMA_CONSTANT_60D, EMA_CONSTANT_120D,
        EMA_CURVE_FEATURES, PREDICTIONS_DAILY_DIR, PREDICTIONS_WEEKLY_DIR,
        REPORTS_QUALITY_DIR, REPORTS_WEEKLY_EMA_DIR,
        EMA_BENCHMARK_DIR, EMA_ROLL_AUDIT,
        EMA_BARCHART_PROBE_RESULTS, EMA_BARCHART_PROBE_REPORT,
        EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS, EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT,
        EMA_CONTINUOUS_PROBE_RESULTS, EMA_CONTINUOUS_PROBE_REPORT,
    ]:
        assert isinstance(p, Path), f"{p} n'est pas un Path"


def test_ema_paths_hierarchy() -> None:
    """Les chemins EMA processed sont bien sous PROCESSED_DIR/euronext."""
    assert EMA_CONTRACT_DAILY.parent == EMA_PROCESSED_DIR
    assert EMA_CONTRACT_REFERENCE.parent == EMA_PROCESSED_DIR
    assert EMA_CURVE_DAILY.parent == EMA_PROCESSED_DIR
    assert EMA_FRONT_RAW.parent == EMA_PROCESSED_DIR
    assert EMA_FRONT_ADJUSTED.parent == EMA_PROCESSED_DIR
    assert EMA_LIQUID_RAW.parent == EMA_PROCESSED_DIR
    assert EMA_LIQUID_ADJUSTED.parent == EMA_PROCESSED_DIR
    assert EMA_CURVE_FEATURES.parent == EMA_PROCESSED_DIR
    assert EMA_BARCHART_PROBE_RESULTS.parent == EMA_BARCHART_PROBE_REPORT.parent
    assert EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS.parent == EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT.parent
    assert EMA_CONTINUOUS_PROBE_RESULTS.parent == EMA_CONTINUOUS_PROBE_REPORT.parent


def test_ensure_dirs_creates_ema_dirs(tmp_path, monkeypatch) -> None:
    """ensure_dirs() crée les répertoires EMA sans lever d'exception."""
    import mais.paths as paths_module

    monkeypatch.setattr(paths_module, "EMA_CONTRACTS_RAW_DIR", tmp_path / "ema_contracts")
    monkeypatch.setattr(paths_module, "EMA_BACKFILL_DIR", tmp_path / "ema_backfill")
    monkeypatch.setattr(paths_module, "EMA_PROCESSED_DIR", tmp_path / "ema_processed")
    monkeypatch.setattr(paths_module, "PREDICTIONS_DAILY_DIR", tmp_path / "pred_daily")
    monkeypatch.setattr(paths_module, "PREDICTIONS_WEEKLY_DIR", tmp_path / "pred_weekly")
    monkeypatch.setattr(paths_module, "REPORTS_QUALITY_DIR", tmp_path / "rep_quality")
    monkeypatch.setattr(paths_module, "REPORTS_WEEKLY_EMA_DIR", tmp_path / "rep_weekly")
    monkeypatch.setattr(paths_module, "EMA_BENCHMARK_DIR", tmp_path / "benchmark")
    monkeypatch.setattr(paths_module, "EMA_ROLL_AUDIT", tmp_path / "roll_audit" / "report.txt")
    monkeypatch.setattr(
        paths_module,
        "EMA_BARCHART_PROBE_RESULTS",
        tmp_path / "euronext_artifacts" / "barchart_probe_results.csv",
    )
    monkeypatch.setattr(
        paths_module,
        "EMA_BARCHART_PROBE_REPORT",
        tmp_path / "euronext_artifacts" / "barchart_probe_report.txt",
    )
    monkeypatch.setattr(
        paths_module,
        "EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS",
        tmp_path / "euronext_artifacts" / "barchart_contract_download_results.csv",
    )
    monkeypatch.setattr(
        paths_module,
        "EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT",
        tmp_path / "euronext_artifacts" / "barchart_contract_download_report.txt",
    )
    monkeypatch.setattr(
        paths_module,
        "EMA_CONTINUOUS_PROBE_RESULTS",
        tmp_path / "euronext_artifacts" / "ema_continuous_probe_results.csv",
    )
    monkeypatch.setattr(
        paths_module,
        "EMA_CONTINUOUS_PROBE_REPORT",
        tmp_path / "euronext_artifacts" / "ema_continuous_probe_report.txt",
    )

    paths_module.ensure_dirs()

    assert (tmp_path / "ema_contracts").is_dir()
    assert (tmp_path / "ema_processed").is_dir()
    assert (tmp_path / "pred_daily").is_dir()
    assert (tmp_path / "roll_audit").is_dir()
    assert (tmp_path / "euronext_artifacts").is_dir()

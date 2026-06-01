"""Centralised file-system layout for the project.

All paths are derived from PROJECT_ROOT, which is the directory containing
``pyproject.toml``. This avoids the relative-path nightmares of the legacy
``script/corrige/database.py`` (which used ``"../../csv/corrige"``).
"""

from __future__ import annotations

from pathlib import Path


def _find_project_root(start: Path | None = None) -> Path:
    """Walk upwards from ``start`` until a directory containing ``pyproject.toml``."""
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError(f"pyproject.toml not found above {here}")


PROJECT_ROOT: Path = _find_project_root()

# Configuration
CONFIG_DIR: Path = PROJECT_ROOT / "config"
SOURCES_YAML: Path = CONFIG_DIR / "sources.yaml"
FEATURES_YAML: Path = CONFIG_DIR / "features.yaml"
MODELS_YAML: Path = CONFIG_DIR / "models.yaml"
DECISION_YAML: Path = CONFIG_DIR / "decision.yaml"

# New data tree
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
INTERIM_DIR: Path = DATA_DIR / "interim"
PROCESSED_DIR: Path = DATA_DIR / "processed"
METADATA_DIR: Path = DATA_DIR / "metadata"

FEATURES_PARQUET: Path = PROCESSED_DIR / "features.parquet"
TARGETS_PARQUET: Path = PROCESSED_DIR / "targets.parquet"
DATA_DICTIONARY_PARQUET: Path = METADATA_DIR / "data_dictionary.parquet"
LEAKAGE_AUDIT_PARQUET: Path = METADATA_DIR / "anti_leakage_audit.parquet"

# Legacy locations (kept read-only - ``data`` lives next to them, not above)
LEGACY_CSV_DIR: Path = PROJECT_ROOT / "csv"
LEGACY_CSV_CORRIGE: Path = LEGACY_CSV_DIR / "corrige"
LEGACY_DATABASE_CSV: Path = LEGACY_CSV_CORRIGE / "database.csv"

# Model artefacts
ARTEFACTS_DIR: Path = PROJECT_ROOT / "artefacts"
PREDICTIONS_DIR: Path = ARTEFACTS_DIR / "predictions"
META_DB_PARQUET: Path = ARTEFACTS_DIR / "meta_database.parquet"

# Study outputs (professional study artefacts)
STUDY_DIR: Path = ARTEFACTS_DIR / "study"

# Logs
LOGS_DIR: Path = PROJECT_ROOT / "logs"

# EMA raw — snapshots quotidiens par contrat
EMA_CONTRACTS_RAW_DIR: Path = RAW_DIR / "euronext_ema_contracts"
EMA_BACKFILL_DIR: Path      = RAW_DIR / "euronext_ema" / "manual_backfill"

# EMA processed — séries continues et features
EMA_PROCESSED_DIR: Path      = PROCESSED_DIR / "euronext"
EMA_CONTRACT_REFERENCE: Path = EMA_PROCESSED_DIR / "ema_contract_reference.parquet"
EMA_CONTRACT_DAILY: Path     = EMA_PROCESSED_DIR / "ema_contract_daily.parquet"
EMA_CURVE_DAILY: Path        = EMA_PROCESSED_DIR / "ema_curve_daily.parquet"
EMA_FRONT_RAW: Path          = EMA_PROCESSED_DIR / "ema_front_continuous_raw.parquet"
EMA_FRONT_ADJUSTED: Path     = EMA_PROCESSED_DIR / "ema_front_continuous_adjusted.parquet"
EMA_LIQUID_RAW: Path         = EMA_PROCESSED_DIR / "ema_liquid_continuous_raw.parquet"
EMA_LIQUID_ADJUSTED: Path    = EMA_PROCESSED_DIR / "ema_liquid_continuous_adjusted.parquet"
EMA_MOST_LIQUID: Path        = EMA_PROCESSED_DIR / "ema_most_liquid_continuous.parquet"
EMA_HARVEST_NOV: Path        = EMA_PROCESSED_DIR / "ema_harvest_nov.parquet"
EMA_CONSTANT_30D: Path       = EMA_PROCESSED_DIR / "ema_constant_maturity_30d.parquet"
EMA_CONSTANT_60D: Path       = EMA_PROCESSED_DIR / "ema_constant_maturity_60d.parquet"
EMA_CONSTANT_120D: Path      = EMA_PROCESSED_DIR / "ema_constant_maturity_120d.parquet"
EMA_CURVE_FEATURES: Path     = EMA_PROCESSED_DIR / "ema_curve_features.parquet"

# Prédictions et rapports
PREDICTIONS_DAILY_DIR: Path  = DATA_DIR / "predictions" / "daily"
PREDICTIONS_WEEKLY_DIR: Path = DATA_DIR / "predictions" / "weekly"
REPORTS_QUALITY_DIR: Path    = DATA_DIR / "reports" / "quality"
REPORTS_WEEKLY_EMA_DIR: Path = DATA_DIR / "reports" / "weekly"

# Artefacts benchmark EMA
EMA_BENCHMARK_DIR: Path = ARTEFACTS_DIR / "benchmark_pivot"
EMA_ROLL_AUDIT: Path    = ARTEFACTS_DIR / "roll_audit" / "roll_audit_report.txt"
EMA_BARCHART_PROBE_RESULTS: Path = ARTEFACTS_DIR / "euronext" / "barchart_probe_results.csv"
EMA_BARCHART_PROBE_REPORT: Path  = ARTEFACTS_DIR / "euronext" / "barchart_probe_report.txt"
EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS: Path = ARTEFACTS_DIR / "euronext" / "barchart_contract_download_results.csv"
EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT: Path  = ARTEFACTS_DIR / "euronext" / "barchart_contract_download_report.txt"
EMA_CONTINUOUS_PROBE_RESULTS: Path = ARTEFACTS_DIR / "euronext" / "ema_continuous_probe_results.csv"
EMA_CONTINUOUS_PROBE_REPORT: Path  = ARTEFACTS_DIR / "euronext" / "ema_continuous_probe_report.txt"


def ensure_dirs() -> None:
    """Create all directories above (idempotent)."""
    for d in [
        DATA_DIR, RAW_DIR, INTERIM_DIR, PROCESSED_DIR, METADATA_DIR,
        ARTEFACTS_DIR, PREDICTIONS_DIR, STUDY_DIR, LOGS_DIR,
        EMA_CONTRACTS_RAW_DIR, EMA_BACKFILL_DIR, EMA_PROCESSED_DIR,
        PREDICTIONS_DAILY_DIR, PREDICTIONS_WEEKLY_DIR,
        REPORTS_QUALITY_DIR, REPORTS_WEEKLY_EMA_DIR,
        EMA_BENCHMARK_DIR, EMA_ROLL_AUDIT.parent,
        EMA_BARCHART_PROBE_RESULTS.parent, EMA_BARCHART_PROBE_REPORT.parent,
        EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS.parent,
        EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT.parent,
        EMA_CONTINUOUS_PROBE_RESULTS.parent, EMA_CONTINUOUS_PROBE_REPORT.parent,
    ]:
        d.mkdir(parents=True, exist_ok=True)

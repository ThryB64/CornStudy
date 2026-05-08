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

# Logs
LOGS_DIR: Path = PROJECT_ROOT / "logs"


def ensure_dirs() -> None:
    """Create all directories above (idempotent)."""
    for d in [
        DATA_DIR, RAW_DIR, INTERIM_DIR, PROCESSED_DIR, METADATA_DIR,
        ARTEFACTS_DIR, PREDICTIONS_DIR, LOGS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)

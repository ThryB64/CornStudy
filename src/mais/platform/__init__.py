"""Generic AutoML platform.

Entry point: ``run_automl(csv_path, target_col)`` → Markdown report.
CLI: ``mais platform run --csv dataset.csv --target col``
"""

from .preprocessing import GenericPreprocessor
from .profiler import ProfileReport, profile_dataset
from .reporting import run_automl

__all__ = ["ProfileReport", "profile_dataset", "GenericPreprocessor", "run_automl"]

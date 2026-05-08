"""YAML configuration loaders."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mais.paths import (
    DECISION_YAML,
    FEATURES_YAML,
    MODELS_YAML,
    SOURCES_YAML,
)


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML must be a mapping ({p})")
    return data


@lru_cache(maxsize=1)
def load_sources() -> dict[str, Any]:
    return load_yaml(SOURCES_YAML)


@lru_cache(maxsize=1)
def load_features() -> dict[str, Any]:
    return load_yaml(FEATURES_YAML)


@lru_cache(maxsize=1)
def load_models() -> dict[str, Any]:
    return load_yaml(MODELS_YAML)


@lru_cache(maxsize=1)
def load_decision() -> dict[str, Any]:
    return load_yaml(DECISION_YAML)

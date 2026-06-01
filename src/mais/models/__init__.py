"""Model adapters.

Each legacy model in ``Models/models/*.py`` will be wrapped behind the
``ModelAdapter`` ABC so that the orchestrator (walk-forward + Optuna)
can call them with a uniform signature regardless of their internals.

Phase 3 deliverable: progressively port the 50 legacy models. This module
ships the registry + a few concrete adapters as proof-of-concept.
"""

from .base import ModelAdapter, ModelRequirement, ModelTask
from .registry import ModelRegistry, get_compatible_models, list_models

__all__ = [
    "ModelAdapter",
    "ModelTask",
    "ModelRequirement",
    "ModelRegistry",
    "list_models",
    "get_compatible_models",
]

"""Model registry: wires the catalog from ``config/models.yaml`` to actual classes.

For Phase 3 launch, only a handful of adapters are wired (baselines + ridge +
lightgbm). The rest exist as ``LegacyShim`` placeholders that raise a clear
NotImplementedError pointing to the legacy file - making the porting work
explicit rather than silent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Type

from mais.utils import get_logger, load_models

from .base import ModelAdapter, ModelMeta, ModelRequirement, ModelTask

log = get_logger("mais.models.registry")

LEGACY_DIR = Path("Models/models")


class LegacyShim(ModelAdapter):
    """Placeholder for models not yet ported.

    Each shim carries the path to the legacy implementation - run
    ``mais train --model NAME`` to get a clear error pointing at it.
    """

    def __init__(self, legacy_path: str, **params):
        super().__init__(**params)
        self.legacy_path = legacy_path

    def fit(self, X, y, X_val=None, y_val=None):
        raise NotImplementedError(
            f"Model not ported yet. Wrap the legacy implementation at "
            f"{self.legacy_path} into a ModelAdapter subclass."
        )

    def predict(self, X):
        raise NotImplementedError(self.legacy_path)


_REGISTRY: dict[str, ModelAdapter] | None = None


def _build_registry() -> dict[str, ModelAdapter]:
    cfg = load_models()
    out: dict[str, ModelAdapter] = {}
    for entry in cfg.get("models", []):
        name = entry["name"]
        meta = ModelMeta(
            name=name,
            group=entry.get("group", "ml"),
            task_types=[ModelTask(t) for t in entry.get("task_types", ["regression"])],
            requires=[ModelRequirement(r) for r in entry.get("requires", [])],
            min_samples=int(entry.get("min_samples", 100)),
            max_samples=entry.get("max_samples"),
            legacy_path=str(LEGACY_DIR / f"{name}.py"),
        )
        adapter_cls = _CONCRETE_ADAPTERS.get(name)
        if adapter_cls is None:
            shim = LegacyShim(legacy_path=str(meta.legacy_path))
            shim.meta = meta
            out[name] = shim
        else:
            inst = adapter_cls()
            inst.meta = meta
            out[name] = inst
    return out


def list_models() -> list[str]:
    """All model names from the registry."""
    return list(_get().keys())


def get_compatible_models(
    task: ModelTask,
    requirements: set[ModelRequirement],
    n_samples: int,
) -> list[str]:
    """Filter registry to models compatible with a given task / requirements / size."""
    out = []
    for name, m in _get().items():
        meta = m.meta
        if task not in meta.task_types:
            continue
        if not requirements.issuperset(meta.requires):
            continue
        if n_samples < meta.min_samples:
            continue
        if meta.max_samples and n_samples > meta.max_samples:
            continue
        out.append(name)
    return out


def get(name: str) -> ModelAdapter:
    return _get()[name]


def _get() -> dict[str, ModelAdapter]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


# ---------------------------------------------------------------------------
# Concrete adapters (incremental porting)
# ---------------------------------------------------------------------------

# Imported lazily to avoid pulling sklearn etc. when only browsing the registry.

def _make_concrete_adapters() -> dict[str, Type[ModelAdapter]]:
    from .adapters_basic import (
        NaiveLastAdapter,
        NaiveDriftAdapter,
        EMABaselineAdapter,
        AR1BaselineAdapter,
        RidgeAdapter,
        LassoAdapter,
        ElasticNetAdapter,
    )
    out = {
        "naive_last":   NaiveLastAdapter,
        "naive_drift":  NaiveDriftAdapter,
        "ema_baseline": EMABaselineAdapter,
        "ar1_baseline": AR1BaselineAdapter,
        "ridge_reg":    RidgeAdapter,
        "lasso_reg":    LassoAdapter,
        "elastic_net":  ElasticNetAdapter,
    }
    # Optional ML adapters (only if dependencies available)
    try:
        from .adapters_ml import LightGBMAdapter, XGBoostAdapter, RandomForestAdapter
        out["lgbm_reg"] = LightGBMAdapter
        out["xgboost_reg"] = XGBoostAdapter
        out["rf_reg"] = RandomForestAdapter
    except ImportError:
        log.info("ml_adapters_skipped", reason="optional deps missing")
    return out


# Lazy concrete adapter resolution - rebuilt every call to avoid cache issues
class _LazyAdapterDict:
    def get(self, key, default=None):
        try:
            return _make_concrete_adapters().get(key, default)
        except Exception as e:
            log.warning("adapter_lookup_failed", key=key, error=str(e))
            return default


_CONCRETE_ADAPTERS = _LazyAdapterDict()


class ModelRegistry:
    """Convenience class wrapper, useful for typing and discoverability."""

    @staticmethod
    def list() -> list[str]:
        return list_models()

    @staticmethod
    def compatible(task: ModelTask, requirements: set[ModelRequirement],
                    n_samples: int) -> list[str]:
        return get_compatible_models(task, requirements, n_samples)

    @staticmethod
    def get(name: str) -> ModelAdapter:
        return get(name)

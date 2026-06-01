"""V7-INFRA-00 — Registre global des expériences V7."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path("artefacts/registry/experiments.jsonl")


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()[:12]
    except Exception:
        return "unknown"


def _features_hash(feature_names: list[str]) -> str:
    s = "|".join(sorted(feature_names))
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def register_experiment(
    experiment_id: str,
    target: str,
    horizon: int,
    model: str,
    cv_protocol: str,
    embargo_days: int,
    n_oof: int,
    features: list[str],
    metrics: dict[str, Any],
    p_value: float | None,
    verdict: str,
    artefact_paths: list[str],
    dataset_version: str = "proxy_v1",
    review_status: str = "PENDING",
) -> dict[str, Any]:
    """Enregistre une expérience V7 dans le registre JSONL append-only."""
    entry: dict[str, Any] = {
        "experiment_id": experiment_id,
        "date": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "dataset_version": dataset_version,
        "features_hash": _features_hash(features),
        "n_features": len(features),
        "target": target,
        "horizon": horizon,
        "model": model,
        "cv_protocol": cv_protocol,
        "embargo_days": embargo_days,
        "n_oof": n_oof,
        **metrics,
        "p_value": p_value,
        "q_bh": None,
        "verdict": verdict,
        "artefact_paths": artefact_paths,
        "review_status": review_status,
    }
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def load_registry() -> list[dict[str, Any]]:
    """Charge le registre en dédupliquant par experiment_id (dernier écrit gagne)."""
    if not REGISTRY_PATH.exists():
        return []
    seen: dict[str, dict[str, Any]] = {}
    with open(REGISTRY_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                seen[e["experiment_id"]] = e
            except json.JSONDecodeError:
                continue
    return list(seen.values())


def update_bh_corrections(corrections: list[dict[str, Any]]) -> None:
    """Met à jour q_bh et verdict_adjusted dans le registre (append mis à jour)."""
    for entry in corrections:
        patched = {**entry}
        register_experiment(
            experiment_id=patched["experiment_id"],
            target=patched.get("target", ""),
            horizon=patched.get("horizon", 0),
            model=patched.get("model", ""),
            cv_protocol=patched.get("cv_protocol", ""),
            embargo_days=patched.get("embargo_days", 0),
            n_oof=patched.get("n_oof", 0),
            features=[],
            metrics={
                k: v
                for k, v in patched.items()
                if k not in {
                    "experiment_id", "date", "git_commit", "dataset_version",
                    "features_hash", "n_features", "target", "horizon", "model",
                    "cv_protocol", "embargo_days", "n_oof", "p_value", "q_bh",
                    "verdict", "artefact_paths", "review_status",
                }
            },
            p_value=patched.get("p_value"),
            verdict=patched.get("verdict_adjusted", patched.get("verdict", "")),
            artefact_paths=patched.get("artefact_paths", []),
            dataset_version=patched.get("dataset_version", "proxy_v1"),
            review_status=patched.get("review_status", "PENDING"),
        )

"""V6 experiment registry for reproducible research runs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT

_REGISTRY_DIR = ARTEFACTS_DIR / "experiments"
_CSV_OUTPUT = _REGISTRY_DIR / "experiment_registry_v6.csv"
_PARQUET_OUTPUT = _REGISTRY_DIR / "experiment_registry_v6.parquet"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EXPERIMENT_REGISTRY_V6.md"


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    date_run: str
    git_commit: str
    dataset_version: str
    feature_set: str
    target: str
    horizon: str
    model: str
    cv_protocol: str
    train_period: str
    test_period: str
    metrics: dict[str, Any]
    artefact_paths: list[str]
    verdict: str
    notes: str = ""
    config_hash: str = field(default="")


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return "NO_GIT"
    commit = result.stdout.strip()
    return commit or "NO_GIT"


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def make_record(
    *,
    experiment_id: str,
    feature_set: str,
    target: str,
    horizon: int | str,
    model: str,
    cv_protocol: str,
    metrics: dict[str, Any],
    verdict: str,
    artefact_paths: list[str] | None = None,
    train_period: str = "expanding_train",
    test_period: str = "crop_year_oof",
    dataset_version: str = "features.parquet_current",
    notes: str = "",
) -> ExperimentRecord:
    config = {
        "experiment_id": experiment_id,
        "feature_set": feature_set,
        "target": target,
        "horizon": str(horizon),
        "model": model,
        "cv_protocol": cv_protocol,
        "dataset_version": dataset_version,
    }
    return ExperimentRecord(
        experiment_id=experiment_id,
        date_run=str(pd.Timestamp.now().date()),
        git_commit=_git_commit(),
        dataset_version=dataset_version,
        feature_set=feature_set,
        target=target,
        horizon=str(horizon),
        model=model,
        cv_protocol=cv_protocol,
        train_period=train_period,
        test_period=test_period,
        metrics=metrics,
        artefact_paths=artefact_paths or [],
        verdict=verdict,
        notes=notes,
        config_hash=_stable_hash(config),
    )


def _flatten(record: ExperimentRecord) -> dict[str, Any]:
    data = asdict(record)
    metrics = data.pop("metrics")
    artefacts = data.pop("artefact_paths")
    flat = {**data, "artefact_paths": json.dumps(artefacts, ensure_ascii=True)}
    for key, value in metrics.items():
        flat[f"metric_{key}"] = value
    return flat


def records_to_frame(records: list[ExperimentRecord]) -> pd.DataFrame:
    return pd.DataFrame([_flatten(record) for record in records])


def save_registry(records: list[ExperimentRecord], *, csv_path: Path | None = None, parquet_path: Path | None = None) -> dict:
    csv_out = csv_path or _CSV_OUTPUT
    parquet_out = parquet_path or _PARQUET_OUTPUT
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    frame = records_to_frame(records)
    frame.to_csv(csv_out, index=False)
    frame.to_parquet(parquet_out, index=False)
    _write_doc(frame, _DOC_OUTPUT)
    return {
        "csv": str(csv_out),
        "parquet": str(parquet_out),
        "n_records": int(len(frame)),
        "verdicts": frame["verdict"].value_counts().to_dict() if not frame.empty else {},
    }


def seed_registry() -> list[ExperimentRecord]:
    """Seed V6 registry with the first planned research blocks."""
    return [
        make_record(
            experiment_id="V6-00",
            feature_set="registry",
            target="experiment_tracking",
            horizon="NA",
            model="registry",
            cv_protocol="NA",
            metrics={"n_required_fields": 16},
            verdict="GO",
            artefact_paths=[
                "artefacts/experiments/experiment_registry_v6.csv",
                "artefacts/experiments/experiment_registry_v6.parquet",
            ],
            notes="Global experiment registry initialized.",
        ),
        make_record(
            experiment_id="V6-plan-ema-premium",
            feature_set="ema_premium_v5",
            target="y_rel_outperform_when_basis_extreme_h90",
            horizon=90,
            model="planned_cross_target_stack",
            cv_protocol="crop_year_oof",
            metrics={"baseline_auc": 0.881, "baseline_top20_da": 0.912},
            verdict="PROMISING",
            artefact_paths=["artefacts/ema_study/ema_target_lab_v5.json"],
            notes="Best V5 target becomes a V6 priority.",
        ),
        make_record(
            experiment_id="V6-plan-cbot",
            feature_set="cbot_global",
            target="y_cbot_up_h60",
            horizon=60,
            model="planned_cbot_stack",
            cv_protocol="crop_year_oof",
            metrics={"reference_auc": 0.675, "reference_da": 0.624},
            verdict="PROMISING",
            artefact_paths=["artefacts/canonical"],
            notes="CBOT J+60 benchmark remains the global driver reference.",
        ),
    ]


def build_experiment_registry_v6() -> dict:
    records = seed_registry()
    saved = save_registry(records)
    return {
        "status": "OK",
        "registry": saved,
        "required_fields": list(asdict(records[0]).keys()),
        "records": [asdict(record) for record in records],
    }


def _write_doc(frame: pd.DataFrame, path: Path) -> None:
    lines = [
        "# EXPERIMENT REGISTRY V6",
        "",
        "> Registry global des experiences V6. Chaque experience doit garder son protocole, ses metriques, son verdict et ses artefacts.",
        "",
        f"- Records : {len(frame)}",
        "",
        "| Experiment | Target | Model | CV | Verdict |",
        "|---|---|---|---|---|",
    ]
    for _, row in frame.iterrows():
        lines.append(
            f"| `{row['experiment_id']}` | `{row['target']}` | `{row['model']}` | "
            f"`{row['cv_protocol']}` | `{row['verdict']}` |"
        )
    lines += [
        "",
        "## Regles",
        "",
        "- Toute experience V6 doit enregistrer `experiment_id`, `target`, `horizon`, `model`, `cv_protocol`, `metrics`, `verdict`.",
        "- Les predictions utilisees comme meta-features doivent etre OOF.",
        "- Les backtests restent `RESEARCH_ONLY_NOT_TRADING` tant que la source EMA est proxy.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    if isinstance(obj, bool):
        return bool(obj)
    raise TypeError(f"Not serialisable: {type(obj)}")


if __name__ == "__main__":
    result = build_experiment_registry_v6()
    print(json.dumps(result["registry"], indent=2, default=_json_default))

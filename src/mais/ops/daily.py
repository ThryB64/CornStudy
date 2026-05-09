"""Daily operational pipeline.

This module is intentionally boring: it runs the same commands a human would
run, records every step, and writes a machine-readable status file for the UI
and cron logs. It is the bridge between a research project and a daily tool.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from mais.paths import (
    ARTEFACTS_DIR,
    FEATURES_PARQUET,
    LOGS_DIR,
    TARGETS_PARQUET,
    ensure_dirs,
)
from mais.utils import get_logger, write_parquet

log = get_logger("mais.ops.daily")

DAILY_DIR = ARTEFACTS_DIR / "daily"
DAILY_STATUS_JSON = DAILY_DIR / "daily_status.json"
DAILY_STATUS_PARQUET = DAILY_DIR / "daily_status.parquet"


@dataclass
class StepStatus:
    step: str
    status: str
    started_at: str
    finished_at: str
    duration_sec: float
    message: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _run_step(name: str, fn: Callable[[], str | None], fail_fast: bool) -> StepStatus:
    started = _utc_now()
    t0 = time.perf_counter()
    status = "PASS"
    message = ""
    try:
        result = fn()
        message = "" if result is None else str(result)
    except Exception as exc:
        status = "FAIL"
        message = f"{type(exc).__name__}: {exc}"
        log.exception("daily_step_failed", step=name, error=message)
        if fail_fast:
            finished = _utc_now()
            return StepStatus(name, status, started, finished, time.perf_counter() - t0, message)
    finished = _utc_now()
    return StepStatus(name, status, started, finished, time.perf_counter() - t0, message)


def run_daily_pipeline(
    collect: bool = False,
    train: bool = False,
    study: bool = True,
    backtest: bool = True,
    fail_fast: bool = True,
) -> dict:
    """Run the daily production pipeline and write a status artefact.

    ``collect`` defaults to false because several official APIs require local
    keys. On a configured server, cron should call ``mais daily-run --collect``.
    """
    ensure_dirs()
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    steps: list[StepStatus] = []

    stopped = False

    def add(name: str, fn: Callable[[], str | None]) -> bool:
        step = _run_step(name, fn, fail_fast=fail_fast)
        steps.append(step)
        return not (fail_fast and step.status == "FAIL")

    if collect:
        def _collect() -> str:
            from mais.collect import run_all_collectors
            summary = run_all_collectors()
            failed = {k: v for k, v in summary.items() if str(v).startswith("FAIL")}
            if failed:
                raise RuntimeError(f"Collectors failed: {failed}")
            return json.dumps(summary, ensure_ascii=True)

        stopped = not add("collect", _collect)

    if not stopped:
        stopped = not add("features", lambda: _run_features())
    if not stopped:
        stopped = not add("targets", lambda: _run_targets())
    if not stopped:
        stopped = not add("audit_leakage", lambda: _run_audit())
    if not stopped:
        stopped = not add("factors", lambda: _run_factors())

    if train and not stopped:
        stopped = not add("train_all", lambda: _run_train_all())
    if train and not stopped:
        stopped = not add("stack", lambda: _run_stack())

    if study and not stopped:
        stopped = not add("study", lambda: _run_study())

    if backtest and not stopped:
        stopped = not add("farmer_backtest", lambda: _run_farmer_backtest())

    status = {
        "generated_at": _utc_now(),
        "overall_status": "PASS" if all(s.status == "PASS" for s in steps) else "FAIL",
        "features_exists": FEATURES_PARQUET.exists(),
        "targets_exists": TARGETS_PARQUET.exists(),
        "steps": [asdict(s) for s in steps],
    }
    DAILY_STATUS_JSON.write_text(json.dumps(status, indent=2, ensure_ascii=True), encoding="utf-8")
    write_parquet(pd.DataFrame(status["steps"]), DAILY_STATUS_PARQUET)
    log.info("daily_pipeline_done", status=status["overall_status"], steps=len(steps))
    return status


def load_daily_status() -> dict:
    if not DAILY_STATUS_JSON.exists():
        return {"overall_status": "missing", "steps": []}
    return json.loads(DAILY_STATUS_JSON.read_text(encoding="utf-8"))


def _run_features() -> str:
    from mais.features import build_features
    df = build_features()
    return f"{len(df)} rows, {df.shape[1] - 1} features"


def _run_targets() -> str:
    from mais.paths import INTERIM_DIR
    from mais.targets import TargetSpec, build_and_save
    from mais.utils import read_table
    prices = read_table(INTERIM_DIR / "database.parquet", date_col="Date")
    targets = build_and_save(prices, TargetSpec(), TARGETS_PARQUET)
    return f"{len(targets)} rows, {targets.shape[1] - 1} targets"


def _run_audit() -> str:
    from mais.leakage import audit_features_targets
    from mais.paths import LEAKAGE_AUDIT_PARQUET
    from mais.utils import read_parquet
    audit = audit_features_targets(
        read_parquet(FEATURES_PARQUET),
        read_parquet(TARGETS_PARQUET),
        write_report_to=LEAKAGE_AUDIT_PARQUET,
    )
    if not audit.passed:
        raise RuntimeError(audit.summary())
    return audit.summary()


def _run_factors() -> str:
    from mais.features import build_factors, save_factors
    from mais.utils import read_parquet
    result = build_factors(read_parquet(FEATURES_PARQUET), read_parquet(TARGETS_PARQUET))
    save_factors(result)
    return f"{result.factors.shape[1] - 1} factors"


def _run_train_all() -> str:
    from mais.optimize import run_training
    return str(run_training(model=None, all_models=True, target="y_logret_h20", n_trials=10))


def _run_stack() -> str:
    from mais.meta import run_stacking
    return str(run_stacking(target="y_logret_h20", meta_model="ridge"))


def _run_study() -> str:
    from mais.study import build_professional_study
    result = build_professional_study(force_rebuild_factors=False)
    return f"report={result.report_path}"


def _run_farmer_backtest() -> str:
    from mais.decision import run_backtest
    return run_backtest(horizon=20, farmer_state="iowa")

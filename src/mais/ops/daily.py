"""Daily operational pipeline.

This module is intentionally boring: it runs the same commands a human would
run, records every step, and writes a machine-readable status file for the UI
and cron logs. It is the bridge between a research project and a daily tool.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import (
    ARTEFACTS_DIR,
    DATA_DIR,
    FEATURES_PARQUET,
    INTERIM_DIR,
    LOGS_DIR,
    PROJECT_ROOT,
    RAW_DIR,
    TARGETS_PARQUET,
    ensure_dirs,
)
from mais.utils import get_logger, load_sources, read_parquet, write_parquet

log = get_logger("mais.ops.daily")

DAILY_DIR = ARTEFACTS_DIR / "daily"
DAILY_STATUS_JSON = DAILY_DIR / "daily_status.json"
DAILY_STATUS_PARQUET = DAILY_DIR / "daily_status.parquet"
REPORTS_DIR = DATA_DIR / "reports"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
COLLECT_TTL_HOURS = 20.0
# Sources dont l'échec doit BLOQUER le pipeline (le prix CBOT cœur alimente build_features()).
# Toute autre source en échec -> WARNING non bloquant (cf. V22-LIVE-01).
ESSENTIAL_COLLECTORS = ("cbot_corn",)
CRON_COMMAND = (
    "15 7 * * 1-5 cd "
    f"{PROJECT_ROOT} && venv/bin/python -m mais.cli daily-run --collect "
    ">> logs/cron_daily.log 2>&1"
)


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
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    total_t0 = time.perf_counter()
    steps: list[StepStatus] = []
    collection_summary: dict[str, str] = {}
    collection_warnings: dict[str, str] = {}
    prediction_validation: dict[str, Any] = {}
    daily_snapshot: dict[str, Any] = {}

    stopped = False

    def add(name: str, fn: Callable[[], str | None]) -> bool:
        step = _run_step(name, fn, fail_fast=fail_fast)
        steps.append(step)
        return not (fail_fast and step.status == "FAIL")

    if collect:
        def _collect() -> str:
            nonlocal collection_summary, collection_warnings
            collection_summary = _run_incremental_collect(ttl_hours=COLLECT_TTL_HOURS)
            failed = {k: v for k, v in collection_summary.items() if str(v).startswith("FAIL")}
            essential_failed = {k: v for k, v in failed.items() if k in ESSENTIAL_COLLECTORS}
            collection_warnings = {k: v for k, v in failed.items() if k not in ESSENTIAL_COLLECTORS}
            if essential_failed:
                raise RuntimeError(f"Essential collectors failed: {essential_failed}")
            msg = _compact_mapping(collection_summary)
            if collection_warnings:
                msg += f" | WARNINGS(non-essential FAIL): {sorted(collection_warnings)}"
            return msg

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

    # V27 — suivi forward officiel (live EMA officiel). Non bloquant : SKIP propre si réseau absent.
    if not stopped:
        stopped = not add("official_forward", lambda: _run_official_forward())

    if not stopped:
        def _validate() -> str:
            nonlocal prediction_validation
            prediction_validation = _validate_past_predictions()
            return _validation_message(prediction_validation)

        stopped = not add("prediction_validation", _validate)

    if not stopped:
        def _snapshot() -> str:
            nonlocal daily_snapshot
            daily_snapshot = _build_daily_snapshot()
            _write_json(SNAPSHOTS_DIR / f"{_local_today()}.json", daily_snapshot)
            return _snapshot_message(daily_snapshot)

        stopped = not add("daily_snapshot", _snapshot)

    def _overall(step_list: list[StepStatus]) -> str:
        if not all(s.status == "PASS" for s in step_list):
            return "FAIL"
        return "PASS_WITH_WARNINGS" if collection_warnings else "PASS"

    status = {
        "generated_at": _utc_now(),
        "generated_for_date": _local_today(),
        "overall_status": _overall(steps),
        "duration_sec": round(time.perf_counter() - total_t0, 3),
        "features_exists": FEATURES_PARQUET.exists(),
        "targets_exists": TARGETS_PARQUET.exists(),
        "collection_summary": collection_summary,
        "collection_warnings": collection_warnings,
        "prediction_validation": prediction_validation,
        "daily_snapshot": daily_snapshot,
        "daily_report": None,
        "cron_recommendation": CRON_COMMAND,
        "steps": [asdict(s) for s in steps],
    }
    report_step = _run_step("daily_markdown_report", lambda: _write_daily_report(status), fail_fast=False)
    steps.append(report_step)
    status["steps"] = [asdict(s) for s in steps]
    status["overall_status"] = _overall(steps)
    status["daily_report"] = _daily_report_path(status["generated_for_date"]).as_posix()
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


# Features de courbe EMA éparses (>=2 contrats sur ~15% des dates), déjà shift(1) dans
# euronext_curve.py (causales). Leur nature en escalier fait faux-positiver l'heuristique cheap
# shift(-1) de l'audit (improvement 0.05-0.10, abs corr à peine >0.10). Exemptées du check future_dep
# comme les features calendaires. Le basis_z de la baseline figée n'en fait PAS partie.
_EMA_SPARSE_CURVE_FEATURES = [
    "ema_curve_slope_6", "ema_roll_yield_ann", "ema_backwardation_flag",
    "ema_carry_front_second", "ema_contango_flag", "ema_spread_f0_f1",
]


def _run_audit() -> str:
    from mais.leakage import audit_features_targets
    from mais.paths import LEAKAGE_AUDIT_PARQUET
    from mais.utils import read_parquet
    audit = audit_features_targets(
        read_parquet(FEATURES_PARQUET),
        read_parquet(TARGETS_PARQUET),
        write_report_to=LEAKAGE_AUDIT_PARQUET,
        skip_future_dep_for=_EMA_SPARSE_CURVE_FEATURES,
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


def _run_official_forward() -> str:
    from mais.research.v27_official_forward import run_v27_forward
    out = run_v27_forward()
    sig = out.get("signal", {})
    appended = out.get("journal_append", {})
    if sig.get("verdict") != "OFFICIAL_SIGNAL_COMPUTED":
        return f"SKIP official forward ({sig.get('verdict', 'unknown')})"
    return (f"{appended.get('status')} {sig.get('price_date')} tier={sig.get('signal_tier')} "
            f"basis={sig.get('basis_official_eur_t')} (journal {out['journal_summary'].get('n_days')}j)")


def _run_incremental_collect(ttl_hours: float = COLLECT_TTL_HOURS) -> dict[str, str]:
    """Run only enabled collectors whose local outputs are stale.

    Freshness is based on existing raw/interim files. This keeps cron cheap and
    avoids hammering official APIs while still making ``--collect`` useful on a
    configured production box.
    """
    from mais.collect import run_collector

    cfg = load_sources()
    summary: dict[str, str] = {}
    for src in cfg.get("sources", []):
        name = str(src.get("name", "unknown"))
        if not src.get("enabled", False):
            summary[name] = "SKIP disabled"
            continue
        freshness = _source_freshness(name)
        if freshness is not None and freshness["age_hours"] <= ttl_hours:
            summary[name] = f"SKIP fresh ({freshness['age_hours']:.1f}h, {freshness['path']})"
            continue
        summary[name] = run_collector(name)
    return summary


def _source_freshness(name: str) -> dict[str, Any] | None:
    candidates = [RAW_DIR / name]
    candidates.extend(_known_interim_outputs(name))
    newest: Path | None = None
    newest_mtime = 0.0
    for candidate in candidates:
        paths = list(candidate.rglob("*")) if candidate.is_dir() else [candidate]
        for path in paths:
            if not path.is_file():
                continue
            mtime = path.stat().st_mtime
            if mtime > newest_mtime:
                newest = path
                newest_mtime = mtime
    if newest is None:
        return None
    age_hours = max(0.0, (time.time() - newest_mtime) / 3600.0)
    return {"path": str(newest.relative_to(PROJECT_ROOT)), "age_hours": age_hours}


def _known_interim_outputs(name: str) -> list[Path]:
    mapping = {
        "cbot_corn": "market.parquet",
        "fred_macro": "macro_fred.parquet",
        "usda_wasde": "wasde.parquet",
        "cftc_cot_corn": "cftc_cot.parquet",
        "eia_ethanol": "eia_ethanol.parquet",
        "openmeteo_states": "meteo.parquet",
        "us_drought_monitor": "drought_monitor.parquet",
        "usda_fas_export_sales": "fas_export_sales.parquet",
        "usda_nass_crop_progress": "crop_progress.parquet",
        "usda_calendar": "usda_calendar.parquet",
        # Euronext / EU / monde (raw CSV, pas encore intégré à interim)
        "euronext_ema": "euronext_ema/euronext_ema.csv",
        "eu_cross_assets": "eu_cross_assets/eu_cross_assets.csv",
        "dce_dalian_corn": "dce_dalian_corn/dce_corn.csv",
        "brazil_fob_prices": "brazil_fob_prices",
        "brazil_export_inspections": "brazil_export_inspections",
        "ukraine_exports": "ukraine_exports",
        "conab_brazil": "conab_brazil",
        "bcr_argentina": "bcr_argentina",
    }
    if name.startswith(("cbot_", "nymex_", "ice_", "brent", "rbob_")):
        return [INTERIM_DIR / "market.parquet"]
    mapped = mapping.get(name)
    if mapped is None:
        return []
    # Euronext/EU raw files are in RAW_DIR, not INTERIM_DIR
    eu_raw_sources = {
        "euronext_ema", "eu_cross_assets", "dce_dalian_corn",
        "brazil_fob_prices", "brazil_export_inspections",
        "ukraine_exports", "conab_brazil", "bcr_argentina",
    }
    if name in eu_raw_sources:
        return [RAW_DIR / mapped]
    return [INTERIM_DIR / mapped]


def _validate_past_predictions() -> dict[str, Any]:
    path = ARTEFACTS_DIR / "professional_study" / "calibrated_predictions.parquet"
    if not path.exists():
        return {"status": "missing", "path": str(path), "message": "No calibrated predictions available."}
    df = read_parquet(path)
    if df.empty:
        return {"status": "empty", "path": str(path), "message": "Calibrated predictions file is empty."}

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "y_true", "y_pred", "horizon"])
    if df.empty:
        return {"status": "empty", "path": str(path), "message": "No mature predictions with y_true/y_pred."}

    today = pd.Timestamp.utcnow().tz_localize(None).normalize()
    df["matures_at"] = df["Date"] + pd.to_timedelta(df["horizon"].astype(int), unit="D")
    mature = df[df["matures_at"] <= today].copy()
    if mature.empty:
        return {"status": "waiting", "path": str(path), "message": "No predictions have matured yet."}

    recent_start = mature["Date"].max() - pd.Timedelta(days=252)
    recent = mature[mature["Date"] >= recent_start].copy()
    if recent.empty:
        recent = mature.copy()

    preferred = recent[recent.get("model", "") == "ridge_factors"]
    eval_df = preferred if not preferred.empty else recent
    rows = []
    for (horizon, model), sub in eval_df.groupby(["horizon", "model"], sort=True):
        y_true = pd.to_numeric(sub["y_true"], errors="coerce")
        y_pred = pd.to_numeric(sub["y_pred"], errors="coerce")
        valid = y_true.notna() & y_pred.notna()
        if not valid.any():
            continue
        yt = y_true[valid].to_numpy(dtype=float)
        yp = y_pred[valid].to_numpy(dtype=float)
        row = {
            "horizon": int(horizon),
            "model": str(model),
            "n": int(len(yt)),
            "rmse": float(math.sqrt(np.mean((yt - yp) ** 2))),
            "mae": float(np.mean(np.abs(yt - yp))),
            "directional_accuracy": float(np.mean(np.sign(yt) == np.sign(yp))),
        }
        if "covered_90" in sub.columns:
            row["coverage_90"] = float(pd.to_numeric(sub.loc[valid, "covered_90"], errors="coerce").mean())
        rows.append(row)

    latest = mature.sort_values("Date").tail(1).iloc[0]
    return {
        "status": "ok",
        "path": str(path),
        "mature_rows": int(len(mature)),
        "recent_window_start": str(recent_start.date()),
        "latest_mature_prediction_date": str(pd.Timestamp(latest["Date"]).date()),
        "metrics": rows,
    }


def _build_daily_snapshot() -> dict[str, Any]:
    decision_path = ARTEFACTS_DIR / "professional_study" / "decision_snapshot.json"
    study_summary_path = ARTEFACTS_DIR / "professional_study" / "study_summary.json"
    decision = _read_json(decision_path)
    study_summary = _read_json(study_summary_path)
    return {
        "date": _local_today(),
        "decision": decision,
        "best_models": study_summary.get("best_by_horizon", []),
        "cqr_mean_coverage": study_summary.get("cqr_mean_coverage"),
        "split_conformal_mean_coverage": study_summary.get("split_conformal_mean_coverage"),
    }


def _write_daily_report(status: dict[str, Any]) -> str:
    report_path = _daily_report_path(status["generated_for_date"])
    validation = status.get("prediction_validation") or {}
    snapshot = status.get("daily_snapshot") or {}
    decision = snapshot.get("decision") if isinstance(snapshot, dict) else {}
    recommendation = (decision or {}).get("recommendation", {}) if isinstance(decision, dict) else {}

    lines = [
        f"# Rapport quotidien maïs — {status['generated_for_date']}",
        "",
        "## Statut pipeline",
        "",
        f"- Statut global : **{status['overall_status']}**",
        f"- Durée : {status.get('duration_sec', 0):.1f} sec",
        f"- Features disponibles : `{status.get('features_exists')}`",
        f"- Targets disponibles : `{status.get('targets_exists')}`",
        "",
        "| Étape | Statut | Durée sec | Message |",
        "|---|---:|---:|---|",
    ]
    for step in status.get("steps", []):
        lines.append(
            "| {step} | {status} | {duration:.1f} | {message} |".format(
                step=step.get("step", ""),
                status=step.get("status", ""),
                duration=float(step.get("duration_sec", 0.0)),
                message=_md_escape(str(step.get("message", ""))[:240]),
            )
        )

    lines.extend([
        "",
        "## Décision courante",
        "",
    ])
    if isinstance(decision, dict) and decision.get("status") == "ok":
        lines.extend([
            f"- Date signal : `{decision.get('as_of')}`",
            f"- Prix cash estimé : {float(decision.get('cash_price_usd_per_bu', 0.0)):.2f} USD/bu",
            f"- Régime : `{decision.get('regime', 'unknown')}`",
            f"- Action : **{recommendation.get('action', 'unknown')}**",
            f"- Fraction à vendre : {float(recommendation.get('sell_fraction', 0.0)):.0%}",
            f"- Règle : `{recommendation.get('rule_id', 'unknown')}`",
        ])
    else:
        lines.append("- Décision indisponible dans `decision_snapshot.json`.")

    lines.extend([
        "",
        "## Validation des prédictions passées",
        "",
        f"- Statut : `{validation.get('status', 'missing')}`",
        f"- Lignes matures : {validation.get('mature_rows', 0)}",
        "",
        "| Horizon | Modèle | N | RMSE | MAE | DA | Couverture 90% |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ])
    for row in validation.get("metrics", []):
        lines.append(
            "| {horizon} | `{model}` | {n} | {rmse:.4f} | {mae:.4f} | {da:.1%} | {cov} |".format(
                horizon=row.get("horizon", ""),
                model=row.get("model", ""),
                n=row.get("n", 0),
                rmse=float(row.get("rmse", 0.0)),
                mae=float(row.get("mae", 0.0)),
                da=float(row.get("directional_accuracy", 0.0)),
                cov=_pct_or_dash(row.get("coverage_90")),
            )
        )

    lines.extend([
        "",
        "## Collecte incrémentale",
        "",
    ])
    collection = status.get("collection_summary") or {}
    if collection:
        lines.extend(["| Source | Résultat |", "|---|---|"])
        for key, value in collection.items():
            lines.append(f"| `{key}` | {_md_escape(str(value))} |")
    else:
        lines.append("- Non lancée sur ce run (`--collect` absent).")

    lines.extend([
        "",
        "## Cron recommandé",
        "",
        "```cron",
        str(status.get("cron_recommendation", CRON_COMMAND)),
        "```",
        "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def _daily_report_path(day: str) -> Path:
    return REPORTS_DIR / f"{day}.md"


def _local_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _validation_message(validation: dict[str, Any]) -> str:
    if validation.get("status") != "ok":
        return str(validation.get("message", validation.get("status", "missing")))
    metrics = validation.get("metrics", [])
    return f"{validation.get('mature_rows', 0)} mature rows, {len(metrics)} metric groups"


def _snapshot_message(snapshot: dict[str, Any]) -> str:
    decision = snapshot.get("decision", {})
    if isinstance(decision, dict) and decision.get("status") == "ok":
        rec = decision.get("recommendation", {})
        return f"{rec.get('action', 'unknown')} ({float(rec.get('sell_fraction', 0.0)):.0%})"
    return "decision snapshot unavailable"


def _compact_mapping(mapping: dict[str, str]) -> str:
    counts: dict[str, int] = {}
    for value in mapping.values():
        key = str(value).split(" ", maxsplit=1)[0]
        counts[key] = counts.get(key, 0) + 1
    return json.dumps(counts, ensure_ascii=True, sort_keys=True)


def _pct_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    try:
        if not np.isfinite(float(value)):
            return "-"
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "-"


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

"""Mais command-line interface (Typer).

All sub-commands map to one function in src/mais/. The CLI is the only entry
point for ``make`` targets, and is also what the Streamlit/FastAPI layer call
behind the scenes.

Examples
--------
::

    mais migrate-legacy
    mais targets --price corn_close
    mais audit-leakage
    mais collect all
    mais train --all
    mais stack
    mais backtest
    mais study
    mais daily-run
"""

from __future__ import annotations

import json
from datetime import date as date_cls
from pathlib import Path
from typing import Annotated

import typer

from mais.paths import (
    CONFIG_DIR,
    EMA_CONTRACT_REFERENCE,
    EMA_CURVE_FEATURES,
    FEATURES_PARQUET,
    INTERIM_DIR,
    LEAKAGE_AUDIT_PARQUET,
    PREDICTIONS_DAILY_DIR,
    REPORTS_WEEKLY_EMA_DIR,
    TARGETS_PARQUET,
    ensure_dirs,
)
from mais.utils import get_logger

log = get_logger("mais.cli")

app = typer.Typer(add_completion=False, no_args_is_help=True,
                   help="Corn (CBOT) prediction & farmer decision support.")


# ---------------------------------------------------------------------------
# Phase 0: legacy migration
# ---------------------------------------------------------------------------


@app.command("migrate-legacy")
def cli_migrate_legacy() -> None:
    """Convert legacy csv/corrige/* into data/interim/*.parquet (+ bug fixes)."""
    from mais.clean import migrate_legacy
    ensure_dirs()
    written = migrate_legacy()
    typer.echo(f"Migrated {len(written)} sources into {INTERIM_DIR}:")
    for name, path in written.items():
        typer.echo(f"  - {name:14s} -> {path.relative_to(path.parents[2])}")


# ---------------------------------------------------------------------------
# Phase 1: data pipeline
# ---------------------------------------------------------------------------


collect_app = typer.Typer(help="Download raw data from external sources.")
app.add_typer(collect_app, name="collect")

backfill_app = typer.Typer(help="Backfill historical datasets.")
app.add_typer(backfill_app, name="backfill")

report_app = typer.Typer(help="Generate EMA daily and weekly reports.")
app.add_typer(report_app, name="report")


@collect_app.command("all")
def cli_collect_all() -> None:
    """Download every source listed in config/sources.yaml (skips disabled)."""
    from mais.collect import run_all_collectors
    ensure_dirs()
    summary = run_all_collectors()
    for name, status in summary.items():
        typer.echo(f"  {name:25s} {status}")


@collect_app.command("source")
def cli_collect_source(name: str = typer.Argument(..., help="Source name from sources.yaml")) -> None:
    """Download a single source by name."""
    from mais.collect import run_collector
    ensure_dirs()
    status = run_collector(name)
    typer.echo(f"{name}: {status}")


@backfill_app.command("euronext")
def cli_backfill_euronext(
    from_date: Annotated[str, typer.Option("--from", help="Start date YYYY-MM-DD.")] = "2014-01-01",
    to_date: Annotated[str | None, typer.Option("--to", help="End date YYYY-MM-DD, default today.")] = None,
    manual: Annotated[Path | None, typer.Option("--manual", help="Manual EMA historical CSV.")] = None,
    throttle_sec: Annotated[
        float,
        typer.Option("--throttle-sec", help="Seconds between Euronext/Barchart calls."),
    ] = 2.0,
    coverage_only: Annotated[
        bool,
        typer.Option("--barchart-coverage-only", help="Write Barchart coverage artefacts only."),
    ] = False,
) -> None:
    """Backfill Euronext EMA contracts from manual CSV, Barchart web, or chart history."""
    from datetime import date

    from mais.collect.euronext_backfill import run_barchart_eod_coverage, run_full_backfill

    ensure_dirs()
    start = date.fromisoformat(from_date)
    end = date.today() if to_date in {None, "today"} else date.fromisoformat(str(to_date))
    if coverage_only:
        report = run_barchart_eod_coverage(start, end, throttle_sec=throttle_sec)
        typer.echo(
            "Barchart EMA coverage: "
            f"verdict={report['verdict']} contracts={report['contracts']} "
            f"report={report['report_path']}"
        )
        return
    report = run_full_backfill(start, end, manual=manual, throttle_sec=throttle_sec)
    typer.echo(
        "EMA backfill: "
        f"source={report['source_used']} rows={report['rows_written']} "
        f"coverage={report['coverage_pct']}% contracts={len(report['contracts_found'])}"
    )


@app.command("build-ema-dataset")
def cli_build_ema_dataset() -> None:
    """Build EMA continuous series, curve features, targets, then master features."""
    from mais.collect.ema_contract_reference import (
        build_contract_reference,
        write_contract_reference,
    )
    from mais.collect.euronext_contracts_daily import canonicalise_contract_daily_parquet
    from mais.features import build_features
    from mais.features.ema_targets import build_and_save_ema_targets
    from mais.features.euronext_continuous import build_and_save_continuous_series
    from mais.features.euronext_curve import build_and_save_curve_features

    ensure_dirs()
    if not EMA_CONTRACT_REFERENCE.exists():
        reference = build_contract_reference(2010, date_cls.today().year)
        write_contract_reference(reference, output_path=EMA_CONTRACT_REFERENCE)
    contract_rows = canonicalise_contract_daily_parquet()
    continuous = build_and_save_continuous_series()
    curve = build_and_save_curve_features()
    targets = build_and_save_ema_targets()
    master = build_features()
    typer.echo(
        "EMA dataset OK: "
        f"contracts_canonicalised={contract_rows} "
        f"continuous={continuous} "
        f"curve_rows={len(curve)} "
        f"targets_rows={len(targets)} "
        f"master_shape={master.shape} "
        f"curve_path={EMA_CURVE_FEATURES}"
    )


@app.command("predict-ema")
def cli_predict_ema(
    signal_date: Annotated[
        str | None,
        typer.Option("--date", help="Signal date YYYY-MM-DD, default latest feature date."),
    ] = None,
) -> None:
    """Write a provisional EMA direction signal from Module A context features."""
    ensure_dirs()
    day = _parse_date_option(signal_date)
    payload = _build_ema_prediction_payload(day)
    path = _write_ema_prediction_payload(payload)
    typer.echo(
        "EMA signal: "
        f"date={payload['date']} signal={payload['signal']} "
        f"probability_up={payload['probability_up']:.3f} "
        f"confidence={payload['confidence']:.3f} path={path}"
    )


@report_app.command("daily")
def cli_report_daily(
    report_date: Annotated[
        str | None,
        typer.Option("--date", help="Report date YYYY-MM-DD, default today."),
    ] = None,
) -> None:
    """Generate the daily EMA markdown report and companion quality JSON."""
    from mais.collect.data_quality import generate_quality_report

    ensure_dirs()
    day = _parse_date_option(report_date) or date_cls.today()
    quality_path = generate_quality_report(day)
    prediction = _build_ema_prediction_payload(day)
    prediction_path = _write_ema_prediction_payload(prediction)
    report_path = _write_ema_daily_report(day, prediction, quality_path)
    typer.echo(
        "EMA daily report: "
        f"report={report_path} signal={prediction['signal']} "
        f"prediction={prediction_path} quality={quality_path}"
    )


@report_app.command("weekly")
def cli_report_weekly(
    week: Annotated[
        str | None,
        typer.Option("--week", help="ISO week YYYY-WXX, default current week."),
    ] = None,
) -> None:
    """Generate a concise weekly EMA markdown report from the latest week signal."""
    ensure_dirs()
    week_label, week_start = _parse_week_option(week)
    prediction = _build_ema_prediction_payload(week_start)
    report_path = _write_ema_weekly_report(week_label, prediction)
    typer.echo(
        "EMA weekly report: "
        f"week={week_label} report={report_path} signal={prediction['signal']}"
    )


@app.command("data-quality")
def cli_data_quality(
    report_date: Annotated[
        str | None,
        typer.Option("--date", help="Quality report date YYYY-MM-DD, default today."),
    ] = None,
) -> None:
    """Generate the EMA data-quality JSON report for one date."""
    from mais.collect.data_quality import generate_quality_report

    ensure_dirs()
    day = _parse_date_option(report_date) or date_cls.today()
    path = generate_quality_report(day)
    typer.echo(f"EMA data quality report: {path}")


@app.command("clean")
def cli_clean() -> None:
    """Clean raw -> interim : migre le legacy si besoin puis etend database.parquet."""
    from mais.clean import migrate_legacy, refresh_database
    from mais.paths import INTERIM_DIR
    ensure_dirs()
    if not (INTERIM_DIR / "database.parquet").exists():
        typer.echo("database.parquet absent -> migration legacy (csv/corrige/).")
        migrate_legacy()
    res = refresh_database()
    typer.echo(f"database.parquet etendu : +{res['appended']} lignes (derniere date {res['last']})")


@app.command("features")
def cli_features() -> None:
    """Build data/processed/features.parquet from data/interim/."""
    from mais.features import build_features
    ensure_dirs()
    df = build_features()
    typer.echo(f"Wrote {FEATURES_PARQUET} ({len(df)} rows, {df.shape[1]} cols)")


@app.command("factors")
def cli_factors() -> None:
    """Build data/processed/factors.parquet from existing features + targets."""
    from mais.features import build_factors, save_factors
    from mais.utils import read_parquet

    if not FEATURES_PARQUET.exists():
        typer.echo(f"Missing features file: {FEATURES_PARQUET}", err=True)
        raise typer.Exit(2)
    if not TARGETS_PARQUET.exists():
        typer.echo(f"Missing targets file: {TARGETS_PARQUET}", err=True)
        raise typer.Exit(2)

    features = read_parquet(FEATURES_PARQUET)
    targets = read_parquet(TARGETS_PARQUET)
    result = build_factors(features, targets)
    out, meta = save_factors(result)
    typer.echo(f"Wrote {out} ({len(result.factors)} rows, {result.factors.shape[1]} cols)")
    typer.echo(f"Wrote {meta}")


@app.command("targets")
def cli_targets(
    price_col: Annotated[str, typer.Option("--price", help="Price column.")] = "corn_close",
    horizons: Annotated[
        str,
        typer.Option("--horizons", help="Comma-separated horizons."),
    ] = "5,10,20,30",
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            help="Source parquet/csv to read prices from. Defaults to interim/database.parquet.",
        ),
    ] = INTERIM_DIR / "database.parquet",
) -> None:
    """Build data/processed/targets.parquet (y_logret_h{H}, classes, binaries)."""
    from mais.targets import TargetSpec, build_and_save
    from mais.utils import read_table
    ensure_dirs()
    horizon_values = tuple(int(h) for h in horizons.split(","))
    spec = TargetSpec(horizons=horizon_values, price_col=price_col)

    if not Path(source).exists():
        typer.echo(f"Source not found: {source}", err=True)
        raise typer.Exit(code=2)
    prices = read_table(source, date_col="Date")
    targets = build_and_save(prices, spec, TARGETS_PARQUET)
    typer.echo(f"Wrote {TARGETS_PARQUET} ({len(targets)} rows, {targets.shape[1]} cols)")


@app.command("audit-leakage")
def cli_audit_leakage(
    features: Annotated[Path, typer.Option("--features")] = FEATURES_PARQUET,
    targets: Annotated[Path, typer.Option("--targets")] = TARGETS_PARQUET,
    perfect_fit_threshold: Annotated[float, typer.Option("--threshold")] = 0.97,
    fail_on_violation: Annotated[bool, typer.Option("--fail/--no-fail")] = True,
) -> None:
    """Run the 5 anti-leakage checks and write a report. Non-zero exit on FAIL."""
    from mais.leakage import audit_features_targets
    from mais.utils import read_parquet

    if not features.exists():
        typer.echo(f"Features file missing: {features}", err=True)
        raise typer.Exit(2)
    if not targets.exists():
        typer.echo(f"Targets file missing: {targets}", err=True)
        raise typer.Exit(2)

    f_df = read_parquet(features)
    t_df = read_parquet(targets)
    audit = audit_features_targets(
        f_df, t_df, perfect_fit_threshold=perfect_fit_threshold,
        write_report_to=LEAKAGE_AUDIT_PARQUET,
    )
    typer.echo(audit.summary())
    if not audit.passed:
        typer.echo(f"Detailed report: {LEAKAGE_AUDIT_PARQUET}")
        if fail_on_violation:
            raise typer.Exit(code=1)


@app.command("study")
def cli_study(
    rebuild_factors: Annotated[
        bool,
        typer.Option("--rebuild-factors", help="Force rebuild factors.parquet."),
    ] = False,
    optuna_trials: Annotated[
        int,
        typer.Option("--optuna-trials", help="Run Optuna tuning with N trials (0=skip)."),
    ] = 0,
) -> None:
    """Build artefacts/professional_study/* and docs/PROFESSIONAL_STUDY_REPORT.md."""
    from mais.study import build_professional_study

    ensure_dirs()
    if optuna_trials == 0:
        # Try to read from indicator.yaml
        try:
            import yaml

            cfg_path = CONFIG_DIR / "indicator.yaml"
            if cfg_path.exists():
                with open(cfg_path) as f:
                    cfg = yaml.safe_load(f) or {}
                optuna_trials = int(cfg.get("optuna", {}).get("n_trials", 0))
        except Exception:
            pass
    run_optuna = optuna_trials > 0
    result = build_professional_study(
        force_rebuild_factors=rebuild_factors,
        optimize=run_optuna,
        optuna_trials=max(1, optuna_trials) if run_optuna else 12,
    )
    typer.echo(f"Study OK -> {result.report_path}")


@app.command("daily-run")
def cli_daily_run(
    collect: Annotated[
        bool,
        typer.Option("--collect", help="Run collectors first (may require API keys)."),
    ] = False,
    train: Annotated[
        bool,
        typer.Option("--train", help="Run train --all and stack after data pipeline."),
    ] = False,
    no_study: Annotated[
        bool,
        typer.Option("--no-study", help="Skip professional study."),
    ] = False,
    no_backtest: Annotated[
        bool,
        typer.Option("--no-backtest", help="Skip farmer backtest."),
    ] = False,
) -> None:
    """Run features → targets → audit → factors → optional train/study/backtest; write daily status."""
    from mais.ops.daily import run_daily_pipeline

    ensure_dirs()
    status = run_daily_pipeline(
        collect=collect,
        train=train,
        study=not no_study,
        backtest=not no_backtest,
    )
    typer.echo(status["overall_status"])
    if status["overall_status"] != "PASS":
        raise typer.Exit(code=1)


@app.command("status")
def cli_status() -> None:
    """Print latest daily pipeline status (from artefacts/daily/daily_status.json)."""
    import json

    from mais.ops.daily import load_daily_status

    typer.echo(json.dumps(load_daily_status(), indent=2, ensure_ascii=True))


# ---------------------------------------------------------------------------
# Phase 2: indicator
# ---------------------------------------------------------------------------


@app.command("backtest")
def cli_backtest(
    horizon: Annotated[int, typer.Option("--horizon", help="Horizon to use for decisions.")] = 20,
    farmer_state: Annotated[str, typer.Option("--state")] = "iowa",
) -> None:
    """Run the agronomic backtest of decision rules vs baselines."""
    from mais.decision import run_backtest
    ensure_dirs()
    summary = run_backtest(horizon=horizon, farmer_state=farmer_state)
    typer.echo(summary)


@app.command("advise")
def cli_advise(
    horizon: Annotated[int, typer.Option("--horizon")] = 20,
    farmer_state: Annotated[str, typer.Option("--state")] = "iowa",
) -> None:
    """Print the current sell/store/wait recommendation for today."""
    from mais.decision import advise_today
    typer.echo(advise_today(horizon=horizon, farmer_state=farmer_state))


@app.command("sale-score")
def cli_sale_score(
    holdout: Annotated[bool, typer.Option("--holdout", help="Evaluer le holdout 2024+ (1 fois).")] = False,
    latest: Annotated[bool, typer.Option("--latest", help="Afficher seulement le dernier score.")] = False,
) -> None:
    """Score de vente / direction / risque CBOT (etape 7, aide a la decision, pas un bot)."""
    from mais.indicator.cbot_sale_score_report import finalize
    ensure_dirs()
    if latest:
        from mais.indicator import cbot_sale_score as sale
        from mais.indicator import cbot_sale_score_features as feats
        cfg = sale.load_config()
        df, _ = feats.build_frame()
        frame = sale.score_timeseries(df, sale.build_models(df, cfg))
        typer.echo(json.dumps(sale.latest_record(frame, cfg), ensure_ascii=False, indent=2))
        return
    res = finalize(do_holdout=holdout)
    typer.echo(f"VERDICT: {res['verdict']}")
    typer.echo(res["reason"])
    typer.echo(f"Dernier signal: {res['latest']['recommendation']} "
               f"(p_down_h90={res['latest']['p_down_h90']})")
    typer.echo("Artefacts: artefacts/final_cbot_sale_score/")


@app.command("euronext-indicator")
def cli_euronext_indicator() -> None:
    """Indicateur Euronext visuel (score de vente CBOT applique a l'historique EMA) + dashboard HTML."""
    from mais.indicator.euronext_indicator_dashboard import finalize
    ensure_dirs()
    res = finalize()
    typer.echo(f"VERDICT: {res['verdict']}")
    typer.echo(res["reason"])
    typer.echo(f"Dernier signal: {res['latest']['recommendation']} au {res['latest']['signal_date']} "
               f"({res['latest']['euronext_price']} EUR/t)")
    typer.echo("Dashboard: artefacts/final_euronext_indicator/euronext_indicator_dashboard.html")


# ---------------------------------------------------------------------------
# Phase 3: training, stacking
# ---------------------------------------------------------------------------


@app.command("train")
def cli_train(
    model: Annotated[str | None, typer.Option("--model", help="Model name from models.yaml.")] = None,
    all_models: Annotated[
        bool,
        typer.Option("--all", help="Train every compatible model."),
    ] = False,
    target: Annotated[str, typer.Option("--target")] = "y_logret_h20",
    n_trials: Annotated[int, typer.Option("--trials")] = 20,
) -> None:
    """Train one or more models with walk-forward + Optuna."""
    from mais.optimize import run_training
    ensure_dirs()
    if not (model or all_models):
        typer.echo("Specify --model NAME or --all", err=True)
        raise typer.Exit(2)
    summary = run_training(model=model, all_models=all_models, target=target, n_trials=n_trials)
    typer.echo(summary)


@app.command("stack")
def cli_stack(
    target: Annotated[str, typer.Option("--target")] = "y_logret_h20",
    meta_model: Annotated[
        str,
        typer.Option("--meta", help="Meta model: ridge|lasso|lgbm"),
    ] = "ridge",
) -> None:
    """Build the meta-database from base predictions and fit the stacking model."""
    from mais.meta import run_stacking
    ensure_dirs()
    typer.echo(run_stacking(target=target, meta_model=meta_model))


@app.command("profile")
def cli_profile(csv_path: Annotated[Path, typer.Argument()]) -> None:
    """Profile any CSV (auto-detect time-series vs tabular, target type, ...).
    Outputs the list of compatible models from models.yaml."""
    from mais.optimize.profiler import profile_dataset
    typer.echo(profile_dataset(csv_path))


platform_app = typer.Typer(help="Generic AutoML platform — profile, preprocess, benchmark, report.")
app.add_typer(platform_app, name="platform")


@platform_app.command("run")
def cli_platform_run(
    csv: Annotated[Path, typer.Option("--csv", help="Input CSV or Parquet file.")],
    target: Annotated[str, typer.Option("--target", help="Column to predict.")],
    out_dir: Annotated[
        Path | None,
        typer.Option("--out-dir", help="Output directory (default: automl_<stem>/)."),
    ] = None,
    date_col: Annotated[
        str | None,
        typer.Option("--date-col", help="Date column (auto-detected if omitted)."),
    ] = None,
    splits: Annotated[
        int,
        typer.Option("--splits", help="Number of CV folds or walk-forward blocks."),
    ] = 5,
) -> None:
    """Run the full AutoML pipeline and generate a Markdown report."""
    from mais.platform.reporting import run_automl
    report = run_automl(
        csv_path=csv,
        target_col=target,
        out_dir=out_dir,
        date_col=date_col or None,
        n_splits=splits,
    )
    typer.echo(f"Report: {report}")


@platform_app.command("profile")
def cli_platform_profile(
    csv: Annotated[Path, typer.Option("--csv", help="Input CSV or Parquet file.")],
    target: Annotated[
        str | None,
        typer.Option("--target", help="Target column (auto-detected if omitted)."),
    ] = None,
) -> None:
    """Profile a CSV/Parquet and print the ProfileReport summary."""
    from mais.platform.profiler import profile_dataset
    report = profile_dataset(csv, target_col=target or None)
    typer.echo(report.summary())


def _parse_date_option(value: str | None) -> date_cls | None:
    if value is None:
        return None
    if value.lower() == "today":
        return date_cls.today()
    return date_cls.fromisoformat(value)


def _parse_week_option(value: str | None) -> tuple[str, date_cls]:
    today = date_cls.today()
    if value is None:
        iso = today.isocalendar()
        return f"{iso.year}-W{iso.week:02d}", date_cls.fromisocalendar(iso.year, iso.week, 1)
    year_text, week_text = value.split("-W", maxsplit=1)
    year = int(year_text)
    week = int(week_text)
    return f"{year}-W{week:02d}", date_cls.fromisocalendar(year, week, 1)


def _build_ema_prediction_payload(signal_date: date_cls | None = None) -> dict:
    import pandas as pd

    from mais.indicator.module_a_context import compute_context_score

    if not FEATURES_PARQUET.exists():
        typer.echo(f"Missing master features file: {FEATURES_PARQUET}", err=True)
        raise typer.Exit(code=2)
    features = pd.read_parquet(FEATURES_PARQUET)
    if "Date" not in features.columns or features.empty:
        typer.echo(f"Invalid master features file: {FEATURES_PARQUET}", err=True)
        raise typer.Exit(code=2)

    work = features.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    if signal_date is not None:
        work = work[work["Date"] <= pd.Timestamp(signal_date)]
    if work.empty:
        typer.echo(f"No features available at or before {signal_date}", err=True)
        raise typer.Exit(code=2)

    work = work.sort_values("Date").reset_index(drop=True)
    row = work.iloc[-1]
    feature_date = pd.Timestamp(row["Date"]).date()
    stale_days = (signal_date - feature_date).days if signal_date is not None else 0
    context = compute_context_score(row, work)
    context_score = float(context["context_score"])
    availability = float(context["data_availability_score"])
    probability_up = max(0.05, min(0.95, 0.5 + 0.25 * context_score))
    signal = _signal_from_orientation(str(context["orientation"]))
    confidence = max(0.0, min(1.0, 0.20 * availability + 0.80 * abs(context_score)))
    typed_uncertainty = context["typed_uncertainty"]
    if stale_days > 7:
        signal = "UNCERTAIN"
        confidence = min(confidence, 0.10)
        typed_uncertainty = "stale_features"
    return {
        "date": feature_date.isoformat(),
        "requested_date": signal_date.isoformat() if signal_date is not None else None,
        "stale_days": int(max(stale_days, 0)),
        "signal": signal,
        "orientation": context["orientation"],
        "probability_up": probability_up,
        "confidence": confidence,
        "context_score": context_score,
        "dominant_signal": context["dominant_signal"],
        "data_availability_score": availability,
        "typed_uncertainty": typed_uncertainty,
        "block_scores": context["block_scores"],
        "model_status": "module_a_context_rule_until_ema_models_are_validated",
        "source_quality_note": (
            "EMA prices currently use barchart_proxy_exploratory, not official Euronext settlement."
        ),
    }


def _write_ema_prediction_payload(payload: dict) -> Path:
    PREDICTIONS_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    path = PREDICTIONS_DAILY_DIR / f"{payload['date']}_ema_signal.json"
    path.write_text(json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_ema_daily_report(day: date_cls, prediction: dict, quality_path: Path) -> Path:
    report_dir = REPORTS_WEEKLY_EMA_DIR.parent / "daily"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{day.isoformat()}_ema_daily.md"
    lines = [
        f"# Rapport quotidien EMA - {day.isoformat()}",
        "",
        f"- Signal : `{prediction['signal']}`",
        f"- Date signal effective : `{prediction['date']}`",
        f"- Retard features : `{prediction['stale_days']}` jours",
        f"- P(hausse) : `{prediction['probability_up']:.3f}`",
        f"- Confiance : `{prediction['confidence']:.3f}`",
        f"- Score contexte : `{prediction['context_score']:.3f}`",
        f"- Disponibilite donnees : `{prediction['data_availability_score']:.3f}`",
        f"- Facteur dominant : `{prediction['dominant_signal']}`",
        f"- Rapport qualite : `{quality_path}`",
        "",
        prediction["source_quality_note"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_ema_weekly_report(week_label: str, prediction: dict) -> Path:
    REPORTS_WEEKLY_EMA_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_WEEKLY_EMA_DIR / f"{week_label}_ema_weekly.md"
    lines = [
        f"# Rapport hebdomadaire EMA - {week_label}",
        "",
        "## Signal",
        "",
        f"- Signal : `{prediction['signal']}`",
        f"- Date signal effective : `{prediction['date']}`",
        f"- Retard features : `{prediction['stale_days']}` jours",
        f"- P(hausse) : `{prediction['probability_up']:.3f}`",
        f"- Confiance : `{prediction['confidence']:.3f}`",
        f"- Score contexte : `{prediction['context_score']:.3f}`",
        "",
        "## Lecture contexte",
        "",
        f"- Orientation : `{prediction['orientation']}`",
        f"- Facteur dominant : `{prediction['dominant_signal']}`",
        f"- Disponibilite donnees : `{prediction['data_availability_score']:.3f}`",
        f"- Incertitude typee : `{prediction['typed_uncertainty']}`",
        "",
        "## Reserve source",
        "",
        prediction["source_quality_note"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _signal_from_orientation(orientation: str) -> str:
    return {
        "HAUSSIER": "BULLISH",
        "BAISSIER": "BEARISH",
        "NEUTRE": "NEUTRAL",
        "UNCERTAIN": "UNCERTAIN",
    }.get(orientation, "UNCERTAIN")


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def main() -> None:
    """Entry-point used by ``python -m mais.cli`` and the ``mais`` script."""
    app()


if __name__ == "__main__":
    main()

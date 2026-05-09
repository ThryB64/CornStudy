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
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from mais.paths import (
    FEATURES_PARQUET,
    INTERIM_DIR,
    LEAKAGE_AUDIT_PARQUET,
    PROCESSED_DIR,
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


@app.command("clean")
def cli_clean() -> None:
    """Clean raw -> interim (validate, dedupe, harmonise frequencies)."""
    from mais.clean import migrate_legacy
    ensure_dirs()
    typer.echo("Note: full raw->interim cleaning pipeline not yet implemented.")
    typer.echo("Falling back to legacy migration (works on csv/corrige/).")
    migrate_legacy()


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
    price_col: str = typer.Option("corn_close", "--price", help="Price column."),
    horizons: str = typer.Option("5,10,20,30", "--horizons", help="Comma-separated horizons."),
    source: Path = typer.Option(
        INTERIM_DIR / "database.parquet", "--source",
        help="Source parquet/csv to read prices from. Defaults to interim/database.parquet."
    ),
) -> None:
    """Build data/processed/targets.parquet (y_logret_h{H}, classes, binaries)."""
    from mais.targets import TargetSpec, build_and_save
    from mais.utils import read_table
    ensure_dirs()
    H = tuple(int(h) for h in horizons.split(","))
    spec = TargetSpec(horizons=H, price_col=price_col)

    if not Path(source).exists():
        typer.echo(f"Source not found: {source}", err=True)
        raise typer.Exit(code=2)
    prices = read_table(source, date_col="Date")
    targets = build_and_save(prices, spec, TARGETS_PARQUET)
    typer.echo(f"Wrote {TARGETS_PARQUET} ({len(targets)} rows, {targets.shape[1]} cols)")


@app.command("audit-leakage")
def cli_audit_leakage(
    features: Path = typer.Option(FEATURES_PARQUET, "--features"),
    targets: Path = typer.Option(TARGETS_PARQUET, "--targets"),
    perfect_fit_threshold: float = typer.Option(0.97, "--threshold"),
    fail_on_violation: bool = typer.Option(True, "--fail/--no-fail"),
) -> None:
    """Run the 5 anti-leakage checks and write a report. Non-zero exit on FAIL."""
    from mais.leakage import audit_features_targets
    from mais.utils import read_parquet

    if not features.exists():
        typer.echo(f"Features file missing: {features}", err=True); raise typer.Exit(2)
    if not targets.exists():
        typer.echo(f"Targets file missing: {targets}", err=True); raise typer.Exit(2)

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


# ---------------------------------------------------------------------------
# Phase 2: indicator
# ---------------------------------------------------------------------------


@app.command("backtest")
def cli_backtest(
    horizon: int = typer.Option(20, "--horizon", help="Horizon to use for decisions."),
    farmer_state: str = typer.Option("iowa", "--state"),
) -> None:
    """Run the agronomic backtest of decision rules vs baselines."""
    from mais.decision import run_backtest
    ensure_dirs()
    summary = run_backtest(horizon=horizon, farmer_state=farmer_state)
    typer.echo(summary)


@app.command("advise")
def cli_advise(
    horizon: int = typer.Option(20, "--horizon"),
    farmer_state: str = typer.Option("iowa", "--state"),
) -> None:
    """Print the current sell/store/wait recommendation for today."""
    from mais.decision import advise_today
    typer.echo(advise_today(horizon=horizon, farmer_state=farmer_state))


# ---------------------------------------------------------------------------
# Phase 3: training, stacking
# ---------------------------------------------------------------------------


@app.command("train")
def cli_train(
    model: Optional[str] = typer.Option(None, "--model", help="Model name from models.yaml."),
    all_models: bool = typer.Option(False, "--all", help="Train every compatible model."),
    target: str = typer.Option("y_logret_h20", "--target"),
    n_trials: int = typer.Option(20, "--trials"),
) -> None:
    """Train one or more models with walk-forward + Optuna."""
    from mais.optimize import run_training
    ensure_dirs()
    if not (model or all_models):
        typer.echo("Specify --model NAME or --all", err=True); raise typer.Exit(2)
    summary = run_training(model=model, all_models=all_models, target=target, n_trials=n_trials)
    typer.echo(summary)


@app.command("stack")
def cli_stack(
    target: str = typer.Option("y_logret_h20", "--target"),
    meta_model: str = typer.Option("ridge", "--meta", help="Meta model: ridge|lasso|lgbm"),
) -> None:
    """Build the meta-database from base predictions and fit the stacking model."""
    from mais.meta import run_stacking
    ensure_dirs()
    typer.echo(run_stacking(target=target, meta_model=meta_model))


@app.command("profile")
def cli_profile(
    csv_path: Path = typer.Argument(...),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Profile any CSV (auto-detect time-series vs tabular, target type, ...).
    Outputs the list of compatible models from models.yaml."""
    from mais.optimize.profiler import profile_dataset, profile_dataset_json
    typer.echo(profile_dataset_json(csv_path) if as_json else profile_dataset(csv_path))


@app.command("study")
def cli_study(
    force_rebuild_factors: bool = typer.Option(False, "--force-factors/--no-force-factors"),
) -> None:
    """Build the professional corn price study artefacts and report."""
    from mais.study import build_professional_study

    ensure_dirs()
    result = build_professional_study(force_rebuild_factors=force_rebuild_factors)
    typer.echo(f"Wrote {result.report_path}")
    for name, path in result.summary.get("artefacts", {}).items():
        typer.echo(f"  - {name}: {path}")


@app.command("daily-run")
def cli_daily_run(
    collect: bool = typer.Option(False, "--collect/--no-collect", help="Run enabled collectors first."),
    train: bool = typer.Option(False, "--train/--no-train", help="Run train-all + stacking."),
    study: bool = typer.Option(True, "--study/--no-study", help="Regenerate professional study."),
    backtest: bool = typer.Option(True, "--backtest/--no-backtest", help="Run farmer revenue backtest."),
    fail_fast: bool = typer.Option(True, "--fail-fast/--keep-going"),
) -> None:
    """Run the daily operational pipeline and write monitoring status."""
    from mais.ops import DAILY_STATUS_JSON, run_daily_pipeline

    ensure_dirs()
    status = run_daily_pipeline(
        collect=collect,
        train=train,
        study=study,
        backtest=backtest,
        fail_fast=fail_fast,
    )
    typer.echo(f"Daily status: {status['overall_status']}")
    typer.echo(f"Wrote {DAILY_STATUS_JSON}")
    for step in status.get("steps", []):
        typer.echo(
            f"  {step['step']:18s} {step['status']:4s} "
            f"{step['duration_sec']:.1f}s {step['message'][:140]}"
        )


@app.command("status")
def cli_status() -> None:
    """Print the latest daily pipeline status."""
    from mais.ops import DAILY_STATUS_JSON, load_daily_status

    status = load_daily_status()
    typer.echo(f"Daily status: {status.get('overall_status')}")
    typer.echo(f"Generated at: {status.get('generated_at', 'NA')}")
    typer.echo(f"File: {DAILY_STATUS_JSON}")
    for step in status.get("steps", []):
        typer.echo(f"  {step.get('step'):18s} {step.get('status'):4s} {step.get('message', '')[:160]}")


def main() -> None:
    """Entry-point used by ``python -m mais.cli`` and the ``mais`` script."""
    app()


if __name__ == "__main__":
    main()

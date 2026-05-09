"""Agronomic revenue backtest of sell/store recommendations.

The backtest simulates a farmer with one normalized bushel available after
harvest. Every business day the decision rules can sell a fraction of the
remaining inventory. Unsold grain pays a daily storage cost. Any inventory left
before the next harvest is liquidated.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, INTERIM_DIR
from mais.study.professional import CALIBRATED_PREDICTIONS_PARQUET, REGIME_PARQUET
from mais.utils import get_logger, load_decision, read_parquet, read_table, write_parquet

from .rules import Action, advise, load_rules

log = get_logger("mais.decision.backtest")

BACKTEST_DIR = ARTEFACTS_DIR / "farmer_backtest"
BACKTEST_DAILY_PARQUET = BACKTEST_DIR / "daily_decisions.parquet"
BACKTEST_SUMMARY_JSON = BACKTEST_DIR / "summary.json"
BACKTEST_REPORT = Path("docs/FARMER_BACKTEST_REPORT.md")


@dataclass(frozen=True)
class StrategyResult:
    strategy: str
    avg_revenue_per_bu: float
    sharpe_per_year: float
    pct_years_beating_harvest_only: float
    max_drawdown_revenue: float
    n_years: int


def run_backtest(horizon: int = 20, farmer_state: str = "iowa") -> str:
    """Run a full historical farmer revenue backtest and write artefacts."""
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    cfg = load_decision()
    profile = cfg.get("farmer_profile", {}).get("default", {}).copy()
    profile["location_state"] = farmer_state
    basis = float(profile.get("basis_local_typical_usd_per_bu", -0.20))
    storage_monthly = float(profile.get("storage_cost_usd_per_bu_per_month", 0.04))

    prices = _load_cash_prices(basis)
    predictions = _load_prediction_inputs(horizon)
    regimes = _load_regimes()
    daily = prices.merge(predictions, on="Date", how="inner").merge(regimes, on="Date", how="left")
    daily = daily.sort_values("Date").reset_index(drop=True)
    if daily.empty:
        return "Farmer backtest aborted: no aligned price/prediction rows. Run `mais study` first."

    rules, _ = load_rules()
    strategy_daily, strategy_years = _simulate_strategy(
        daily=daily,
        horizon=horizon,
        profile=profile,
        rules=rules,
        storage_monthly=storage_monthly,
    )
    harvest_years = _simulate_harvest_baseline(daily, storage_monthly=storage_monthly)
    dca_years = _simulate_dca_baseline(daily, storage_monthly=storage_monthly)

    all_years = pd.concat([strategy_years, harvest_years, dca_years], ignore_index=True)
    write_parquet(strategy_daily, BACKTEST_DAILY_PARQUET)
    write_parquet(all_years, BACKTEST_DIR / "yearly_results.parquet")

    summary_rows = _summarise_years(all_years)
    summary = {
        "horizon": horizon,
        "farmer_state": farmer_state,
        "basis_usd_per_bu": basis,
        "storage_cost_usd_per_bu_per_month": storage_monthly,
        "date_min": str(daily["Date"].min().date()),
        "date_max": str(daily["Date"].max().date()),
        "n_decision_days": int(len(strategy_daily)),
        "strategies": [r.__dict__ for r in summary_rows],
        "artefacts": {
            "daily_decisions": str(BACKTEST_DAILY_PARQUET),
            "yearly_results": str(BACKTEST_DIR / "yearly_results.parquet"),
        },
    }
    BACKTEST_SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")
    _write_backtest_report(summary, all_years)
    best = max(summary_rows, key=lambda r: r.avg_revenue_per_bu)
    adviser = next((r for r in summary_rows if r.strategy == "model_adviser"), None)
    adviser_line = ""
    if adviser:
        adviser_line = (
            f"Model adviser: revenue={adviser.avg_revenue_per_bu:.3f} USD/bu, "
            f"Sharpe={adviser.sharpe_per_year:.2f}, "
            f"beats harvest={adviser.pct_years_beating_harvest_only:.1%}\n"
        )
    return (
        f"Farmer revenue backtest H{horizon} ({farmer_state})\n"
        f"Period: {summary['date_min']} -> {summary['date_max']} | days={len(strategy_daily)}\n"
        f"{adviser_line}"
        f"Best strategy: {best.strategy} ({best.avg_revenue_per_bu:.3f} USD/bu)\n"
        f"Wrote {BACKTEST_SUMMARY_JSON}"
    )


def _load_cash_prices(basis: float) -> pd.DataFrame:
    db = read_table(INTERIM_DIR / "database.parquet", date_col="Date")
    if "corn_close" not in db.columns:
        raise KeyError("interim/database.parquet missing corn_close")
    out = db[["Date", "corn_close"]].copy()
    raw = pd.to_numeric(out["corn_close"], errors="coerce")
    out["futures_usd_per_bu"] = np.where(raw > 50, raw / 100.0, raw)
    out["cash_price"] = out["futures_usd_per_bu"] + basis
    return out[["Date", "futures_usd_per_bu", "cash_price"]].dropna()


def _load_prediction_inputs(horizon: int) -> pd.DataFrame:
    if not CALIBRATED_PREDICTIONS_PARQUET.exists():
        raise FileNotFoundError(f"Missing {CALIBRATED_PREDICTIONS_PARQUET}; run `mais study`.")
    cal = read_parquet(CALIBRATED_PREDICTIONS_PARQUET)
    cal["Date"] = pd.to_datetime(cal["Date"])
    model = _best_available_model(cal, horizon)
    h = cal[(cal["horizon"] == horizon) & (cal["model"] == model)].copy()
    h10 = cal[(cal["horizon"] == 10) & (cal["model"] == _best_available_model(cal, 10))].copy()
    keep = ["Date", "q10_logret", "q50_logret", "q90_logret", f"p_up_strong_h{horizon}"]
    h = h[[c for c in keep if c in h.columns]]
    h = h.rename(
        columns={
            "q10_logret": f"q10_logret_h{horizon}",
            "q50_logret": f"q50_logret_h{horizon}",
            "q90_logret": f"q90_logret_h{horizon}",
        }
    )
    if f"p_up_strong_h{horizon}" not in h.columns:
        h[f"p_up_strong_h{horizon}"] = 0.5
    if not h10.empty and "p_down_strong_h10" in h10.columns:
        h = h.merge(h10[["Date", "p_down_strong_h10"]], on="Date", how="left")
    else:
        h["p_down_strong_h10"] = 0.2
    return h


def _best_available_model(cal: pd.DataFrame, horizon: int) -> str:
    sub = cal[cal["horizon"] == horizon]
    if sub.empty:
        raise ValueError(f"No calibrated predictions for horizon {horizon}")
    # Prefer the operational model used by the study snapshot, then robust tree models.
    for name in ("rf_factors", "lgbm_factors", "hgb_factors", "ridge_factors"):
        if name in set(sub["model"]):
            return name
    return str(sub["model"].iloc[0])


def _load_regimes() -> pd.DataFrame:
    if not REGIME_PARQUET.exists():
        return pd.DataFrame(columns=["Date", "regime"])
    r = read_table(REGIME_PARQUET, date_col="Date")
    return r[["Date", "regime"]].drop_duplicates("Date")


def _simulate_strategy(
    daily: pd.DataFrame,
    horizon: int,
    profile: dict[str, Any],
    rules: list[dict[str, Any]],
    storage_monthly: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    years = []
    for season, season_df in _season_groups(daily):
        inventory = 1.0
        revenue = 0.0
        storage_paid = 0.0
        season_rows = []
        for _, row in season_df.iterrows():
            if inventory <= 1e-9:
                break
            cash = float(row["cash_price"])
            preds = _row_predictions(row, horizon, cash)
            rec = advise(preds, profile=profile, rules=rules)
            fraction = min(max(float(rec.sell_fraction), 0.0), 1.0)
            if rec.action in {Action.STORE, Action.WAIT}:
                fraction = 0.0
            sell_qty = inventory * fraction
            revenue += sell_qty * cash
            inventory -= sell_qty
            daily_storage = inventory * storage_monthly / 30.0
            storage_paid += daily_storage
            season_rows.append(
                {
                    "Date": row["Date"],
                    "season": season,
                    "strategy": "model_adviser",
                    "cash_price": cash,
                    "action": rec.action.value,
                    "rule_id": rec.rule_id,
                    "sell_fraction": fraction,
                    "sold_bushels": sell_qty,
                    "inventory_remaining": inventory,
                    "storage_cost_cum": storage_paid,
                    "gross_revenue": revenue,
                }
            )
        if inventory > 1e-9 and not season_df.empty:
            final_cash = float(season_df["cash_price"].iloc[-1])
            revenue += inventory * final_cash
            season_rows.append(
                {
                    "Date": season_df["Date"].iloc[-1],
                    "season": season,
                    "strategy": "model_adviser",
                    "cash_price": final_cash,
                    "action": "FORCE_LIQUIDATE",
                    "rule_id": "season_end",
                    "sell_fraction": 1.0,
                    "sold_bushels": inventory,
                    "inventory_remaining": 0.0,
                    "storage_cost_cum": storage_paid,
                    "gross_revenue": revenue,
                }
            )
            inventory = 0.0
        rows.extend(season_rows)
        years.append(
            {
                "season": season,
                "strategy": "model_adviser",
                "gross_revenue_per_bu": revenue,
                "storage_cost_per_bu": storage_paid,
                "net_revenue_per_bu": revenue - storage_paid,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(years)


def _row_predictions(row: pd.Series, horizon: int, cash: float) -> dict[str, Any]:
    q10 = cash * math.exp(float(row.get(f"q10_logret_h{horizon}", 0.0)))
    q50 = cash * math.exp(float(row.get(f"q50_logret_h{horizon}", 0.0)))
    q90 = cash * math.exp(float(row.get(f"q90_logret_h{horizon}", 0.0)))
    return {
        f"p_up_strong_h{horizon}": float(row.get(f"p_up_strong_h{horizon}", 0.5)),
        "p_down_strong_h10": float(row.get("p_down_strong_h10", 0.2)),
        f"q10_h{horizon}": q10,
        f"q50_h{horizon}": q50,
        f"q90_h{horizon}": q90,
        "q10_h20": q10,
        "q50_h20": q50,
        "q90_h20": q90,
        "regime": str(row.get("regime", "unknown")),
        "p_t": cash,
    }


def _simulate_harvest_baseline(daily: pd.DataFrame, storage_monthly: float) -> pd.DataFrame:
    rows = []
    for season, season_df in _season_groups(daily):
        if season_df.empty:
            continue
        price = float(season_df["cash_price"].iloc[0])
        rows.append(
            {
                "season": season,
                "strategy": "sell_at_harvest_100",
                "gross_revenue_per_bu": price,
                "storage_cost_per_bu": 0.0,
                "net_revenue_per_bu": price,
            }
        )
    return pd.DataFrame(rows)


def _simulate_dca_baseline(daily: pd.DataFrame, storage_monthly: float) -> pd.DataFrame:
    rows = []
    for season, season_df in _season_groups(daily):
        if season_df.empty:
            continue
        checkpoints = np.linspace(0, len(season_df) - 1, 4, dtype=int)
        inventory = 1.0
        revenue = 0.0
        storage = 0.0
        for i, (_, row) in enumerate(season_df.iterrows()):
            if i in set(checkpoints[:-1]) and inventory > 1e-9:
                qty = min(1.0 / 3.0, inventory)
                revenue += qty * float(row["cash_price"])
                inventory -= qty
            storage += inventory * storage_monthly / 30.0
        if inventory > 1e-9:
            revenue += inventory * float(season_df["cash_price"].iloc[-1])
        rows.append(
            {
                "season": season,
                "strategy": "sell_dca_monthly",
                "gross_revenue_per_bu": revenue,
                "storage_cost_per_bu": storage,
                "net_revenue_per_bu": revenue - storage,
            }
        )
    return pd.DataFrame(rows)


def _season_groups(daily: pd.DataFrame):
    df = daily.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["season"] = np.where(df["Date"].dt.month >= 10, df["Date"].dt.year, df["Date"].dt.year - 1)
    # Simulate marketing year from Oct 15 through Sep 30.
    df = df[(df["Date"].dt.month > 10) | ((df["Date"].dt.month == 10) & (df["Date"].dt.day >= 15)) | (df["Date"].dt.month < 10)]
    for season, sub in df.groupby("season", sort=True):
        if len(sub) >= 40:
            yield int(season), sub.sort_values("Date")


def _summarise_years(all_years: pd.DataFrame) -> list[StrategyResult]:
    if all_years.empty:
        return []
    pivot = all_years.pivot_table(
        index="season", columns="strategy", values="net_revenue_per_bu", aggfunc="first"
    )
    baseline = pivot.get("sell_at_harvest_100")
    out = []
    for strategy, sub in all_years.groupby("strategy"):
        vals = sub.sort_values("season")["net_revenue_per_bu"].astype(float)
        avg = float(vals.mean())
        sd = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
        sharpe = float(avg / sd) if sd > 0 else 0.0
        pct = 0.0
        if baseline is not None:
            aligned = sub.set_index("season")["net_revenue_per_bu"].reindex(baseline.index)
            mask = aligned.notna() & baseline.notna()
            pct = float((aligned[mask] > baseline[mask]).mean()) if mask.any() else 0.0
        running = vals.cumsum()
        drawdown = running - running.cummax()
        out.append(
            StrategyResult(
                strategy=str(strategy),
                avg_revenue_per_bu=avg,
                sharpe_per_year=sharpe,
                pct_years_beating_harvest_only=pct,
                max_drawdown_revenue=float(drawdown.min()) if len(drawdown) else 0.0,
                n_years=int(vals.count()),
            )
        )
    return sorted(out, key=lambda r: r.avg_revenue_per_bu, reverse=True)


def _write_backtest_report(summary: dict[str, Any], all_years: pd.DataFrame) -> None:
    BACKTEST_REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Backtest agriculteur",
        "",
        f"- Horizon: J+{summary['horizon']}",
        f"- État/profil: `{summary['farmer_state']}`",
        f"- Période: `{summary['date_min']}` -> `{summary['date_max']}`",
        f"- Basis: {summary['basis_usd_per_bu']:.2f} USD/bu",
        f"- Coût stockage: {summary['storage_cost_usd_per_bu_per_month']:.2f} USD/bu/mois",
        "",
        "## Résumé stratégies",
        "",
        "| Stratégie | Revenu net moyen USD/bu | Sharpe annuel | Années > harvest | Max drawdown | N années |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary.get("strategies", []):
        lines.append(
            f"| `{row['strategy']}` | {row['avg_revenue_per_bu']:.3f} | "
            f"{row['sharpe_per_year']:.2f} | {row['pct_years_beating_harvest_only']:.1%} | "
            f"{row['max_drawdown_revenue']:.3f} | {int(row['n_years'])} |"
        )
    lines.extend(["", "## Résultats annuels", ""])
    if not all_years.empty:
        pivot = all_years.pivot_table(
            index="season", columns="strategy", values="net_revenue_per_bu", aggfunc="first"
        ).reset_index()
        cols = ["season"] + [c for c in pivot.columns if c != "season"]
        lines.append("| " + " | ".join(str(c) for c in cols) + " |")
        lines.append("|" + "|".join(["---:"] * len(cols)) + "|")
        for _, row in pivot[cols].iterrows():
            vals = [str(int(row["season"]))]
            for c in cols[1:]:
                vals.append("" if pd.isna(row[c]) else f"{float(row[c]):.3f}")
            lines.append("| " + " | ".join(vals) + " |")
    lines.extend(
        [
            "",
            "Lecture: ce backtest simule un boisseau normalisé disponible après récolte. "
            "Le modèle vend une fraction du stock selon les règles agriculteur, paie le "
            "stockage sur l'inventaire restant, puis liquide tout reliquat avant la saison suivante.",
        ]
    )
    BACKTEST_REPORT.write_text("\n".join(lines), encoding="utf-8")

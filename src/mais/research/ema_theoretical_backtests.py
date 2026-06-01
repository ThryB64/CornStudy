"""FIX-EMA-08 — Backtests théoriques EMA relatif/basis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_direction_benchmarks_v2 import _load_dataset

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_theoretical_backtests.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_THEORETICAL_BACKTESTS.md"
_HORIZONS = (40, 60)
_COST_EUR_T = 1.0


def _max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return float("nan")
    curve = values.cumsum()
    drawdown = curve - curve.cummax()
    return float(drawdown.min())


def _yearly_stats(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {}
    yearly = trades.groupby(trades["Date"].dt.year)["pnl_eur_t"].sum()
    return {str(int(year)): float(value) for year, value in yearly.items()}


def _summarise(trades: pd.DataFrame, strategy: str, horizon: int) -> dict:
    if trades.empty:
        return {
            "strategy": strategy,
            "horizon_days": int(horizon),
            "status": "SKIPPED",
            "reason": "no_trades",
            "n_trades": 0,
        }
    pnl = trades["pnl_eur_t"]
    yearly = _yearly_stats(trades)
    worst_year = min(yearly, key=yearly.get) if yearly else None
    sharpe = float(pnl.mean() / pnl.std() * np.sqrt(len(pnl))) if pnl.std() > 0 else float("nan")
    return {
        "strategy": strategy,
        "horizon_days": int(horizon),
        "status": "OK",
        "n_trades": int(len(trades)),
        "hit_rate": float((pnl > 0).mean()),
        "pnl_total_eur_t": float(pnl.sum()),
        "pnl_mean_eur_t": float(pnl.mean()),
        "pnl_median_eur_t": float(pnl.median()),
        "sharpe_naive": sharpe,
        "max_drawdown_eur_t": _max_drawdown(pnl),
        "worst_year": worst_year,
        "worst_year_pnl_eur_t": yearly.get(worst_year) if worst_year else None,
        "yearly_pnl_eur_t": yearly,
    }


def _trade_frame(df: pd.DataFrame, horizon: int, signal: pd.Series, mode: str) -> pd.DataFrame:
    step = max(int(horizon), 1)
    idx = np.arange(0, len(df), step)
    work = df.iloc[idx].copy()
    sig = signal.iloc[idx].reindex(work.index)
    ema_change = df["ema_front_price"].shift(-horizon) - df["ema_front_price"]
    cbot_change = df["cbot_eur_t"].shift(-horizon) - df["cbot_eur_t"]
    if mode == "relative":
        gross = sig * (ema_change.iloc[idx].to_numpy() - cbot_change.iloc[idx].to_numpy())
        cost = _COST_EUR_T * 2.0
    elif mode == "ema_direct":
        gross = sig * ema_change.iloc[idx].to_numpy()
        cost = _COST_EUR_T
    else:
        raise ValueError(f"Unknown mode: {mode}")
    trades = pd.DataFrame({
        "Date": work["Date"].to_numpy(),
        "signal": sig.to_numpy(dtype=float),
        "pnl_eur_t": gross - cost,
    })
    trades = trades.replace([np.inf, -np.inf], np.nan).dropna()
    trades = trades[trades["signal"].ne(0.0)].copy()
    return trades


def _signals(df: pd.DataFrame) -> dict[str, pd.Series]:
    basis_z = df["ema_cbot_basis_zscore_52w"]
    ema_momentum = np.where(df["ema_front_price"].pct_change(20) > 0, 1.0, -1.0)
    relative_basis = np.where(basis_z < 0, 1.0, -1.0)
    basis_extreme = pd.Series(0.0, index=df.index)
    basis_extreme.loc[basis_z > 2.0] = -1.0
    basis_extreme.loc[basis_z < -2.0] = 1.0
    return {
        "ema_direct_momentum": pd.Series(ema_momentum, index=df.index),
        "relative_basis_z_rule": pd.Series(relative_basis, index=df.index),
        "basis_extreme_mean_reversion": basis_extreme,
    }


def build_theoretical_backtests() -> dict:
    df = _load_dataset().dropna(subset=["ema_front_price", "cbot_eur_t", "ema_cbot_basis_zscore_52w"]).copy()
    sigs = _signals(df)
    rows = []
    for horizon in _HORIZONS:
        for strategy, signal in sigs.items():
            mode = "ema_direct" if strategy == "ema_direct_momentum" else "relative"
            trades = _trade_frame(df, horizon, signal, mode)
            rows.append(_summarise(trades, strategy, horizon))
    ok = [row for row in rows if row.get("status") == "OK"]
    best = max(ok, key=lambda row: row["pnl_mean_eur_t"], default={})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "status": "THEORETICAL_ONLY_NOT_PRODUCTION",
        "cost_assumption_eur_t_per_leg": _COST_EUR_T,
        "protocol": "Non-overlapping approximate trades; no leverage; simple EUR/t cost; exploratory proxy EMA data.",
        "results": rows,
        "key_findings": {
            "best_strategy": best.get("strategy"),
            "best_horizon_days": best.get("horizon_days"),
            "best_pnl_mean_eur_t": best.get("pnl_mean_eur_t"),
            "best_hit_rate": best.get("hit_rate"),
            "production_verdict": "NO_PRODUCTION_BACKTEST",
        },
    }


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


def _fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    value_float = float(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA THEORETICAL BACKTESTS",
        "",
        "> Backtests exploratoires. Ce n'est pas un système de trading ni une validation production.",
        "",
        "## Verdict",
        "",
        f"- Statut : {data['status']}",
        f"- Meilleure stratégie : {k.get('best_strategy')} H{k.get('best_horizon_days')}",
        f"- PnL moyen meilleur cas : {_fmt(k.get('best_pnl_mean_eur_t'), 2)} EUR/t",
        f"- Hit rate meilleur cas : {_fmt(k.get('best_hit_rate'))}",
        f"- Verdict production : {k.get('production_verdict')}",
        "",
        "## Résultats",
        "",
        "| Stratégie | H | n | Hit rate | PnL total | PnL moyen | Worst year | Max DD |",
        "|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| {row['strategy']} | {row['horizon_days']} | {row.get('n_trades', 0)} | "
            f"{_fmt(row.get('hit_rate'))} | {_fmt(row.get('pnl_total_eur_t'), 2)} | "
            f"{_fmt(row.get('pnl_mean_eur_t'), 2)} | {row.get('worst_year')} | "
            f"{_fmt(row.get('max_drawdown_eur_t'), 2)} |"
        )
    lines += [
        "",
        "Limites : source EMA proxy, frictions simplifiées, pas de liquidité réelle, pas de bid-ask historique, pas de sizing, pas de levier.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_theoretical_backtests(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_theoretical_backtests()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_theoretical_backtests()
    print(f"Theoretical backtests saved -> {out}")

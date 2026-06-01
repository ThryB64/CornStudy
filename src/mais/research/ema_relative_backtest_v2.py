"""EMA-BT-01 — Backtest relatif EMA/CBOT V2 avec couts stresses."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import build_relative_frame, oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_backtest_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_BACKTEST_V2.md"
_COSTS_PER_LEG = (1.0, 2.0, 3.0, 5.0)
_ROLL_RISK_MONTHS = {2, 3, 5, 6, 7, 8, 10, 11}


def _basis_score(zscore: pd.Series) -> pd.Series:
    return 1.0 / (1.0 + np.exp(zscore.clip(-8, 8)))


def _base_frame() -> pd.DataFrame:
    base = build_relative_frame((40, 90)).sort_values("Date").reset_index(drop=True)
    base["entry_pos"] = np.arange(len(base))
    for horizon in (40, 90):
        base[f"relative_change_eur_t_h{horizon}"] = (
            base["ema_front_price"].shift(-horizon)
            - base["ema_front_price"]
            - (base["cbot_eur_t"].shift(-horizon) - base["cbot_eur_t"])
        )
    keep_cols = ["Date", "entry_pos", "relative_change_eur_t_h40", "relative_change_eur_t_h90"]
    h40 = oof_relative_predictions(base, horizon=40).rename(
        columns={"prob": "prob_h40", "confidence": "confidence_h40"}
    )
    h90 = oof_relative_predictions(base, horizon=90)[["Date", "prob", "confidence"]].rename(
        columns={"prob": "prob_h90", "confidence": "confidence_h90"}
    )
    out = h40.merge(h90, on="Date", how="inner").merge(base[keep_cols], on="Date", how="left")
    out["Date"] = pd.to_datetime(out["Date"])
    out["month"] = out["Date"].dt.month
    out["year"] = out["Date"].dt.year
    out["roll_risk_proxy"] = out["month"].isin(_ROLL_RISK_MONTHS)
    out["basis_score"] = _basis_score(out["ema_cbot_basis_zscore_52w"])
    out["combined_score"] = 0.40 * out["prob_h40"] + 0.30 * out["prob_h90"] + 0.30 * out["basis_score"]
    out["combined_confidence"] = (out["combined_score"] - 0.5).abs()
    out = out.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["entry_pos", "relative_change_eur_t_h40", "relative_change_eur_t_h90"]
    )
    return out.sort_values("Date").reset_index(drop=True)


def _weekly_last(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.set_index("Date").resample("W-FRI").last().dropna(subset=["entry_pos"]).reset_index()
    out["roll_risk_proxy"] = out["roll_risk_proxy"].astype(bool)
    return out


def _strategy_frame(frame: pd.DataFrame, strategy: str) -> tuple[pd.DataFrame, int, str]:
    work = _weekly_last(frame)
    if strategy == "h40_top20_confidence_weekly":
        cutoff = work["confidence_h40"].quantile(0.80)
        work = work[work["confidence_h40"] >= cutoff].copy()
        work["score"] = work["prob_h40"]
        horizon = 40
    elif strategy == "h40_basis_extreme_weekly":
        work = work[work["ema_cbot_basis_zscore_52w"].abs() >= 1.5].copy()
        work["score"] = work["prob_h40"]
        horizon = 40
    elif strategy == "h90_combined_top40_weekly":
        cutoff = work["combined_confidence"].quantile(0.60)
        work = work[work["combined_confidence"] >= cutoff].copy()
        work["score"] = work["combined_score"]
        horizon = 90
    elif strategy == "premium_medium_high_no_roll_weekly":
        work = work[(work["combined_confidence"] >= 0.15) & (~work["roll_risk_proxy"])].copy()
        work["score"] = work["combined_score"]
        horizon = 40
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    work["signal"] = np.where(work["score"] >= 0.5, 1.0, -1.0)
    return work, horizon, f"relative_change_eur_t_h{horizon}"


def _non_overlapping(work: pd.DataFrame, horizon: int) -> pd.DataFrame:
    selected = []
    last_exit = -horizon - 1
    for _, row in work.sort_values("Date").iterrows():
        entry = int(row["entry_pos"])
        if entry <= last_exit:
            continue
        selected.append(row)
        last_exit = entry + horizon
    return pd.DataFrame(selected)


def _max_drawdown(pnl: pd.Series) -> float | None:
    if pnl.empty:
        return None
    curve = pnl.cumsum()
    return float((curve - curve.cummax()).min())


def _profit_factor(pnl: pd.Series) -> float | None:
    gains = pnl[pnl > 0].sum()
    losses = pnl[pnl < 0].sum()
    if losses == 0:
        return None
    return float(gains / abs(losses))


def _summarise(trades: pd.DataFrame, strategy: str, horizon: int, cost_per_leg: float) -> dict:
    if trades.empty:
        return {
            "strategy": strategy,
            "horizon_days": int(horizon),
            "cost_per_leg_eur_t": float(cost_per_leg),
            "status": "SKIPPED",
            "n_trades": 0,
        }
    pnl = trades["pnl_net_eur_t"]
    yearly = trades.groupby(trades["Date"].dt.year)["pnl_net_eur_t"].sum()
    worst_year = str(int(yearly.idxmin())) if len(yearly) else None
    return {
        "strategy": strategy,
        "horizon_days": int(horizon),
        "cost_per_leg_eur_t": float(cost_per_leg),
        "status": "OK",
        "n_trades": int(len(trades)),
        "hit_rate": float((pnl > 0).mean()),
        "pnl_total_eur_t": float(pnl.sum()),
        "pnl_mean_eur_t": float(pnl.mean()),
        "profit_factor": _profit_factor(pnl),
        "max_drawdown_eur_t": _max_drawdown(pnl),
        "worst_year": worst_year,
        "worst_year_pnl_eur_t": float(yearly.min()) if len(yearly) else None,
        "positive_year_share": float((yearly > 0).mean()) if len(yearly) else None,
        "yearly_pnl_eur_t": {str(int(year)): float(value) for year, value in yearly.items()},
    }


def _backtest_strategy(frame: pd.DataFrame, strategy: str, cost_per_leg: float) -> dict:
    work, horizon, change_col = _strategy_frame(frame, strategy)
    work = _non_overlapping(work, horizon)
    if work.empty:
        return _summarise(pd.DataFrame(), strategy, horizon, cost_per_leg)
    work["pnl_gross_eur_t"] = work["signal"] * work[change_col]
    work["cost_eur_t"] = 2.0 * cost_per_leg
    work["pnl_net_eur_t"] = work["pnl_gross_eur_t"] - work["cost_eur_t"]
    return _summarise(work, strategy, horizon, cost_per_leg)


def build_relative_backtest_v2() -> dict:
    frame = _base_frame()
    strategies = [
        "h40_top20_confidence_weekly",
        "h40_basis_extreme_weekly",
        "h90_combined_top40_weekly",
        "premium_medium_high_no_roll_weekly",
    ]
    rows = []
    for cost in _COSTS_PER_LEG:
        for strategy in strategies:
            rows.append(_backtest_strategy(frame, strategy, cost))
    ok = [row for row in rows if row.get("status") == "OK"]
    best = max(ok, key=lambda row: (row.get("pnl_mean_eur_t", -np.inf), row.get("hit_rate", 0)), default={})
    stress = [
        row for row in ok if row["strategy"] == best.get("strategy")
    ]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "production_verdict": "NO_PRODUCTION_BACKTEST",
        "protocol": {
            "entries": "weekly Friday last available observation",
            "overlap": "strict non-overlap by horizon row position",
            "costs_per_leg_eur_t": list(_COSTS_PER_LEG),
            "legs": 2,
            "execution_limits": "No bid-ask history, no margin model, proxy settlement-to-settlement.",
        },
        "results": rows,
        "key_findings": {
            "best_strategy": best.get("strategy"),
            "best_cost_per_leg": best.get("cost_per_leg_eur_t"),
            "best_horizon_days": best.get("horizon_days"),
            "best_n_trades": best.get("n_trades"),
            "best_hit_rate": best.get("hit_rate"),
            "best_pnl_mean_eur_t": best.get("pnl_mean_eur_t"),
            "best_pnl_total_eur_t": best.get("pnl_total_eur_t"),
            "same_strategy_cost_stress": stress,
            "interpretation": _interpretation(best, stress),
        },
    }


def _interpretation(best: dict, stress: list[dict]) -> str:
    if not best:
        return "No valid strategy under weekly non-overlap constraints."
    high_cost = next((row for row in stress if row.get("cost_per_leg_eur_t") == max(_COSTS_PER_LEG)), None)
    if high_cost and (high_cost.get("pnl_mean_eur_t") or 0) > 0:
        return "Best strategy stays positive even under high simplified costs, but proxy data prevents production use."
    return "Signal is sensitive to costs; keep as research-only until execution data are available."


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
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA RELATIVE BACKTEST V2",
        "",
        "> Backtest de recherche avec entrees weekly, non-overlap strict et stress de couts.",
        "",
        "## Verdict",
        "",
        f"- Statut : {data['status']}",
        f"- Verdict production : {data['production_verdict']}",
        f"- Meilleure strategie : `{k.get('best_strategy')}`",
        f"- Cout meilleur cas : {_fmt(k.get('best_cost_per_leg'), 1)} EUR/t par leg",
        f"- Trades : {k.get('best_n_trades')}",
        f"- Hit rate : {_fmt(k.get('best_hit_rate'))}",
        f"- PnL moyen : {_fmt(k.get('best_pnl_mean_eur_t'), 2)} EUR/t",
        f"- Lecture : {k.get('interpretation')}",
        "",
        "## Resultats",
        "",
        "| Strategie | H | Cout/leg | n | Hit rate | PnL total | PnL moyen | PF | Max DD | Pos years |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| {row['strategy']} | {row.get('horizon_days')} | {_fmt(row.get('cost_per_leg_eur_t'), 1)} | "
            f"{row.get('n_trades', 0)} | {_fmt(row.get('hit_rate'))} | {_fmt(row.get('pnl_total_eur_t'), 2)} | "
            f"{_fmt(row.get('pnl_mean_eur_t'), 2)} | {_fmt(row.get('profit_factor'))} | "
            f"{_fmt(row.get('max_drawdown_eur_t'), 2)} | {_fmt(row.get('positive_year_share'))} |"
        )
    lines += [
        "",
        "## Limites",
        "",
        "- Source EMA exploratoire/proxy.",
        "- Pas de bid-ask historique ni de profondeur de carnet.",
        "- Pas de modele de marge, change, roll execution reel ou sizing.",
        "- Resultat recherche seulement.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_backtest_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_backtest_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_backtest_v2()
    print(f"Relative backtest V2 saved -> {out}")

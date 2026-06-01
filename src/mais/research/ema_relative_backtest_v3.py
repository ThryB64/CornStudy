"""EMA-BT-03 — Backtest relatif V3 avec contraintes d'execution proxy."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_seasonality import _season
from mais.research.ema_relative_study import build_relative_frame, oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_backtest_v3.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_BACKTEST_V3.md"
_HORIZON = 90
_SLIPPAGE_STRESS = (1.0, 2.0, 3.0, 5.0)
_COMMISSION_PER_LEG = 0.5
_ROLL_COST_PER_LEG = 1.0
_NEAR_ROLL_MONTHS = {2, 5, 7, 10}
_ALLOWED_SEASONS = {"sep_nov_eu_harvest", "jul_aug_yield_stress", "dec_import_export_arbitrage"}


def _basis_score(zscore: pd.Series) -> pd.Series:
    return 1.0 / (1.0 + np.exp(zscore.clip(-8, 8)))


def _base_frame() -> pd.DataFrame:
    base = build_relative_frame((40, _HORIZON)).sort_values("Date").reset_index(drop=True)
    base["entry_pos"] = np.arange(len(base))
    base["relative_change_eur_t"] = (
        base["ema_front_price"].shift(-_HORIZON)
        - base["ema_front_price"]
        - (base["cbot_eur_t"].shift(-_HORIZON) - base["cbot_eur_t"])
    )
    h90 = oof_relative_predictions(base, horizon=_HORIZON).rename(
        columns={"prob": "prob_h90", "confidence": "confidence_h90"}
    )
    h40 = oof_relative_predictions(base, horizon=40)[["Date", "prob"]].rename(columns={"prob": "prob_h40"})
    out = h90.merge(h40, on="Date", how="inner").merge(
        base[["Date", "entry_pos", "relative_change_eur_t"]],
        on="Date",
        how="left",
    )
    out["Date"] = pd.to_datetime(out["Date"])
    out["year"] = out["Date"].dt.year
    out["month"] = out["Date"].dt.month
    out["season"] = out["month"].apply(_season)
    out["basis_score"] = _basis_score(out["ema_cbot_basis_zscore_52w"])
    out["combined_score"] = 0.40 * out["prob_h40"] + 0.30 * out["prob_h90"] + 0.30 * out["basis_score"]
    out["combined_confidence"] = (out["combined_score"] - 0.5).abs()
    out["near_roll_proxy"] = out["month"].isin(_NEAR_ROLL_MONTHS)
    return out.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["entry_pos", "relative_change_eur_t", "combined_score", "combined_confidence"]
    )


def _weekly(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.set_index("Date").resample("W-FRI").last().dropna(subset=["entry_pos"]).reset_index()
    out["near_roll_proxy"] = out["near_roll_proxy"].astype(bool)
    return out


def _train_only_signals(frame: pd.DataFrame) -> pd.DataFrame:
    weekly = _weekly(frame)
    selected = []
    years = sorted(weekly["year"].unique())
    for idx in range(3, len(years)):
        train_years = years[:idx]
        test_year = years[idx]
        train = weekly[weekly["year"].isin(train_years)]
        test = weekly[weekly["year"].eq(test_year)].copy()
        if len(train) < 100 or test.empty:
            continue
        cutoff = float(train["combined_confidence"].quantile(0.60))
        test = test[
            (test["combined_confidence"] >= cutoff)
            & (test["season"].isin(_ALLOWED_SEASONS))
            & (~test["near_roll_proxy"])
        ].copy()
        if test.empty:
            continue
        test["confidence_cutoff_train_only"] = cutoff
        selected.append(test)
    if not selected:
        return pd.DataFrame()
    out = pd.concat(selected, ignore_index=True).sort_values("Date").reset_index(drop=True)
    out["signal"] = np.where(out["combined_score"] >= 0.5, 1.0, -1.0)
    return out


def _non_overlap(frame: pd.DataFrame) -> pd.DataFrame:
    selected = []
    last_exit = -_HORIZON - 1
    for _, row in frame.sort_values("Date").iterrows():
        entry = int(row["entry_pos"])
        if entry <= last_exit:
            continue
        selected.append(row)
        last_exit = entry + _HORIZON
    return pd.DataFrame(selected)


def _profit_factor(pnl: pd.Series) -> float | None:
    gains = pnl[pnl > 0].sum()
    losses = pnl[pnl < 0].sum()
    if losses == 0:
        return None
    return float(gains / abs(losses))


def _max_drawdown(pnl: pd.Series) -> float | None:
    if pnl.empty:
        return None
    curve = pnl.cumsum()
    return float((curve - curve.cummax()).min())


def _sortino(pnl: pd.Series) -> float | None:
    downside = pnl[pnl < 0].std()
    if downside is None or not np.isfinite(downside) or downside == 0:
        return None
    return float(pnl.mean() / downside * np.sqrt(len(pnl)))


def _summarise(trades: pd.DataFrame, slippage_per_leg: float) -> dict:
    if trades.empty:
        return {
            "slippage_per_leg_eur_t": float(slippage_per_leg),
            "status": "SKIPPED",
            "n_trades": 0,
        }
    pnl = trades["pnl_net_eur_t"]
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    yearly = trades.groupby(trades["Date"].dt.year)["pnl_net_eur_t"].sum()
    worst_idx = pnl.idxmin()
    return {
        "slippage_per_leg_eur_t": float(slippage_per_leg),
        "status": "OK",
        "horizon_days": _HORIZON,
        "n_trades": int(len(trades)),
        "hit_rate": float((pnl > 0).mean()),
        "pnl_total_eur_t": float(pnl.sum()),
        "pnl_mean_eur_t": float(pnl.mean()),
        "profit_factor": _profit_factor(pnl),
        "sortino_naive": _sortino(pnl),
        "max_drawdown_eur_t": _max_drawdown(pnl),
        "avg_win_eur_t": float(wins.mean()) if len(wins) else None,
        "avg_loss_eur_t": float(losses.mean()) if len(losses) else None,
        "worst_trade_eur_t": float(pnl.loc[worst_idx]),
        "worst_trade_date": str(pd.Timestamp(trades.loc[worst_idx, "Date"]).date()),
        "positive_year_share": float((yearly > 0).mean()) if len(yearly) else None,
        "yearly_pnl_eur_t": {str(int(year)): float(value) for year, value in yearly.items()},
    }


def _run_cost_scenario(signals: pd.DataFrame, slippage_per_leg: float) -> dict:
    trades = _non_overlap(signals)
    if trades.empty:
        return _summarise(trades, slippage_per_leg)
    cost_per_trade = 2.0 * (_COMMISSION_PER_LEG + _ROLL_COST_PER_LEG + slippage_per_leg)
    trades = trades.copy()
    trades["pnl_gross_eur_t"] = trades["signal"] * trades["relative_change_eur_t"]
    trades["cost_eur_t"] = cost_per_trade
    trades["pnl_net_eur_t"] = trades["pnl_gross_eur_t"] - trades["cost_eur_t"]
    return _summarise(trades, slippage_per_leg)


def build_relative_backtest_v3() -> dict:
    frame = _base_frame()
    signals = _train_only_signals(frame)
    rows = [_run_cost_scenario(signals, slippage) for slippage in _SLIPPAGE_STRESS]
    ok = [row for row in rows if row.get("status") == "OK"]
    high_cost = next((row for row in ok if row["slippage_per_leg_eur_t"] == max(_SLIPPAGE_STRESS)), {})
    best = max(ok, key=lambda row: row.get("pnl_mean_eur_t", -np.inf), default={})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "production_verdict": "NO_PRODUCTION_BACKTEST",
        "protocol": {
            "target": "relative_ema_outperformance_h90",
            "entries": "weekly Friday",
            "threshold": "combined confidence top40 threshold learned on prior years only",
            "season_filter": sorted(_ALLOWED_SEASONS),
            "no_trade_near_roll_proxy_months": sorted(_NEAR_ROLL_MONTHS),
            "non_overlap": "strict by 90 trading-row horizon",
            "commission_per_leg_eur_t": _COMMISSION_PER_LEG,
            "roll_cost_per_leg_eur_t": _ROLL_COST_PER_LEG,
            "slippage_stress_per_leg_eur_t": list(_SLIPPAGE_STRESS),
        },
        "n_candidate_signals_before_non_overlap": int(len(signals)),
        "results": rows,
        "key_findings": {
            "best_slippage_per_leg": best.get("slippage_per_leg_eur_t"),
            "best_n_trades": best.get("n_trades"),
            "best_hit_rate": best.get("hit_rate"),
            "best_pnl_mean_eur_t": best.get("pnl_mean_eur_t"),
            "high_cost_pnl_mean_eur_t": high_cost.get("pnl_mean_eur_t"),
            "high_cost_positive": (high_cost.get("pnl_mean_eur_t") or 0) > 0 if high_cost else None,
            "interpretation": _interpretation(high_cost),
        },
    }


def _interpretation(high_cost: dict) -> str:
    if high_cost and (high_cost.get("pnl_mean_eur_t") or 0) > 0:
        return "V3 remains positive under the highest proxy slippage, but sample size and proxy execution keep it research-only."
    return "V3 is too sensitive to execution costs for an economic claim."


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
        "# EMA RELATIVE BACKTEST V3",
        "",
        "> Backtest de recherche H90 avec seuils train-only et contraintes d'execution proxy.",
        "",
        "## Verdict",
        "",
        f"- Statut : {data['status']}",
        f"- Production : {data['production_verdict']}",
        f"- Signaux candidats avant non-overlap : {data['n_candidate_signals_before_non_overlap']}",
        f"- Meilleur slippage/leg : {_fmt(k.get('best_slippage_per_leg'), 1)} EUR/t",
        f"- Meilleurs trades : {k.get('best_n_trades')}",
        f"- Meilleur hit rate : {_fmt(k.get('best_hit_rate'))}",
        f"- PnL moyen meilleur cas : {_fmt(k.get('best_pnl_mean_eur_t'), 2)} EUR/t",
        f"- PnL moyen high cost : {_fmt(k.get('high_cost_pnl_mean_eur_t'), 2)} EUR/t",
        f"- Lecture : {k.get('interpretation')}",
        "",
        "## Resultats",
        "",
        "| Slippage/leg | n | Hit rate | PnL total | PnL moyen | PF | Sortino | Avg win | Avg loss | Max DD | Pos years |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| {_fmt(row.get('slippage_per_leg_eur_t'), 1)} | {row.get('n_trades', 0)} | {_fmt(row.get('hit_rate'))} | "
            f"{_fmt(row.get('pnl_total_eur_t'), 2)} | {_fmt(row.get('pnl_mean_eur_t'), 2)} | "
            f"{_fmt(row.get('profit_factor'))} | {_fmt(row.get('sortino_naive'))} | "
            f"{_fmt(row.get('avg_win_eur_t'), 2)} | {_fmt(row.get('avg_loss_eur_t'), 2)} | "
            f"{_fmt(row.get('max_drawdown_eur_t'), 2)} | {_fmt(row.get('positive_year_share'))} |"
        )
    lines += [
        "",
        "## Limites",
        "",
        "- Source EMA proxy.",
        "- Roll cost et slippage restent proxies.",
        "- Pas de bid-ask reel, marge, change, taille ou execution carnet.",
        "- Recherche seulement.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_backtest_v3(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_backtest_v3()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_backtest_v3()
    print(f"Relative backtest V3 saved -> {out}")

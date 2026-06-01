"""REL-EMA-05 — Backtest relatif EMA/CBOT H40."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import build_relative_frame, oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_backtest.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_BACKTEST.md"
_HORIZON = 40
_COST_PER_LEG_EUR_T = 1.0
_ROLL_RISK_MONTHS = {2, 3, 5, 6, 7, 8, 10, 11}


def _finite_or_none(value: float | int | None) -> float | int | None:
    if value is None:
        return None
    value_float = float(value)
    return value_float if np.isfinite(value_float) else None


def _max_drawdown(pnl: pd.Series) -> float | None:
    if pnl.empty:
        return None
    curve = pnl.cumsum()
    drawdown = curve - curve.cummax()
    return _finite_or_none(drawdown.min())


def _profit_factor(pnl: pd.Series) -> float | None:
    gains = pnl[pnl > 0].sum()
    losses = pnl[pnl < 0].sum()
    if losses == 0:
        return None
    return _finite_or_none(gains / abs(losses))


def _yearly_pnl(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return {}
    yearly = trades.groupby(trades["Date"].dt.year)["pnl_net_eur_t"].sum()
    return {str(int(year)): float(value) for year, value in yearly.items()}


def _base_predictions() -> pd.DataFrame:
    base = build_relative_frame((_HORIZON,)).sort_values("Date").reset_index(drop=True)
    base["entry_pos"] = np.arange(len(base))
    base["ema_change_eur_t"] = base["ema_front_price"].shift(-_HORIZON) - base["ema_front_price"]
    base["cbot_change_eur_t"] = base["cbot_eur_t"].shift(-_HORIZON) - base["cbot_eur_t"]
    keep_cols = [
        "Date",
        "entry_pos",
        "ema_front_price",
        "cbot_eur_t",
        "ema_change_eur_t",
        "cbot_change_eur_t",
    ]
    pred = oof_relative_predictions(base, horizon=_HORIZON)
    pred = pred.merge(base[keep_cols], on="Date", how="left")
    pred["Date"] = pd.to_datetime(pred["Date"])
    pred["month"] = pred["Date"].dt.month
    pred["year"] = pred["Date"].dt.year
    pred["roll_risk_proxy"] = pred["month"].isin(_ROLL_RISK_MONTHS)
    pred["basis_extreme"] = pred["ema_cbot_basis_zscore_52w"].abs() >= 1.5
    pred["model_signal"] = np.where(pred["y_pred"].astype(float) >= 0.5, 1.0, -1.0)
    pred["basis_rule_signal"] = np.where(pred["ema_cbot_basis_zscore_52w"] < 0, 1.0, -1.0)
    pred["relative_change_eur_t"] = pred["ema_change_eur_t"] - pred["cbot_change_eur_t"]
    return pred.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["entry_pos", "relative_change_eur_t", "model_signal", "basis_rule_signal"]
    )


def _strategy_masks(pred: pd.DataFrame) -> dict[str, pd.Series]:
    top20_cutoff = pred["confidence"].quantile(0.80)
    top40_cutoff = pred["confidence"].quantile(0.60)
    return {
        "model_all": pd.Series(True, index=pred.index),
        "model_top20_confidence": pred["confidence"] >= top20_cutoff,
        "model_top40_confidence": pred["confidence"] >= top40_cutoff,
        "model_basis_extreme_filter": pred["basis_extreme"],
        "model_top20_basis_extreme": (pred["confidence"] >= top20_cutoff) & pred["basis_extreme"],
        "model_no_roll_risk": ~pred["roll_risk_proxy"],
        "basis_zscore_rule": pd.Series(True, index=pred.index),
    }


def _select_non_overlapping(work: pd.DataFrame, horizon: int = _HORIZON) -> pd.DataFrame:
    selected = []
    last_entry_pos = -horizon - 1
    for _, row in work.sort_values("Date").iterrows():
        entry_pos = int(row["entry_pos"])
        if entry_pos <= last_entry_pos + horizon:
            continue
        selected.append(row)
        last_entry_pos = entry_pos
    return pd.DataFrame(selected)


def _build_trades(pred: pd.DataFrame, strategy: str, mask: pd.Series) -> pd.DataFrame:
    sub = pred[mask].copy()
    sub = _select_non_overlapping(sub)
    if sub.empty:
        return pd.DataFrame()
    signal_col = "basis_rule_signal" if strategy == "basis_zscore_rule" else "model_signal"
    sub["signal"] = sub[signal_col].astype(float)
    sub["pnl_gross_eur_t"] = sub["signal"] * sub["relative_change_eur_t"]
    sub["cost_eur_t"] = _COST_PER_LEG_EUR_T * 2.0
    sub["pnl_net_eur_t"] = sub["pnl_gross_eur_t"] - sub["cost_eur_t"]
    sub["hit"] = sub["pnl_net_eur_t"] > 0
    cols = [
        "Date",
        "crop_year",
        "year",
        "signal",
        "prob",
        "confidence",
        "ema_cbot_basis_zscore_52w",
        "roll_risk_proxy",
        "basis_extreme",
        "relative_change_eur_t",
        "pnl_gross_eur_t",
        "cost_eur_t",
        "pnl_net_eur_t",
        "hit",
    ]
    return sub[cols].reset_index(drop=True)


def _summarise(trades: pd.DataFrame, strategy: str) -> dict:
    if trades.empty:
        return {
            "strategy": strategy,
            "status": "SKIPPED",
            "reason": "no_trades_after_filter_and_non_overlap",
            "horizon_days": _HORIZON,
            "n_trades": 0,
        }
    pnl = trades["pnl_net_eur_t"]
    yearly = _yearly_pnl(trades)
    worst_year = min(yearly, key=yearly.get) if yearly else None
    years = max(1.0, (trades["Date"].max() - trades["Date"].min()).days / 365.25)
    sharpe = pnl.mean() / pnl.std() * np.sqrt(len(pnl)) if pnl.std() > 0 else np.nan
    return {
        "strategy": strategy,
        "status": "OK",
        "horizon_days": _HORIZON,
        "n_trades": int(len(trades)),
        "turnover_trades_per_year": _finite_or_none(len(trades) / years),
        "hit_rate": _finite_or_none((pnl > 0).mean()),
        "pnl_total_eur_t": _finite_or_none(pnl.sum()),
        "pnl_mean_eur_t": _finite_or_none(pnl.mean()),
        "pnl_median_eur_t": _finite_or_none(pnl.median()),
        "gross_pnl_total_eur_t": _finite_or_none(trades["pnl_gross_eur_t"].sum()),
        "total_costs_eur_t": _finite_or_none(trades["cost_eur_t"].sum()),
        "avg_cost_eur_t": _finite_or_none(trades["cost_eur_t"].mean()),
        "profit_factor": _profit_factor(pnl),
        "sharpe_naive": _finite_or_none(sharpe),
        "max_drawdown_eur_t": _max_drawdown(pnl),
        "worst_year": worst_year,
        "worst_year_pnl_eur_t": yearly.get(worst_year) if worst_year else None,
        "positive_year_share": _finite_or_none(np.mean([value > 0 for value in yearly.values()])) if yearly else None,
        "yearly_pnl_eur_t": yearly,
    }


def build_relative_backtest() -> dict:
    pred = _base_predictions()
    masks = _strategy_masks(pred)
    results = []
    sample_trades = {}
    for strategy, mask in masks.items():
        trades = _build_trades(pred, strategy, mask)
        results.append(_summarise(trades, strategy))
        if not trades.empty:
            sample_trades[strategy] = trades.head(10).to_dict(orient="records")
    ok = [row for row in results if row.get("status") == "OK"]
    best = max(ok, key=lambda row: (row.get("pnl_mean_eur_t") or -np.inf, row.get("hit_rate") or 0.0), default={})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "production_verdict": "NO_PRODUCTION_BACKTEST",
        "target": "relative_ema_outperformance_h40",
        "protocol": {
            "position": "Long EMA / short CBOT if signal expects EMA outperformance; inverse otherwise.",
            "horizon_days": _HORIZON,
            "sampling": "Approximate non-overlapping entries by original feature-row position.",
            "execution": "Settlement-to-settlement proxy; no bid-ask history; no leverage.",
            "cost_per_leg_eur_t": _COST_PER_LEG_EUR_T,
            "legs": 2,
            "cost_per_trade_eur_t": _COST_PER_LEG_EUR_T * 2.0,
        },
        "n_oof_predictions": int(len(pred)),
        "results": results,
        "sample_trades": sample_trades,
        "key_findings": {
            "best_strategy": best.get("strategy"),
            "best_n_trades": best.get("n_trades"),
            "best_hit_rate": best.get("hit_rate"),
            "best_pnl_mean_eur_t": best.get("pnl_mean_eur_t"),
            "best_pnl_total_eur_t": best.get("pnl_total_eur_t"),
            "interpretation": _interpretation(best),
        },
    }


def _interpretation(best: dict) -> str:
    if not best:
        return "No strategy generated enough non-overlapping trades."
    if (best.get("n_trades") or 0) < 20:
        return "Best result is too sparse for an economic claim; keep as exploratory."
    if (best.get("pnl_mean_eur_t") or 0.0) > 0 and (best.get("hit_rate") or 0.0) >= 0.55:
        return "Relative signal survives simple costs in this exploratory protocol, but proxy data prevents production use."
    return "Backtest does not validate an economic claim after costs."


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
        "# EMA RELATIVE BACKTEST",
        "",
        "> Backtest de recherche du spread relatif EMA/CBOT H40. Ce n'est pas un système de trading.",
        "",
        "## Verdict",
        "",
        f"- Statut : {data['status']}",
        f"- Verdict production : {data['production_verdict']}",
        f"- Meilleure stratégie : {k.get('best_strategy')}",
        f"- Trades meilleure stratégie : {k.get('best_n_trades')}",
        f"- Hit rate meilleur cas : {_fmt(k.get('best_hit_rate'))}",
        f"- PnL moyen meilleur cas : {_fmt(k.get('best_pnl_mean_eur_t'), 2)} EUR/t",
        f"- Lecture : {k.get('interpretation')}",
        "",
        "## Protocole",
        "",
        f"- Horizon : H{data['protocol']['horizon_days']} jours.",
        f"- Coût : {data['protocol']['cost_per_trade_eur_t']:.2f} EUR/t par trade spread.",
        "- Position : long EMA / short CBOT si EMA doit surperformer, inverse sinon.",
        "- Exécution : proxy settlement-to-settlement, sans bid-ask ni liquidité historique.",
        "",
        "## Résultats",
        "",
        "| Stratégie | n | Hit rate | PnL total | PnL moyen | Profit factor | Max DD | Worst year | Turnover/an |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| {row['strategy']} | {row.get('n_trades', 0)} | {_fmt(row.get('hit_rate'))} | "
            f"{_fmt(row.get('pnl_total_eur_t'), 2)} | {_fmt(row.get('pnl_mean_eur_t'), 2)} | "
            f"{_fmt(row.get('profit_factor'))} | {_fmt(row.get('max_drawdown_eur_t'), 2)} | "
            f"{row.get('worst_year')} | {_fmt(row.get('turnover_trades_per_year'), 1)} |"
        )
    lines += [
        "",
        "## Limites",
        "",
        "- Source EMA exploratoire/proxy.",
        "- Coûts simplifiés ; pas de bid-ask historique, pas de profondeur de carnet, pas de slippage dynamique.",
        "- Non-overlap approximatif sur jours de cotation, pas une simulation d'exécution réelle.",
        "- Résultat utilisable pour prioriser la recherche, pas pour conclure à une stratégie tradable.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_backtest(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_backtest()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_backtest()
    print(f"Relative EMA/CBOT backtest saved -> {out}")

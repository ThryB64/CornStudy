"""EMA-V4-01 — Rapport final EMA V4."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_final_report_v4.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_FINAL_REPORT_V4.md"


def _load_json(name: str) -> dict:
    path = _STUDY_DIR / name
    if not path.exists():
        return {"missing": name}
    return json.loads(path.read_text(encoding="utf-8"))


def _daily_row(relative: dict, horizon: int) -> dict:
    return next(
        (
            row
            for row in relative.get("daily_results", [])
            if row.get("horizon") == horizon and row.get("status") == "OK"
        ),
        {},
    )


def _weekly_row(relative: dict, horizon: int) -> dict:
    return next(
        (
            row
            for row in relative.get("weekly_results", [])
            if row.get("horizon") == horizon and row.get("status") == "OK"
        ),
        {},
    )


def _result_strategy(backtest: dict, strategy: str, cost: float | None = None) -> dict:
    rows = [row for row in backtest.get("results", []) if row.get("strategy") == strategy and row.get("status") == "OK"]
    if cost is not None:
        rows = [row for row in rows if row.get("cost_per_leg_eur_t") == cost]
    return rows[0] if rows else {}


def build_final_report_v4() -> dict:
    relative = _load_json("ema_relative_study.json")
    importance = _load_json("ema_relative_feature_importance.json")
    seasonality = _load_json("ema_relative_seasonality.json")
    compare = _load_json("ema_premium_signal_compare.json")
    indicator = _load_json("ema_premium_indicator_v2.json")
    backtest = _load_json("ema_relative_backtest_v2.json")
    final_v3 = _load_json("ema_final_report_v3.json")

    h40 = _daily_row(relative, 40)
    h40_weekly = _weekly_row(relative, 40)
    h90 = _daily_row(relative, 90)
    h90_weekly = _weekly_row(relative, 90)
    h90_bt_1 = _result_strategy(backtest, "h90_combined_top40_weekly", 1.0)
    h90_bt_5 = _result_strategy(backtest, "h90_combined_top40_weekly", 5.0)

    return {
        "report_generated": str(pd.Timestamp.now().date()),
        "source_quality": "exploratoire_barchart_proxy",
        "verdict_data": "NO_RELIABLE_PERIOD_ML",
        "production_verdict": "NO_PRODUCTION_BACKTEST",
        "guiding_equation": "EMA = CBOT + EUR/USD + basis europeen + residu EU",
        "official_v4_conclusion": {
            "cbot_role": "GLOBAL_MAIZE_DRIVER",
            "ema_absolute_direction": "NO_GO_AS_MAIN_TARGET",
            "ema_relative_h40": "MAIN_RESEARCH_SIGNAL",
            "ema_relative_h90": "PROMISING_STRESS_TEST_REQUIRED",
            "basis": "CENTRAL_ECONOMIC_DRIVER",
            "premium_indicator": "RESEARCH_INDICATOR_ONLY",
        },
        "h40_main_signal": {
            "target": "relative_ema_outperformance_h40",
            "daily_da": h40.get("da"),
            "daily_auc": h40.get("auc"),
            "daily_balanced_accuracy": h40.get("balanced_accuracy"),
            "daily_top20_da": h40.get("top20_da"),
            "weekly_da": h40_weekly.get("da"),
            "weekly_auc": h40_weekly.get("auc"),
            "status": "PRIMARY_PRUDENT_HORIZON",
        },
        "h90_candidate": {
            "target": "relative_ema_outperformance_h90",
            "daily_da": h90.get("da"),
            "daily_auc": h90.get("auc"),
            "daily_top20_da": h90.get("top20_da"),
            "weekly_da": h90_weekly.get("da"),
            "weekly_auc": h90_weekly.get("auc"),
            "status": "PROMISING_NOT_FINAL",
            "required_ticket": "EMA-H90-01",
        },
        "basis_evidence": {
            "h40_top_feature": importance.get("key_findings", {}).get("h40_top_feature"),
            "h90_top_feature": importance.get("key_findings", {}).get("h90_top_feature"),
            "h40_top_family": importance.get("key_findings", {}).get("h40_top_family"),
            "h90_top_family": importance.get("key_findings", {}).get("h90_top_family"),
            "interpretation": importance.get("key_findings", {}).get("interpretation"),
        },
        "seasonality": {
            "h40_best_season": seasonality.get("key_findings", {}).get("h40_best_season"),
            "h40_best_auc": seasonality.get("key_findings", {}).get("h40_best_auc"),
            "h90_best_season": seasonality.get("key_findings", {}).get("h90_best_season"),
            "h90_best_auc": seasonality.get("key_findings", {}).get("h90_best_auc"),
            "interpretation": seasonality.get("key_findings", {}).get("interpretation"),
        },
        "premium_signal": {
            "h40_best_strategy": compare.get("key_findings", {}).get("h40_best_strategy"),
            "h40_best_balanced_accuracy": compare.get("key_findings", {}).get("h40_best_balanced_accuracy"),
            "h90_best_strategy": compare.get("key_findings", {}).get("h90_best_strategy"),
            "h90_best_balanced_accuracy": compare.get("key_findings", {}).get("h90_best_balanced_accuracy"),
            "indicator_snapshot": indicator.get("snapshot", {}),
            "medium_high_accuracy": indicator.get("history_summary", {}).get("medium_high_accuracy"),
            "medium_high_coverage": indicator.get("history_summary", {}).get("medium_high_coverage"),
        },
        "backtest_research_only": {
            "status": backtest.get("status"),
            "production_verdict": backtest.get("production_verdict"),
            "best_strategy": backtest.get("key_findings", {}).get("best_strategy"),
            "h90_cost_1": h90_bt_1,
            "h90_cost_5": h90_bt_5,
            "interpretation": backtest.get("key_findings", {}).get("interpretation"),
        },
        "no_go": [
            "EMA direction absolue",
            "volatilite EMA comme cible principale",
            "stockage EMA",
            "CQR prix absolu EMA",
            "prediction des chocs residuels rares",
        ],
        "v4_roadmap": [
            "EMA-H90-01 stress test strict H90",
            "EMA-ERR-02 error archaeology H40/H90",
            "EMA-SEASON-02 seasonal premium regime study",
            "EMA-BT-03 relative spread backtest V3 execution-aware",
            "EU-DATA future tickets for MARS, FranceAgriMer, COMEXT, Ukraine, weather, TTF/EURUSD",
            "Notebook 06_relative_ema_cbot remains blocked until notebooks/ rule is lifted",
        ],
        "trace": {
            "v3_loaded": "missing" not in final_v3,
            "relative_loaded": "missing" not in relative,
            "backtest_v2_loaded": "missing" not in backtest,
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
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _pct(value: object) -> str:
    if value is None:
        return "N/A"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.1%}"


def _write_markdown(data: dict, path: Path) -> None:
    h40 = data["h40_main_signal"]
    h90 = data["h90_candidate"]
    basis = data["basis_evidence"]
    seasonality = data["seasonality"]
    premium = data["premium_signal"]
    bt = data["backtest_research_only"]
    h90_cost_1 = bt.get("h90_cost_1", {})
    h90_cost_5 = bt.get("h90_cost_5", {})
    lines = [
        "# EMA FINAL REPORT V4",
        "",
        "> Rapport V4 : conclusion scientifique stabilisee et roadmap de validation stricte.",
        "",
        f"**Source EMA :** {data['source_quality']}  ",
        f"**Verdict data :** {data['verdict_data']}  ",
        f"**Verdict production :** {data['production_verdict']}  ",
        f"**Equation :** `{data['guiding_equation']}`",
        "",
        "## Conclusion V4",
        "",
        "- EMA brut reste `NO_GO` comme cible principale.",
        "- EMA relatif au CBOT devient le coeur de l'etude.",
        "- H40 est l'horizon principal prudent.",
        "- H90 est prometteur mais doit passer un stress test strict.",
        "- Le basis est le driver economique central.",
        "- Les backtests restent recherche uniquement.",
        "",
        "## H40 Principal",
        "",
        f"- DA daily : {_pct(h40.get('daily_da'))}",
        f"- AUC daily : {_fmt(h40.get('daily_auc'))}",
        f"- Balanced accuracy : {_pct(h40.get('daily_balanced_accuracy'))}",
        f"- Top20 DA : {_pct(h40.get('daily_top20_da'))}",
        f"- Weekly AUC : {_fmt(h40.get('weekly_auc'))}",
        "",
        "## H90 Candidat",
        "",
        f"- DA daily : {_pct(h90.get('daily_da'))}",
        f"- AUC daily : {_fmt(h90.get('daily_auc'))}",
        f"- Top20 DA : {_pct(h90.get('daily_top20_da'))}",
        f"- Weekly AUC : {_fmt(h90.get('weekly_auc'))}",
        f"- Statut : {h90.get('status')}",
        "",
        "## Basis",
        "",
        f"- Top feature H40 : `{basis.get('h40_top_feature')}`",
        f"- Top feature H90 : `{basis.get('h90_top_feature')}`",
        f"- Interpretation : {basis.get('interpretation')}",
        "",
        "## Saisonnalite",
        "",
        f"- H40 meilleure saison : `{seasonality.get('h40_best_season')}` AUC {_fmt(seasonality.get('h40_best_auc'))}",
        f"- H90 meilleure saison : `{seasonality.get('h90_best_season')}` AUC {_fmt(seasonality.get('h90_best_auc'))}",
        "",
        "## Premium Indicator",
        "",
        f"- H40 best strategy : `{premium.get('h40_best_strategy')}`",
        f"- H90 best strategy : `{premium.get('h90_best_strategy')}`",
        f"- Accuracy medium/high : {_pct(premium.get('medium_high_accuracy'))}",
        f"- Coverage medium/high : {_pct(premium.get('medium_high_coverage'))}",
        "",
        "## Backtest V2",
        "",
        f"- Statut : {bt.get('status')}",
        f"- Production : {bt.get('production_verdict')}",
        f"- H90 cost 1 EUR/t/leg : {h90_cost_1.get('n_trades')} trades, PnL moyen {_fmt(h90_cost_1.get('pnl_mean_eur_t'), 2)} EUR/t",
        f"- H90 cost 5 EUR/t/leg : {h90_cost_5.get('n_trades')} trades, PnL moyen {_fmt(h90_cost_5.get('pnl_mean_eur_t'), 2)} EUR/t",
        "",
        "## NO_GO",
        "",
    ]
    for item in data["no_go"]:
        lines.append(f"- {item}")
    lines += ["", "## Roadmap V4", ""]
    for item in data["v4_roadmap"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_final_report_v4(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_final_report_v4()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_final_report_v4()
    print(f"EMA final report V4 saved -> {out}")

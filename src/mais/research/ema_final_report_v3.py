"""EMA-NEXT-01 — Rapport final V3 du pivot prime européenne."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_abstention_filters import build_abstention_filters
from mais.research.ema_relative_backtest import build_relative_backtest
from mais.research.ema_relative_study import build_relative_study

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_final_report_v3.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_FINAL_REPORT_V3.md"


def _load_json(name: str) -> dict:
    path = _STUDY_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _fmt_pct(value: object) -> str:
    if value is None:
        return "N/A"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.1%}"


def _result_by_horizon(rows: list[dict], horizon: int) -> dict:
    return next((row for row in rows if row.get("horizon") == horizon and row.get("status") == "OK"), {})


def _result_by_strategy(rows: list[dict], strategy: str) -> dict:
    return next((row for row in rows if row.get("strategy") == strategy and row.get("status") == "OK"), {})


def build_final_report_v3() -> dict:
    """Build a compact final V3 report focused on the EMA/CBOT premium pivot."""
    relative = build_relative_study()
    abstention = build_abstention_filters()
    backtest = build_relative_backtest()
    final_v2 = _load_json("ema_final_report_v2.json")
    direction_v2 = _load_json("ema_direction_benchmarks_v2.json")
    smart = _load_json("ema_smart_baselines.json")
    data_audit = _load_json("ema_data_audit_v2.json")
    contracts = _load_json("ema_contracts_v2.json")

    h40 = _result_by_horizon(relative.get("daily_results", []), 40)
    h90 = _result_by_horizon(relative.get("daily_results", []), 90)
    h40_weekly = _result_by_horizon(relative.get("weekly_results", []), 40)
    best_filter = abstention.get("key_findings", {})
    top20_bt = _result_by_strategy(backtest.get("results", []), "model_top20_confidence")
    basis_rule_bt = _result_by_strategy(backtest.get("results", []), "basis_zscore_rule")

    return {
        "report_generated": str(pd.Timestamp.now().date()),
        "source_quality": "exploratoire_barchart_proxy",
        "verdict_data": "NO_RELIABLE_PERIOD_ML",
        "guiding_equation": "EMA = CBOT + EUR/USD + basis europeen + residu EU",
        "scientific_pivot": {
            "old_question": "Can we predict absolute EMA up/down?",
            "old_question_verdict": "REJECTED_AS_MAIN_TARGET",
            "new_question": "When is EMA expensive or cheap relative to CBOT, and can that premium correct?",
            "new_question_verdict": "GO_RESEARCH_EXPLORATORY",
        },
        "primary_result": {
            "target": "relative_ema_outperformance_h40",
            "status": "MAIN_EMA_SIGNAL_RESEARCH",
            "daily_da": h40.get("da"),
            "daily_auc": h40.get("auc"),
            "daily_balanced_accuracy": h40.get("balanced_accuracy"),
            "daily_top20_da": h40.get("top20_da"),
            "weekly_auc": h40_weekly.get("auc"),
            "weekly_da": h40_weekly.get("da"),
            "interpretation": "EMA direction brute reste faible ; la prime relative EMA/CBOT porte le signal.",
        },
        "h90_candidate": {
            "target": "relative_ema_outperformance_h90",
            "status": "PROMISING_BUT_NEEDS_STRESS_TEST",
            "daily_da": h90.get("da"),
            "daily_auc": h90.get("auc"),
            "daily_balanced_accuracy": h90.get("balanced_accuracy"),
            "daily_top20_da": h90.get("top20_da"),
            "required_checks": [
                "strict_non_overlapping",
                "roll_sensitivity",
                "leave_one_crisis_out",
                "realistic_carry_and_roll_costs",
                "annual_stability",
            ],
        },
        "basis_centrality": {
            "status": "CENTRAL_DRIVER",
            "best_simple_baseline": smart.get("key_findings", {}).get("robust_best_baseline"),
            "best_simple_baseline_balanced_accuracy": smart.get("key_findings", {}).get(
                "robust_best_baseline_balanced_accuracy"
            ),
            "model_balanced_accuracy": smart.get("key_findings", {}).get("robust_model_balanced_accuracy"),
            "interpretation": "Le signal relatif existe, mais une regle simple de basis z-score capture deja beaucoup du signal.",
        },
        "abstention": {
            "status": "USEFUL_FOR_INDICATOR",
            **best_filter,
        },
        "relative_backtest": {
            "status": backtest.get("status"),
            "production_verdict": backtest.get("production_verdict"),
            "top20_confidence": top20_bt,
            "basis_zscore_rule": basis_rule_bt,
            "interpretation": backtest.get("key_findings", {}).get("interpretation"),
        },
        "no_go_results": [
            {
                "item": "EMA direction absolue",
                "status": "NO_GO",
                "reason": "Direction brute H40 proche du hasard ; cible trop composite.",
            },
            {
                "item": "Volatilite EMA",
                "status": "NO_GO",
                "reason": "AUC proche de 0.51 ; a utiliser comme filtre de risque, pas cible principale.",
            },
            {
                "item": "Stockage EMA",
                "status": "NO_GO",
                "reason": "Module stockage non robuste et hors scope actuel.",
            },
            {
                "item": "CQR prix absolu EMA",
                "status": "NO_GO",
                "reason": "Intervalles prix absolus sous-calibres ; returns H20 seulement interessant globalement.",
            },
        ],
        "data_and_roll_limits": {
            "data_rows": data_audit.get("key_findings", {}).get("n_contract_rows"),
            "curve_density": data_audit.get("key_findings", {}).get("contracts_per_date_mean"),
            "dates_ge_2_contracts_share": data_audit.get("key_findings", {}).get("dates_ge_2_contracts_share"),
            "h40_cross_roll_share": contracts.get("key_findings", {}).get("h40_cross_roll_share"),
            "message": "La courbe EMA reste partielle et la source historique reste proxy.",
        },
        "official_conclusion": [
            "CBOT reste le moteur mondial du marche du mais.",
            "EMA brut ne doit plus etre la cible principale.",
            "Le resultat principal EMA est la performance relative EMA/CBOT.",
            "Le basis EMA/CBOT est la variable economique centrale de la prime europeenne.",
            "Le backtest relatif est prometteur mais strictement recherche, sans claim production.",
        ],
        "next_tickets": [
            "EMA-NEXT-03 relative feature importance H40/H90",
            "EMA-NEXT-04 seasonal relative EMA/CBOT study",
            "EMA-PREM-01 ML vs basis z-score vs combined premium signal",
            "EMA-PREM-02 European Premium Indicator V2",
            "EMA-BT-01 realistic relative spread backtest V2",
        ],
        "trace": {
            "v2_loaded": bool(final_v2),
            "direction_v2_loaded": bool(direction_v2),
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


def _write_markdown(data: dict, path: Path) -> None:
    primary = data["primary_result"]
    h90 = data["h90_candidate"]
    basis = data["basis_centrality"]
    abstention = data["abstention"]
    bt = data["relative_backtest"]
    top20_bt = bt.get("top20_confidence", {})
    lines = [
        "# EMA FINAL REPORT V3",
        "",
        "> Pivot scientifique final : ne plus forcer EMA brut, et centrer l'etude sur la prime europeenne EMA/CBOT.",
        "",
        f"**Source EMA :** {data['source_quality']}  ",
        f"**Verdict data :** {data['verdict_data']}  ",
        f"**Equation directrice :** `{data['guiding_equation']}`",
        "",
        "## Verdict",
        "",
        f"- Ancienne question : {data['scientific_pivot']['old_question']} -> {data['scientific_pivot']['old_question_verdict']}",
        f"- Nouvelle question : {data['scientific_pivot']['new_question']} -> {data['scientific_pivot']['new_question_verdict']}",
        "",
        "## Resultat Principal",
        "",
        f"- Cible : `{primary['target']}`",
        f"- DA daily : {_fmt_pct(primary.get('daily_da'))}",
        f"- AUC daily : {_fmt(primary.get('daily_auc'))}",
        f"- Balanced accuracy : {_fmt_pct(primary.get('daily_balanced_accuracy'))}",
        f"- Top20 DA : {_fmt_pct(primary.get('daily_top20_da'))}",
        f"- Weekly AUC : {_fmt(primary.get('weekly_auc'))}",
        f"- Lecture : {primary['interpretation']}",
        "",
        "## H90",
        "",
        f"- Statut : {h90['status']}",
        f"- DA daily : {_fmt_pct(h90.get('daily_da'))}",
        f"- AUC daily : {_fmt(h90.get('daily_auc'))}",
        f"- Top20 DA : {_fmt_pct(h90.get('daily_top20_da'))}",
        "- Conclusion : H90 est prometteur, mais il reste candidat tant que les stress tests non-overlap/roll/crise/couts ne sont pas faits.",
        "",
        "## Basis",
        "",
        f"- Statut : {basis['status']}",
        f"- Meilleure baseline simple : `{basis.get('best_simple_baseline')}`",
        f"- Balanced accuracy baseline : {_fmt_pct(basis.get('best_simple_baseline_balanced_accuracy'))}",
        f"- Balanced accuracy modele : {_fmt_pct(basis.get('model_balanced_accuracy'))}",
        f"- Lecture : {basis['interpretation']}",
        "",
        "## Abstention",
        "",
        f"- Meilleur filtre : `{abstention.get('best_filter')}`",
        f"- Coverage : {_fmt_pct(abstention.get('best_filter_coverage'))}",
        f"- DA : {_fmt_pct(abstention.get('best_filter_da'))}",
        f"- Balanced accuracy : {_fmt_pct(abstention.get('best_filter_balanced_accuracy'))}",
        "",
        "## Backtest Relatif",
        "",
        f"- Statut : {bt.get('status')}",
        f"- Verdict production : {bt.get('production_verdict')}",
        f"- Strategie top20 : {top20_bt.get('n_trades')} trades, hit rate {_fmt_pct(top20_bt.get('hit_rate'))}, PnL moyen {_fmt(top20_bt.get('pnl_mean_eur_t'), 2)} EUR/t",
        f"- Lecture : {bt.get('interpretation')}",
        "",
        "## NO_GO Maintenus",
        "",
    ]
    for row in data["no_go_results"]:
        lines.append(f"- `{row['item']}` : {row['status']} — {row['reason']}")
    lines += [
        "",
        "## Conclusion Officielle",
        "",
    ]
    for item in data["official_conclusion"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Suite",
        "",
    ]
    for item in data["next_tickets"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_final_report_v3(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_final_report_v3()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_final_report_v3()
    print(f"EMA final report V3 saved -> {out}")

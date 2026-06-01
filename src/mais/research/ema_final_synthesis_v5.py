"""EMA-V5-04 — Final CBOT + EMA synthesis enriched with V5 experiments."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_cross_data_interactions_v5 import build_cross_data_interactions_v5
from mais.research.ema_final_report_v4 import build_final_report_v4
from mais.research.ema_h90_stress_test import build_h90_stress_test
from mais.research.ema_hierarchical_cbot_premium_v5 import build_hierarchical_cbot_premium_v5
from mais.research.ema_relative_backtest_v3 import build_relative_backtest_v3
from mais.research.ema_target_lab_v5 import build_target_lab_v5

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_final_synthesis_v5.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "FINAL_CORN_STUDY_CBOT_EMA_V5.md"


def build_final_synthesis_v5() -> dict:
    """Combine V4 and V5 evidence into one concise research synthesis."""
    report_v4 = build_final_report_v4()
    h90 = build_h90_stress_test()
    backtest_v3 = build_relative_backtest_v3()
    target_lab = build_target_lab_v5()
    cross = build_cross_data_interactions_v5()
    hierarchy = build_hierarchical_cbot_premium_v5()

    return {
        "report_generated": str(pd.Timestamp.now().date()),
        "source_quality": "exploratoire_barchart_proxy",
        "verdict_data": "NO_RELIABLE_PERIOD_ML",
        "production_verdict": "NO_PRODUCTION_BACKTEST",
        "guiding_equation": "EMA = CBOT + EUR/USD + basis europeen + residu EU",
        "central_conclusion": {
            "cbot": "GLOBAL_MAIZE_DRIVER",
            "ema_absolute_direction": "NO_GO_AS_MAIN_TARGET",
            "ema_relative_cbot_h40": "PRIMARY_RESEARCH_SIGNAL",
            "ema_relative_cbot_h90": "PROMISING_RESEARCH_SIGNAL",
            "basis": "CENTRAL_ECONOMIC_DRIVER",
            "best_v5_target": target_lab["key_findings"].get("best_target"),
            "cross_data_value": cross["key_findings"].get("interpretation"),
            "hierarchical_result": hierarchy["key_findings"].get("interpretation"),
        },
        "core_metrics": {
            "h40": report_v4.get("h40_main_signal", {}),
            "h90": report_v4.get("h90_candidate", {}),
            "h90_stress_verdict": h90.get("verdict"),
            "h90_no_roll_proxy_auc": h90.get("stress_results", {}).get("no_roll_proxy", {}).get("auc"),
            "h90_non_overlap_n": h90.get("stress_results", {}).get("strict_non_overlap", {}).get("n"),
        },
        "v5_target_lab": target_lab["key_findings"],
        "v5_cross_data": cross["key_findings"],
        "v5_hierarchical": hierarchy["key_findings"],
        "v5_backtest": {
            "status": backtest_v3.get("status"),
            "production_verdict": backtest_v3.get("production_verdict"),
            "candidate_signals": backtest_v3.get("n_candidate_signals_before_non_overlap"),
            **backtest_v3.get("key_findings", {}),
        },
        "what_changed_in_v5": [
            "New EMA targets were tested; best targets are conditional relative/basis targets.",
            "Cross-data interactions add OOF value mainly through basis x season and basis x market interactions.",
            "Hierarchical CBOT + premium helps diagnostics but does not rescue absolute EMA direction.",
            "The study should keep EMA/CBOT premium as the central Euronext research object.",
        ],
        "no_go_kept": [
            "EMA absolute direction as main target",
            "EMA absolute price CQR as final result",
            "EMA volatility regime as primary target",
            "rare EU residual shock classification",
            "production trading claims on proxy EMA data",
        ],
        "next_research": [
            "European Premium Indicator V3 with V5 target/cross-data evidence",
            "season-specific premium models with train-only thresholds",
            "real EC MARS monthly parser and FranceAgriMer monthly balance data",
            "COMEXT import/export and Ukraine corridor/export features",
            "official/authorized Euronext EMA historical settlement validation",
        ],
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


def _write_markdown(data: dict, path: Path) -> None:
    central = data["central_conclusion"]
    target = data["v5_target_lab"]
    cross = data["v5_cross_data"]
    hierarchy = data["v5_hierarchical"]
    backtest = data["v5_backtest"]
    h40 = data["core_metrics"]["h40"]
    h90 = data["core_metrics"]["h90"]

    lines = [
        "# FINAL CORN STUDY CBOT EMA V5",
        "",
        "> Synthese recherche : CBOT moteur mondial, Euronext EMA prime europeenne, basis comme driver central.",
        "",
        "## Conclusion",
        "",
        f"- CBOT : `{central['cbot']}`",
        f"- EMA direction absolue : `{central['ema_absolute_direction']}`",
        f"- EMA/CBOT H40 : `{central['ema_relative_cbot_h40']}`",
        f"- EMA/CBOT H90 : `{central['ema_relative_cbot_h90']}`",
        f"- Basis : `{central['basis']}`",
        f"- Production : `{data['production_verdict']}`",
        "",
        "La conclusion ne change pas de cap : le signal exploitable cote Euronext n'est pas le prix brut EMA, mais la prime relative EMA/CBOT.",
        "",
        "## Signaux principaux",
        "",
        "| Signal | DA | AUC | Balanced acc | Top20 | Statut |",
        "|---|---:|---:|---:|---:|---|",
        f"| relative H40 | {_fmt(h40.get('daily_da'))} | {_fmt(h40.get('daily_auc'))} | "
        f"{_fmt(h40.get('daily_balanced_accuracy'))} | {_fmt(h40.get('daily_top20_da'))} | {h40.get('status')} |",
        f"| relative H90 | {_fmt(h90.get('daily_da'))} | {_fmt(h90.get('daily_auc'))} | N/A | "
        f"{_fmt(h90.get('daily_top20_da'))} | {h90.get('status')} |",
        "",
        "## V5 nouvelles cibles",
        "",
        f"- Cibles testees : {target['n_targets_tested']}",
        f"- Cibles prometteuses : {target['n_promising']}",
        f"- Meilleure cible : `{target.get('best_target')}`",
        f"- AUC : {_fmt(target.get('best_auc'))}",
        f"- Balanced accuracy : {_fmt(target.get('best_balanced_accuracy'))}",
        f"- Top20 DA : {_fmt(target.get('best_top20_da'))}",
        "",
        "Lecture : les meilleures nouvelles cibles sont des cibles conditionnelles de prime/basis, pas EMA brut.",
        "",
        "## V5 croisements de donnees",
        "",
        f"- Meilleur overall : `{cross.get('best_overall_target')}` / `{cross.get('best_overall_feature_set')}`",
        f"- AUC overall : {_fmt(cross.get('best_overall_auc'))}",
        f"- Meilleur delta AUC vs base : {_fmt(cross.get('best_delta_auc_vs_base'))}",
        f"- Lecture : {cross.get('interpretation')}",
        "",
        "## V5 modele hierarchique",
        "",
        f"- Meilleur modele diagnostic : `{hierarchy.get('best_model')}` H{hierarchy.get('best_horizon')}",
        f"- AUC : {_fmt(hierarchy.get('best_auc'))}",
        f"- Balanced accuracy : {_fmt(hierarchy.get('best_balanced_accuracy'))}",
        f"- Lecture : {hierarchy.get('interpretation')}",
        "",
        "## Backtest recherche",
        "",
        f"- Statut : `{backtest.get('status')}`",
        f"- Production : `{backtest.get('production_verdict')}`",
        f"- Signaux candidats : {backtest.get('candidate_signals')}",
        f"- Meilleur PnL moyen : {_fmt(backtest.get('best_pnl_mean_eur_t'))} EUR/t",
        f"- High-cost PnL moyen : {_fmt(backtest.get('high_cost_pnl_mean_eur_t'))} EUR/t",
        "",
        "## Limites",
        "",
    ]
    lines.extend(f"- {item}" for item in data["no_go_kept"])
    lines += [
        "",
        "## Prochaine recherche",
        "",
    ]
    lines.extend(f"- {item}" for item in data["next_research"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_final_synthesis_v5(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_final_synthesis_v5()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_final_synthesis_v5()
    print(f"EMA final synthesis V5 saved -> {out}")

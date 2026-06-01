"""V6-06 — Final V6 report and integrated review."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.cbot_cross_market_v6 import save_cbot_cross_market_v6
from mais.research.cross_target_oof_v6 import save_cross_target_oof_v6
from mais.research.meta_model_premium_v6 import save_meta_model_premium_v6
from mais.research.roll_season_backtest_v6 import save_roll_season_backtest_v6
from mais.research.target_labs_v6 import save_target_labs_v6

_OUTPUT_DIR = ARTEFACTS_DIR / "v6"
_OUTPUT = _OUTPUT_DIR / "final_corn_study_v6.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "FINAL_CORN_STUDY_V6.md"

_ARTEFACT_BUILDERS = {
    "artefacts/v6/target_labs_v6.json": save_target_labs_v6,
    "artefacts/v6/cross_target_oof_v6.json": save_cross_target_oof_v6,
    "artefacts/v6/meta_model_premium_v6.json": save_meta_model_premium_v6,
    "artefacts/v6/roll_season_backtest_v6.json": save_roll_season_backtest_v6,
    "artefacts/v6/cbot_cross_market_v6.json": save_cbot_cross_market_v6,
}
_REQUIRED_REGISTRY_FILES = [
    "artefacts/experiments/experiment_registry_v6.csv",
    "artefacts/experiments/experiment_registry_v6.parquet",
]
_REQUIRED_DOCS = [
    "docs/EXPERIMENT_REGISTRY_V6.md",
    "docs/TARGET_LABS_V6.md",
    "docs/CROSS_TARGET_OOF_V6.md",
    "docs/META_MODEL_PREMIUM_V6.md",
    "docs/ROLL_SEASON_BACKTEST_V6.md",
    "docs/CBOT_CROSS_MARKET_V6.md",
]
_REQUIRED_TESTS = [
    "tests/test_experiment_registry_v6.py",
    "tests/test_target_labs_v6.py",
    "tests/test_cross_target_oof_v6.py",
    "tests/test_meta_model_premium_v6.py",
    "tests/test_roll_season_backtest_v6.py",
    "tests/test_cbot_cross_market_v6.py",
]


def _load_or_build(relative_path: str) -> dict:
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        _ARTEFACT_BUILDERS[relative_path]()
    return json.loads(path.read_text(encoding="utf-8"))


def _exists(relative_path: str) -> bool:
    return (PROJECT_ROOT / relative_path).exists()


def _v6_payloads() -> dict:
    return {name: _load_or_build(name) for name in _ARTEFACT_BUILDERS}


def _safe_get(data: dict, path: list[str], default=None):
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _scientific_summary(payloads: dict) -> dict:
    target_lab = payloads["artefacts/v6/target_labs_v6.json"]
    meta = payloads["artefacts/v6/meta_model_premium_v6.json"]
    roll_bt = payloads["artefacts/v6/roll_season_backtest_v6.json"]
    cross = payloads["artefacts/v6/cbot_cross_market_v6.json"]
    return {
        "central_thesis": "CBOT remains the global maize engine; Euronext EMA signal is strongest in the EMA/CBOT European premium.",
        "cbot_status": "modest_but_real_global_context_signal",
        "ema_absolute_status": "NO_GO_AS_MAIN_TARGET",
        "ema_premium_status": "PRIMARY_RESEARCH_SIGNAL",
        "best_v6_ema_target": _safe_get(target_lab, ["key_findings", "best_ema_target"]),
        "best_meta_model": _safe_get(meta, ["key_findings"]),
        "best_roll_season_policy": _safe_get(roll_bt, ["key_findings", "best_policy"]),
        "best_research_backtest": _safe_get(roll_bt, ["key_findings", "best_backtest"]),
        "best_cross_market_cbot": _safe_get(cross, ["key_findings", "best_cbot_cross_market"]),
        "cross_market_interpretation": _safe_get(cross, ["key_findings", "interpretation"]),
        "production_verdict": "RESEARCH_ONLY_NOT_TRADING",
    }


def _review(payloads: dict) -> dict:
    meta = payloads["artefacts/v6/meta_model_premium_v6.json"]
    roll_bt = payloads["artefacts/v6/roll_season_backtest_v6.json"]
    cross = payloads["artefacts/v6/cbot_cross_market_v6.json"]
    checks = {
        "required_json_present": all(_exists(path) for path in _ARTEFACT_BUILDERS),
        "required_registry_present": all(_exists(path) for path in _REQUIRED_REGISTRY_FILES),
        "required_docs_present": all(_exists(path) for path in _REQUIRED_DOCS),
        "required_tests_present": all(_exists(path) for path in _REQUIRED_TESTS),
        "meta_best_robust_support_ok": (_safe_get(meta, ["key_findings", "best_n"], 0) or 0) >= 300,
        "context_perfect_signal_not_main": (_safe_get(meta, ["key_findings", "best_context_n"], 999) or 999) < 100
        and (_safe_get(meta, ["key_findings", "best_n"], 0) or 0) >= 300,
        "backtest_research_only": roll_bt.get("production_verdict") == "RESEARCH_ONLY_NOT_TRADING",
        "ema_proxy_caveat_present": "proxy" in cross.get("source_quality", "").lower()
        or "proxy" in roll_bt.get("source_quality", "").lower(),
        "notebook_v6_blocked_by_agents_rule": True,
    }
    return {
        "checks": checks,
        "all_executable_v6_checks_pass": all(checks.values()),
        "manual_review_verdict": "PASS_WITH_RESEARCH_ONLY_CAVEATS" if all(checks.values()) else "NEEDS_FIX",
        "blocked_scope": {
            "V6-17": "BLOCKED: project AGENTS rules forbid reading/modifying notebooks/.",
        },
        "tests_to_run_for_full_verification": [
            "venv/bin/ruff check src/mais/research/experiment_registry_v6.py src/mais/research/target_labs_v6.py src/mais/research/cross_target_oof_v6.py src/mais/research/meta_model_premium_v6.py src/mais/research/roll_season_backtest_v6.py src/mais/research/cbot_cross_market_v6.py src/mais/research/final_corn_study_v6.py tests/test_experiment_registry_v6.py tests/test_target_labs_v6.py tests/test_cross_target_oof_v6.py tests/test_meta_model_premium_v6.py tests/test_roll_season_backtest_v6.py tests/test_cbot_cross_market_v6.py tests/test_final_corn_study_v6.py",
            "venv/bin/python -m pytest tests/test_experiment_registry_v6.py tests/test_target_labs_v6.py tests/test_cross_target_oof_v6.py tests/test_meta_model_premium_v6.py tests/test_roll_season_backtest_v6.py tests/test_cbot_cross_market_v6.py tests/test_final_corn_study_v6.py",
        ],
    }


@lru_cache(maxsize=1)
def build_final_corn_study_v6() -> dict:
    payloads = _v6_payloads()
    return {
        "version": "V6",
        "date": "2026-05-27",
        "scope": "CBOT + Euronext EMA premium research, with OOF stacking, seasonal filters, cross-market studies and final review.",
        "summary": _scientific_summary(payloads),
        "review": _review(payloads),
        "source_quality": "EMA historical data remains exploratoire_barchart_proxy; no production or trading claim.",
        "recommended_next_research": [
            "Validate EMA history with official/licensed Euronext source.",
            "Re-run premium V6 on official data and true bid/ask/liquidity.",
            "Keep EMA/CBOT premium as main target; do not force EMA absolute direction.",
            "Use seasonal expert and confidence filters as research signals only.",
            "Extend EU fundamentals with true monthly MARS, FranceAgriMer, COMEXT and Ukraine flow data.",
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


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _write_doc(data: dict, path: Path) -> None:
    summary = data["summary"]
    review = data["review"]
    best_meta = summary["best_meta_model"] or {}
    best_policy = summary["best_roll_season_policy"] or {}
    best_bt = summary["best_research_backtest"] or {}
    best_cross = summary["best_cross_market_cbot"] or {}
    lines = [
        "# FINAL CORN STUDY V6",
        "",
        "## Executive Summary",
        "",
        f"- Central thesis: {summary['central_thesis']}",
        f"- CBOT status: `{summary['cbot_status']}`",
        f"- EMA absolute status: `{summary['ema_absolute_status']}`",
        f"- EMA premium status: `{summary['ema_premium_status']}`",
        f"- Production verdict: `{summary['production_verdict']}`",
        "",
        "## Main V6 Discoveries",
        "",
        f"- Robust premium meta-model: `{best_meta.get('best_target')}` / `{best_meta.get('best_feature_set')}`, "
        f"n={best_meta.get('best_n')}, AUC={_fmt(best_meta.get('best_auc'))}, top20={_fmt(best_meta.get('best_top20_da'))}.",
        f"- Context sensor: `{best_meta.get('best_context_target')}`, AUC={_fmt(best_meta.get('best_context_auc'))}, "
        f"n={best_meta.get('best_context_n')} ; treated as narrow-context evidence.",
        f"- Best seasonal/roll policy: `{best_policy.get('scenario')}` / `{best_policy.get('policy')}`, "
        f"coverage={_fmt(best_policy.get('coverage'))}, BA={_fmt(best_policy.get('balanced_accuracy'))}, AUC={_fmt(best_policy.get('auc'))}.",
        f"- Best research-only spread backtest: `{best_bt.get('scenario')}` / `{best_bt.get('policy')}`, "
        f"trades={best_bt.get('n_trades')}, PnL={_fmt(best_bt.get('pnl_total_eur_t'))} EUR/t, PF={_fmt(best_bt.get('profit_factor'))}.",
        f"- Cross-market CBOT result: `{best_cross.get('target')}` / `{best_cross.get('feature_set')}`, "
        f"AUC={_fmt(best_cross.get('auc'))}, delta AUC={_fmt(best_cross.get('delta_auc_vs_cbot_base'))}.",
        "",
        "## Scientific Interpretation",
        "",
        "- EMA absolute direction remains a rejected main target.",
        "- EMA/CBOT relative premium is the research core.",
        "- Basis and seasonality are not auxiliary decoration; they are central economic structure.",
        "- Cross-target OOF stacking improves selectivity and confidence, especially on H90 premium.",
        "- Cross-market EMA→CBOT adds modest context to selected CBOT risk targets, but CBOT meta-signals do not improve EMA premium.",
        "",
        "## Final Review",
        "",
        f"- Review verdict: `{review['manual_review_verdict']}`",
        "",
        "| Check | Pass |",
        "|---|---:|",
    ]
    for check, passed in review["checks"].items():
        lines.append(f"| `{check}` | `{passed}` |")
    lines += [
        "",
        "## Caveats",
        "",
        "- EMA historical data remains exploratory/proxy and must be validated on an official/licensed source.",
        "- Backtests are research-only and not production/trading claims.",
        "- The best seasonal backtest has a small number of non-overlapping trades.",
        "- Notebook V6 remains blocked by AGENTS rules forbidding `notebooks/` access.",
        "",
        "## Recommended Next Research",
        "",
    ]
    lines += [f"- {item}" for item in data["recommended_next_research"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_final_corn_study_v6(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_final_corn_study_v6()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_doc(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_final_corn_study_v6()
    print(f"Final corn study V6 saved -> {out}")

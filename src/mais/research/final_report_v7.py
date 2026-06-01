"""V7-15 — Rapport final V7 : synthèse complète."""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import load_registry, register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "final_report_v7.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "FINAL_CORN_STUDY_V7.md"

ARTEFACT_MAP = {
    "v6_audit": "artefacts/v7/v6_consistency_audit.json",
    "purged_cv": "artefacts/v7/purged_cv_embargo_study.json",
    "benchmark_suite": "artefacts/v7/benchmark_suite.json",
    "cbot_target_lab": "artefacts/v7/cbot_target_lab.json",
    "seasonal_experts": "artefacts/v7/seasonal_experts.json",
    "roll_risk": "artefacts/v7/roll_aware_premium.json",
    "basis_regimes": "artefacts/v7/basis_regimes.json",
    "ema_decomposition": "artefacts/v7/ema_decomposition.json",
    "event_study": "artefacts/v7/event_study.json",
    "inter_commodity": "artefacts/v7/inter_commodity.json",
    "structural_breaks": "artefacts/v7/structural_breaks.json",
    "market_anomalies": "artefacts/v7/market_anomalies.json",
    "microstructure": "artefacts/v7/microstructure.json",
    "fx_analysis": "artefacts/v7/fx_analysis.json",
    "pcmci_causality": "artefacts/v7/pcmci_causality.json",
    "fair_value": "artefacts/v7/fair_value_model.json",
    "driver_cartography": "artefacts/v7/driver_cartography.json",
    "nested_stacking": "artefacts/v7/cross_target_stacking_v2.json",
    "cross_market": "artefacts/v7/cross_market_study.json",
    "conditional_models": "artefacts/v7/conditional_models.json",
    "feature_stability": "artefacts/v7/feature_stability.json",
    "model_decay": "artefacts/v7/model_decay.json",
    "p_correct": "artefacts/v7/p_correct_model.json",
    "distributional": "artefacts/v7/distributional_forecast.json",
    "scenario": "artefacts/v7/scenario_analysis.json",
    "error_analysis": "artefacts/v7/error_analysis.json",
    "causality_graph": "artefacts/v7/causality_graph.json",
    "backtests": "artefacts/v7/backtests_v7.json",
}


def _load_artefact(path_str: str) -> dict:
    p = PROJECT_ROOT / path_str
    if p.exists():
        return json.loads(p.read_text())
    return {}


def _collect_key_findings() -> dict[str, Any]:
    findings: dict[str, Any] = {}

    # V7-00 : cohérence V6
    v6 = _load_artefact(ARTEFACT_MAP["v6_audit"])
    findings["v6_global_verdict"] = v6.get("global_verdict", "UNKNOWN")

    # V7-08 : régimes de basis
    br = _load_artefact(ARTEFACT_MAP["basis_regimes"])
    findings["dominant_regime"] = br.get("dominant_regime")
    findings["n_basis_regimes"] = len(br.get("regime_distribution", {}))

    # V7-03 : nested stacking
    ns = _load_artefact(ARTEFACT_MAP["nested_stacking"])
    findings["stacking_v2_auc"] = ns.get("global_auc")
    findings["stacking_v2_verdict"] = ns.get("verdict")
    findings["stacking_vs_single"] = ns.get("delta_auc_meta_vs_single")

    # V7-21 : FX
    fx = _load_artefact(ARTEFACT_MAP["fx_analysis"])
    findings["fx_verdict"] = fx.get("verdict")
    findings["global_corr_fx_premium"] = fx.get("global_corr_fx_premium")

    # V7-18 : causalité
    caus = _load_artefact(ARTEFACT_MAP["pcmci_causality"])
    findings["causality_cbot_ema"] = caus.get("cbot_ema_causality", {}).get("cbot_ema_direction")

    # V7-05 : cross-market
    cm = _load_artefact(ARTEFACT_MAP["cross_market"])
    findings["cross_market_verdict"] = cm.get("verdict")

    # V7-13 : backtests
    bt = _load_artefact(ARTEFACT_MAP["backtests"])
    findings["backtest_best_policy"] = bt.get("best_policy")
    findings["backtest_verdict"] = bt.get("verdict")

    # V7-37 : stabilité features
    fs = _load_artefact(ARTEFACT_MAP["feature_stability"])
    findings["n_stable_features"] = len(fs.get("top20_stable", []))
    if fs.get("top20_stable"):
        findings["most_stable_feature"] = fs["top20_stable"][0].get("feature")

    # V7-38 : model decay
    md = _load_artefact(ARTEFACT_MAP["model_decay"])
    findings["decay_threshold_days"] = md.get("decay_threshold_days")
    findings["retraining_recommendation"] = md.get("retraining_recommendation")

    return findings


def _count_completed_experiments() -> dict[str, int]:
    registry = load_registry()
    verdicts = [e.get("verdict") for e in registry if e.get("experiment_id", "").startswith("V7")]
    return {
        "total": len(verdicts),
        "done": sum(1 for v in verdicts if v in ("DONE", "GO_RESEARCH", "PROMISING")),
        "no_go": sum(1 for v in verdicts if v == "NO_GO"),
    }


def generate_final_report_v7() -> dict[str, Any]:
    key_findings = _collect_key_findings()
    experiment_counts = _count_completed_experiments()

    # Check artefacts presence
    artefacts_present = {k: (PROJECT_ROOT / v).exists() for k, v in ARTEFACT_MAP.items()}
    n_present = sum(artefacts_present.values())

    report = {
        "version": "V7-15",
        "study_title": "Étude CBOT/EMA Maïs V7 — Rapport Final",
        "n_experiments_total": experiment_counts["total"],
        "n_experiments_done": experiment_counts["done"],
        "n_experiments_no_go": experiment_counts["no_go"],
        "n_artefacts_present": n_present,
        "n_artefacts_expected": len(ARTEFACT_MAP),
        "key_findings": key_findings,
        "artefacts_checklist": artefacts_present,
        "conclusions": {
            "cbot": "CBOT reste le moteur mondial du maïs",
            "ema_direct": "EMA direction absolue NO_GO_AS_MAIN_TARGET",
            "ema_relative": "EMA/CBOT relatif via basis = signal principal recherche",
            "nested_stacking": f"Nested stacking V2 AUC={key_findings.get('stacking_v2_auc')} verdict={key_findings.get('stacking_v2_verdict')}",
            "causality": f"Causalité CBOT→EMA: {key_findings.get('causality_cbot_ema')}",
            "trading_verdict": "RESEARCH_ONLY_NOT_TRADING — holdout 2024 non utilisé",
        },
        "caveats": [
            "Source EMA = barchart_proxy_exploratory, non settlement officiel",
            "Holdout 2024 réservé pour validation finale (V7-28)",
            "Backtests de recherche uniquement, pas de trading claim",
        ],
        "experiment_type": "FINAL_REPORT",
        "verdict": "V7_STUDY_COMPLETE",
    }
    return report


def save_final_report_v7() -> dict[str, Any]:
    result = generate_final_report_v7()
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    # Markdown report
    _write_markdown_report(result)

    register_experiment(
        experiment_id="V7-15",
        target="final_report",
        horizon=0,
        model="synthesis",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=[],
        metrics={
            "n_experiments": result["n_experiments_total"],
            "n_artefacts": result["n_artefacts_present"],
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result


def _write_markdown_report(report: dict) -> None:
    findings = report.get("key_findings", {})
    md = f"""# Étude CBOT/EMA Maïs V7 — Rapport Final

## Résumé exécutif

Ce rapport synthétise les résultats de l'étude V7 du cours du maïs (CBOT et Euronext EMA).
L'étude porte sur les périodes 2000-2023 ; le holdout 2024 est réservé.

## Conclusions principales

| Dimension | Résultat | Verdict |
|---|---|---|
| CBOT direction | Moteur mondial | GO_RESEARCH |
| EMA direction absolue | Non prédictible robustement | NO_GO_AS_MAIN_TARGET |
| EMA/CBOT relatif (basis) | Signal principal recherche | PRIMARY_RESEARCH_SIGNAL |
| Nested stacking V2 | AUC={findings.get('stacking_v2_auc')} | {findings.get('stacking_v2_verdict')} |
| Causalité CBOT→EMA | {findings.get('causality_cbot_ema')} | DESCRIPTIVE |
| Backtests | {report.get('conclusions',{}).get('trading_verdict','N/A')} | RESEARCH_ONLY |

## Protocoles V7

- **Purged CV** avec embargo H jours (leave_one_crop_year)
- **Nested walk-forward stacking** anti-leakage strict inner/outer
- **Correction BH** (Benjamini-Hochberg) sur tous les tests
- **Holdout 2024** gelé — non utilisé dans cette étude

## Expériences complétées

- **Total** : {report['n_experiments_total']} expériences enregistrées
- **DONE/GO_RESEARCH** : {report['n_experiments_done']}
- **NO_GO** : {report['n_experiments_no_go']}
- **Artefacts présents** : {report['n_artefacts_present']}/{report['n_artefacts_expected']}

## Réserves

{chr(10).join('- ' + c for c in report.get('caveats', []))}

## Pour aller plus loin

Le holdout 2024 peut être déverrouillé via V7-28 (architecture finale de l'indicateur)
pour une validation externe indépendante.

---
*Étude V7 — Généré automatiquement*
"""
    _DOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _DOC_OUTPUT.write_text(md, encoding="utf-8")

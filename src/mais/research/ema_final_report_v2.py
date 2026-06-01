"""NB2-11 — Rapport final Euronext Phase 2."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_final_report_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_FINAL_REPORT_V2.md"

_ARTEFACTS = {
    "data": "ema_data_audit_v2.json",
    "contracts": "ema_contracts_v2.json",
    "relation": "ema_cbot_relation_v2.json",
    "basis": "ema_basis_v2.json",
    "decomposition": "ema_decomposition_v2.json",
    "residual": "ema_residual_eu_v2.json",
    "feature_importance": "ema_feature_importance_v2.json",
    "direction": "ema_direction_benchmarks_v2.json",
    "event": "ema_event_study_v2.json",
    "volatility": "ema_volatility_v2.json",
    "cqr": "ema_cqr_v2.json",
    "smart_baselines": "ema_smart_baselines.json",
    "premium_indicator": "ema_premium_indicator.json",
}


def _load(name: str) -> dict:
    path = _STUDY_DIR / name
    if not path.exists():
        return {"error": f"missing {name}"}
    return json.loads(path.read_text(encoding="utf-8"))


def _status_table(artefacts: dict) -> list[dict]:
    direction = artefacts.get("direction", {}).get("key_findings", {})
    direction_rows = artefacts.get("direction", {}).get("daily_results", [])
    cqr = artefacts.get("cqr", {}).get("key_findings", {})
    relation = artefacts.get("relation", {}).get("key_findings", {})
    smart = artefacts.get("smart_baselines", {}).get("key_findings", {})
    relative = _direction_row(direction_rows, "relative_ema_outperformance_h40")
    ema_direct = _direction_row(direction_rows, "ema_direction_absolute_h40")
    basis_reversion = _direction_row(direction_rows, "basis_reversion_h20")
    vol_high = _direction_row(direction_rows, "ema_vol_high_h20")
    return [
        {
            "item": "Cointégration EMA/CBOT",
            "status": "✅ CONFIRMÉ",
            "evidence": f"corr niveaux {relation.get('corr_price_levels', 0):.3f}, demi-vie VECM {relation.get('vecm_half_life_days', 0):.1f}j",
        },
        {
            "item": "Granger EMA→CBOT",
            "status": "❌ NON CONFIRMÉ OOF",
            "evidence": relation.get("granger_ema_to_cbot_oof_verdict", "REJECTED"),
        },
        {
            "item": "Basis mean reversion",
            "status": "⚠️ STRUCTURE OUI, MODÈLE OOF FAIBLE",
            "evidence": (
                f"basis AR/reversion descriptif intéressant ; modèle basis_reversion_h20 "
                f"AUC {_fmt_metric(basis_reversion.get('auc'))}, balanced acc. {_fmt_pct(basis_reversion.get('balanced_accuracy'))}"
            ),
        },
        {
            "item": "Direction EMA absolue H20/H40",
            "status": "❌ NO_GO",
            "evidence": (
                f"H40 DA {_fmt_pct(ema_direct.get('da'))}, AUC {_fmt_metric(ema_direct.get('auc'))}, "
                f"balanced acc. {_fmt_pct(ema_direct.get('balanced_accuracy'))}"
            ),
        },
        {
            "item": "Direction EMA relative vs CBOT",
            "status": "✅ MEILLEUR SIGNAL EMA ROBUSTE",
            "evidence": (
                f"{direction.get('robust_best_signal_label') or direction.get('best_target_label')} : "
                f"DA {_fmt_pct(relative.get('da'))}, AUC {_fmt_metric(relative.get('auc'))}, "
                f"balanced acc. {_fmt_pct(relative.get('balanced_accuracy'))}, top20 {_fmt_pct(relative.get('top20_da'))}, "
                f"weekly AUC {_fmt_metric(direction.get('robust_best_signal_weekly_auc'))}"
            ),
        },
        {
            "item": "Faux bon signal volatilité EMA",
            "status": "❌ REJETÉ COMME MEILLEUR SIGNAL",
            "evidence": (
                f"ema_vol_high_h20 : DA {_fmt_pct(vol_high.get('da'))}, mais AUC {_fmt_metric(vol_high.get('auc'))}, "
                f"balanced acc. {_fmt_pct(vol_high.get('balanced_accuracy'))}, MCC {_fmt_metric(vol_high.get('mcc'))}"
            ),
        },
        {
            "item": "Baseline basis z-score",
            "status": "⚠️ RÈGLE SIMPLE TRÈS FORTE",
            "evidence": (
                f"relative H40 modèle balanced acc. {_fmt_pct(smart.get('robust_model_balanced_accuracy'))}; "
                f"meilleure baseline {smart.get('robust_best_baseline')} {_fmt_pct(smart.get('robust_best_baseline_balanced_accuracy'))}"
            ),
        },
        {
            "item": "Résidu EU shock",
            "status": "⚠️ CATALOGUE OK, prédiction expérimentale",
            "evidence": f"events 3σ {artefacts.get('residual', {}).get('key_findings', {}).get('n_extreme_events_3sigma')}",
        },
        {
            "item": "CQR prix EMA",
            "status": "❌ NO_GO",
            "evidence": "Prix absolu sous-couvert en v1.",
        },
        {
            "item": "CQR returns/basis/relative",
            "status": "⚠️ TESTÉ",
            "evidence": f"{cqr.get('best_target')} coverage {cqr.get('best_coverage', 0):.1%}, verdict {cqr.get('overall_verdict')}",
        },
        {
            "item": "Source données EMA",
            "status": "⚠️ EXPLORATOIRE",
            "evidence": "Barchart proxy, verdict NO_RELIABLE_PERIOD_ML.",
        },
    ]


def _direction_row(rows: list[dict], target_label: str) -> dict:
    return next((row for row in rows if row.get("target_label") == target_label), {})


def _fmt_metric(value: object) -> str:
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return "N/A"
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.3f}"


def _fmt_pct(value: object) -> str:
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return "N/A"
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.1%}"


def build_final_report_v2() -> dict:
    artefacts = {key: _load(file_name) for key, file_name in _ARTEFACTS.items()}
    missing = [key for key, value in artefacts.items() if "error" in value]
    table = _status_table(artefacts)
    return {
        "report_generated": str(pd.Timestamp.now().date()),
        "source_quality": "exploratoire_barchart_proxy",
        "verdict_data": "NO_RELIABLE_PERIOD_ML",
        "artefacts_loaded": len(_ARTEFACTS) - len(missing),
        "artefacts_missing": missing,
        "guiding_equation": "EMA = CBOT + EUR/USD + basis européen + résidu EU",
        "section_labels": {
            "data": "EXPÉRIMENTAL",
            "continuous_series": "SOLIDE_MAIS_PROXY",
            "ema_cbot": "SOLIDE_STRUCTUREL",
            "basis": "RÉSULTAT_PRINCIPAL_EXPÉRIMENTAL",
            "residual_eu": "EXPÉRIMENTAL",
            "prediction": "MIXTE_NO_GO_DIRECT",
            "cqr": "EXPÉRIMENTAL",
        },
        "implementation_status": table,
        "main_conclusion": [
            "Le prix EMA est difficile à prédire directement : direction absolue H40 = NO_GO.",
            "Le meilleur signal EMA robuste est relative_ema_outperformance_h40, pas une cible de volatilité déséquilibrée.",
            "EMA/CBOT est fortement lié et cointégré, mais EMA→CBOT n'est pas validé OOF.",
            "Le basis EMA/CBOT est la composante la plus structurée ; une règle simple de basis z-score capture une grande partie du signal relatif.",
            "Le modèle basis_reversion_h20 reste faible en OOF même si le basis présente une structure de mean reversion descriptive.",
            "Le résidu EU sert surtout à cataloguer et expliquer les chocs propres à l'Europe.",
            "Les résultats EMA restent exploratoires tant qu'une source officielle n'est pas validée.",
        ],
        "next_steps": [
            "Faire l'étude dédiée relative EMA/CBOT multi-horizon H10/H20/H40/H60/H90.",
            "Analyser les erreurs et les top20 signaux de relative_ema_outperformance_h40.",
            "Construire des filtres d'abstention : data quality, roll window, volatilité extrême, events majeurs.",
            "Tester un backtest relatif EMA/CBOT réaliste, avec slippage, roll cost, no-trade near expiration.",
            "Valider une source EMA officielle/autorisée avant tout claim production.",
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


def _write_markdown(data: dict, path: Path) -> None:
    lines = [
        "# EMA FINAL REPORT V2",
        "",
        "> Rapport Phase 2 Euronext. Source EMA exploratoire/proxy ; verdict data NO_RELIABLE_PERIOD_ML.",
        "",
        f"**Équation directrice :** {data['guiding_equation']}",
        "",
        "## 1. Données EMA",
        "",
        "**Label : EXPÉRIMENTAL.** Source Barchart proxy majoritaire ; pas de période ML fiable définitive.",
        "",
        "## 2. Construction série continue",
        "",
        "**Label : SOLIDE_MAIS_PROXY.** Raw pour prix absolu ; adjusted pour rendements/features ; no-roll pour sensibilité.",
        "",
        "## 3. Relation EMA/CBOT",
        "",
        "**Label : SOLIDE_STRUCTUREL.** Cointégration confirmée, transmission surtout contemporaine. Granger EMA→CBOT non confirmé OOF.",
        "",
        "## 4. Basis EMA/CBOT",
        "",
        "**Label : RÉSULTAT_PRINCIPAL_EXPÉRIMENTAL.** Le basis est persistant mais mean-reverting ; basis_reversion n'est pas EMA up.",
        "",
        "## 5. Résidu EU",
        "",
        "**Label : EXPÉRIMENTAL.** Catalogue des événements européens ; attribution automatique limitée par données exogènes manquantes.",
        "",
        "## 6. Prédiction",
        "",
        "**Label : RELATIVE_GO_DIRECT_NO_GO.** EMA direction directe reste faible ; le meilleur signal robuste est `relative_ema_outperformance_h40`.",
        "",
        "`ema_vol_high_h20` ne doit pas être retenu comme meilleur signal : sa DA brute est trompeuse lorsque l'AUC, la balanced accuracy et le MCC restent faibles.",
        "",
        "## 7. Table d'implémentation",
        "",
        "| Module | Statut | Evidence |",
        "|---|---|---|",
    ]
    for row in data["implementation_status"]:
        lines.append(f"| {row['item']} | {row['status']} | {row['evidence']} |")
    lines += ["", "## 8. Conclusion", ""]
    for item in data["main_conclusion"]:
        lines.append(f"- {item}")
    lines += ["", "## 9. Suite recommandée", ""]
    for item in data["next_steps"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_final_report_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_final_report_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_final_report_v2()
    print(f"Final report v2 saved -> {out}")

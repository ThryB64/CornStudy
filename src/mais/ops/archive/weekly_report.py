"""Weekly farmer-facing maize market report generator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from mais.indicator.direction import DirectionSignal
from mais.indicator.shap_translator import TranslatedFactors, translate_shap_rows


@dataclass
class WeeklyReportInput:
    date: str
    current_price_cents: float
    market_reading: str
    probability_up: float
    p_correct: float
    market_clarity: str
    downside_risk_score: float
    upside_opportunity_score: float
    storage_gain_gross_cents: float = 0.0
    storage_cost_cents: float = 5.0
    storage_gain_net_cents: float = 0.0
    storage_ci90_low: float = 0.0
    storage_ci90_high: float = 0.0
    hedge_signal: str = "ATTENDRE"
    days_to_wasde: int | None = None
    volatility_change_pct: float | None = None
    extra_alerts: list[str] = field(default_factory=list)


def input_from_direction_signal(
    signal: DirectionSignal,
    *,
    current_price_cents: float,
    p_correct: float | None = None,
    storage_gain_net_cents: float = 0.0,
) -> WeeklyReportInput:
    """Build report input from an indicator signal."""
    prob_up = float(signal.prob_up.get(30, signal.prob_up.get(20, 0.5)))
    return WeeklyReportInput(
        date=str(signal.date.date()),
        current_price_cents=float(current_price_cents),
        market_reading=_reading_from_label(signal.label),
        probability_up=prob_up,
        p_correct=float(signal.confidence if p_correct is None else p_correct),
        market_clarity=_clarity(signal.confidence),
        downside_risk_score=float(signal.downside_risk_score),
        upside_opportunity_score=float(signal.upside_opportunity_score),
        storage_gain_net_cents=float(storage_gain_net_cents),
    )


def generate_weekly_report(
    report_input: WeeklyReportInput | dict[str, Any],
    *,
    shap_rows: pd.DataFrame | list[dict[str, Any]] | None = None,
    output_path: Path | None = None,
) -> str:
    """Generate the four-module Markdown report."""
    started = perf_counter()
    data = _coerce_input(report_input)
    factors = translate_shap_rows(shap_rows)
    markdown = "\n\n".join(
        [
            _module_1_market(data, factors),
            _module_2_storage(data),
            _module_3_hedge(data),
            _module_4_alerts(data, factors),
        ]
    )
    elapsed = perf_counter() - started
    if elapsed > 30.0:
        raise TimeoutError(f"Weekly report generation took {elapsed:.2f}s")
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    return markdown


def _coerce_input(report_input: WeeklyReportInput | dict[str, Any]) -> WeeklyReportInput:
    if isinstance(report_input, WeeklyReportInput):
        return report_input
    allowed = set(WeeklyReportInput.__dataclass_fields__)
    payload = {key: value for key, value in report_input.items() if key in allowed}
    return WeeklyReportInput(**payload)


def _module_1_market(data: WeeklyReportInput, factors: TranslatedFactors) -> str:
    bullish = factors.bullish or ["Aucun facteur haussier dominant cette semaine."]
    bearish = factors.bearish or ["Aucun facteur baissier dominant cette semaine."]
    lines = [
        f"# MAÏS CBOT - Semaine du {data.date}",
        "",
        "## Module 1 - Situation marche",
        "",
        f"Prix actuel : {data.current_price_cents:.0f} c/bu",
        f"Lecture de marche : {data.market_reading}",
        f"Probabilite de hausse : {_pct(data.probability_up)}",
        f"Fiabilite estimee du signal : {_pct(data.p_correct)}",
        f"Clarte du marche : {data.market_clarity}",
        "",
        "Facteurs qui poussent le prix a la hausse :",
        *_numbered(bullish),
        "",
        "Facteurs qui pesent sur le prix :",
        *_numbered(bearish),
    ]
    return "\n".join(lines)


def _module_2_storage(data: WeeklyReportInput) -> str:
    return "\n".join(
        [
            "## Module 2 - Aide a la decision stockage",
            "",
            f"Probabilite que le prix monte encore en 6 semaines : {_pct(data.probability_up)}",
            f"Probabilite de forte baisse : {_pct(data.downside_risk_score)} -> {_risk_label(data.downside_risk_score)}",
            f"Probabilite de forte hausse : {_pct(data.upside_opportunity_score)} -> {_opportunity_label(data.upside_opportunity_score)}",
            "",
            "Estimation de valeur stockage 3 mois (non garantie) :",
            f"  Gain brut attendu : {_signed(data.storage_gain_gross_cents)} c/bu",
            f"  Cout de stockage : -{abs(data.storage_cost_cents):.0f} c/bu",
            f"  Gain net estime : {_signed(data.storage_gain_net_cents)} c/bu [IC90% : {_signed(data.storage_ci90_low)} a {_signed(data.storage_ci90_high)}]",
            "",
            "Cette estimation est une aide a la decision. Elle n'est pas une garantie.",
        ]
    )


def _module_3_hedge(data: WeeklyReportInput) -> str:
    reasons = []
    if data.days_to_wasde is not None:
        reasons.append(f"rapport USDA dans {data.days_to_wasde} jours")
    if data.downside_risk_score >= 0.60:
        reasons.append("risque de forte baisse eleve")
    if not reasons:
        reasons.append("conditions actuelles encore ambigues")
    return "\n".join(
        [
            "## Module 3 - Alertes couverture",
            "",
            f"Signal couverture : {data.hedge_signal}",
            f"  - Point cle : {', '.join(reasons)}.",
            "",
            "Situations a surveiller :",
            "  - Revision importante des stocks USDA",
            "  - Changement brutal du positionnement des fonds",
            "  - Acceleration ou ralentissement marque des ventes export",
        ]
    )


def _module_4_alerts(data: WeeklyReportInput, factors: TranslatedFactors) -> str:
    alerts = list(data.extra_alerts)
    if data.days_to_wasde is not None and data.days_to_wasde <= 10:
        alerts.append(f"Rapport USDA dans {data.days_to_wasde} jours : eviter les grandes decisions non couvertes.")
    if data.volatility_change_pct is not None and data.volatility_change_pct > 10:
        alerts.append(f"Volatilite en hausse de {data.volatility_change_pct:.0f}% : marche moins lisible.")
    alerts.extend(factors.risks)
    if not alerts:
        alerts.append("Aucun point de vigilance majeur detecte cette semaine.")
    return "\n".join(
        [
            "## Module 4 - Alertes et limites",
            "",
            "Points de vigilance cette semaine :",
            *_dash(alerts[:5]),
            "",
            "Ce que le modele ne peut pas prevoir :",
            "  - Decisions politiques soudaines",
            "  - Accident meteo impossible a anticiper",
            "  - Choc economique mondial",
        ]
    )


def _reading_from_label(label: str) -> str:
    return {
        "BULLISH": "HAUSSIERE",
        "BEARISH": "BAISSIERE",
        "NEUTRAL": "NEUTRE",
        "UNCERTAIN": "INCERTAINE",
    }.get(label, str(label))


def _clarity(confidence: float) -> str:
    if confidence >= 0.70:
        return "FORTE"
    if confidence >= 0.55:
        return "MODEREE"
    return "FAIBLE"


def _pct(value: float) -> str:
    return f"{100.0 * float(value):.0f} %"


def _signed(value: float) -> str:
    return f"{float(value):+.0f}"


def _risk_label(value: float) -> str:
    if value >= 0.60:
        return "ELEVEE"
    if value >= 0.35:
        return "PRESENTE"
    return "FAIBLE"


def _opportunity_label(value: float) -> str:
    if value >= 0.60:
        return "FORTE"
    if value >= 0.35:
        return "PRESENTE"
    return "FAIBLE"


def _numbered(items: list[str]) -> list[str]:
    return [f"  {idx}. {item}" for idx, item in enumerate(items, start=1)]


def _dash(items: list[str]) -> list[str]:
    return [f"  - {item}" for item in items]


def as_dict(data: WeeklyReportInput) -> dict[str, Any]:
    return asdict(data)

from __future__ import annotations

import time

import pandas as pd

from mais.indicator.shap_translator import translate_shap_rows
from mais.ops.archive.weekly_report import WeeklyReportInput, generate_weekly_report


def _report_input() -> WeeklyReportInput:
    return WeeklyReportInput(
        date="2026-05-18",
        current_price_cents=485.0,
        market_reading="HAUSSIERE",
        probability_up=0.64,
        p_correct=0.71,
        market_clarity="MODEREE",
        downside_risk_score=0.22,
        upside_opportunity_score=0.41,
        storage_gain_gross_cents=18.0,
        storage_cost_cents=5.0,
        storage_gain_net_cents=13.0,
        storage_ci90_low=2.0,
        storage_ci90_high=27.0,
        hedge_signal="ATTENDRE",
        days_to_wasde=8,
        volatility_change_pct=15.0,
    )


def _shap_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"feature": "wasde_ending_stocks_surprise", "shap_value": 0.21},
            {"feature": "export_pace_vs_5y_avg", "shap_value": 0.14},
            {"feature": "macro_dollar_index", "shap_value": -0.12},
            {"feature": "cot_mm_extreme_long_flag", "shap_value": 0.11},
        ]
    )


def test_report_generation_time():
    start = time.perf_counter()

    report = generate_weekly_report(_report_input(), shap_rows=_shap_rows())

    assert time.perf_counter() - start < 30.0
    assert "MAÏS CBOT" in report


def test_report_four_modules_present():
    report = generate_weekly_report(_report_input(), shap_rows=_shap_rows())

    assert "Module 1 - Situation marche" in report
    assert "Module 2 - Aide a la decision stockage" in report
    assert "Module 3 - Alertes couverture" in report
    assert "Module 4 - Alertes et limites" in report


def test_shap_no_jargon_in_module1():
    report = generate_weekly_report(_report_input(), shap_rows=_shap_rows())
    module_1 = report.split("## Module 2", maxsplit=1)[0]

    for forbidden in ("SHAP", "AUC", "feature", "z-score", "percentile"):
        assert forbidden not in module_1


def test_cot_contrarian_framing():
    report = generate_weekly_report(_report_input(), shap_rows=_shap_rows())
    module_1 = report.split("## Module 2", maxsplit=1)[0]
    module_4 = report.split("## Module 4", maxsplit=1)[1]

    assert "fonds speculatifs sont tres achetes" not in module_1
    assert "fonds speculatifs sont tres achetes" in module_4


def test_shap_translator_uses_signed_contribution():
    translated = translate_shap_rows(
        [
            {"feature": "export_pace_vs_5y_avg", "shap_value": 0.2},
            {"feature": "macro_dollar_index", "shap_value": -0.2},
        ]
    )

    assert translated.bullish
    assert translated.bearish

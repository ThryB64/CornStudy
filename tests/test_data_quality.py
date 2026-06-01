from __future__ import annotations

import json
from datetime import date

from mais.collect.data_quality import (
    QUALITY_WEIGHTS,
    build_quality_report,
    compute_data_availability_score,
    summarize_euronext_contracts,
    typed_uncertainty_flags,
    write_quality_report,
)

CONTRACTS = [
    {
        "contract_code": "EMA_M2026",
        "days_to_expiry": 13,
        "settlement": 210.5,
        "open_interest": 4448,
        "is_proxy": False,
        "quality_flag": "ok",
    },
    {
        "contract_code": "EMA_Q2026",
        "days_to_expiry": 74,
        "settlement": 216.5,
        "open_interest": 13765,
        "is_proxy": False,
        "quality_flag": "ok",
    },
]


def test_compute_data_availability_score_weighted() -> None:
    full = dict.fromkeys(QUALITY_WEIGHTS, True)
    partial = {"euronext_settlement": True, "cbot_corn": True}

    assert compute_data_availability_score(full) == 1.0
    assert compute_data_availability_score(partial) == 0.5


def test_summarize_euronext_contracts() -> None:
    summary = summarize_euronext_contracts(CONTRACTS)

    assert summary["contracts_count"] == 2
    assert summary["is_proxy"] is False
    assert summary["avg_oi_front"] == 4448.0
    assert summary["settlement_present"] is True


def test_typed_uncertainty_flags() -> None:
    report = build_quality_report(
        date(2026, 5, 19),
        euronext_contracts=[{**CONTRACTS[0], "open_interest": 100, "is_proxy": True}],
        source_status={},
        wasde={"days_to_next": 3},
    )

    assert typed_uncertainty_flags(report) == [
        "DATA_MISSING",
        "PROXY_DATA",
        "LOW_LIQUIDITY",
        "NEAR_WASDE",
    ]
    assert report["signal_status"] == "UNCERTAIN"


def test_quality_report_usability_when_sources_available() -> None:
    status = dict.fromkeys(QUALITY_WEIGHTS, True)
    report = build_quality_report(date(2026, 5, 19), euronext_contracts=CONTRACTS, source_status=status)

    assert report["data_availability_score"] == 1.0
    assert report["uncertainty_flags"] == []
    assert report["signal_status"] == "USABLE"


def test_write_quality_report(tmp_path) -> None:
    report = build_quality_report(date(2026, 5, 19), euronext_contracts=CONTRACTS)
    out = write_quality_report(report, tmp_path)

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["date"] == "2026-05-19"
    assert payload["euronext"]["contracts_count"] == 2

"""Daily data-quality report for the EMA pipeline."""

from __future__ import annotations

import json
from datetime import date as date_cls
from pathlib import Path
from typing import Any

from mais.paths import EMA_CONTRACTS_RAW_DIR, REPORTS_QUALITY_DIR

QUALITY_WEIGHTS = {
    "euronext_settlement": 0.30,
    "cbot_corn": 0.20,
    "eurusd_rate": 0.15,
    "ttf_natgas": 0.05,
    "wasde": 0.15,
    "cot": 0.10,
    "fas_export_sales": 0.05,
}


def compute_data_availability_score(source_status: dict[str, bool]) -> float:
    """Return the weighted availability score in [0, 1]."""
    score = sum(weight for source, weight in QUALITY_WEIGHTS.items() if source_status.get(source, False))
    return round(float(score), 6)


def build_quality_report(
    report_date: date_cls,
    *,
    euronext_contracts: list[dict[str, Any]],
    source_status: dict[str, bool] | None = None,
    wasde: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a quality report and typed uncertainty flags."""
    euronext = summarize_euronext_contracts(euronext_contracts)
    status = dict(source_status or {})
    status["euronext_settlement"] = bool(euronext["contracts_count"] and not euronext["is_proxy"])
    for source in QUALITY_WEIGHTS:
        status.setdefault(source, False)
    score = compute_data_availability_score(status)
    wasde_block = {"days_to_next": None, **(wasde or {})}
    report = {
        "date": report_date.isoformat(),
        "data_availability_score": score,
        "source_status": status,
        "euronext": euronext,
        "wasde": wasde_block,
    }
    flags = typed_uncertainty_flags(report)
    report["uncertainty_flags"] = flags
    report["signal_status"] = "UNCERTAIN" if flags else "USABLE"
    return report


def summarize_euronext_contracts(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize Euronext contract coverage and liquidity."""
    if not contracts:
        return {
            "contracts_count": 0,
            "is_proxy": True,
            "avg_oi_front": 0.0,
            "avg_oi_all": 0.0,
            "settlement_present": False,
            "quality_flags": [],
            "contracts": [],
        }
    sorted_contracts = sorted(contracts, key=lambda c: c.get("days_to_expiry") or 10**9)
    front = sorted_contracts[0]
    oi_values = [float(c["open_interest"]) for c in contracts if c.get("open_interest") is not None]
    return {
        "contracts_count": len(contracts),
        "is_proxy": any(bool(c.get("is_proxy", False)) for c in contracts),
        "avg_oi_front": float(front.get("open_interest") or 0.0),
        "avg_oi_all": round(sum(oi_values) / len(oi_values), 6) if oi_values else 0.0,
        "settlement_present": any(c.get("settlement") is not None for c in contracts),
        "quality_flags": sorted({str(c.get("quality_flag", "unknown")) for c in contracts}),
        "contracts": [str(c.get("contract_code")) for c in sorted_contracts],
    }


def typed_uncertainty_flags(report: dict[str, Any]) -> list[str]:
    """Return uncertainty codes triggered by a quality report."""
    flags: list[str] = []
    if report["data_availability_score"] < 0.70:
        flags.append("DATA_MISSING")
    if report["euronext"]["is_proxy"]:
        flags.append("PROXY_DATA")
    if report["euronext"]["avg_oi_front"] < 500:
        flags.append("LOW_LIQUIDITY")
    days_to_next = report.get("wasde", {}).get("days_to_next")
    if days_to_next is not None and int(days_to_next) <= 5:
        flags.append("NEAR_WASDE")
    return flags


def write_quality_report(report: dict[str, Any], out_dir: Path | None = None) -> Path:
    """Write the quality report JSON."""
    target_dir = out_dir or REPORTS_QUALITY_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{report['date']}_quality.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_euronext_snapshot(report_date: date_cls) -> list[dict[str, Any]]:
    """Load the daily EMA JSON snapshot produced by DATA-EMA-01."""
    path = EMA_CONTRACTS_RAW_DIR / f"{report_date.isoformat()}.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("contracts", []))


def generate_quality_report(
    report_date: date_cls,
    *,
    source_status: dict[str, bool] | None = None,
    wasde: dict[str, Any] | None = None,
) -> Path:
    """Load the EMA snapshot, build and write the daily quality report."""
    contracts = load_euronext_snapshot(report_date)
    report = build_quality_report(
        report_date,
        euronext_contracts=contracts,
        source_status=source_status,
        wasde=wasde,
    )
    return write_quality_report(report)


__all__ = [
    "QUALITY_WEIGHTS",
    "build_quality_report",
    "compute_data_availability_score",
    "generate_quality_report",
    "load_euronext_snapshot",
    "summarize_euronext_contracts",
    "typed_uncertainty_flags",
    "write_quality_report",
]

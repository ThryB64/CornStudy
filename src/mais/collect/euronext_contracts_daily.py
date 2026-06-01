"""Daily Euronext EMA active-contract collector."""

from __future__ import annotations

import json
import os
from datetime import date as date_cls
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from mais.collect.euronext_ema_collector import (
    CURRENT_OFFICIAL_EMA_MONTHS,
    parse_contract_label,
)
from mais.collect.euronext_endpoint_probe import fetch_endpoint_html, parse_prices_html
from mais.paths import EMA_CONTRACT_DAILY, EMA_CONTRACT_REFERENCE, EMA_CONTRACTS_RAW_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.euronext_contracts_daily")

BARCHART_EMA_PREFIX = "CWH"
REAL_SOURCE_RANK = {
    "euronext_ajax_prices": 30,
    "barchart": 20,
    "manual_backfill": 15,
    "proxy_cbot": 10,
}
OFFICIAL_EURONEXT_SOURCES = {"euronext_ajax_prices", "euronext_chart_history"}


def download_active_contracts(date: date_cls | None = None, *, html: str | None = None) -> list[dict[str, Any]]:
    """Fetch all active EMA contracts from the validated Euronext endpoint."""
    as_of = date or date_cls.today()
    try:
        raw_html = html if html is not None else fetch_endpoint_html()
        rows, session_date = parse_prices_html(raw_html)
        contracts = [_normalise_contract(row, session_date or as_of.isoformat()) for row in rows]
        if contracts:
            return contracts
    except Exception as exc:
        log.warning("euronext_daily_scrape_failed", error=str(exc))

    barchart_contracts = _download_from_barchart(as_of)
    if barchart_contracts:
        return barchart_contracts

    proxy_contracts = _build_proxy_contracts(as_of)
    if proxy_contracts:
        return proxy_contracts

    raise RuntimeError("No Euronext EMA contracts available from scraper, Barchart, or proxy fallback")


def save_daily_snapshot(date: date_cls, contracts: list[dict[str, Any]]) -> Path:
    """Save or merge a daily JSON snapshot without degrading real data with proxy rows."""
    EMA_CONTRACTS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = EMA_CONTRACTS_RAW_DIR / f"{date.isoformat()}.json"
    existing: list[dict[str, Any]] = []
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        existing = list(payload.get("contracts", []))
    merged = _merge_contract_rows(existing, contracts)
    payload = {
        "date": date.isoformat(),
        "source": "euronext_scraper",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "contracts": merged,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def update_contract_daily_parquet(date: date_cls, contracts: list[dict[str, Any]]) -> int:
    """Update ``ema_contract_daily.parquet`` incrementally."""
    EMA_CONTRACT_DAILY.parent.mkdir(parents=True, exist_ok=True)
    incoming = normalise_contract_daily_frame(pd.DataFrame(contracts))
    if incoming.empty:
        return 0
    incoming = incoming[incoming["import_verdict"].eq("usable")].copy()
    if incoming.empty:
        return 0
    incoming["date"] = pd.to_datetime(incoming["date"]).dt.normalize()
    incoming["snapshot_date"] = pd.Timestamp(date)
    if EMA_CONTRACT_DAILY.exists():
        existing = normalise_contract_daily_frame(pd.read_parquet(EMA_CONTRACT_DAILY))
        existing["date"] = pd.to_datetime(existing["date"]).dt.normalize()
        combined = pd.concat([existing, incoming], ignore_index=True, sort=False)
    else:
        combined = incoming
    combined = normalise_contract_daily_frame(combined)
    combined["_source_rank"] = combined["source"].map(REAL_SOURCE_RANK).fillna(0)
    combined["_proxy_rank"] = (~combined["is_proxy"].fillna(False).astype(bool)).astype(int)
    combined = combined.sort_values(["date", "contract_code", "_proxy_rank", "_source_rank"])
    combined = combined.drop_duplicates(["date", "contract_code"], keep="last")
    combined = combined.drop(columns=["_source_rank", "_proxy_rank"])
    combined = combined.sort_values(["date", "contract_code"]).reset_index(drop=True)
    combined.to_parquet(EMA_CONTRACT_DAILY, index=False)
    return int(len(incoming))


def canonicalise_contract_daily_parquet(path: Path = EMA_CONTRACT_DAILY) -> int:
    """Canonicalise an existing EMA contract daily parquet in place."""
    if not path.exists():
        return 0
    fixed = normalise_contract_daily_frame(pd.read_parquet(path))
    fixed.to_parquet(path, index=False)
    return int(len(fixed))


def download(out_dir: Path, src: dict) -> str:
    """Standard collector entrypoint for ``mais.collect.run_collector``."""
    contracts = download_active_contracts()
    if not contracts:
        # Source EMA daily indisponible (réseau / endpoint vide) : non bloquant -> STUB.
        raise NotImplementedError(
            "euronext daily: aucun contrat disponible (source proxy/endpoint indisponible)")
    snapshot_date = pd.to_datetime(contracts[0]["date"]).date()
    snapshot_path = save_daily_snapshot(snapshot_date, contracts)
    rows = update_contract_daily_parquet(snapshot_date, contracts)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(contracts).to_csv(out_dir / "euronext_ema_daily.csv", index=False)
    log.info("euronext_daily_saved", rows=rows, snapshot=str(snapshot_path))
    return f"{rows} rows ({snapshot_path.name})"


def quality_flag(contract: dict[str, Any]) -> str:
    """Assign a compact quality flag to one contract row."""
    if contract.get("is_proxy"):
        return "proxy_cbot"
    if contract.get("settlement") is None:
        return "settlement_missing"
    if contract.get("open_interest") is None:
        return "oi_missing"
    volume = contract.get("volume")
    open_interest = contract.get("open_interest")
    if (volume is None or float(volume) == 0.0) or float(open_interest) < 500:
        return "low_liquidity"
    return "ok"


def normalise_contract_daily_frame(
    frame: pd.DataFrame,
    *,
    reference_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Repair/complete EMA contract daily rows before merge or feature builds."""
    if frame.empty:
        return frame.copy()
    work = frame.copy()
    if "date" not in work.columns and "Date" in work.columns:
        work["date"] = work["Date"]
    if "contract_code" not in work.columns:
        raise ValueError("EMA contract rows require contract_code")
    work["contract_code"] = work["contract_code"].astype(str)
    parsed = work["contract_code"].str.extract(r"^EMA_([A-Z])(\d{4})$")
    parsed_month = parsed[0]
    parsed_year = pd.to_numeric(parsed[1], errors="coerce")

    _ensure_column(work, "month_code", None)
    work.loc[_blank_mask(work["month_code"]) & parsed_month.notna(), "month_code"] = parsed_month
    official_month = work["month_code"].isin(CURRENT_OFFICIAL_EMA_MONTHS)

    _ensure_column(work, "canonical_contract_code", None)
    canonical_missing = _blank_mask(work["canonical_contract_code"]) & official_month
    work.loc[canonical_missing, "canonical_contract_code"] = work.loc[canonical_missing, "contract_code"]

    _ensure_column(work, "contract_month", pd.NA)
    for code, month in CURRENT_OFFICIAL_EMA_MONTHS.items():
        mask = _blank_mask(work["contract_month"]) & work["month_code"].eq(code)
        work.loc[mask, "contract_month"] = month
    _ensure_column(work, "contract_year", pd.NA)
    work.loc[_blank_mask(work["contract_year"]) & parsed_year.notna(), "contract_year"] = parsed_year

    _ensure_column(work, "active_month_status", None)
    active_missing = _blank_mask(work["active_month_status"]) & official_month
    work.loc[active_missing, "active_month_status"] = "current_official"
    legacy_missing = _blank_mask(work["active_month_status"]) & ~official_month
    work.loc[legacy_missing, "active_month_status"] = "legacy_or_ambiguous"

    _ensure_column(work, "import_verdict", None)
    import_missing = _blank_mask(work["import_verdict"])
    work.loc[import_missing & official_month, "import_verdict"] = "usable"
    work.loc[import_missing & ~official_month, "import_verdict"] = "do_not_import"

    _ensure_column(work, "close_or_last", pd.NA)
    for candidate in ("settlement", "last", "close"):
        if candidate in work.columns:
            mask = _blank_mask(work["close_or_last"]) & work[candidate].notna()
            work.loc[mask, "close_or_last"] = work.loc[mask, candidate]

    work = _apply_reference_expiry(work, reference_frame=reference_frame)
    if "quality_flag" not in work.columns:
        work["quality_flag"] = None
    quality_missing = _blank_mask(work["quality_flag"])
    if quality_missing.any():
        work.loc[quality_missing, "quality_flag"] = work.loc[quality_missing].apply(
            lambda row: quality_flag(row.to_dict()),
            axis=1,
        )
    if "source_quality" not in work.columns:
        work["source_quality"] = work["source"].map(
            lambda source: "exploratory" if source == "barchart_proxy_exploratory" else "official_or_manual"
        )
    return work


def _normalise_contract(row: dict[str, Any], session_date: str) -> dict[str, Any]:
    contract_code = row["contract_code"]
    month_code = contract_code.split("_", 1)[1][0]
    year = int(contract_code[-4:])
    month = CURRENT_OFFICIAL_EMA_MONTHS[month_code]
    close = row.get("settlement") if row.get("settlement") is not None else row.get("last")
    expiry_date = date_cls(year, month, 1)
    current_date = pd.to_datetime(session_date).date()
    contract = {
        "date": session_date,
        "contract_code": contract_code,
        "source_symbol": row.get("source_symbol") or contract_code,
        "canonical_contract_code": contract_code,
        "month_code": month_code,
        "active_month_status": "current_official",
        "import_verdict": "usable",
        "product": "EMA",
        "product_code": "EMA",
        "contract_month": month,
        "contract_year": year,
        "expiry_date": expiry_date.isoformat(),
        "days_to_expiry": (expiry_date - current_date).days,
        "delivery": row.get("delivery"),
        "bid": row.get("bid"),
        "ask": row.get("ask"),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "last": row.get("last"),
        "close": close,
        "close_or_last": close,
        "settlement": row.get("settlement"),
        "volume": row.get("day_volume"),
        "open_interest": row.get("open_interest"),
        "currency": "EUR",
        "unit": "EUR/t",
        "lot_size": 50,
        "source": row.get("source", "euronext_ajax_prices"),
        "is_proxy": bool(row.get("is_proxy", False)),
        "expiry_estimated": True,
    }
    contract["quality_flag"] = quality_flag(contract)
    return contract


def _merge_contract_rows(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_code: dict[str, dict[str, Any]] = {}
    for row in [*existing, *incoming]:
        code = row["contract_code"]
        previous = by_code.get(code)
        if previous is None or _row_rank(row) >= _row_rank(previous):
            by_code[code] = row
    return [by_code[key] for key in sorted(by_code)]


def _row_rank(row: dict[str, Any]) -> tuple[int, int]:
    real_rank = 0 if row.get("is_proxy") else 1
    source_rank = REAL_SOURCE_RANK.get(str(row.get("source")), 0)
    return real_rank, source_rank


def _download_from_barchart(as_of: date_cls) -> list[dict[str, Any]]:
    if not os.getenv("BARCHART_API_KEY"):
        return []
    log.warning("barchart_ema_not_implemented", as_of=as_of.isoformat(), prefix=BARCHART_EMA_PREFIX)
    return []


def _build_proxy_contracts(as_of: date_cls) -> list[dict[str, Any]]:
    log.warning("euronext_daily_proxy_unavailable", as_of=as_of.isoformat())
    return []


def _apply_reference_expiry(
    frame: pd.DataFrame,
    *,
    reference_frame: pd.DataFrame | None,
) -> pd.DataFrame:
    work = frame.copy()
    reference = reference_frame
    if reference is None and EMA_CONTRACT_REFERENCE.exists():
        reference = pd.read_parquet(EMA_CONTRACT_REFERENCE)
    ref_expiry = pd.Series(pd.NaT, index=work.index, dtype="datetime64[ns]")
    if reference is not None and not reference.empty and "canonical_contract_code" in reference.columns:
        ref = reference.copy()
        ref["canonical_contract_code"] = ref["canonical_contract_code"].astype(str)
        date_col = "last_trade_date" if "last_trade_date" in ref.columns else "expiry_date"
        ref = ref[["canonical_contract_code", date_col]].dropna(subset=["canonical_contract_code"])
        ref = ref.drop_duplicates("canonical_contract_code", keep="last").rename(columns={date_col: "_ref_expiry"})
        lookup = work[["canonical_contract_code"]].copy()
        lookup["canonical_contract_code"] = lookup["canonical_contract_code"].astype(str)
        ref_expiry = pd.to_datetime(
            lookup.merge(ref, on="canonical_contract_code", how="left")["_ref_expiry"],
            errors="coerce",
        )

    _ensure_column(work, "expiry_date", pd.NaT)
    existing_expiry = pd.to_datetime(work["expiry_date"], errors="coerce")
    source = work["source"].astype(str) if "source" in work.columns else pd.Series("", index=work.index)
    official_source = source.isin(OFFICIAL_EURONEXT_SOURCES)
    first_day_official = official_source & existing_expiry.notna() & existing_expiry.dt.day.eq(1)
    use_reference = ref_expiry.notna() & (existing_expiry.isna() | first_day_official)

    fallback_expiry = pd.to_datetime(
        {
            "year": pd.to_numeric(work["contract_year"], errors="coerce"),
            "month": pd.to_numeric(work["contract_month"], errors="coerce"),
            "day": 1,
        },
        errors="coerce",
    )
    expiry = existing_expiry.where(~use_reference, ref_expiry)
    use_fallback = expiry.isna() & fallback_expiry.notna()
    expiry = expiry.where(~use_fallback, fallback_expiry)
    work["expiry_date"] = expiry.dt.date.astype("string")

    if "expiry_estimated" not in work.columns:
        work["expiry_estimated"] = False
    estimated = work["expiry_estimated"].fillna(False).astype(bool)
    estimated = estimated | use_fallback | (first_day_official & ~use_reference)
    estimated = estimated & ~use_reference
    work["expiry_estimated"] = estimated.astype(bool)

    if "days_to_expiry" not in work.columns:
        work["days_to_expiry"] = pd.NA
    if "date" in work.columns:
        computed_dte = (expiry - pd.to_datetime(work["date"], errors="coerce")).dt.days
        dte_missing = _blank_mask(work["days_to_expiry"]) & computed_dte.notna()
        work.loc[dte_missing, "days_to_expiry"] = computed_dte.loc[dte_missing]
    return work


def _ensure_column(frame: pd.DataFrame, column: str, default: Any) -> None:
    if column not in frame.columns:
        frame[column] = default


def _blank_mask(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().isin({"", "None", "none", "nan", "NaN", "NaT"})


__all__ = [
    "BARCHART_EMA_PREFIX",
    "canonicalise_contract_daily_parquet",
    "download",
    "download_active_contracts",
    "normalise_contract_daily_frame",
    "parse_contract_label",
    "quality_flag",
    "save_daily_snapshot",
    "update_contract_daily_parquet",
]

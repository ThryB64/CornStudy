"""USDA FAS Export Sales collector (Phase 1 NEW).

Weekly. Released Thursday 8:30 ET for the week ending the prior Thursday.
Use ``publication_lag_days`` from ``sources.yaml`` at feature-merge time
(``shift(1)`` + merge-asof in ``build_features()``).

API: https://apps.fas.usda.gov/OpenData/
Free key + docs: register at FAS Open Data portal, set ``FAS_API_KEY``.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.collect.fas")

_COMMODITY_CODES = {
    "CORN": "0410",
    "SOYBEANS": "0810",
    "WHEAT": "0110",
}


def _decode_payload(payload: object, *, context: str) -> list[dict]:
    if isinstance(payload, list):
        out = []
        for item in payload:
            if isinstance(item, dict):
                out.append(item)
        return out
    if isinstance(payload, dict):
        for k in ("results", "data", "exports", "items"):
            v = payload.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        log.warning("fas_unexpected_shape", context=context, keys=list(payload.keys())[:25])
    else:
        log.warning("fas_payload_type", context=context, type_=type(payload).__name__)
    return []


def _http_get_json(url: str, *, context: str) -> list[dict]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "mais-etude-mais/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:800]
        log.warning("fas_http_error", context=context, code=e.code, body=body)
        return []
    except urllib.error.URLError as e:
        log.warning("fas_url_error", context=context, error=str(e))
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        log.warning("fas_json_error", context=context, error=str(e))
        return []
    return _decode_payload(payload, context=context)


def _fetch_exports(api_key: str, commodity_code: str) -> list[dict]:
    base = (
        "https://apps.fas.usda.gov/OpenData/api/esr/exports/"
        f"commodityCode/{commodity_code}"
    )

    params = {"api_key": api_key}
    url = f"{base}?{urllib.parse.urlencode(params)}"
    rows = _http_get_json(url, context="commodity_all")
    if rows:
        log.info("fas_fetch_ok", mode="no_market_year", n=len(rows))
        return rows

    cy = datetime.now().year
    out: list[dict] = []
    for myid in range(cy - 24, cy + 2):
        q = urllib.parse.urlencode({"marketYearId": str(myid), "api_key": api_key})
        chunk = _http_get_json(f"{base}?{q}", context=f"market_year_{myid}")
        if chunk:
            log.info("fas_fetch_ok", mode="market_year_id", market_year=myid, n=len(chunk))
        out.extend(chunk)

    if out:
        return out

    for y in range(cy - 8, cy + 1):
        my_str = f"{y}/{y + 1}"
        q = urllib.parse.urlencode({"marketYearId": my_str, "api_key": api_key})
        chunk = _http_get_json(f"{base}?{q}", context=f"market_year_{my_str}")
        if chunk:
            log.info("fas_fetch_ok", mode="market_year_str", market_year=my_str, n=len(chunk))
        out.extend(chunk)

    return out


def _row_week_date(record: dict) -> pd.Timestamp | None:
    for k in (
        "weekEndingDate",
        "WeekEndingDate",
        "weekEnding",
        "WeekEnding",
        "reportingWeek",
        "ReportingWeek",
    ):
        if k in record and record[k] not in (None, ""):
            ts = pd.to_datetime(record[k], errors="coerce")
            if pd.notna(ts):
                return pd.Timestamp(ts).normalize()
    return None


def _row_weekly_export_mt(record: dict) -> float | None:
    """Extract weekly net sales, falling back to export shipment fields.

    FAS endpoint payloads have varied field casing/names across examples and
    API vintages. The project feature is named ``export_sales_mt`` and should
    represent net export sales when that field is present.
    """
    keys = (
        "weeklyNetSales",
        "WeeklyNetSales",
        "netSales",
        "NetSales",
        "currentMYNetSales",
        "CurrentMYNetSales",
        "weeklySales",
        "WeeklySales",
        "grossNewSales",
        "GrossNewSales",
        "weeklyExports",
        "WeeklyExports",
        "weeklyExport",
        "WeeklyExport",
    )
    for k in keys:
        if k in record:
            v = pd.to_numeric(record[k], errors="coerce")
            if pd.notna(v):
                return float(v)
    return None


def _records_to_weekly_totals(rows: list[dict]) -> pd.DataFrame:
    buckets: dict[pd.Timestamp, float] = {}
    for r in rows:
        d = _row_week_date(r)
        if d is None:
            continue
        v = _row_weekly_export_mt(r)
        if v is None:
            continue
        buckets[d] = buckets.get(d, 0.0) + v

    if not buckets:
        return pd.DataFrame(columns=["Date", "export_sales_mt"])
    df = pd.DataFrame([{"Date": k, "export_sales_mt": buckets[k]} for k in sorted(buckets)])
    return df.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)


def download(out_dir: Path, src: dict) -> str:
    api_key = os.environ.get(src.get("api_key_env", "FAS_API_KEY"))
    if not api_key:
        raise NotImplementedError(
            "Set FAS_API_KEY (https://apps.fas.usda.gov/OpenData/). "
            "Collector writes ``fas_export_sales.parquet`` under data/interim when successful."
        )

    commodity_key = str(src.get("commodity", "CORN")).upper()
    commodity_code = _COMMODITY_CODES.get(commodity_key, _COMMODITY_CODES["CORN"])

    rows = _fetch_exports(api_key, commodity_code)
    if not rows:
        raise RuntimeError(
            "FAS API returned no usable rows. Check api_key, commodity code, or USDA availability."
        )

    weekly = _records_to_weekly_totals(rows)
    if weekly.empty:
        raise RuntimeError("FAS rows parsed but weekly export_sales_mt series is empty.")

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "fas_export_sales.csv"
    weekly.to_csv(csv_path, index=False)

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    interim_path = INTERIM_DIR / "fas_export_sales.parquet"
    write_parquet(weekly, interim_path)

    return f"{csv_path.name} + {interim_path.name} ({len(weekly)} weekly rows)"

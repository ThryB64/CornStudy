"""USDA FAS Export Sales collector (Phase 1 NEW).

Weekly. Released Thursday 8:30 ET for the week ending the prior Thursday : l'interim est daté à la
PUBLICATION (semaine + 7 j ; backlog shutdown 2025 → 2026-01-08), build_features ajoute shift(1).

API : api.fas.usda.gov (ancien apps.fas.usda.gov/OpenData refuse les clés api.data.gov).
Clé gratuite : https://api.data.gov/signup/ → ``FAS_API_KEY``.
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
    "CORN": "401",
    "SOYBEANS": "801",
    "WHEAT": "107",
}
API_BASE = "https://api.fas.usda.gov/api/esr"
FIRST_MARKET_YEAR = 1999
CHINA_CODE = 5700
SHUTDOWN_WEEKS = (pd.Timestamp("2025-09-25"), pd.Timestamp("2026-01-01"))
SHUTDOWN_CAUGHT_UP = pd.Timestamp("2026-01-08")


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
    """api.fas.usda.gov (clé api.data.gov) — une requête par campagne (marketYear = année de fin)."""
    base = f"{API_BASE}/exports/commodityCode/{commodity_code}/allCountries/marketYear"
    out: list[dict] = []
    for my in range(FIRST_MARKET_YEAR, datetime.now().year + 2):
        q = urllib.parse.urlencode({"api_key": api_key})
        chunk = [r | {"marketYear": my} for r in _http_get_json(f"{base}/{my}?{q}", context=f"market_year_{my}")]
        if chunk:
            log.info("fas_fetch_ok", market_year=my, n=len(chunk))
        out.extend(chunk)
    return out


def release_date(week_ending: pd.Series) -> pd.Series:
    """Publication = jeudi suivant la semaine ; backlog shutdown 2025 rattrapé le 2026-01-08."""
    rel = week_ending + pd.Timedelta(days=7)
    backlog = week_ending.between(*SHUTDOWN_WEEKS)
    return rel.where(~backlog, rel.clip(lower=SHUTDOWN_CAUGHT_UP))


def build_weekly(rows: list[dict]) -> pd.DataFrame:
    """Totaux hebdo tous pays (ventes nettes, engagements, Chine), datés à la publication."""
    df = pd.DataFrame(rows)
    df["week_ending"] = pd.to_datetime(df["weekEndingDate"]).dt.normalize()
    # semaine à cheval sur deux campagnes : renvoyée par les deux requêtes → garder la nouvelle campagne
    df = df[df["marketYear"] == df.groupby("week_ending")["marketYear"].transform("max")]
    num = ["currentMYNetSales", "currentMYTotalCommitment"]
    df[num] = df[num].apply(pd.to_numeric, errors="coerce")
    g = df.groupby("week_ending")
    out = pd.DataFrame({
        "export_sales_mt": g["currentMYNetSales"].sum(),
        "export_sales_accumulated_mt": g["currentMYTotalCommitment"].sum(),
        "export_china_sales_mt": df[df["countryCode"] == CHINA_CODE].groupby("week_ending")["currentMYNetSales"].sum(),
    }).reset_index()
    out["export_china_sales_mt"] = out["export_china_sales_mt"].fillna(0.0)
    out["usda_export_forecast_mt"] = float("nan")
    out.insert(0, "Date", release_date(out["week_ending"]))
    out = out.sort_values("week_ending").drop_duplicates("Date", keep="last")
    return out.drop(columns=["week_ending"]).reset_index(drop=True)


def download(out_dir: Path, src: dict) -> str:
    api_key = os.environ.get(src.get("api_key_env", "FAS_API_KEY"))
    if not api_key:
        raise NotImplementedError(
            "Set FAS_API_KEY (https://api.data.gov/signup/). "
            "Collector writes ``fas_export_sales.parquet`` under data/interim when successful."
        )

    commodity_key = str(src.get("commodity", "CORN")).upper()
    commodity_code = _COMMODITY_CODES.get(commodity_key, _COMMODITY_CODES["CORN"])

    rows = _fetch_exports(api_key, commodity_code)
    if not rows:
        raise RuntimeError(
            "FAS API returned no usable rows. Check api_key, commodity code, or USDA availability."
        )

    weekly = build_weekly(rows)
    if weekly.empty:
        raise RuntimeError("FAS rows parsed but weekly export_sales_mt series is empty.")

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "fas_export_sales.csv"
    weekly.to_csv(csv_path, index=False)

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    interim_path = INTERIM_DIR / "fas_export_sales.parquet"
    write_parquet(weekly, interim_path)

    return f"{csv_path.name} + {interim_path.name} ({len(weekly)} weekly rows)"

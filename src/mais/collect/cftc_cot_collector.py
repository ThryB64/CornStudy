"""CFTC Commitments of Traders — Disaggregated Futures Only, maïs CBOT (002602).

Source : API Socrata publicreporting.cftc.gov (www.cftc.gov bloque les téléchargements scriptés).
Positions arrêtées au mardi, publiées le vendredi 15:30 ET → interim daté au VENDREDI de publication
(build_features applique ensuite shift(1) → utilisable dès la séance suivante).
Shutdown US 2025 : rapports du 30/09 au 23/12/2025 publiés en rattrapage jusqu'au 29/12/2025
(CFTC PR 9147-25) → datés au 29/12/2025 (borne conservatrice).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.cot")

API = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
MARKET_CODE = "002602"
FIELDS = {
    "open_interest_all": "cot_open_interest",
    "m_money_positions_long_all": "cot_mm_long",
    "m_money_positions_short_all": "cot_mm_short",
    "prod_merc_positions_long": "cot_pm_long",
    "prod_merc_positions_short": "cot_pm_short",
    "swap_positions_long_all": "cot_sd_long",
    "swap__positions_short_all": "cot_sd_short",
}
SHUTDOWN_ASOF = (pd.Timestamp("2025-09-30"), pd.Timestamp("2025-12-23"))
SHUTDOWN_RELEASE = pd.Timestamp("2025-12-29")


def _fetch(start: str = "2006-01-01", timeout: int = 120) -> pd.DataFrame:
    q = {
        "$select": ",".join(["report_date_as_yyyy_mm_dd", *FIELDS]),
        "$where": f"cftc_contract_market_code='{MARKET_CODE}' AND report_date_as_yyyy_mm_dd >= '{start}'",
        "$order": "report_date_as_yyyy_mm_dd",
        "$limit": "50000",
    }
    url = API + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}),
                                timeout=timeout) as resp:
        return pd.DataFrame(json.loads(resp.read().decode("utf-8")))


def release_date(asof: pd.Series) -> pd.Series:
    rel = asof + pd.Timedelta(days=3)
    in_shutdown = asof.between(*SHUTDOWN_ASOF)
    return rel.where(~in_shutdown, SHUTDOWN_RELEASE)


def build_cot(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns=FIELDS)
    asof = pd.to_datetime(df["report_date_as_yyyy_mm_dd"]).dt.normalize()
    out = pd.DataFrame({"asof_date": asof})
    for col in FIELDS.values():
        out[col] = pd.to_numeric(df[col], errors="coerce")
    out["Date"] = release_date(out["asof_date"])
    out = out.sort_values("asof_date").drop_duplicates("asof_date", keep="last")
    # rattrapage shutdown : plusieurs rapports à la même date → seul le plus récent est « connu »
    out = out.drop_duplicates("Date", keep="last")
    oi = out["cot_open_interest"].where(out["cot_open_interest"] > 0)
    for grp in ("mm", "pm", "sd"):
        out[f"cot_{grp}_net"] = out[f"cot_{grp}_long"] - out[f"cot_{grp}_short"]
    out["cot_mm_long_pct"] = out["cot_mm_long"] / oi
    out["cot_mm_short_pct"] = out["cot_mm_short"] / oi
    out["cot_mm_net_pct_oi"] = out["cot_mm_net"] / oi
    out["cot_pm_net_pct_oi"] = out["cot_pm_net"] / oi
    cols = ["Date", *FIELDS.values(), "cot_mm_net", "cot_pm_net", "cot_sd_net",
            "cot_mm_long_pct", "cot_mm_short_pct", "cot_mm_net_pct_oi", "cot_pm_net_pct_oi"]
    return out[cols].reset_index(drop=True)


def download(out_dir: Path, src: dict) -> str:
    raw = _fetch()
    if raw.empty:
        raise RuntimeError("CFTC API: aucune ligne pour 002602")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    raw.to_csv(Path(out_dir) / "cot_disagg_corn_raw.csv", index=False)
    cot = build_cot(raw)
    cot.to_parquet(INTERIM_DIR / "cftc_cot.parquet", index=False)
    last = pd.to_datetime(raw["report_date_as_yyyy_mm_dd"]).max().date()
    log.info("cot_saved", rows=len(cot), last_asof=str(last))
    return f"{len(cot)} rapports, dernier arrêté au {last}"

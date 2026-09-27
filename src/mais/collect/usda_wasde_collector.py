"""USDA WASDE collector (ESMIS) — US corn supply & use, daté à la PUBLICATION réelle.

Télécharge les wasdeMMYY.txt manquants depuis ESMIS (dates de publication lues sur la page),
parse la section CORN (colonne la plus récente = projection courante, sémantique legacy),
puis construit data/interim/wasde.parquet quotidien effectif au jour ouvré SUIVANT la publication.

Correctif anti-leakage 2026-09-27 : le legacy datait chaque rapport au 1er du mois (nom de fichier)
alors que la publication a lieu vers le 8-12 → ~8 séances de fuite. Rapports sans date connue
(anciens fichiers hors pages scannées) : repli conservateur au 14 du mois.
"""

from __future__ import annotations

import contextlib
import re
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BusinessDay

from mais.paths import DATA_DIR, INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.wasde")

ESMIS = "https://esmis.nal.usda.gov"
LIST_URL = ESMIS + "/publication/world-agricultural-supply-and-demand-estimates?page={page}"
TXT_DIR = DATA_DIR / "wasde_raw"
RELEASES_CSV = TXT_DIR / "release_dates.csv"
# valeurs legacy par rapport (2002-2025, anciens formats non re-parsés), re-datées ici à la publication
LEGACY_CSV = TXT_DIR / "legacy_reports.csv"
FALLBACK_DAY = 14
Z_MIN = 24
UA = {"User-Agent": "Mozilla/5.0 (research; etude-mais)"}

_TXT_RE = re.compile(r"/sites/default/release-files/[^\"\s]+?/(wasde[^\"/\s]*?)\.txt", re.IGNORECASE)
_DATE_RE = re.compile(r"([A-Z][a-z]{2} \d{1,2} \d{4})")

LABELS = {
    "area planted": "area_planted", "area harvested": "area_harvested",
    "yield per harvested acre": "yield_per_acre", "beginning stocks": "beginning_stocks",
    "production": "production", "imports": "imports", "supply, total": "supply_total",
    "feed and residual": "feed_and_residual", "food,seed& industrial": "food_seed_industrial",
    "food, seed & industrial": "food_seed_industrial", "ethanol & by-products": "ethanol_byproducts",
    "ethanol for fuel": "ethanol_byproducts", "domestic, total": "domestic_total",
    "exports": "exports", "use, total": "use_total", "ending stocks": "ending_stocks",
    "avg.farmprice ($/bu)": "avg_farm_price", "avg. farm price": "avg_farm_price",
    "average farm price": "avg_farm_price",
}
MAJORS = ["wasde_production", "wasde_ending_stocks", "wasde_use_total", "wasde_exports",
          "wasde_avg_farm_price", "wasde_stocks_to_use_ratio"]


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def scan_releases(max_pages: int = 40, stop_year: int = 2008) -> pd.DataFrame:
    """(yymm, file, url, release_date) depuis les pages ESMIS, plus récent d'abord."""
    rows = []
    for page in range(max_pages):
        html = _get(LIST_URL.format(page=page)).decode("utf-8", errors="replace")
        found = 0
        for chunk in re.split(r"<tr[ >]", html):
            m = _TXT_RE.search(chunk)
            if not m:
                continue
            dates = [pd.to_datetime(d, format="%b %d %Y")
                     for d in _DATE_RE.findall(re.sub(r"<[^>]+>", " ", chunk))]
            if not dates:
                continue
            # le mois du rapport = mois de publication (noms de fichiers hétérogènes selon l'époque)
            # date max = conservateur si le fichier a été corrigé (v2) après la publication
            rd = max(dates)
            rows.append({"yymm": min(dates).strftime("%y%m"), "file": m.group(1), "url": ESMIS + m.group(0),
                         "release_date": rd.date()})
            found += 1
        if not found or (rows and pd.Timestamp(rows[-1]["release_date"]).year < stop_year):
            break
        time.sleep(0.5)
    df = pd.DataFrame(rows).drop_duplicates("yymm", keep="first")
    return df.sort_values("yymm").reset_index(drop=True)


def _merge_release_table(new: pd.DataFrame) -> pd.DataFrame:
    if RELEASES_CSV.exists():
        old = pd.read_csv(RELEASES_CSV, dtype={"yymm": str})
        new = pd.concat([old, new]).drop_duplicates("yymm", keep="last")
    new = new.sort_values("yymm").reset_index(drop=True)
    new.to_csv(RELEASES_CSV, index=False)
    return new


def download_missing(releases: pd.DataFrame) -> list[str]:
    TXT_DIR.mkdir(parents=True, exist_ok=True)
    got = []
    for r in releases.itertuples():
        path = TXT_DIR / f"wasde{r.yymm}.txt"
        if path.exists():
            continue
        path.write_bytes(_get(r.url))
        got.append(path.name)
        time.sleep(0.5)
    return got


def _corn_section(content: str) -> str | None:
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip().upper() == "CORN":
            return "\n".join(lines[i:i + 20])
    for i, line in enumerate(lines):
        if "corn supply and use" in line.lower():
            for j in range(i + 1, min(i + 50, len(lines))):
                if lines[j].strip().upper() == "CORN":
                    return "\n".join(lines[j:j + 20])
    return None


def parse_report(path: Path) -> dict[str, float] | None:
    section = _corn_section(path.read_text(encoding="utf-8", errors="ignore"))
    if not section:
        return None
    data: dict[str, float] = {}
    for line in section.split("\n"):
        low = line.strip().lower()
        for key, col in LABELS.items():
            if key in low:
                nums = re.findall(r"[-+]?\d[\d,\.]*", line)
                if nums:
                    with contextlib.suppress(ValueError):
                        data[col] = float(nums[-1].replace(",", "").rstrip("."))
                break
    if not any(k in data for k in ("production", "ending_stocks")):
        return None
    if data.get("ending_stocks") and data.get("use_total"):
        data["stocks_to_use_ratio"] = round(data["ending_stocks"] / data["use_total"] * 100, 2)
    return data


def _release_date(yymm: str, table: dict[str, str]) -> pd.Timestamp:
    if yymm in table:
        return pd.Timestamp(table[yymm])
    return pd.Timestamp(f"20{yymm[:2]}-{yymm[2:]}-{FALLBACK_DAY:02d}")


def _pct(s: pd.Series, n: int) -> pd.Series:
    base = s.shift(n)
    return (s - base) / base.replace(0, np.nan) * 100.0


def build_interim(sessions: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    table = {}
    if RELEASES_CSV.exists():
        rel = pd.read_csv(RELEASES_CSV, dtype={"yymm": str})
        table = dict(zip(rel["yymm"], rel["release_date"], strict=True))
    reports: dict[str, dict] = {}
    if LEGACY_CSV.exists():
        leg = pd.read_csv(LEGACY_CSV, dtype={"yymm": str}).set_index("yymm")
        reports = {k: {c: v for c, v in row.items() if pd.notna(v)} | {"source": "legacy"}
                   for k, row in leg.iterrows()}
    for path in sorted(TXT_DIR.glob("wasde*.txt")):
        m = re.fullmatch(r"wasde(\d{2})(\d{2})", path.stem)
        if not m:
            continue
        data = parse_report(path)
        if data is not None:
            reports[m.group(1) + m.group(2)] = data | {"source": "txt"}
    recs = []
    for yymm, data in reports.items():
        rd = _release_date(yymm, table)
        recs.append({"yymm": yymm, "release_date": rd, "release_known": yymm in table,
                     "effective": rd.normalize() + BusinessDay(1), **data})
    rep = pd.DataFrame(recs).sort_values("effective").drop_duplicates("effective", keep="last")
    base = rep.set_index("effective").drop(columns=["yymm", "release_date", "release_known", "source"])
    base = base.apply(pd.to_numeric, errors="coerce").add_prefix("wasde_")
    b = base
    b["wasde_stocks_to_use_calc"] = b["wasde_ending_stocks"] / b["wasde_use_total"].replace(0, np.nan) * 100
    b["wasde_export_ratio_calc"] = b["wasde_exports"] / b["wasde_use_total"].replace(0, np.nan) * 100
    b["wasde_domestic_ratio_calc"] = b["wasde_domestic_total"] / b["wasde_use_total"].replace(0, np.nan) * 100
    b["wasde_supply_minus_use"] = b["wasde_supply_total"] - b["wasde_use_total"]
    for c in MAJORS:
        b[f"{c}_mom_diff"] = b[c].diff(1)
        b[f"{c}_mom_pct"] = _pct(b[c], 1)
        b[f"{c}_yoy_pct"] = _pct(b[c], 12)
    for c in ("wasde_stocks_to_use_calc", "wasde_avg_farm_price", "wasde_supply_minus_use"):
        e = b[c].expanding(min_periods=Z_MIN)
        b[f"{c}_z"] = ((b[c] - e.mean()) / e.std(ddof=0)).clip(-6, 6)
    if sessions is None:
        sessions = pd.bdate_range(b.index.min(), pd.Timestamp.today().normalize())
    sessions = sessions[sessions >= b.index.min()]
    daily = b.reindex(sessions, method="ffill")
    daily.index.name = "Date"
    keep = ["wasde_production", "wasde_ending_stocks", "wasde_use_total", "wasde_exports",
            "wasde_domestic_total", "wasde_supply_total", "wasde_avg_farm_price",
            "wasde_stocks_to_use_ratio", "wasde_stocks_to_use_calc", "wasde_export_ratio_calc",
            "wasde_domestic_ratio_calc", "wasde_supply_minus_use"]
    keep += [f"{c}_{s}" for c in MAJORS for s in ("mom_diff", "mom_pct", "yoy_pct")]
    keep += ["wasde_stocks_to_use_calc_z", "wasde_avg_farm_price_z", "wasde_supply_minus_use_z"]
    out = daily.reset_index()[["Date", *[c for c in keep if c in daily.columns]]]
    rep.to_csv(TXT_DIR / "wasde_reports_parsed.csv", index=False)
    return out


def download(out_dir: Path, src: dict) -> str:
    try:
        releases = _merge_release_table(scan_releases(max_pages=int(src.get("max_pages", 3))))
        got = download_missing(releases)
    except Exception as exc:  # noqa: BLE001
        log.warning("wasde_esmis_failed", error=str(exc))
        got = []
    sessions = None
    db = INTERIM_DIR / "database.parquet"
    if db.exists():
        sessions = pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(db, columns=["Date"])["Date"]))
    out = build_interim(sessions)
    out.to_parquet(INTERIM_DIR / "wasde.parquet", index=False)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    log.info("wasde_saved", new_reports=got, rows=len(out), last=str(out["Date"].max().date()))
    return f"{len(got)} nouveaux rapports, interim jusqu'au {out['Date'].max().date()}"

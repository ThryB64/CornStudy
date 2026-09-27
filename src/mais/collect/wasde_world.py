"""DATA-WORLD-01 — WASDE « World Corn Supply and Use » (réécrit 2026-09-27).

Parse les deux pages de la table monde (années estimées + projection avec lignes mensuelles,
on garde la ligne du mois courant). Pour chaque rapport : campagne la plus récente par région.
Datage : date de publication ESMIS (data/wasde_raw/release_dates.csv, repli jour 14) puis shift(1).
L'ancien parser étiquetait « eu » des lignes d'autres tables (production UE 2.85 Mt au lieu de ~60).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

_WASDE_RAW_DIR = Path(__file__).parents[3] / "data" / "wasde_raw"
_OUTPUT_DIR = Path(__file__).parents[3] / "data" / "raw" / "wasde_world"
_AUDIT_OUTPUT = ARTEFACTS_DIR / "ema_study" / "wasde_world_audit.json"

_COLS = ["beg_stocks", "production", "imports", "feed", "dom_total", "exports", "end_stocks"]
_REGIONS = {
    "world": re.compile(r"^World\b(?!\s+Less)"),
    "world_less_china": re.compile(r"^World Less China"),
    "us": re.compile(r"^United States"),
    "argentina": re.compile(r"^Argentina"),
    "brazil": re.compile(r"^Brazil"),
    "ukraine": re.compile(r"^Ukraine"),
    "eu": re.compile(r"^(European Union|EU-\d+)"),
    "china": re.compile(r"^China"),
}
_YEAR_RE = re.compile(r"^\s*(\d{4})/(\d{2})")
_NUM_RE = re.compile(r"-?\d+\.\d+")
_MONTH_RE = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b")
FALLBACK_DAY = 14


def _report_yymm(path: Path) -> str | None:
    m = re.fullmatch(r"wasde(\d{4})", path.stem)
    return m.group(1) if m else None


def _parse_wasde_file(path: Path) -> list[dict]:
    """Lignes (crop_year, country, 7 colonnes) de la table World Corn, mois courant pour les projections."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return []
    yymm = _report_yymm(path)
    if yymm is None:
        return []
    out: dict[tuple[int, str], dict] = {}
    in_table, crop_year, region = False, None, None
    for raw_line in lines:
        # formats 2000-2015 : séparateurs « : », mois en toutes lettres, région + mois sur une ligne
        line = raw_line.replace("\r", "").replace(":", " ")
        if "World Corn Supply and Use" in line:
            in_table, crop_year, region = True, None, None
            continue
        if not in_table:
            continue
        if "Supply and Use" in line:
            in_table = False
            continue
        stripped = line.strip()
        nums = _NUM_RE.findall(line)
        y = _YEAR_RE.match(stripped)
        if y and not nums:
            crop_year = int(y.group(1)) + 1
            continue
        if not crop_year:
            continue
        if not _MONTH_RE.match(stripped):
            region = next((k for k, rx in _REGIONS.items() if rx.match(stripped)), None)
        if region and len(nums) >= 7:
            out[(crop_year, region)] = dict(zip(_COLS, map(float, nums[-7:]), strict=True))
    return [{"yymm": yymm, "crop_year": cy, "country": reg, **vals} for (cy, reg), vals in out.items()]


def _release_dates() -> dict[str, pd.Timestamp]:
    path = _WASDE_RAW_DIR / "release_dates.csv"
    if not path.exists():
        return {}
    rel = pd.read_csv(path, dtype={"yymm": str})
    return {k: pd.Timestamp(v) for k, v in zip(rel["yymm"], rel["release_date"], strict=True)}


def _load_all_wasde_world(wasde_dir: Path) -> pd.DataFrame:
    rel = _release_dates()
    records = []
    for f in sorted(wasde_dir.glob("wasde*.txt")):
        for r in _parse_wasde_file(f):
            yymm = r["yymm"]
            r["pub_date"] = rel.get(yymm, pd.Timestamp(f"20{yymm[:2]}-{yymm[2:]}-{FALLBACK_DAY:02d}"))
            records.append(r)
    return pd.DataFrame(records)


def latest_by_region(raw: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par (pub_date, région) : campagne la plus récente du rapport."""
    raw = raw.sort_values(["pub_date", "country", "crop_year"])
    return raw.groupby(["pub_date", "country"]).last().reset_index()


def us_export_forecast(raw: pd.DataFrame) -> pd.DataFrame:
    """(pub_date, crop_year, us_exports_mt) — toutes campagnes, pour aligner sur la campagne FAS."""
    us = raw[raw["country"] == "us"][["pub_date", "crop_year", "exports"]]
    return us.rename(columns={"exports": "usda_export_forecast_mt"}).assign(
        usda_export_forecast_mt=lambda d: d["usda_export_forecast_mt"] * 1e6)


def _build_features(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    lat = latest_by_region(raw)
    wide = lat.pivot(index="pub_date", columns="country", values=["production", "exports", "end_stocks", "dom_total"])
    feats = pd.DataFrame(index=wide.index)
    names = {"eu": "eu", "ukraine": "ukraine", "brazil": "brazil", "argentina": "argentina",
             "china": "china", "world": "world", "world_less_china": "world_ex_china"}
    for reg, nm in names.items():
        if ("production", reg) not in wide.columns:
            continue
        feats[f"wasde_{nm}_production_mt"] = wide[("production", reg)]
        feats[f"wasde_{nm}_exports_mt"] = wide[("exports", reg)]
        feats[f"wasde_{nm}_ending_stocks_mt"] = wide[("end_stocks", reg)]
        feats[f"wasde_{nm}_stock_use_ratio"] = wide[("end_stocks", reg)] / wide[("dom_total", reg)].replace(0, np.nan)
    # révision mensuelle de production à campagne constante (surprise du rapport)
    for reg, nm in names.items():
        sub = raw[raw["country"] == reg].sort_values("pub_date")
        rev = sub.groupby("crop_year")["production"].diff()
        sub = sub.assign(rev=rev.values)
        last = sub.sort_values(["pub_date", "crop_year"]).groupby("pub_date")["rev"].last()
        feats[f"wasde_{nm}_production_rev_mt"] = last.reindex(feats.index)
    feats = feats.reset_index().rename(columns={"pub_date": "Date"})

    date_range = pd.DataFrame({"Date": pd.date_range("2000-01-01", pd.Timestamp.now().normalize())})
    daily = date_range.merge(feats, on="Date", how="left")
    feat_cols = [c for c in daily.columns if c != "Date"]
    level_cols = [c for c in feat_cols if not c.endswith("_rev_mt")]
    daily[level_cols] = daily[level_cols].ffill()
    # la révision n'a de sens que jusqu'au rapport suivant : ffill borné à ~1 mois
    rev_cols = [c for c in feat_cols if c.endswith("_rev_mt")]
    daily[rev_cols] = daily[rev_cols].ffill(limit=35)
    out = daily[["Date"]].copy()
    for col in feat_cols:
        out[f"{col}_lag1"] = daily[col].shift(1)
    return out


def build_wasde_world_features(wasde_dir: Path | None = None) -> pd.DataFrame:
    wdir = wasde_dir or _WASDE_RAW_DIR
    raw = _load_all_wasde_world(wdir)
    out_dir = _OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    if not raw.empty:
        raw.to_parquet(out_dir / "wasde_world_raw.parquet", index=False)
    else:
        parquet = out_dir / "wasde_world_raw.parquet"
        if parquet.exists():
            raw = pd.read_parquet(parquet)
    return _build_features(raw)


def build_audit(df: pd.DataFrame) -> dict:
    audit: dict = {"source": "WASDE TXT parsed — World Corn Supply section", "features": {}}
    if df.empty:
        audit["error"] = "no_data"
        return audit
    lag_cols = [c for c in df.columns if c.endswith("_lag1")]
    if lag_cols:
        valid = df.dropna(subset=[lag_cols[0]])
        if len(valid):
            audit["start"] = str(valid["Date"].iloc[0].date())
            audit["end"] = str(valid["Date"].iloc[-1].date())
    audit["n_rows"] = int(len(df))
    for col in lag_cols:
        s = df[col]
        audit["features"][col] = {
            "n_valid": int(s.notna().sum()),
            "nan_pct": float(s.isna().mean()),
        }
    return audit


def save_wasde_world(output_path: Path | None = None) -> Path:
    path = output_path or _AUDIT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)

    df = build_wasde_world_features()
    if not df.empty:
        df.to_parquet(_OUTPUT_DIR / "wasde_world_features.parquet", index=False)

    audit = build_audit(df)
    audit["note"] = (
        "WASDE TXT World Corn Supply and Use (monde, UE, Ukraine, Brésil, Argentine, Chine). "
        "Datage = publication ESMIS réelle puis shift(1). Stock/use = ending / domestic total."
    )

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(audit, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_wasde_world()
    print(f"WASDE world audit saved → {out}")

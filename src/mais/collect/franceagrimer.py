"""DATA-EU-03 — Collecteur FranceAgriMer / Agreste.

Source : Eurostat apro_cpsh1 — production maïs France (annuel).
Note : FranceAgriMer bilans mensuels disponibles sur data.gouv.fr mais
       pas d'API structurée — utilisation d'Eurostat comme source primaire.
Anti-leakage : publication annuelle (Nov N) → shift(1) + forward-fill.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

_RAW_DIR = Path(__file__).parents[3] / "data" / "raw" / "franceagrimer"
_AUDIT_OUTPUT = ARTEFACTS_DIR / "ema_study" / "franceagrimer_audit.json"

_EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/apro_cpsh1"
_CORN_CODE = "C1500"

_QUERIES = {
    "fr_mais_production_kt": f"{_EUROSTAT_BASE}/A.{_CORN_CODE}.HPRD_HUMD_EU_THS_T.FR?format=JSON&lang=EN&sinceTimePeriod=2000",
    "ro_mais_production_kt": f"{_EUROSTAT_BASE}/A.{_CORN_CODE}.HPRD_HUMD_EU_THS_T.RO?format=JSON&lang=EN&sinceTimePeriod=2000",
    "hu_mais_production_kt": f"{_EUROSTAT_BASE}/A.{_CORN_CODE}.HPRD_HUMD_EU_THS_T.HU?format=JSON&lang=EN&sinceTimePeriod=2000",
}


def _fetch_eurostat_series(url: str, col: str) -> pd.Series:
    try:
        import requests
    except ImportError:
        return pd.Series(dtype=float)
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return pd.Series(dtype=float)
    time_index = data.get("dimension", {}).get("time", {}).get("category", {}).get("index", {})
    values = data.get("value", {})
    if not time_index or not values:
        return pd.Series(dtype=float)
    idx_to_year = {v: int(k) for k, v in time_index.items()}
    result = {idx_to_year[int(k)]: float(v) for k, v in values.items() if int(k) in idx_to_year}
    return pd.Series(result, name=col)


def build_franceagrimer_features(out_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = out_dir or _RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    series = {}
    for col, url in _QUERIES.items():
        s = _fetch_eurostat_series(url, col)
        if not s.empty:
            series[col] = s

    if not series:
        parquet = raw_dir / "franceagrimer_raw.parquet"
        if parquet.exists():
            annual = pd.read_parquet(parquet)
        else:
            return pd.DataFrame()
    else:
        annual = pd.DataFrame(series).reset_index().rename(columns={"index": "year"})
        annual.to_parquet(raw_dir / "franceagrimer_raw.parquet", index=False)

    annual = annual.sort_values("year").reset_index(drop=True)

    # Compute anomalies and ratios
    if "fr_mais_production_kt" in annual.columns:
        mu = annual["fr_mais_production_kt"].expanding(min_periods=3).mean()
        annual["fr_mais_prod_anomaly"] = annual["fr_mais_production_kt"] - mu
        annual["fr_mais_prod_yoy_pct"] = annual["fr_mais_production_kt"].pct_change() * 100

    # EU3 production share (FR+RO+HU as fraction of EU production)
    if all(c in annual.columns for c in ["fr_mais_production_kt", "ro_mais_production_kt", "hu_mais_production_kt"]):
        annual["fr_ro_hu_mais_total_kt"] = (
            annual["fr_mais_production_kt"].fillna(0)
            + annual["ro_mais_production_kt"].fillna(0)
            + annual["hu_mais_production_kt"].fillna(0)
        )

    # Publication date = November 15 of harvest year (Eurostat annual)
    feat_cols = ["fr_mais_production_kt", "ro_mais_production_kt", "hu_mais_production_kt",
                 "fr_mais_prod_anomaly", "fr_mais_prod_yoy_pct", "fr_ro_hu_mais_total_kt"]
    feat_cols = [c for c in feat_cols if c in annual.columns]

    rows = []
    for _, row in annual.iterrows():
        pub_date = pd.Timestamp(f"{int(row['year'])}-11-15")
        r_dict = {"Date": pub_date}
        for col in feat_cols:
            r_dict[col] = row.get(col)
        rows.append(r_dict)

    pub_df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    date_range = pd.DataFrame({"Date": pd.date_range("2000-01-01", pd.Timestamp.now().normalize())})
    merged = date_range.merge(pub_df, on="Date", how="left")
    for col in feat_cols:
        if col in merged.columns:
            merged[col] = merged[col].ffill()

    # Anti-leakage: shift(1)
    out_cols = ["Date"]
    for col in feat_cols:
        if col in merged.columns:
            merged[f"{col}_lag1"] = merged[col].shift(1)
            out_cols.append(f"{col}_lag1")

    return merged[out_cols]


def build_audit(df: pd.DataFrame) -> dict:
    audit: dict = {"source": "Eurostat apro_cpsh1 FR+RO+HU maïs grain (annuel)", "features": {}}
    if df.empty:
        audit["error"] = "no_data"
        return audit
    audit["n_rows"] = int(len(df))
    lag_cols = [c for c in df.columns if c.endswith("_lag1")]
    if lag_cols:
        valid = df.dropna(subset=[lag_cols[0]])
        if len(valid):
            audit["start"] = str(valid["Date"].iloc[0].date())
            audit["end"] = str(valid["Date"].iloc[-1].date())
    for col in lag_cols:
        s = df[col]
        audit["features"][col] = {
            "n_valid": int(s.notna().sum()),
            "nan_pct": float(s.isna().mean()),
        }
    return audit


def save_franceagrimer(output_path: Path | None = None) -> Path:
    path = output_path or _AUDIT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)

    df = build_franceagrimer_features()
    if not df.empty:
        df.to_parquet(_RAW_DIR / "franceagrimer_monthly.parquet", index=False)

    audit = build_audit(df)
    audit["note"] = (
        "Eurostat apro_cpsh1 France+Roumanie+Hongrie maïs grain (annuel). "
        "FranceAgriMer bilans mensuels (data.gouv.fr) non parsés automatiquement — API non structurée. "
        "Publication ~Nov 15. Anti-leakage shift(1)."
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
    out = save_franceagrimer()
    print(f"FranceAgriMer audit saved → {out}")

"""DATA-EU-01 — Collecteur EC MARS (Eurostat apro_cpsh1).

Source : Eurostat apro_cpsh1 — production/rendement maïs grain EU.
Code maïs grain : C1500 (Grain maize and corn-cob-mix).
Accès via SDMX 2.1 REST API, sans authentification.
Anti-leakage : publication annuelle (automne N) → shift(1) + forward-fill.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

_RAW_DIR = Path(__file__).parents[3] / "data" / "raw" / "ec_mars"
_AUDIT_OUTPUT = ARTEFACTS_DIR / "ema_study" / "ec_mars_audit.json"

_EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/apro_cpsh1"
_CORN_CODE = "C1500"

_QUERIES: dict[str, str] = {
    "production_eu_kt": f"{_EUROSTAT_BASE}/A.{_CORN_CODE}.HPRD_HUMD_EU_THS_T.EU27_2020?format=JSON&lang=EN&sinceTimePeriod=2000",
}


def _fetch_series(url: str, col: str) -> pd.Series:
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


def build_ec_mars_features(out_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = out_dir or _RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    series = {}
    for col, url in _QUERIES.items():
        s = _fetch_series(url, col)
        if not s.empty:
            series[col] = s

    if not series:
        parquet_path = raw_dir / "ec_mars_eurostat_raw.parquet"
        if parquet_path.exists():
            annual = pd.read_parquet(parquet_path)
        else:
            return pd.DataFrame()
    else:
        annual = pd.DataFrame(series).reset_index().rename(columns={"index": "year"})
        annual.to_parquet(raw_dir / "ec_mars_eurostat_raw.parquet", index=False)

    if "year" not in annual.columns:
        return pd.DataFrame()

    annual = annual.sort_values("year").reset_index(drop=True)

    if "production_eu_kt" in annual.columns:
        mu = annual["production_eu_kt"].expanding(min_periods=3).mean()
        annual["ec_mars_prod_anomaly_eu"] = annual["production_eu_kt"] - mu
        annual["ec_mars_prod_yoy_pct"] = annual["production_eu_kt"].pct_change() * 100

    # Publication date = November 15 of the harvest year
    rows = []
    for _, row in annual.iterrows():
        pub_date = pd.Timestamp(f"{int(row['year'])}-11-15")
        rows.append({
            "Date": pub_date,
            "ec_mars_production_eu_kt": row.get("production_eu_kt"),
            "ec_mars_prod_anomaly_eu": row.get("ec_mars_prod_anomaly_eu"),
            "ec_mars_prod_yoy_pct": row.get("ec_mars_prod_yoy_pct"),
        })

    pub_df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)

    # Forward-fill to daily calendar (known from pub date)
    date_range = pd.DataFrame({
        "Date": pd.date_range("2000-01-01", pd.Timestamp.now().normalize())
    })
    merged = date_range.merge(pub_df, on="Date", how="left")
    feat_cols = ["ec_mars_production_eu_kt", "ec_mars_prod_anomaly_eu", "ec_mars_prod_yoy_pct"]
    for col in feat_cols:
        if col in merged.columns:
            merged[col] = merged[col].ffill()

    # Anti-leakage: shift(1) — rename with _lag1
    out_cols = ["Date"]
    for col in feat_cols:
        if col in merged.columns:
            merged[f"{col}_lag1"] = merged[col].shift(1)
            out_cols.append(f"{col}_lag1")

    return merged[out_cols].dropna(subset=["Date"])


def build_audit(df: pd.DataFrame) -> dict:
    audit: dict = {"source": "Eurostat apro_cpsh1 (C1500 grain maize EU27)", "features": {}}
    if df.empty:
        audit["error"] = "no_data_collected"
        return audit
    audit["n_rows"] = int(len(df))
    lag_cols = [c for c in df.columns if c.endswith("_lag1")]
    if lag_cols and len(df.dropna(subset=[lag_cols[0]])):
        valid = df.dropna(subset=[lag_cols[0]])
        audit["start"] = str(valid["Date"].iloc[0].date())
        audit["end"] = str(valid["Date"].iloc[-1].date())
    for col in lag_cols:
        s = df[col]
        audit["features"][col] = {
            "n_valid": int(s.notna().sum()),
            "nan_pct": float(s.isna().mean()),
        }
    return audit


def save_ec_mars(output_path: Path | None = None) -> Path:
    path = output_path or _AUDIT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)

    df = build_ec_mars_features()
    if not df.empty:
        df.to_parquet(_RAW_DIR / "ec_mars_monthly.parquet", index=False)

    audit = build_audit(df)
    audit["note"] = (
        "Eurostat apro_cpsh1 maïs grain EU27 (annuel). "
        "Publication hypothétique Nov 15. "
        "Features forward-filled + shift(1). "
        "MARS bulletins mensuels (PDF) non parsés automatiquement."
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
    out = save_ec_mars()
    print(f"EC MARS audit saved → {out}")

"""DATA-EU-04 — ETS CO₂ et TTF enrichi.

TTF=F via yfinance : disponible depuis 2017-10.
CO2.L (ICE EUA futures) via yfinance : disponible depuis 2021-10.
Toutes les features sont shift(1) — anti-leakage obligatoire.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

_RAW_DIR = Path(__file__).parents[3] / "data" / "raw" / "eu_carbon"
_AUDIT_OUTPUT = ARTEFACTS_DIR / "ema_study" / "eu_carbon_audit.json"

_TICKERS = {
    "TTF=F": "ttf_eur_mwh",
    "CO2.L": "ets_co2_eur_t",
}


def _download_yf(ticker: str, col: str, start: str = "2010-01-01") -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as e:
        raise RuntimeError("yfinance not installed") from e
    df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if df.empty:
        return pd.DataFrame(columns=["Date", col])
    close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
    out = close.reset_index()
    out.columns = ["Date", col]
    out["Date"] = pd.to_datetime(out["Date"]).dt.tz_localize(None)
    return out.sort_values("Date").reset_index(drop=True)


def _expanding_zscore(series: pd.Series, min_periods: int = 52) -> pd.Series:
    mu = series.expanding(min_periods=min_periods).mean().shift(1)
    sigma = series.expanding(min_periods=min_periods).std().shift(1)
    return (series - mu) / sigma.replace(0, np.nan)


def build_eu_carbon_features(out_dir: Path | None = None) -> pd.DataFrame:
    """Collecte TTF et ETS CO₂, calcule features avec anti-leakage shift(1)."""
    raw_dir = out_dir or _RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for ticker, col in _TICKERS.items():
        df = _download_yf(ticker, col)
        if not df.empty:
            df.to_parquet(raw_dir / f"{col}.parquet", index=False)
        frames.append(df)

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="Date", how="outer")
    merged = merged.sort_values("Date").reset_index(drop=True)

    ttf_col = "ttf_eur_mwh"
    co2_col = "ets_co2_eur_t"

    if ttf_col in merged.columns:
        merged["ttf_return_1d"] = merged[ttf_col].pct_change().shift(1)
        merged["ttf_zscore_52w"] = _expanding_zscore(merged[ttf_col])
    if co2_col in merged.columns:
        merged["ets_co2_return_1d"] = merged[co2_col].pct_change().shift(1)
        merged["ets_co2_zscore_52w"] = _expanding_zscore(merged[co2_col])

    return merged


def build_audit(df: pd.DataFrame) -> dict:
    audit: dict = {}
    for col in ["ttf_eur_mwh", "ets_co2_eur_t", "ttf_zscore_52w", "ets_co2_zscore_52w"]:
        if col not in df.columns:
            audit[col] = {"available": False}
            continue
        mask = df[col].notna()
        s_dates = df.loc[mask, "Date"]
        audit[col] = {
            "available": True,
            "n": int(mask.sum()),
            "start": str(s_dates.iloc[0].date()) if len(s_dates) else None,
            "end": str(s_dates.iloc[-1].date()) if len(s_dates) else None,
            "nan_pct": float(df[col].isna().mean()),
        }
    return audit


def save_eu_carbon(output_path: Path | None = None) -> Path:
    path = output_path or _AUDIT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)

    df = build_eu_carbon_features()
    df.to_parquet(_RAW_DIR / "eu_carbon_features.parquet", index=False)

    audit = build_audit(df)
    audit["note"] = "TTF=F depuis 2017-10; CO2.L depuis 2021-10 via yfinance. Anti-leakage shift(1) appliqué."

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
    out = save_eu_carbon()
    print(f"EU carbon audit saved → {out}")

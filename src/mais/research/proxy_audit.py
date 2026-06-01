"""Audit CBOT-derived proxy prices against real/exploratory EMA prices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, EMA_FRONT_RAW, RAW_DIR

PROXY_VS_REAL_EMA_REPORT = ARTEFACTS_DIR / "proxy_vs_real_ema_report.json"
DEFAULT_PROXY_PATH = RAW_DIR / "euronext_ema" / "euronext_ema.csv"
PROXY_COLUMNS = ("is_proxy", "ema_is_proxy")


def compare_proxy_vs_real(proxy: pd.DataFrame, real: pd.DataFrame) -> dict[str, Any]:
    """Compare a CBOT-derived EMA proxy against real/exploratory EMA prices."""
    proxy_norm = _normalise_price_frame(proxy, price_name="proxy_price")
    real_norm = _normalise_price_frame(real, price_name="real_price")
    merged = proxy_norm.merge(real_norm, on="Date", how="inner").dropna(
        subset=["proxy_price", "real_price"]
    )
    if merged.empty:
        return {
            "n_overlap": 0,
            "verdict": "INCONCLU",
            "reason": "no overlapping non-null proxy/real prices",
            "proxy_allowed_in_benchmark": False,
        }
    spread = merged["proxy_price"] - merged["real_price"]
    abs_spread = spread.abs()
    spread_std = float(spread.std()) if len(spread) > 1 else 0.0
    threshold = 2.0 * spread_std
    extreme = merged.loc[abs_spread > threshold, ["Date", "proxy_price", "real_price"]].copy()
    extreme["spread_proxy_minus_real_eur_t"] = spread.loc[extreme.index]
    extreme["abs_spread_eur_t"] = abs_spread.loc[extreme.index]
    corr = merged["proxy_price"].corr(merged["real_price"])
    payload = {
        "n_overlap": int(len(merged)),
        "date_start": merged["Date"].min().date().isoformat(),
        "date_end": merged["Date"].max().date().isoformat(),
        "correlation": _json_float(corr),
        "mae_eur_t": float(abs_spread.mean()),
        "rmse_eur_t": float(np.sqrt(np.mean(np.square(spread)))),
        "spread_proxy_minus_real_mean_eur_t": float(spread.mean()),
        "spread_proxy_minus_real_std_eur_t": spread_std,
        "pct_periods_abs_spread_gt_2sigma": float((abs_spread > threshold).mean()) if threshold > 0 else 0.0,
        "extreme_periods": [
            {
                "Date": row["Date"].date().isoformat(),
                "proxy_price": float(row["proxy_price"]),
                "real_price": float(row["real_price"]),
                "spread_proxy_minus_real_eur_t": float(row["spread_proxy_minus_real_eur_t"]),
                "abs_spread_eur_t": float(row["abs_spread_eur_t"]),
            }
            for _, row in extreme.head(50).iterrows()
        ],
        "proxy_allowed_in_benchmark": False,
        "exclusion_rule": "Any row with is_proxy=True or ema_is_proxy=True must be excluded from model benchmarks.",
        "verdict": "PROXY_FORBIDDEN",
    }
    return payload


def assert_no_proxy_in_benchmark(
    features: pd.DataFrame,
    signals: pd.DataFrame | None = None,
) -> None:
    """Raise if proxy rows are included in a benchmark frame."""
    offenders: dict[str, int] = {}
    for name, frame in {"features": features, "signals": signals}.items():
        if frame is None:
            continue
        for col in PROXY_COLUMNS:
            if col in frame.columns:
                count = int(pd.Series(frame[col]).fillna(False).astype(bool).sum())
                if count:
                    offenders[f"{name}.{col}"] = count
    if offenders:
        raise ValueError(f"Proxy EMA rows are forbidden in benchmarks: {offenders}")


def run_proxy_audit(
    *,
    proxy_path: Path = DEFAULT_PROXY_PATH,
    real_path: Path = EMA_FRONT_RAW,
    output_path: Path = PROXY_VS_REAL_EMA_REPORT,
) -> dict[str, Any]:
    """Load default proxy/real series, compare and write report JSON."""
    proxy = _read_frame(proxy_path)
    real = _read_frame(real_path)
    report = compare_proxy_vs_real(proxy, real)
    report["proxy_path"] = str(proxy_path)
    report["real_path"] = str(real_path)
    report["real_source_note"] = "EMA real series currently uses barchart_proxy_exploratory where applicable."
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _read_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _normalise_price_frame(frame: pd.DataFrame, *, price_name: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Date", price_name])
    work = frame.copy()
    if "Date" not in work.columns and "date" in work.columns:
        work["Date"] = work["date"]
    if "Date" not in work.columns:
        raise ValueError("price frame requires Date or date column")
    price_col = _first_col(work, ["ema_close", "price", "settlement", "close_or_last", "close", "last"])
    if price_col is None:
        raise ValueError("price frame requires a known price column")
    out = pd.DataFrame({
        "Date": pd.to_datetime(work["Date"]).dt.normalize(),
        price_name: pd.to_numeric(work[price_col], errors="coerce"),
    })
    return out.drop_duplicates("Date", keep="last").sort_values("Date").reset_index(drop=True)


def _first_col(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((col for col in candidates if col in frame.columns), None)


def _json_float(value: float) -> float | None:
    return float(value) if pd.notna(value) and np.isfinite(value) else None

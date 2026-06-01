"""CBOT corn futures curve diagnostics and collection helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.futures_curve")

MONTH_CODES = ["Z", "H", "K", "N"]


def build_cbot_symbol(month_code: str, year: int, provider: str = "yfinance") -> str:
    """Build a provider-specific CBOT corn contract symbol."""
    code = month_code.upper()
    if code not in MONTH_CODES:
        raise ValueError(f"Unsupported CBOT corn month code: {month_code}")
    yy = str(int(year))[-2:]
    provider_key = provider.lower()
    if provider_key in {"yfinance", "yahoo"}:
        return f"ZC{code}{yy}.CBT"
    if provider_key in {"barchart", "generic"}:
        return f"ZC{code}{yy}"
    if provider_key == "quandl":
        return f"CHRIS/CME_C{code}{yy}"
    raise ValueError(f"Unsupported futures provider: {provider}")


def diagnose_futures_curve_quality(
    *,
    start_year: int = 2010,
    end_year: int = 2022,
    provider: str = "yfinance",
    expected_trading_days: int = 252,
) -> dict[str, Any]:
    """Return coverage/coherence diagnostics by contract/year."""
    try:
        import yfinance as yf
    except ImportError:
        return {
            "provider": provider,
            "status": "INCONCLU",
            "reason": "yfinance not installed",
            "coverage_mean": None,
            "contracts": {},
        }

    contracts: dict[str, Any] = {}
    coverages: list[float] = []
    for year in range(start_year, end_year + 1):
        for month_code in MONTH_CODES:
            symbol = build_cbot_symbol(month_code, year, provider)
            try:
                data = yf.download(symbol, period="max", interval="1d", auto_adjust=False, progress=False, threads=False)
                close = _close_series(data)
                coverage = float(close.dropna().shape[0] / expected_trading_days)
                coherent = bool(check_no_outliers(close))
                continuous = bool(check_price_continuity_around_expiry(close))
            except Exception as exc:
                coverage = 0.0
                coherent = False
                continuous = False
                contracts[symbol] = {"coverage": coverage, "price_coherent": coherent, "roll_continuity": continuous, "error": str(exc)}
                continue
            contracts[symbol] = {"coverage": coverage, "price_coherent": coherent, "roll_continuity": continuous}
            coverages.append(coverage)

    coverage_mean = float(np.mean(coverages)) if coverages else 0.0
    broken_continuity = sum(1 for row in contracts.values() if not row["roll_continuity"])
    status = "OK" if coverage_mean >= 0.80 and broken_continuity <= 3 else "INCONCLU"
    return {
        "provider": provider,
        "status": status,
        "coverage_mean": coverage_mean,
        "broken_continuity_count": int(broken_continuity),
        "contracts": contracts,
    }


def check_no_outliers(close: pd.Series) -> bool:
    """Basic sanity check for impossible or explosive close prices."""
    values = pd.to_numeric(close, errors="coerce").dropna()
    if values.empty:
        return False
    if (values <= 0).any():
        return False
    returns = values.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    return bool((returns.abs() < 0.50).mean() >= 0.99) if not returns.empty else True


def check_price_continuity_around_expiry(close: pd.Series) -> bool:
    """Detect severe daily jumps indicating bad contract stitching."""
    values = pd.to_numeric(close, errors="coerce").dropna()
    if len(values) < 20:
        return False
    jumps = values.pct_change().abs().dropna()
    return bool((jumps > 0.35).sum() <= 1)


def download(out_dir: Path, src: dict) -> str:
    """Run the diagnostic and write a JSON report.

    This ticket deliberately does not force full integration unless quality is
    good enough; collection of long historical contracts is provider-sensitive.
    """
    import json

    provider = str(src.get("provider_name", "yfinance"))
    report = diagnose_futures_curve_quality(provider=provider)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "futures_curve_diagnostic.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return f"diagnostic {report['status']}, coverage={report.get('coverage_mean')}"


def _close_series(data: pd.DataFrame) -> pd.Series:
    if data is None or data.empty:
        return pd.Series(dtype=float)
    if isinstance(data.columns, pd.MultiIndex):
        data = data.droplevel(1, axis=1)
    close_col = "Close" if "Close" in data.columns else "close"
    if close_col not in data.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(data[close_col], errors="coerce")

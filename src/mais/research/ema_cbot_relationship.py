"""EMA/CBOT relationship, lead-lag and optional Granger diagnostics."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import (
    ARTEFACTS_DIR,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    INTERIM_DIR,
    PROJECT_ROOT,
    RAW_DIR,
)
from mais.research.ema_data_audit import SOURCE_QUALITY_NOTE

BUSHEL_TO_TONNE = 39.3679
EMA_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
EMA_CBOT_RELATIONSHIP_JSON = EMA_STUDY_DIR / "ema_cbot_relationship.json"
EMA_CBOT_RELATIONSHIP_MD = PROJECT_ROOT / "docs" / "EMA_CBOT_RELATIONSHIP.md"
DEFAULT_CBOT_PATH = INTERIM_DIR / "database.parquet"
DEFAULT_EURUSD_PATH = RAW_DIR / "eu_cross_assets" / "eu_cross_assets.csv"


def run_ema_cbot_relationship_study(
    *,
    ema_front_raw_path: Path = EMA_FRONT_RAW,
    ema_front_adjusted_path: Path = EMA_FRONT_ADJUSTED,
    cbot_path: Path = DEFAULT_CBOT_PATH,
    eurusd_path: Path = DEFAULT_EURUSD_PATH,
    output_json_path: Path = EMA_CBOT_RELATIONSHIP_JSON,
    output_markdown_path: Path = EMA_CBOT_RELATIONSHIP_MD,
    max_lag: int = 10,
    rolling_window: int = 60,
    granger_maxlag: int = 5,
) -> dict[str, Any]:
    """Run EMA/CBOT statistical relationship diagnostics."""
    frame = build_relationship_frame(
        ema_front_raw_path=ema_front_raw_path,
        ema_front_adjusted_path=ema_front_adjusted_path,
        cbot_path=cbot_path,
        eurusd_path=eurusd_path,
    )
    lead_lag = lead_lag_correlations(frame, max_lag=max_lag)
    rolling = rolling_relationship_summary(frame, window=rolling_window)
    granger = granger_diagnostics(frame, maxlag=granger_maxlag)
    payload = {
        "source_quality_note": SOURCE_QUALITY_NOTE,
        "n_rows": int(len(frame)),
        "date_start": _date_min(frame),
        "date_end": _date_max(frame),
        "price_relationship": price_relationship_summary(frame),
        "lead_lag": lead_lag,
        "rolling_relationship": rolling,
        "granger": granger,
        "interpretation": interpret_relationship(lead_lag, granger),
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def build_relationship_frame(
    *,
    ema_front_raw_path: Path,
    ema_front_adjusted_path: Path,
    cbot_path: Path,
    eurusd_path: Path,
) -> pd.DataFrame:
    """Build an aligned EMA front / CBOT EUR-t relationship frame."""
    raw = _read_frame(ema_front_raw_path)
    adjusted = _read_frame(ema_front_adjusted_path)
    cbot = _read_frame(cbot_path)
    eurusd = _read_frame(eurusd_path)

    ema_raw = _series_price(raw, "ema_price_raw", candidates=("price", "close_or_last", "settlement"))
    ema_adjusted = _series_price(adjusted, "ema_price_adjusted", candidates=("adjusted_price", "price"))
    cbot_price = _series_price(cbot, "corn_close", candidates=("corn_close", "cbot_cents_bu", "cbot_corn_close"))
    fx = _series_price(eurusd, "eurusd_rate", candidates=("eurusd_rate", "EURUSD", "close", "Close"))

    work = (
        ema_raw.merge(ema_adjusted, on="Date", how="outer")
        .merge(cbot_price, on="Date", how="inner")
        .merge(fx, on="Date", how="inner")
        .sort_values("Date")
        .reset_index(drop=True)
    )
    work["cbot_eur_t"] = (
        pd.to_numeric(work["corn_close"], errors="coerce") / 100.0
    ) / pd.to_numeric(work["eurusd_rate"], errors="coerce").replace(0, np.nan) * BUSHEL_TO_TONNE
    work["ema_cbot_basis"] = pd.to_numeric(work["ema_price_raw"], errors="coerce") - work["cbot_eur_t"]
    work["ema_cbot_basis_z_260"] = rolling_zscore(work["ema_cbot_basis"], window=260)
    work["ema_logret_1d"] = np.log(
        pd.to_numeric(work["ema_price_adjusted"], errors="coerce")
        / pd.to_numeric(work["ema_price_adjusted"], errors="coerce").shift(1)
    )
    work["cbot_eur_logret_1d"] = np.log(work["cbot_eur_t"] / work["cbot_eur_t"].shift(1))
    work["cbot_usd_logret_1d"] = np.log(
        pd.to_numeric(work["corn_close"], errors="coerce")
        / pd.to_numeric(work["corn_close"], errors="coerce").shift(1)
    )
    return work.replace([np.inf, -np.inf], np.nan)


def price_relationship_summary(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize EMA/CBOT price levels and basis."""
    pair = frame[["ema_price_raw", "cbot_eur_t", "ema_cbot_basis"]].dropna()
    returns = frame[["ema_logret_1d", "cbot_eur_logret_1d"]].dropna()
    return {
        "n_price_overlap": int(len(pair)),
        "price_corr": _json_float(pair["ema_price_raw"].corr(pair["cbot_eur_t"])) if len(pair) else None,
        "basis_mean_eur_t": _json_float(pair["ema_cbot_basis"].mean()) if len(pair) else None,
        "basis_std_eur_t": _json_float(pair["ema_cbot_basis"].std()) if len(pair) else None,
        "basis_min_eur_t": _json_float(pair["ema_cbot_basis"].min()) if len(pair) else None,
        "basis_max_eur_t": _json_float(pair["ema_cbot_basis"].max()) if len(pair) else None,
        "n_return_overlap": int(len(returns)),
        "return_corr_1d": _json_float(returns["ema_logret_1d"].corr(returns["cbot_eur_logret_1d"]))
        if len(returns)
        else None,
    }


def lead_lag_correlations(frame: pd.DataFrame, *, max_lag: int = 10) -> dict[str, Any]:
    """Compute corr(EMA return t, CBOT return t+k) for k in [-max_lag, max_lag]."""
    rows: list[dict[str, Any]] = []
    ema = pd.to_numeric(frame["ema_logret_1d"], errors="coerce")
    cbot = pd.to_numeric(frame["cbot_eur_logret_1d"], errors="coerce")
    for lag in range(-int(max_lag), int(max_lag) + 1):
        shifted_cbot = cbot.shift(-lag)
        pair = pd.DataFrame({"ema": ema, "cbot": shifted_cbot}).dropna()
        corr = pair["ema"].corr(pair["cbot"]) if len(pair) >= 20 else np.nan
        rows.append(
            {
                "lag": int(lag),
                "meaning": _lag_meaning(lag),
                "n": int(len(pair)),
                "corr_ema_t_cbot_t_plus_lag": _json_float(corr),
            }
        )
    valid = [row for row in rows if row["corr_ema_t_cbot_t_plus_lag"] is not None]
    best_abs = max(valid, key=lambda row: abs(float(row["corr_ema_t_cbot_t_plus_lag"])), default=None)
    best_ema_leads = max(
        [row for row in valid if int(row["lag"]) > 0],
        key=lambda row: abs(float(row["corr_ema_t_cbot_t_plus_lag"])),
        default=None,
    )
    best_cbot_leads = max(
        [row for row in valid if int(row["lag"]) < 0],
        key=lambda row: abs(float(row["corr_ema_t_cbot_t_plus_lag"])),
        default=None,
    )
    contemporaneous = next((row for row in rows if row["lag"] == 0), None)
    return {
        "max_lag": int(max_lag),
        "definition": "corr(EMA adjusted return at t, CBOT EUR/t return at t+lag). Positive lag means EMA leads CBOT.",
        "rows": rows,
        "contemporaneous": contemporaneous,
        "best_abs": best_abs,
        "best_ema_leads": best_ema_leads,
        "best_cbot_leads": best_cbot_leads,
    }


def rolling_relationship_summary(frame: pd.DataFrame, *, window: int = 60) -> dict[str, Any]:
    """Summarize rolling return correlation."""
    returns = frame[["Date", "ema_logret_1d", "cbot_eur_logret_1d"]].copy()
    corr = returns["ema_logret_1d"].rolling(window, min_periods=max(20, window // 2)).corr(
        returns["cbot_eur_logret_1d"]
    )
    valid = corr.dropna()
    return {
        "window": int(window),
        "n_non_null": int(len(valid)),
        "mean_corr": _json_float(valid.mean()) if len(valid) else None,
        "median_corr": _json_float(valid.median()) if len(valid) else None,
        "min_corr": _json_float(valid.min()) if len(valid) else None,
        "max_corr": _json_float(valid.max()) if len(valid) else None,
        "share_positive": _json_float((valid > 0).mean()) if len(valid) else None,
    }


def granger_diagnostics(frame: pd.DataFrame, *, maxlag: int = 5) -> dict[str, Any]:
    """Run optional Granger diagnostics if statsmodels is installed."""
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        return {"status": "SKIPPED", "reason": f"statsmodels unavailable: {exc}"}

    data = frame[["ema_logret_1d", "cbot_eur_logret_1d", "ema_cbot_basis_z_260"]].dropna()
    if len(data) < max(100, int(maxlag) * 20):
        return {"status": "SKIPPED", "reason": "not enough complete rows", "n": int(len(data))}
    return {
        "status": "OK",
        "maxlag": int(maxlag),
        "n": int(len(data)),
        "ema_returns_to_cbot_returns": _run_granger(
            grangercausalitytests,
            data[["cbot_eur_logret_1d", "ema_logret_1d"]],
            maxlag=maxlag,
        ),
        "cbot_returns_to_ema_returns": _run_granger(
            grangercausalitytests,
            data[["ema_logret_1d", "cbot_eur_logret_1d"]],
            maxlag=maxlag,
        ),
        "basis_to_ema_returns": _run_granger(
            grangercausalitytests,
            data[["ema_logret_1d", "ema_cbot_basis_z_260"]],
            maxlag=maxlag,
        ),
        "basis_to_cbot_returns": _run_granger(
            grangercausalitytests,
            data[["cbot_eur_logret_1d", "ema_cbot_basis_z_260"]],
            maxlag=maxlag,
        ),
    }


def interpret_relationship(lead_lag: dict[str, Any], granger: dict[str, Any]) -> dict[str, Any]:
    """Produce a cautious interpretation of the relationship diagnostics."""
    contemporaneous = lead_lag.get("contemporaneous") or {}
    ema_leads = lead_lag.get("best_ema_leads") or {}
    cbot_leads = lead_lag.get("best_cbot_leads") or {}
    c0 = _safe_float(contemporaneous.get("corr_ema_t_cbot_t_plus_lag"))
    clead = abs(_safe_float(ema_leads.get("corr_ema_t_cbot_t_plus_lag")))
    cback = abs(_safe_float(cbot_leads.get("corr_ema_t_cbot_t_plus_lag")))
    lead_verdict = "mostly_contemporaneous"
    if math.isfinite(clead) and math.isfinite(cback):
        if clead >= cback + 0.03 and clead >= abs(c0) + 0.02:
            lead_verdict = "ema_leads_cbot_candidate"
        elif cback >= clead + 0.03 and cback >= abs(c0) + 0.02:
            lead_verdict = "cbot_leads_ema_candidate"
    granger_summary = _granger_summary(granger)
    return {
        "lead_lag_verdict": lead_verdict,
        "granger_summary": granger_summary,
        "caution": "Granger and lead-lag diagnostics are exploratory and do not prove causality.",
        "next_step": "Run basis mean-reversion study on basis z-score regimes.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the EMA/CBOT relationship report."""
    price = payload["price_relationship"]
    lead_lag = payload["lead_lag"]
    rolling = payload["rolling_relationship"]
    granger = payload["granger"]
    interpretation = payload["interpretation"]
    lines = [
        "# EMA / CBOT Relationship",
        "",
        f"> {payload['source_quality_note']}",
        "",
        "## Dataset",
        "",
        f"- Rows: {payload['n_rows']}",
        f"- Period: {payload['date_start']} -> {payload['date_end']}",
        f"- Price overlap: {price.get('n_price_overlap')}",
        "",
        "## Level And Basis",
        "",
        f"- Price correlation EMA vs CBOT EUR/t: {_fmt(price.get('price_corr'))}",
        f"- 1d return correlation: {_fmt(price.get('return_corr_1d'))}",
        f"- Basis mean: {_fmt(price.get('basis_mean_eur_t'))} EUR/t",
        f"- Basis std: {_fmt(price.get('basis_std_eur_t'))} EUR/t",
        f"- Basis range: {_fmt(price.get('basis_min_eur_t'))} -> {_fmt(price.get('basis_max_eur_t'))} EUR/t",
        "",
        "## Lead-Lag",
        "",
        f"- Definition: {lead_lag['definition']}",
        f"- Contemporaneous: {_lag_line(lead_lag.get('contemporaneous'))}",
        f"- Best EMA leads: {_lag_line(lead_lag.get('best_ema_leads'))}",
        f"- Best CBOT leads: {_lag_line(lead_lag.get('best_cbot_leads'))}",
        f"- Verdict: `{interpretation.get('lead_lag_verdict')}`",
        "",
        "## Rolling Correlation",
        "",
        f"- Window: {rolling.get('window')} days",
        f"- Mean: {_fmt(rolling.get('mean_corr'))}",
        f"- Median: {_fmt(rolling.get('median_corr'))}",
        f"- Range: {_fmt(rolling.get('min_corr'))} -> {_fmt(rolling.get('max_corr'))}",
        f"- Share positive: {_pct(rolling.get('share_positive'))}",
        "",
        "## Granger",
        "",
        f"- Status: `{granger.get('status')}`",
        *_granger_lines(granger),
        "",
        "## Interpretation",
        "",
        f"- {interpretation.get('caution')}",
        f"- Next step: {interpretation.get('next_step')}",
        "",
    ]
    return "\n".join(lines)


def rolling_zscore(series: pd.Series, *, window: int) -> pd.Series:
    """Rolling z-score with conservative min periods."""
    values = pd.to_numeric(series, errors="coerce")
    mean = values.rolling(window, min_periods=max(20, window // 4)).mean()
    std = values.rolling(window, min_periods=max(20, window // 4)).std().replace(0, np.nan)
    return (values - mean) / std


def _run_granger(granger_func: Any, data: pd.DataFrame, *, maxlag: int) -> dict[str, Any]:
    try:
        result = granger_func(data, maxlag=int(maxlag), verbose=False)
    except TypeError:
        result = granger_func(data, maxlag=int(maxlag), verbose=False)
    except Exception as exc:
        return {"status": "FAILED", "reason": str(exc)}
    rows: list[dict[str, Any]] = []
    for lag, tests in result.items():
        ssr_ftest = tests[0].get("ssr_ftest")
        p_value = ssr_ftest[1] if ssr_ftest is not None and len(ssr_ftest) > 1 else np.nan
        rows.append({"lag": int(lag), "p_value_ssr_ftest": _json_float(p_value)})
    valid = [row for row in rows if row["p_value_ssr_ftest"] is not None]
    best = min(valid, key=lambda row: float(row["p_value_ssr_ftest"]), default=None)
    return {
        "status": "OK",
        "rows": rows,
        "best_lag": best,
        "min_p_value": best["p_value_ssr_ftest"] if best else None,
    }


def _granger_summary(granger: dict[str, Any]) -> dict[str, Any]:
    if granger.get("status") != "OK":
        return {"status": granger.get("status"), "reason": granger.get("reason")}
    return {
        key: {
            "min_p_value": value.get("min_p_value"),
            "best_lag": value.get("best_lag", {}).get("lag") if isinstance(value.get("best_lag"), dict) else None,
        }
        for key, value in granger.items()
        if isinstance(value, dict) and key != "status"
    }


def _read_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_parquet(path)


def _series_price(frame: pd.DataFrame, output_col: str, *, candidates: tuple[str, ...]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Date", output_col])
    work = frame.copy()
    if "Date" not in work.columns and "date" in work.columns:
        work["Date"] = work["date"]
    if "Date" not in work.columns:
        raise ValueError(f"{output_col} input requires Date/date column")
    price_col = next((col for col in candidates if col in work.columns), None)
    if price_col is None:
        raise ValueError(f"{output_col} input requires one of {candidates}")
    work["Date"] = pd.to_datetime(work["Date"]).dt.tz_localize(None).dt.normalize()
    work[output_col] = pd.to_numeric(work[price_col], errors="coerce")
    return (
        work[["Date", output_col]]
        .dropna(subset=["Date"])
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )


def _lag_meaning(lag: int) -> str:
    if lag > 0:
        return "EMA leads CBOT"
    if lag < 0:
        return "CBOT leads EMA"
    return "same day"


def _lag_line(row: dict[str, Any] | None) -> str:
    if not row:
        return "N/A"
    return f"lag {row.get('lag')} ({row.get('meaning')}), corr={_fmt(row.get('corr_ema_t_cbot_t_plus_lag'))}, n={row.get('n')}"


def _granger_lines(granger: dict[str, Any]) -> list[str]:
    if granger.get("status") != "OK":
        reason = granger.get("reason")
        return [f"- Reason: {reason}"] if reason else []
    lines: list[str] = []
    for key in (
        "ema_returns_to_cbot_returns",
        "cbot_returns_to_ema_returns",
        "basis_to_ema_returns",
        "basis_to_cbot_returns",
    ):
        result = granger.get(key, {})
        lines.append(f"- `{key}`: min p={_fmt(result.get('min_p_value'))}, best lag={_best_lag(result)}")
    return lines


def _best_lag(result: dict[str, Any]) -> str:
    best = result.get("best_lag")
    if not isinstance(best, dict):
        return "N/A"
    return str(best.get("lag"))


def _date_min(frame: pd.DataFrame) -> str | None:
    if frame.empty or "Date" not in frame:
        return None
    return frame["Date"].min().date().isoformat()


def _date_max(frame: pd.DataFrame) -> str | None:
    if frame.empty or "Date" not in frame:
        return None
    return frame["Date"].max().date().isoformat()


def _fmt(value: Any) -> str:
    number = _safe_float(value)
    return "N/A" if not math.isfinite(number) else f"{number:.4f}"


def _pct(value: Any) -> str:
    number = _safe_float(value)
    return "N/A" if not math.isfinite(number) else f"{number * 100:.1f}%"


def _safe_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def _json_float(value: Any) -> float | None:
    out = _safe_float(value)
    return out if math.isfinite(out) else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float):
        return _json_float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


if __name__ == "__main__":
    report = run_ema_cbot_relationship_study()
    print(json.dumps(_json_ready(report["interpretation"]), indent=2, ensure_ascii=False))

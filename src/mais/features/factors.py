"""Economic factor engineering from raw features.

Goal: reduce 189 raw columns into an interpretable, lower-dimensional set
without adding external data sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import PROCESSED_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.features.factors")


@dataclass
class FactorBuildResult:
    factors: pd.DataFrame
    metadata: dict[str, Any]


FAMILY_ORDER = [
    "market_momentum",
    "market_volatility",
    "wasde_supply_demand",
    "weather_belt_stress",
    "macro_dollar_rates",
    "seasonality",
    "cross_commodity",
    "positioning",
    "raw_signal",
]

FACTOR_METADATA: list[dict[str, Any]] = [
    {
        "factor_name": "factor_market_momentum",
        "family": "market_momentum",
        "source_variables": "corn log returns, moving averages, MACD, RSI, drawdown",
        "economic_interpretation": "Technical price momentum and trend persistence.",
        "expected_sign": "positive",
        "expected_horizon": "h5-h20",
    },
    {
        "factor_name": "factor_market_volatility",
        "family": "market_volatility",
        "source_variables": "ATR, realized volatility, Bollinger bandwidth, volume z-scores",
        "economic_interpretation": "Risk and instability in the futures market.",
        "expected_sign": "mixed",
        "expected_horizon": "h5-h30",
    },
    {
        "factor_name": "factor_wasde_supply_demand",
        "family": "wasde_supply_demand",
        "source_variables": "WASDE stocks, use, exports, production, ethanol demand",
        "economic_interpretation": "Balance-sheet tightness and demand pressure.",
        "expected_sign": "positive_when_tight",
        "expected_horizon": "h20-h90",
    },
    {
        "factor_name": "factor_weather_belt_stress",
        "family": "weather_belt_stress",
        "source_variables": "weather, drought and crop-condition variables",
        "economic_interpretation": "Corn belt agronomic stress.",
        "expected_sign": "positive",
        "expected_horizon": "h10-h60",
    },
    {
        "factor_name": "factor_macro_dollar_rates",
        "family": "macro_dollar_rates",
        "source_variables": "DXY, USD crosses, rates, inflation and macro variables",
        "economic_interpretation": "Dollar and rate pressure on commodity prices.",
        "expected_sign": "negative",
        "expected_horizon": "h20-h90",
    },
    {
        "factor_name": "factor_seasonality",
        "family": "seasonality",
        "source_variables": "month, day-of-year and crop-calendar flags",
        "economic_interpretation": "Seasonal planting, growing and harvest effects.",
        "expected_sign": "seasonal",
        "expected_horizon": "h5-h90",
    },
    {
        "factor_name": "factor_cross_commodity",
        "family": "cross_commodity",
        "source_variables": "soybean, wheat, oil, gas and spread variables",
        "economic_interpretation": "Substitution, energy and broad commodity pressure.",
        "expected_sign": "mixed",
        "expected_horizon": "h10-h60",
    },
    {
        "factor_name": "factor_positioning",
        "family": "positioning",
        "source_variables": "CFTC COT managed money, producers, open interest",
        "economic_interpretation": "Investor positioning and crowded-trade pressure.",
        "expected_sign": "contrarian_or_momentum",
        "expected_horizon": "h5-h30",
    },
    {
        "factor_name": "factor_raw_signal",
        "family": "raw_signal",
        "source_variables": "Unclassified numeric variables retained only as grouped signal.",
        "economic_interpretation": "Residual signal bucket, monitored to avoid interpretation drift.",
        "expected_sign": "unknown",
        "expected_horizon": "diagnostic",
    },
    {
        "factor_name": "factor_drought_severity",
        "family": "weather_belt_stress",
        "source_variables": "drought_composite",
        "economic_interpretation": "Higher drought severity should raise supply-risk premium.",
        "expected_sign": "positive",
        "expected_horizon": "h10-h60",
    },
    {
        "factor_name": "factor_export_demand_surprise",
        "family": "wasde_supply_demand",
        "source_variables": "export_sales_mt",
        "economic_interpretation": "Export demand pressure versus history.",
        "expected_sign": "positive",
        "expected_horizon": "h10-h30",
    },
    {
        "factor_name": "factor_crop_condition_pressure",
        "family": "weather_belt_stress",
        "source_variables": "condition_gd_ex_pct",
        "economic_interpretation": "Poorer crop condition should increase bullish supply risk.",
        "expected_sign": "positive",
        "expected_horizon": "h10-h60",
    },
    {
        "factor_name": "factor_ethanol_demand",
        "family": "wasde_supply_demand",
        "source_variables": "ethanol_production_kbd",
        "economic_interpretation": "Corn demand from ethanol production.",
        "expected_sign": "positive",
        "expected_horizon": "h10-h30",
    },
    {
        "factor_name": "factor_curve_structure",
        "family": "market_momentum",
        "source_variables": "front/second/third month futures spreads",
        "economic_interpretation": "Contango/backwardation and implied scarcity.",
        "expected_sign": "positive_when_backwardated",
        "expected_horizon": "h5-h30",
    },
    {
        "factor_name": "factor_macro_em",
        "family": "macro_dollar_rates",
        "source_variables": "USD/BRL, USD/ARS and emerging-market FX pressure",
        "economic_interpretation": "Export competitiveness of Brazil and Argentina.",
        "expected_sign": "mixed",
        "expected_horizon": "h20-h90",
    },
    {
        "factor_name": "factor_world_supply",
        "family": "wasde_supply_demand",
        "source_variables": "world ending stocks/use, Brazil production, world exports",
        "economic_interpretation": "Global supply tightness beyond the US balance sheet.",
        "expected_sign": "negative_when_abundant",
        "expected_horizon": "h30-h90",
    },
    {
        "factor_name": "factor_market_breadth",
        "family": "positioning",
        "source_variables": "open interest, volume and participation proxies",
        "economic_interpretation": "Breadth and confirmation of price moves.",
        "expected_sign": "confirming",
        "expected_horizon": "h5-h30",
    },
]


def _family_of(col: str) -> str:
    c = col.lower()
    if c.startswith("cot_") or "open_interest" in c or "non_comm" in c:
        return "positioning"
    if c.startswith("wasde_"):
        return "wasde_supply_demand"
    if c.startswith("export_sales"):
        return "wasde_supply_demand"
    if c.startswith("wx_"):
        return "weather_belt_stress"
    if c in {"dow", "month", "doy", "month_sin", "month_cos", "doy_sin", "doy_cos"} or c.startswith(
        "is_"
    ):
        return "seasonality"
    if c.startswith("corn_"):
        if any(k in c for k in ["vol", "atr", "bb_bandwidth", "volume_z"]):
            return "market_volatility"
        if any(k in c for k in ["soy_", "wheat_", "oil_", "gas_", "dxy_"]):
            return "cross_commodity"
        if any(k in c for k in ["logret", "ema", "sma", "macd", "rsi", "drawdown", "dist_"]):
            return "market_momentum"
    if any(k in c for k in ["fedfunds", "cpi", "usd", "dxy", "real_fed_rate"]):
        return "macro_dollar_rates"
    if c.startswith("drought_") or c.startswith("condition_"):
        return "weather_belt_stress"
    if c.startswith("ethanol_"):
        return "wasde_supply_demand"
    return "raw_signal"


def get_factor_metadata() -> pd.DataFrame:
    """Return documented metadata for named economic factors."""
    return pd.DataFrame(FACTOR_METADATA)


def _zscore(s: pd.Series) -> pd.Series:
    mu = s.mean()
    sd = s.std()
    if pd.isna(sd) or sd == 0:
        return pd.Series(0.0, index=s.index)
    return (s - mu) / sd


def _expanding_zscore(s: pd.Series, min_periods: int = 80) -> pd.Series:
    x = s.astype(float)
    mu = x.expanding(min_periods=min_periods).mean()
    sd = x.expanding(min_periods=min_periods).std()
    out = (x - mu) / sd.replace(0, np.nan)
    return out


def _mean_abs_corr_to_targets(df: pd.DataFrame, targets: pd.DataFrame, cols: list[str]) -> dict[str, float]:
    merged = df[["Date"] + cols].merge(targets, on="Date", how="inner")
    tcols = [f"y_logret_h{h}" for h in (5, 10, 20, 30) if f"y_logret_h{h}" in merged.columns]
    scores: dict[str, float] = {}
    for c in cols:
        vals = []
        for t in tcols:
            cc = merged[c].corr(merged[t])
            if pd.notna(cc):
                vals.append(abs(float(cc)))
        scores[c] = float(np.mean(vals)) if vals else 0.0
    return scores


def _drop_redundant(df: pd.DataFrame, cols: list[str], scores: dict[str, float], corr_th: float = 0.95) -> tuple[list[str], list[str]]:
    if len(cols) <= 1:
        return cols, []
    # Keep columns sorted by explanatory score desc.
    ordered = sorted(cols, key=lambda c: scores.get(c, 0.0), reverse=True)
    kept: list[str] = []
    dropped: list[str] = []
    for c in ordered:
        if not kept:
            kept.append(c)
            continue
        is_redundant = False
        for k in kept:
            r = df[c].corr(df[k])
            if pd.notna(r) and abs(r) >= corr_th:
                is_redundant = True
                break
        if is_redundant:
            dropped.append(c)
        else:
            kept.append(c)
    return kept, dropped


def build_factors(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    min_coverage: float = 0.35,
    keep_per_family: dict[str, int] | None = None,
    include_raw_signals: bool = False,
) -> FactorBuildResult:
    """Create interpretable factor blocks from raw features."""
    if keep_per_family is None:
        keep_per_family = {
            "market_momentum": 6,
            "market_volatility": 5,
            "wasde_supply_demand": 10,
            "weather_belt_stress": 5,
            "macro_dollar_rates": 3,
            "seasonality": 4,
            "cross_commodity": 5,
            "positioning": 5,
            "raw_signal": 3,
        }

    df = features.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    base_cols = [c for c in df.columns if c != "Date" and pd.api.types.is_numeric_dtype(df[c])]
    # Remove columns with too many NaNs.
    coverage = 1.0 - df[base_cols].isna().mean()
    candidate_cols = [c for c in base_cols if coverage[c] >= min_coverage]

    family_map = {c: _family_of(c) for c in candidate_cols}
    by_family: dict[str, list[str]] = {f: [] for f in FAMILY_ORDER}
    for c in candidate_cols:
        by_family[family_map[c]].append(c)

    scores = _mean_abs_corr_to_targets(df, targets, candidate_cols)

    selected_by_family: dict[str, list[str]] = {}
    dropped_redundant_by_family: dict[str, list[str]] = {}

    selected_cols: list[str] = []
    for fam in FAMILY_ORDER:
        cols = by_family.get(fam, [])
        if not cols:
            selected_by_family[fam] = []
            dropped_redundant_by_family[fam] = []
            continue
        kept, dropped = _drop_redundant(df, cols, scores=scores, corr_th=0.95)
        k = keep_per_family.get(fam, 3)
        kept = sorted(kept, key=lambda c: scores.get(c, 0.0), reverse=True)[:k]
        selected_by_family[fam] = kept
        dropped_redundant_by_family[fam] = dropped
        selected_cols.extend(kept)

    selected_cols = list(dict.fromkeys(selected_cols))  # preserve order, remove dups
    out = pd.DataFrame({"Date": df["Date"]})

    # Raw inputs are grouped into synthetic factors by default. They can be
    # retained for diagnostics, but the professional study should not rank them
    # directly because that makes interpretation drift into "miscellaneous".
    if include_raw_signals:
        for c in selected_cols:
            out[f"f_raw_signal__{c}"] = df[c]

    # Create one synthetic index per family (signed weighted z-score average).
    # Sign comes from corr with y_logret_h20 so that interpretation is directional.
    merged = df[["Date"] + selected_cols].merge(targets[["Date", "y_logret_h20"]], on="Date", how="left")
    for fam in FAMILY_ORDER:
        fam_cols = selected_by_family.get(fam, [])
        if not fam_cols:
            continue
        zparts = []
        wparts = []
        for c in fam_cols:
            z = _zscore(merged[c].astype(float).fillna(merged[c].mean()))
            corr = merged[c].corr(merged["y_logret_h20"])
            sign = 1.0 if pd.isna(corr) or corr >= 0 else -1.0
            weight = max(scores.get(c, 1e-6), 1e-6)
            zparts.append(sign * z * weight)
            wparts.append(weight)
        idx = sum(zparts) / (sum(wparts) if sum(wparts) > 0 else 1.0)
        out[f"factor_{fam}"] = idx

    out["factor_drought_severity"] = np.nan
    if "drought_composite" in df.columns:
        out["factor_drought_severity"] = _expanding_zscore(df["drought_composite"]).to_numpy()

    out["factor_export_demand_surprise"] = np.nan
    if "export_sales_mt" in df.columns:
        out["factor_export_demand_surprise"] = _expanding_zscore(df["export_sales_mt"]).to_numpy()

    # Inverted: high condition_gd_ex_pct (good crop) = bearish → factor HIGH when conditions poor
    out["factor_crop_condition_pressure"] = np.nan
    if "condition_gd_ex_pct" in df.columns:
        out["factor_crop_condition_pressure"] = -_expanding_zscore(df["condition_gd_ex_pct"]).to_numpy()

    # High ethanol production = more corn demand = bullish
    out["factor_ethanol_demand"] = np.nan
    if "ethanol_production_kbd" in df.columns:
        out["factor_ethanol_demand"] = _expanding_zscore(df["ethanol_production_kbd"]).to_numpy()

    # factor_curve_structure: backwardation proxy (positive = supply tight = bullish)
    if "curve_backwardation_proxy" in df.columns:
        out["factor_curve_structure"] = _expanding_zscore(df["curve_backwardation_proxy"]).to_numpy()
    elif "curve_price_position_52w" in df.columns:
        out["factor_curve_structure"] = _expanding_zscore(df["curve_price_position_52w"]).to_numpy()
    else:
        out["factor_curve_structure"] = np.nan

    # factor_market_breadth: OI participation signal
    breadth_col = next((c for c in ["oi_change_5d", "volume_oi_ratio_proxy"] if c in df.columns), None)
    out["factor_market_breadth"] = (
        _expanding_zscore(df[breadth_col]).to_numpy() if breadth_col else np.nan
    )

    # factor_world_supply: global balance-sheet tightness (negative = abundant = bearish)
    world_col = next((c for c in ["world_stocks_use_ratio", "world_ending_stocks"] if c in df.columns), None)
    if world_col:
        # Invert: higher stocks/use = bearish → factor high when scarce
        out["factor_world_supply"] = -_expanding_zscore(df[world_col]).to_numpy()
    else:
        out["factor_world_supply"] = np.nan

    # factor_wasde_surprises_z: MoM WASDE surprise (z-scored, shift already applied upstream)
    # Aggregates the most informative MoM surprise columns: ending stocks and production.
    wasde_surp_cols = [
        c for c in df.columns
        if c.endswith("_surprise_vs_prev") and any(k in c for k in ["ending_stocks", "production", "use_total"])
    ]
    if wasde_surp_cols:
        parts = []
        for c in wasde_surp_cols:
            z = _expanding_zscore(df[c])
            # Positive ending_stocks surprise = more supply = bearish → invert
            if "ending_stocks" in c:
                z = -z
            parts.append(z)
        out["factor_wasde_surprises_z"] = pd.concat(parts, axis=1).mean(axis=1).to_numpy()
    else:
        out["factor_wasde_surprises_z"] = np.nan

    # factor_weather_advanced: GDD accumulated + rain deficit + extreme heat
    # Positive = stress conditions (bearish supply = bullish price)
    adv_components = []
    if "wx_belt_gdd_accumulated" in df.columns:
        # GDD anomaly vs expanding mean for same DOY — positive when growth ahead of schedule
        adv_components.append(_expanding_zscore(df["wx_belt_gdd_accumulated"].fillna(0)))
    if "wx_belt_rain_deficit_14d" in df.columns:
        # Negative rain_deficit means dry → bearish supply → flip sign
        adv_components.append(-_expanding_zscore(df["wx_belt_rain_deficit_14d"].fillna(0)))
    if "wx_belt_heat_days_38c_30" in df.columns:
        adv_components.append(_expanding_zscore(df["wx_belt_heat_days_38c_30"].fillna(0)))
    if adv_components:
        out["factor_weather_advanced"] = pd.concat(adv_components, axis=1).mean(axis=1).to_numpy()
    else:
        out["factor_weather_advanced"] = np.nan

    # factor_macro_em: USD/EM pressure — not yet collected, placeholder
    macro_em_col = next(
        (c for c in ["usd_brl", "usd_ars", "usd_cny"] if c in df.columns), None
    )
    if macro_em_col:
        # Rising USD/EM = EM exports more competitive = bearish US corn
        out["factor_macro_em"] = _expanding_zscore(df[macro_em_col]).to_numpy()
    else:
        out["factor_macro_em"] = np.nan

    metadata_df = get_factor_metadata()
    documented_family = dict(zip(metadata_df["factor_name"], metadata_df["family"], strict=False))
    factor_columns = [c for c in out.columns if c.startswith("factor_")]
    factor_family = {
        col: documented_family.get(
            col,
            col.replace("factor_", "", 1) if col.startswith("factor_") else "raw_signal",
        )
        for col in factor_columns
    }

    metadata: dict[str, Any] = {
        "n_input_features": len(base_cols),
        "n_candidate_features": len(candidate_cols),
        "n_selected_features": len(selected_cols),
        "families": {fam: by_family.get(fam, []) for fam in FAMILY_ORDER},
        "selected_by_family": selected_by_family,
        "dropped_redundant_by_family": dropped_redundant_by_family,
        "score_mean_abs_corr": {k: float(v) for k, v in scores.items()},
        "factor_columns": factor_columns,
        "raw_factor_columns": [c for c in out.columns if c.startswith("f_raw")],
        "factor_family": factor_family,
        "factor_metadata": metadata_df.to_dict(orient="records"),
    }
    return FactorBuildResult(factors=out, metadata=metadata)


def save_factors(result: FactorBuildResult, out_path: Path | None = None) -> tuple[Path, Path]:
    if out_path is None:
        out_path = PROCESSED_DIR / "factors.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_parquet(result.factors, out_path)

    meta_path = PROCESSED_DIR / "factors_metadata.json"
    import json

    meta_path.write_text(json.dumps(result.metadata, ensure_ascii=True, indent=2), encoding="utf-8")
    log.info(
        "factors_saved",
        out=str(out_path),
        rows=len(result.factors),
        cols=result.factors.shape[1],
        meta=str(meta_path),
    )
    return out_path, meta_path

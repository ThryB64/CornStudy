"""Economic factor engineering from raw features.

The factor table is meant to be a smaller, explainable view of the raw feature
space. Factor values are built from economic recipes only: targets may be passed
for diagnostics, but they are not used to choose, sign, or scale factors.
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


@dataclass(frozen=True)
class FactorRecipe:
    name: str
    family: str
    description: str
    signed_components: dict[str, float]
    transform: str = "expanding_zscore"


FAMILY_ORDER = [
    "market_momentum",
    "market_volatility",
    "wasde_supply_demand",
    "weather_belt_stress",
    "production_fundamentals",
    "ethanol_demand",
    "macro_dollar_rates",
    "cot_positioning",
    "seasonality",
    "cross_commodity",
    "others",
]


FACTOR_RECIPES: tuple[FactorRecipe, ...] = (
    FactorRecipe(
        name="factor_market_short_momentum",
        family="market_momentum",
        description="Momentum court terme du maïs CBOT via rendements récents, RSI et MACD.",
        signed_components={
            "corn_logret_1d": 0.5,
            "corn_logret_5d": 1.0,
            "corn_rsi_14": 0.7,
            "corn_macd_hist": 1.0,
        },
    ),
    FactorRecipe(
        name="factor_market_medium_trend",
        family="market_momentum",
        description="Tendance moyenne via rendement 20 jours et structure des moyennes mobiles.",
        signed_components={
            "corn_logret_20d": 1.0,
            "corn_sma_20": 0.4,
            "corn_sma_50": 0.4,
            "corn_macd_signal": 0.8,
        },
    ),
    FactorRecipe(
        name="factor_market_drawdown_recovery",
        family="market_momentum",
        description="Position dans le range annuel; valeur élevée = prix éloigné des plus bas.",
        signed_components={
            "corn_drawdown_252": 1.0,
            "corn_dist_to_52w_high": 0.8,
            "corn_dist_to_52w_low": 1.0,
            "corn_bb_percent_b_20": 0.6,
        },
    ),
    FactorRecipe(
        name="factor_market_liquidity_volume",
        family="market_volatility",
        description="Activité de marché anormale sur le contrat maïs.",
        signed_components={"corn_volume_z20": 1.0},
    ),
    FactorRecipe(
        name="factor_market_volatility_pressure",
        family="market_volatility",
        description="Expansion de volatilité et d'amplitude sur les futures maïs.",
        signed_components={
            "corn_atr_14": 1.0,
            "corn_realized_vol_20": 1.0,
            "corn_realized_vol_60": 0.7,
            "corn_bb_bandwidth_20": 1.0,
        },
    ),
    FactorRecipe(
        name="factor_cross_soy_relative_value",
        family="cross_commodity",
        description="Valorisation et co-mouvement du maïs relativement au soja.",
        signed_components={"corn_soy_ratio": 1.0, "corn_soy_corr60": 0.5},
    ),
    FactorRecipe(
        name="factor_cross_wheat_relative_value",
        family="cross_commodity",
        description="Valorisation et co-mouvement du maïs relativement au blé.",
        signed_components={"corn_wheat_ratio": 1.0, "corn_wheat_corr60": 0.5},
    ),
    FactorRecipe(
        name="factor_cross_energy_link",
        family="cross_commodity",
        description="Contexte énergie lié à l'éthanol et aux coûts d'intrants.",
        signed_components={
            "corn_oil_ratio": 0.7,
            "corn_oil_corr60": 0.4,
            "corn_gas_ratio": 0.7,
            "corn_gas_corr60": 0.4,
        },
    ),
    FactorRecipe(
        name="factor_cross_dollar_pressure",
        family="cross_commodity",
        description="Force du maïs relativement au proxy dollar US.",
        signed_components={"corn_dxy_ratio": 1.0, "corn_dxy_corr60": 0.5},
    ),
    FactorRecipe(
        name="factor_weather_heat_stress",
        family="weather_belt_stress",
        description="Stress thermique du Corn Belt; valeur élevée = conditions plus chaudes.",
        signed_components={
            "wx_belt_tavg_c_anom_z": 1.0,
            "wx_belt_tmax_c_anom_z": 1.0,
            "wx_belt_heat_days_30": 1.0,
            "wx_iowa_tavg_anom_z": 0.4,
            "wx_illinois_tavg_anom_z": 0.4,
            "wx_nebraska_tavg_anom_z": 0.4,
        },
    ),
    FactorRecipe(
        name="factor_weather_dryness_stress",
        family="weather_belt_stress",
        description="Stress de sécheresse; valeur élevée = précipitations sous la normale.",
        signed_components={
            "wx_belt_prcp_mm_anom_z": -1.0,
            "wx_belt_prcp_30_anom_z": -1.0,
            "wx_belt_prcp_mm": -0.4,
            "wx_belt_prcp_30": -0.4,
        },
    ),
    FactorRecipe(
        name="factor_weather_core_state_stress",
        family="weather_belt_stress",
        description="Anomalie de température sur les principaux états du Corn Belt.",
        signed_components={
            "wx_iowa_tavg_anom_z": 1.0,
            "wx_illinois_tavg_anom_z": 1.0,
            "wx_nebraska_tavg_anom_z": 0.9,
            "wx_minnesota_tavg_anom_z": 0.8,
            "wx_indiana_tavg_anom_z": 0.7,
        },
    ),
    FactorRecipe(
        name="factor_weather_cold_delay",
        family="weather_belt_stress",
        description="Proxy de retard par froid; valeur élevée = températures sous la normale.",
        signed_components={
            "wx_belt_tavg_c_anom_z": -1.0,
            "wx_belt_tmin_c_anom_z": -1.0,
            "wx_belt_tavg_c": -0.3,
        },
    ),
    FactorRecipe(
        name="factor_wasde_balance_tightness",
        family="wasde_supply_demand",
        description="Tension du bilan US via stocks-to-use et mesures de surplus.",
        signed_components={
            "wasde_ending_stocks": -0.8,
            "wasde_stocks_to_use_ratio": -1.0,
            "wasde_stocks_to_use_calc": -1.0,
            "wasde_supply_minus_use": -0.8,
            "wasde_stocks_to_use_calc_z": -1.0,
            "wasde_supply_minus_use_z": -0.8,
        },
    ),
    FactorRecipe(
        name="factor_wasde_supply_risk",
        family="wasde_supply_demand",
        description="Risque de rareté côté offre; valeur élevée = production/offre plus basse.",
        signed_components={
            "wasde_production": -1.0,
            "wasde_supply_total": -0.8,
            "wasde_production_yoy_pct": -0.7,
            "wasde_production_mom_pct": -0.5,
        },
    ),
    FactorRecipe(
        name="factor_wasde_demand_exports",
        family="wasde_supply_demand",
        description="Traction de demande via usage total, demande domestique et exports.",
        signed_components={
            "wasde_use_total": 0.8,
            "wasde_domestic_total": 0.6,
            "wasde_exports": 1.0,
            "wasde_export_ratio_calc": 0.8,
            "wasde_use_total_yoy_pct": 0.8,
            "wasde_exports_yoy_pct": 0.8,
        },
    ),
    FactorRecipe(
        name="factor_wasde_price_regime",
        family="wasde_supply_demand",
        description="Régime de prix ferme USDA et changements récents.",
        signed_components={
            "wasde_avg_farm_price": 1.0,
            "wasde_avg_farm_price_z": 1.0,
            "wasde_avg_farm_price_mom_diff": 0.8,
            "wasde_avg_farm_price_yoy_pct": 0.7,
        },
    ),
    FactorRecipe(
        name="factor_wasde_tightness_surprise",
        family="wasde_supply_demand",
        description="Surprise WASDE haussière si stocks ou stocks-to-use sortent sous l'attendu.",
        signed_components={
            "wasde_ending_stocks_surprise_vs_prev": -0.8,
            "wasde_ending_stocks_surprise_vs_trend": -1.0,
            "wasde_stocks_to_use_ratio_surprise_vs_prev": -0.8,
            "wasde_stocks_to_use_ratio_surprise_vs_trend": -1.0,
            "wasde_supply_minus_use_surprise_vs_trend": -0.8,
            "wasde_stocks_to_use_calc_z_surprise_vs_trend": -0.8,
        },
    ),
    FactorRecipe(
        name="factor_wasde_supply_surprise",
        family="wasde_supply_demand",
        description="Surprise WASDE haussière si production ou offre totale est révisée en baisse.",
        signed_components={
            "wasde_production_surprise_vs_prev": -0.8,
            "wasde_production_surprise_vs_trend": -1.0,
            "wasde_supply_total_surprise_vs_prev": -0.6,
            "wasde_supply_total_surprise_vs_trend": -0.8,
            "wasde_production_mom_pct_surprise_vs_trend": -0.8,
            "wasde_production_yoy_pct_surprise_vs_trend": -0.6,
        },
    ),
    FactorRecipe(
        name="factor_wasde_demand_surprise",
        family="wasde_supply_demand",
        description="Surprise WASDE haussière si usage ou exports sont révisés en hausse.",
        signed_components={
            "wasde_use_total_surprise_vs_prev": 0.7,
            "wasde_use_total_surprise_vs_trend": 0.9,
            "wasde_exports_surprise_vs_prev": 0.8,
            "wasde_exports_surprise_vs_trend": 1.0,
            "wasde_domestic_total_surprise_vs_trend": 0.6,
            "wasde_export_ratio_calc_surprise_vs_trend": 0.8,
        },
    ),
    FactorRecipe(
        name="factor_wasde_price_surprise",
        family="wasde_supply_demand",
        description="Surprise du prix ferme USDA par rapport à l'historique et à la tendance.",
        signed_components={
            "wasde_avg_farm_price_surprise_vs_prev": 0.7,
            "wasde_avg_farm_price_surprise_vs_5y": 0.8,
            "wasde_avg_farm_price_surprise_vs_trend": 1.0,
            "wasde_avg_farm_price_z_surprise_vs_trend": 0.8,
        },
    ),
    FactorRecipe(
        name="factor_wasde_revision_momentum",
        family="wasde_supply_demand",
        description="Pression de révision mensuelle et annuelle sur les champs WASDE clés.",
        signed_components={
            "wasde_ending_stocks_mom_pct": -0.8,
            "wasde_stocks_to_use_ratio_mom_pct": -0.8,
            "wasde_use_total_mom_pct": 0.7,
            "wasde_exports_mom_pct": 0.7,
            "wasde_avg_farm_price_mom_pct": 0.6,
        },
    ),
    FactorRecipe(
        name="factor_season_planting_window",
        family="seasonality",
        description="Exposition calendaire à la fenêtre de semis.",
        signed_components={"is_planting_season": 1.0},
        transform="raw",
    ),
    FactorRecipe(
        name="factor_season_pollination_window",
        family="seasonality",
        description="Exposition calendaire à la fenêtre floraison/pollinisation.",
        signed_components={"is_silking_season": 1.0},
        transform="raw",
    ),
    FactorRecipe(
        name="factor_season_harvest_window",
        family="seasonality",
        description="Exposition calendaire à la fenêtre de récolte.",
        signed_components={"is_harvest_season": 1.0},
        transform="raw",
    ),
    FactorRecipe(
        name="factor_season_annual_cycle",
        family="seasonality",
        description="Cycle annuel lissé via les termes Fourier mensuels.",
        signed_components={"month_sin": 1.0, "month_cos": 1.0},
    ),
    # ---- Production fundamentals (NASS QuickStats) ----
    FactorRecipe(
        name="factor_production_yield_risk",
        family="production_fundamentals",
        description="Risque de rendement ; valeur élevée = rendement sous la normale (haussier prix).",
        signed_components={
            "yield_weighted": -1.0,
            "yoy_yield_pct": -1.0,
            "yield_weighted_surprise_vs_trend": -1.0,
            "yoy_yield_pct_surprise_vs_trend": -0.8,
        },
    ),
    FactorRecipe(
        name="factor_production_area_supply",
        family="production_fundamentals",
        description="Pression d'offre via surfaces ; valeur élevée = plus grandes surfaces (baissier).",
        signed_components={
            "area_planted_total": -1.0,
            "area_harvested_total": -1.0,
            "area_planted_total_surprise_vs_trend": -0.9,
            "area_harvested_total_surprise_vs_trend": -0.9,
        },
        transform="expanding_zscore",
    ),
    FactorRecipe(
        name="factor_stocks_seasonal_tightness",
        family="production_fundamentals",
        description="Tension des stocks trimestriels (Grain Stocks NASS) ; valeur élevée = stocks bas (haussier).",
        signed_components={
            "stocks_mar": -1.0,
            "stocks_jun": -1.0,
            "stocks_sep": -1.0,
            "stocks_dec": -1.0,
            "stocks_mar_surprise_vs_trend": -1.0,
            "stocks_jun_surprise_vs_trend": -1.0,
            "stocks_sep_surprise_vs_trend": -1.0,
            "stocks_dec_surprise_vs_trend": -1.0,
        },
    ),
    FactorRecipe(
        name="factor_production_output_revision",
        family="production_fundamentals",
        description="Révision de la production nationale ; valeur élevée = production révisée en baisse (haussier).",
        signed_components={
            "production_total": -1.0,
            "yoy_production_pct": -0.8,
            "production_total_surprise_vs_prev": -1.0,
            "production_total_surprise_vs_trend": -1.0,
        },
    ),
    # ---- Macro / politique monétaire (FRED) ----
    FactorRecipe(
        name="factor_macro_rates_pressure",
        family="macro_dollar_rates",
        description="Pression monétaire ; valeur élevée = taux réels hauts (baissier pour les matières premières).",
        signed_components={
            "fedfunds": -1.0,
            "fedfunds_z24": -1.0,
            "real_fed_rate": -1.0,
            "fedfunds_chg_3m": -0.8,
        },
    ),
    FactorRecipe(
        name="factor_macro_inflation_signal",
        family="macro_dollar_rates",
        description="Signal inflationniste ; valeur élevée = inflation forte (haussier pour les matières premières).",
        signed_components={
            "cpi_yoy_pct": 1.0,
            "cpi_z24": 1.0,
            "cpi_mom_pct": 0.6,
        },
    ),
    # ---- Ethanol demand / energy economics ----
    FactorRecipe(
        name="factor_ethanol_margin_signal",
        family="ethanol_demand",
        description="Signal de marge éthanol ; valeur élevée = pétrole cher relativement au maïs, donc demande potentiellement soutenue.",
        signed_components={
            "ethanol_proxy_crush_margin": 1.0,
            "ethanol_proxy_crush_margin_surprise_vs_trend": 0.8,
            "ethanol_production_kbd": 0.8,
            "ethanol_production_kbd_surprise_vs_trend": 0.8,
            "ethanol_supply_tightness": 0.6,
        },
    ),
    # ---- COT Positioning (CFTC weekly, 3-day lag) ----
    FactorRecipe(
        name="factor_cot_speculative_pressure",
        family="cot_positioning",
        description="Pression spéculative nette des Managed Money (haussier si net long élevé).",
        signed_components={
            "cot_mm_net": 1.0,
            "cot_mm_net_pct_oi": 1.0,
            "cot_mm_long_pct": 0.8,
            "cot_mm_net_surprise_vs_trend": 0.9,
        },
    ),
    FactorRecipe(
        name="factor_cot_commercial_hedge",
        family="cot_positioning",
        description="Position nette des producteurs/commerciaux (inverse : net short élevé = offre abondante).",
        signed_components={
            "cot_pm_net": -1.0,
            "cot_pm_net_pct_oi": -1.0,
            "cot_pm_net_surprise_vs_trend": -0.8,
        },
    ),
    FactorRecipe(
        name="factor_cot_open_interest_momentum",
        family="cot_positioning",
        description="Dynamique de l'open interest ; expansion = intérêt croissant du marché.",
        signed_components={
            "cot_open_interest": 1.0,
            "cot_open_interest_surprise_vs_trend": 0.8,
        },
    ),
)


_PRODUCTION_KEYWORDS = frozenset([
    "area_planted", "area_harvested", "production_total",
    "yield_weighted", "yoy_production_pct", "yoy_yield_pct",
    "stocks_mar", "stocks_jun", "stocks_sep", "stocks_dec",
    "share_iowa", "share_illinois", "share_nebraska", "share_minnesota",
    "share_indiana", "share_south_dakota", "share_kansas", "share_ohio",
    "share_wisconsin", "share_missouri",
])


def _family_of(col: str) -> str:
    c = col.lower()
    if c.startswith("wasde_"):
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
    if any(k in c for k in ["fedfunds", "cpiaucns", "cpi_", "real_fed_rate"]):
        return "macro_dollar_rates"
    if c.startswith("cot_"):
        return "cot_positioning"
    if c.startswith("ethanol_"):
        return "ethanol_demand"
    # Production fundamentals: exact prefix match or surprise variants thereof
    for kw in _PRODUCTION_KEYWORDS:
        if c == kw or c.startswith(kw + "_surprise"):
            return "production_fundamentals"
    return "others"


def _zscore(s: pd.Series) -> pd.Series:
    mu = s.mean()
    sd = s.std()
    if pd.isna(sd) or sd == 0:
        return pd.Series(0.0, index=s.index)
    return (s - mu) / sd


def _expanding_zscore(s: pd.Series, min_periods: int = 252) -> pd.Series:
    """Z-score using only earlier observations, with a shorter warm-up fallback."""
    x = pd.to_numeric(s, errors="coerce").astype(float)
    mean = x.expanding(min_periods=min_periods).mean().shift(1)
    sd = x.expanding(min_periods=min_periods).std().shift(1)
    z = (x - mean) / sd.replace(0, np.nan)

    warm_mean = x.expanding(min_periods=30).mean().shift(1)
    warm_sd = x.expanding(min_periods=30).std().shift(1)
    warm_z = (x - warm_mean) / warm_sd.replace(0, np.nan)
    return z.fillna(warm_z).clip(-6, 6)


def _component_coverage(df: pd.DataFrame, cols: list[str]) -> dict[str, float]:
    return {c: float(1.0 - df[c].isna().mean()) for c in cols if c in df.columns}


def _safe_corr(x: pd.Series, y: pd.Series) -> float:
    common = x.notna() & y.notna()
    if common.sum() < 30:
        return float("nan")
    a = x[common].astype(float)
    b = y[common].astype(float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(a.corr(b))


def _mean_abs_corr_to_targets(df: pd.DataFrame, targets: pd.DataFrame, cols: list[str]) -> dict[str, float]:
    merged = df[["Date"] + cols].merge(targets, on="Date", how="inner")
    tcols = [f"y_logret_h{h}" for h in (5, 10, 20, 30) if f"y_logret_h{h}" in merged.columns]
    scores: dict[str, float] = {}
    for c in cols:
        vals = []
        for t in tcols:
            cc = _safe_corr(merged[c], merged[t])
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
            common = df[c].notna() & df[k].notna()
            if common.sum() < 30:
                continue
            a = df.loc[common, c].astype(float)
            b = df.loc[common, k].astype(float)
            if a.std() == 0 or b.std() == 0:
                continue
            r = a.corr(b)
            if pd.notna(r) and abs(r) >= corr_th:
                is_redundant = True
                break
        if is_redundant:
            dropped.append(c)
        else:
            kept.append(c)
    return kept, dropped


def _build_recipe_factor(
    df: pd.DataFrame,
    recipe: FactorRecipe,
    min_coverage: float,
) -> tuple[pd.Series | None, dict[str, float]]:
    present: dict[str, float] = {}
    parts: list[pd.Series] = []

    for col, sign in recipe.signed_components.items():
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        coverage = 1.0 - float(df[col].isna().mean())
        if coverage < min_coverage:
            continue
        s = pd.to_numeric(df[col], errors="coerce").astype(float)
        if recipe.transform == "raw":
            transformed = s
        elif recipe.transform == "static_zscore":
            transformed = _zscore(s)
        else:
            transformed = _expanding_zscore(s)
        parts.append(transformed * float(sign))
        present[col] = float(sign)

    if not parts:
        return None, {}

    mat = pd.concat(parts, axis=1)
    weights = np.array([abs(v) for v in present.values()], dtype=float)
    if weights.sum() == 0:
        factor = mat.mean(axis=1)
    else:
        weighted = mat.mul(weights, axis=1)
        active_weight = mat.notna().mul(weights, axis=1).sum(axis=1)
        factor = weighted.sum(axis=1, min_count=1) / active_weight.replace(0, np.nan)
    return factor.astype(float), present


def build_factors(
    features: pd.DataFrame,
    targets: pd.DataFrame | None = None,
    min_coverage: float = 0.35,
) -> FactorBuildResult:
    """Create interpretable factor blocks from raw features.

    ``targets`` is optional and only feeds metadata diagnostics. The factor
    values themselves are target-agnostic and use expanding z-scores so that a
    row never needs future distributional information to be computed.
    """
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

    out = pd.DataFrame({"Date": df["Date"]})

    selected_by_family: dict[str, list[str]] = {f: [] for f in FAMILY_ORDER}
    factor_components: dict[str, dict[str, float]] = {}
    factor_descriptions: dict[str, str] = {}
    factor_family: dict[str, str] = {}

    for recipe in FACTOR_RECIPES:
        factor, present = _build_recipe_factor(df, recipe, min_coverage=min_coverage)
        if factor is None:
            continue
        out[recipe.name] = factor
        factor_components[recipe.name] = present
        factor_descriptions[recipe.name] = recipe.description
        factor_family[recipe.name] = recipe.family
        selected_by_family.setdefault(recipe.family, [])
        selected_by_family[recipe.family].extend(present.keys())

    selected_by_family = {
        fam: sorted(dict.fromkeys(cols))
        for fam, cols in selected_by_family.items()
    }
    selected_cols = sorted({c for cols in selected_by_family.values() for c in cols})

    # Redundancy diagnostics are unsupervised: columns unused by the recipes
    # are intentionally left out of the factor view, not selected by target fit.
    unused_by_family: dict[str, list[str]] = {}
    redundant_by_family: dict[str, list[str]] = {}
    coverage_scores = _component_coverage(df, candidate_cols)
    used = set(selected_cols)
    for fam in FAMILY_ORDER:
        cols = by_family.get(fam, [])
        _, redundant = _drop_redundant(df, cols, scores=coverage_scores, corr_th=0.95)
        unused_by_family[fam] = [c for c in cols if c not in used]
        redundant_by_family[fam] = [c for c in redundant if c not in used]

    scores = _mean_abs_corr_to_targets(df, targets, candidate_cols) if targets is not None else {}

    metadata: dict[str, Any] = {
        "n_input_features": len(base_cols),
        "n_candidate_features": len(candidate_cols),
        "n_selected_components": len(selected_cols),
        "n_factor_columns": int(out.shape[1] - 1),
        "families": {fam: by_family.get(fam, []) for fam in FAMILY_ORDER},
        "selected_by_family": selected_by_family,
        "unused_by_family": unused_by_family,
        "dropped_redundant_by_family": redundant_by_family,
        "score_mean_abs_corr": {k: float(v) for k, v in scores.items()},
        "factor_columns": [c for c in out.columns if c.startswith("factor_")],
        "raw_factor_columns": [],
        "factor_components": factor_components,
        "factor_descriptions": factor_descriptions,
        "factor_family": factor_family,
        "factor_recipe_note": (
            "Les facteurs sont construits depuis des recettes économiques explicites "
            "avec z-scores expanding; les targets servent seulement aux diagnostics."
        ),
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

"""Feature engineering modules.

Each sub-module produces a DataFrame indexed by ``Date`` with one or several
columns. ``build_features()`` orchestrates them into the unified parquet at
``data/processed/features.parquet``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import FEATURES_PARQUET, INTERIM_DIR
from mais.utils import get_logger, read_table, write_parquet

from .cot_advanced import build_cot_advanced_features
from .curve_spreads import build_curve_spread_features
from .ema_features import build_ema_features
from .factors import FactorBuildResult, build_factors, save_factors
from .fas_features import build_fas_features
from .market import build_market_features
from .phenology import build_phenology_features
from .seasonality import build_seasonality_features
from .surprise import add_surprise_features
from .weather_belt import build_weather_belt_features

log = get_logger("mais.features")


def _drought_weekly_to_daily(
    out_dates: pd.Series,
    weekly: pd.DataFrame,
    *,
    max_stale_days: int = 7,
) -> pd.DataFrame:
    """Map weekly USDM-style corn impact stats onto trade dates.

    Uses backward merge-as-of then drops stale observations (weekly cadence → >
    ``max_stale_days`` without a refresh ⇒ NaN). Applies ``shift(1)`` on all
    columns for anti-leakage vs publication lag / intra-week timing.

    Produces drought_composite (legacy) + granular drought_d2plus,
    drought_change_4w, drought_extreme_flag (V3-06).
    """
    w = weekly.copy()
    w["Date"] = pd.to_datetime(w["Date"])
    w = w.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")

    granular_cols = ["drought_d2plus", "drought_change_4w", "drought_extreme_flag"]

    if w.empty:
        base_empty = pd.DataFrame({"Date": pd.to_datetime(pd.Series(out_dates).unique())})
        base_empty["drought_composite"] = np.nan
        for gc in granular_cols:
            base_empty[gc] = np.nan
        return base_empty.sort_values("Date").reset_index(drop=True)

    if "drought_composite" in w.columns:
        comp = pd.to_numeric(w["drought_composite"], errors="coerce")
    else:
        weights = (0.1, 0.3, 0.5, 0.75, 1.0)
        acc = np.zeros(len(w), dtype=float)
        any_col = False
        for i, wt in enumerate(weights):
            aliases = (f"corn_area_d{i}_pct", f"corn_area_d{i}")
            col = next((c for c in aliases if c in w.columns), None)
            if col is not None:
                acc += wt * pd.to_numeric(w[col], errors="coerce").fillna(0).to_numpy()
                any_col = True
        if not any_col:
            log.warning("drought_no_known_columns", cols=list(w.columns))
            comp = pd.Series(np.nan, index=w.index)
        else:
            comp = pd.Series(acc, index=w.index)

    # Granular features from raw D2-D4 columns
    has_granular = all(f"corn_area_d{i}" in w.columns for i in (2, 3, 4))
    if has_granular:
        d2 = pd.to_numeric(w["corn_area_d2"], errors="coerce").fillna(0)
        d3 = pd.to_numeric(w["corn_area_d3"], errors="coerce").fillna(0)
        d4 = pd.to_numeric(w["corn_area_d4"], errors="coerce").fillna(0)
        w_d2plus = 0.5 * d2 + 0.75 * d3 + 1.0 * d4
        w_change4 = w_d2plus.diff(4)
        w_extreme = ((d3 + d4) > 10.0).astype(float)
    else:
        w_d2plus = pd.Series(np.nan, index=w.index)
        w_change4 = pd.Series(np.nan, index=w.index)
        w_extreme = pd.Series(np.nan, index=w.index)

    wk = pd.DataFrame({
        "week_obs": w["Date"].values,
        "_raw_comp": comp.to_numpy(),
        "_d2plus": w_d2plus.to_numpy(),
        "_change4": w_change4.to_numpy(),
        "_extreme": w_extreme.to_numpy(),
    }).sort_values("week_obs")

    base = pd.DataFrame({"Date": pd.to_datetime(out_dates.unique())})
    base = base.sort_values("Date").reset_index(drop=True)

    merged = pd.merge_asof(
        base,
        wk,
        left_on="Date",
        right_on="week_obs",
        direction="backward",
    )
    merged.loc[merged["week_obs"].isna(), ["_raw_comp", "_d2plus", "_change4", "_extreme"]] = np.nan
    staleness = (merged["Date"] - merged["week_obs"]).dt.days
    stale_mask = staleness > max_stale_days
    merged.loc[stale_mask, ["_raw_comp", "_d2plus", "_change4", "_extreme"]] = np.nan

    out = pd.DataFrame({"Date": merged["Date"].values})
    out["drought_composite"] = merged["_raw_comp"].astype(float)
    out["drought_composite"] = out["drought_composite"].shift(1)
    out.loc[stale_mask, "drought_composite"] = np.nan
    out["drought_d2plus"] = merged["_d2plus"].astype(float)
    out["drought_d2plus"] = out["drought_d2plus"].shift(1)
    out.loc[stale_mask, "drought_d2plus"] = np.nan
    out["drought_change_4w"] = merged["_change4"].astype(float)
    out["drought_change_4w"] = out["drought_change_4w"].shift(1)
    out.loc[stale_mask, "drought_change_4w"] = np.nan
    out["drought_extreme_flag"] = merged["_extreme"].astype(float)
    out["drought_extreme_flag"] = out["drought_extreme_flag"].shift(1)
    out.loc[stale_mask, "drought_extreme_flag"] = np.nan
    return out


def _fas_weekly_to_daily(
    out_dates: pd.Series,
    weekly: pd.DataFrame,
    *,
    max_stale_days: int = 10,
    value_col: str = "export_sales_mt",
) -> pd.DataFrame:
    """Map weekly FAS export totals onto trade dates."""
    # value_col retained for backwards compatibility with older tests/callers.
    _ = value_col
    return build_fas_features(weekly, out_dates, max_stale_days=max_stale_days)


def _crop_progress_weekly_to_daily(
    out_dates: pd.Series,
    weekly: pd.DataFrame,
    *,
    max_stale_days: int = 7,
) -> pd.DataFrame:
    """Map weekly NASS Crop Progress onto trade dates.

    NASS releases Monday/Tuesday; data covers May-Oct. Backward merge_asof,
    stale > 7 days → NaN (out-of-season), then shift(1) for anti-leakage.
    """
    w = weekly.copy()
    w["Date"] = pd.to_datetime(w["Date"])
    w = w.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")

    value_cols = [
        "condition_gd_ex_pct",
        "planted_pct",
        "silking_pct",
        "mature_pct",
        "harvested_pct",
    ]
    base = pd.DataFrame({"Date": pd.to_datetime(pd.Series(out_dates).unique())})
    base = base.sort_values("Date").reset_index(drop=True)

    available = [col for col in value_cols if col in w.columns]
    if w.empty or not available:
        for col in [
            "condition_gd_ex_pct",
            "crop_ge_pct",
            "crop_ge_pct_vs_last_year",
            "crop_ge_5y_avg_deviation",
            "crop_ge_zscore_seasonal",
            "crop_planted_pct",
            "crop_silked_pct",
            "crop_mature_pct",
            "crop_harvested_pct",
            "crop_condition_momentum_2w",
            "crop_condition_available",
            "crop_ge_pct_filled",
        ]:
            base[col] = np.nan
        return base

    wk = pd.DataFrame({"week_obs": w["Date"].values})
    for col in available:
        wk[col] = pd.to_numeric(w[col], errors="coerce").to_numpy()
    if "condition_gd_ex_pct" in wk.columns:
        ge = wk["condition_gd_ex_pct"].astype(float)
        wk["crop_ge_pct_vs_last_year"] = ge - ge.shift(52)
        wk["crop_ge_5y_avg_deviation"] = _weekly_doy_deviation(wk["week_obs"], ge)
        mu = ge.expanding(8).mean()
        sd = ge.expanding(8).std().replace(0, np.nan)
        wk["crop_ge_zscore_seasonal"] = (ge - mu) / sd
        wk["crop_condition_momentum_2w"] = ge.diff(2)
    wk = wk.sort_values("week_obs")

    merged = pd.merge_asof(base, wk, left_on="Date", right_on="week_obs", direction="backward")
    staleness = (merged["Date"] - merged["week_obs"]).dt.days
    source_cols = [col for col in merged.columns if col not in {"Date", "week_obs"}]
    merged.loc[merged["week_obs"].isna(), source_cols] = np.nan
    merged.loc[staleness > max_stale_days, source_cols] = np.nan

    out = pd.DataFrame({"Date": merged["Date"].values})
    rename = {
        "condition_gd_ex_pct": "crop_ge_pct",
        "planted_pct": "crop_planted_pct",
        "silking_pct": "crop_silked_pct",
        "mature_pct": "crop_mature_pct",
        "harvested_pct": "crop_harvested_pct",
    }
    for src, dst in rename.items():
        out[dst] = merged[src].astype(float).shift(1) if src in merged.columns else np.nan
        out.loc[staleness > max_stale_days, dst] = np.nan
    for col in ["crop_ge_pct_vs_last_year", "crop_ge_5y_avg_deviation", "crop_ge_zscore_seasonal", "crop_condition_momentum_2w"]:
        out[col] = merged[col].astype(float).shift(1) if col in merged.columns else np.nan
        out.loc[staleness > max_stale_days, col] = np.nan
    out["condition_gd_ex_pct"] = out["crop_ge_pct"]
    out["crop_condition_available"] = out["crop_ge_pct"].notna().astype(float)
    out["crop_ge_pct_filled"] = out["crop_ge_pct"].ffill()
    if out["crop_ge_pct_filled"].notna().any():
        out["crop_ge_pct_filled"] = out["crop_ge_pct_filled"].fillna(out["crop_ge_pct"].median())
    else:
        out["crop_ge_pct_filled"] = np.nan
    return out


def _weekly_doy_deviation(dates: pd.Series, values: pd.Series) -> pd.Series:
    dt = pd.to_datetime(dates)
    iso_week = dt.dt.isocalendar().week.astype(int)
    vals = pd.to_numeric(values, errors="coerce")
    out = pd.Series(np.nan, index=vals.index, dtype=float)
    for i, (week, value) in enumerate(zip(iso_week, vals, strict=False)):
        hist = vals.iloc[:i][iso_week.iloc[:i] == week].tail(5)
        if hist.notna().sum() >= 2 and pd.notna(value):
            out.iloc[i] = float(value - hist.mean())
    return out


def _eia_weekly_to_daily(
    out_dates: pd.Series,
    weekly: pd.DataFrame,
    *,
    max_stale_days: int = 10,
) -> pd.DataFrame:
    """Map weekly EIA ethanol data onto trade dates.

    Published Wednesday 10:30 ET for prior week → shift(1) for anti-leakage.
    """
    w = weekly.copy()
    w["Date"] = pd.to_datetime(w["Date"])
    w = w.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")

    value_cols = [c for c in ("ethanol_production_kbd", "ethanol_stocks_kbbl") if c in w.columns]
    base = pd.DataFrame({"Date": pd.to_datetime(pd.Series(out_dates).unique())})
    base = base.sort_values("Date").reset_index(drop=True)

    if w.empty or not value_cols:
        for vc in ("ethanol_production_kbd", "ethanol_stocks_kbbl"):
            base[vc] = np.nan
        return base

    wk = w[["Date"] + value_cols].rename(columns={"Date": "week_obs"})
    merged = pd.merge_asof(base, wk, left_on="Date", right_on="week_obs", direction="backward")
    staleness = (merged["Date"] - merged["week_obs"]).dt.days
    merged.loc[merged["week_obs"].isna(), value_cols] = np.nan
    merged.loc[staleness > max_stale_days, value_cols] = np.nan

    out = pd.DataFrame({"Date": merged["Date"].values})
    for vc in value_cols:
        out[vc] = merged[vc].astype(float)
        out[vc] = out[vc].shift(1)
        out.loc[staleness > max_stale_days, vc] = np.nan
    for vc in ("ethanol_production_kbd", "ethanol_stocks_kbbl"):
        if vc not in out.columns:
            out[vc] = np.nan
    return out


def _add_curve_proxies(df: pd.DataFrame, db: pd.DataFrame | None = None) -> None:
    """Add futures curve proxy signals derived from existing market data.

    Since we have only front-month prices (no F2/F3), we proxy the term
    structure via price position relative to historical averages.
    `db` is the raw database DataFrame with corn_close before it is dropped
    by build_market_features(). Mutates `df` in place.
    """
    # Retrieve corn_close from db (raw price not kept in features)
    price_src = db if (db is not None and "corn_close" in db.columns) else df
    if "corn_close" in price_src.columns:
        raw_price = price_src[["Date", "corn_close"]].copy() if "Date" in price_src.columns else None
        if raw_price is not None:
            merged = df[["Date"]].merge(raw_price, on="Date", how="left")
            price = merged["corn_close"].astype(float)
            sma252 = price.rolling(252, min_periods=126).mean()
            df["curve_backwardation_proxy"] = ((price - sma252) / sma252.replace(0, np.nan)).shift(1).values
            high52 = price.rolling(252, min_periods=126).max()
            low52 = price.rolling(252, min_periods=126).min()
            spread52 = (high52 - low52).replace(0, np.nan)
            df["curve_price_position_52w"] = ((price - low52) / spread52).shift(1).values

    if "cot_open_interest" in df.columns:
        oi = df["cot_open_interest"].astype(float)
        df["oi_change_5d"] = oi.pct_change(5).shift(1)
        df["oi_change_20d"] = oi.pct_change(20).shift(1)

    if "corn_volume_z20" in df.columns and "cot_open_interest" in df.columns:
        oi = df["cot_open_interest"].astype(float).replace(0, np.nan)
        df["volume_oi_ratio_proxy"] = df["corn_volume_z20"] / oi.rolling(20).mean()


def _add_macro_extended(df: pd.DataFrame) -> None:
    """Add derived extended macro features from existing macro_fred columns.

    Columns may have a ``macro_fred_`` prefix (from legacy database merge).
    Mutates `df` in place.
    """
    def _get(name: str) -> pd.Series | None:
        for candidate in (name, f"macro_fred_{name}"):
            if candidate in df.columns:
                return df[candidate].astype(float)
        return None

    rfr = _get("real_fed_rate")
    if rfr is not None:
        df["real_rate_change_1m"] = rfr.diff(21).shift(1)
        df["real_rate_change_3m"] = rfr.diff(63).shift(1)

    ff = _get("fedfunds")
    if ff is not None:
        mu = ff.expanding(252).mean()
        sd = ff.expanding(252).std().replace(0, np.nan)
        df["fedfunds_level_zscore"] = ((ff - mu) / sd).shift(1)

    cpi = _get("cpi_yoy_pct")
    if cpi is not None:
        df["cpi_acceleration_3m"] = cpi.diff(63).shift(1)


def _add_cot_changes(df: pd.DataFrame) -> None:
    """Add weekly COT position changes (V3-06). Mutates df in place.

    cot_mm_long_chg / cot_mm_short_chg : managed money weekly diff
    cot_pm_long_chg / cot_pm_short_chg : producer/merchant weekly diff
    cot_producer_hedge_ratio            : producer short / (producer long + 1)

    COT is published Friday for the prior Tuesday → shift(1) already applied
    upstream; here we compute diff then shift(1) to keep anti-leakage.
    """
    for base_col, chg_col in [
        ("cot_mm_long", "cot_mm_long_chg"),
        ("cot_mm_short", "cot_mm_short_chg"),
        ("cot_pm_long", "cot_pm_long_chg"),
        ("cot_pm_short", "cot_pm_short_chg"),
    ]:
        if base_col in df.columns:
            df[chg_col] = df[base_col].astype(float).diff(1).shift(1)

    if "cot_pm_long" in df.columns and "cot_pm_short" in df.columns:
        pm_long = df["cot_pm_long"].astype(float).replace(0, np.nan)
        pm_short = df["cot_pm_short"].astype(float)
        df["cot_producer_hedge_ratio"] = (pm_short / (pm_long + 1.0)).shift(1)


def _add_spread_features(df: pd.DataFrame, db: pd.DataFrame | None = None) -> None:
    """Add inter-commodity log-ratio spread features (V3-06). Mutates df in place.

    spread_corn_wheat : log(corn_close / wheat_close)
    spread_corn_soja  : log(corn_close / soy_close)

    Prices are contemporaneous (not fundamentals) → shift(1) for daily alignment.
    Already-computed ratio columns (corn_wheat_ratio, corn_soy_ratio) contain
    simple linear ratios; we add explicit log-ratio spreads here.
    """
    price_src = db if (db is not None and "corn_close" in db.columns) else df
    if "corn_close" not in price_src.columns:
        return

    corn_col = (
        price_src[["Date", "corn_close"]].merge(df[["Date"]], on="Date", how="right")["corn_close"]
        if "Date" in price_src.columns else None
    )
    if corn_col is None:
        return
    corn = corn_col.astype(float).replace(0, np.nan)

    for peer, out_name in [("wheat_close", "spread_corn_wheat"), ("soy_close", "spread_corn_soja")]:
        if peer in price_src.columns:
            if "Date" in price_src.columns:
                peer_col = price_src[["Date", peer]].merge(df[["Date"]], on="Date", how="right")[peer]
            else:
                peer_col = price_src[peer]
            peer_vals = peer_col.astype(float).replace(0, np.nan)
            df[out_name] = np.log(corn / peer_vals).shift(1).values


def _add_world_supply(df: pd.DataFrame, wasde: pd.DataFrame) -> None:
    """Extract world balance sheet signal from WASDE world tables if available.

    Looks for world ending stocks, world use and world exports columns.
    Mutates `df` in place.
    """
    wasde = wasde.copy()
    wasde["Date"] = pd.to_datetime(wasde["Date"])

    # Flexible column detection for world supply metrics
    world_stocks = next(
        (c for c in wasde.columns if "world" in c.lower() and "ending" in c.lower() and "stock" in c.lower()),
        None,
    )
    world_use = next(
        (c for c in wasde.columns if "world" in c.lower() and ("use" in c.lower() or "consumption" in c.lower())),
        None,
    )
    world_exports = next(
        (c for c in wasde.columns if "world" in c.lower() and "export" in c.lower()),
        None,
    )

    if world_stocks is None:
        return  # No world data in this WASDE schema

    # Compute world stocks/use ratio (global tightness)
    if world_use is not None:
        merged = df[["Date"]].merge(
            wasde[["Date", world_stocks, world_use]], on="Date", how="left"
        )
        stocks_val = merged[world_stocks].astype(float)
        use_val = merged[world_use].astype(float).replace(0, np.nan)
        ratio = stocks_val / use_val
        df["world_stocks_use_ratio"] = ratio.shift(1).values
    else:
        merged = df[["Date"]].merge(wasde[["Date", world_stocks]], on="Date", how="left")
        df["world_ending_stocks"] = merged[world_stocks].astype(float).shift(1).values

    if world_exports is not None:
        merged_exp = df[["Date"]].merge(wasde[["Date", world_exports]], on="Date", how="left")
        df["world_exports"] = merged_exp[world_exports].astype(float).shift(1).values


def build_features(
    interim_dir: Path | str = INTERIM_DIR,
    out: Path | str = FEATURES_PARQUET,
) -> pd.DataFrame:
    """Build the complete features parquet.

    Reads everything available in ``data/interim/`` and applies feature
    engineering. Missing sources are skipped with a warning.
    """
    interim_dir = Path(interim_dir)

    # Anchor on market history (lazy: fall back to legacy if needed)
    market_path = interim_dir / "database.parquet"
    if not market_path.exists():
        # Fall back to legacy CSV
        from mais.paths import LEGACY_DATABASE_CSV
        if LEGACY_DATABASE_CSV.exists():
            log.warning("features_using_legacy_csv", path=str(LEGACY_DATABASE_CSV))
            db = read_table(LEGACY_DATABASE_CSV, date_col="Date")
            from mais.utils import dedupe_columns
            db = dedupe_columns(db)
        else:
            raise FileNotFoundError(
                f"Neither {market_path} nor {LEGACY_DATABASE_CSV} exists. "
                "Run `mais migrate-legacy` or `mais collect all` first."
            )
    else:
        db = read_table(market_path, date_col="Date")

    out_df = pd.DataFrame({"Date": pd.to_datetime(db["Date"])})

    # 1) Market features (returns, vols, technical indicators)
    try:
        market_feats = build_market_features(db)
        out_df = out_df.merge(market_feats, on="Date", how="left")
        log.info("features_market_added", n=market_feats.shape[1] - 1)
    except Exception as e:
        log.warning("features_market_failed", error=str(e))

    # 2) Belt-weighted weather (Phase 1 NEW - replaces 280 wx_* columns)
    meteo_path = interim_dir / "meteo.parquet"
    if meteo_path.exists():
        try:
            wx = read_table(meteo_path, date_col="Date")
            belt_feats = build_weather_belt_features(wx)
            out_df = out_df.merge(belt_feats, on="Date", how="left")
            log.info("features_weather_belt_added", n=belt_feats.shape[1] - 1)
        except Exception as e:
            log.warning("features_weather_belt_failed", error=str(e))

    # 3) Calendar (USDA event calendar)
    cal_path = interim_dir / "usda_calendar.parquet"
    if cal_path.exists():
        try:
            cal = read_table(cal_path, date_col="Date")
            out_df = out_df.merge(cal, on="Date", how="left")
            log.info("features_calendar_added", n=cal.shape[1] - 1)
        except Exception as e:
            log.warning("features_calendar_failed", error=str(e))

    # 4) Seasonality (Fourier, agronomic seasons)
    seas = build_seasonality_features(out_df["Date"])
    out_df = out_df.merge(seas, on="Date", how="left")
    log.info("features_seasonality_added", n=seas.shape[1] - 1)

    pheno = build_phenology_features(out_df["Date"])
    out_df = out_df.merge(pheno, on="Date", how="left")
    log.info("features_phenology_added", n=pheno.shape[1] - 1)

    # 5) Add WASDE / fundamentals + surprise variants
    fundamentals_path = interim_dir / "wasde.parquet"
    if fundamentals_path.exists():
        try:
            fund = read_table(fundamentals_path, date_col="Date")
            fund = add_surprise_features(fund, exclude_cols=["Date"])
            out_df = out_df.merge(fund, on="Date", how="left")
            log.info("features_wasde_added", n=fund.shape[1] - 1)
        except Exception as e:
            log.warning("features_wasde_failed", error=str(e))

    # 6) CFTC COT (weekly positioning + surprise variants)
    cot_path = interim_dir / "cftc_cot.parquet"
    if cot_path.exists():
        try:
            cot = read_table(cot_path, date_col="Date")
            cot = add_surprise_features(cot, exclude_cols=["Date"])
            cot_reindexed = (
                cot.set_index("Date")
                .reindex(out_df["Date"])
                .ffill()
                .shift(1)
                .reset_index()
                .rename(columns={"index": "Date"})
            )
            out_df = out_df.merge(cot_reindexed, on="Date", how="left")
            log.info("features_cftc_cot_added", n=cot.shape[1] - 1)
            try:
                _add_cot_changes(out_df)
                log.info("features_cot_changes_added")
            except Exception as e_cot:
                log.warning("features_cot_changes_failed", error=str(e_cot))
            try:
                cot_advanced = build_cot_advanced_features(out_df)
                out_df = out_df.merge(cot_advanced, on="Date", how="left")
                log.info("features_cot_advanced_added", n=len(cot_advanced.columns) - 1)
            except Exception as e_cot_adv:
                log.warning("features_cot_advanced_failed", error=str(e_cot_adv))
        except Exception as e:
            log.warning("features_cftc_cot_failed", error=str(e))

    # 7) US Drought Monitor (weekly → daily, staleness cap, shift(1))
    drought_candidates = (
        interim_dir / "drought_monitor.parquet",
        interim_dir / "us_drought_monitor.parquet",
    )
    for drought_path in drought_candidates:
        if not drought_path.exists():
            continue
        try:
            drought_w = read_table(drought_path, date_col="Date")
            drought_daily = _drought_weekly_to_daily(out_df["Date"], drought_w)
            out_df = out_df.merge(drought_daily, on="Date", how="left")
            log.info("features_drought_added", path=str(drought_path), n=len(drought_daily.columns) - 1)
            break
        except Exception as e:
            log.warning("features_drought_failed", path=str(drought_path), error=str(e))

    # 8) FAS export sales (weekly → daily, staleness cap, shift(1))
    fas_path = interim_dir / "fas_export_sales.parquet"
    if fas_path.exists():
        try:
            fas_w = read_table(fas_path, date_col="Date")
            fas_daily = _fas_weekly_to_daily(out_df["Date"], fas_w)
            out_df = out_df.merge(fas_daily, on="Date", how="left")
            log.info("features_fas_export_added", path=str(fas_path), n=len(fas_daily.columns) - 1)
        except Exception as e:
            log.warning("features_fas_export_failed", path=str(fas_path), error=str(e))
    else:
        out_df["export_sales_mt"] = np.nan
        for col in [
            "export_sales_weekly_mt",
            "export_sales_accumulated_mt",
            "export_pace_vs_usda_forecast",
            "export_pace_vs_5y_avg",
            "export_sales_weekly_zscore",
            "export_china_pct_total",
            "export_momentum_4w",
            "export_vs_same_week_last_year",
        ]:
            out_df[col] = np.nan
        log.warning("features_fas_export_missing_schema_only")

    # 9) NASS Crop Progress (weekly → daily, May-Oct seasonal, shift(1))
    crop_progress_candidates = (
        interim_dir / "crop_progress.parquet",
        interim_dir.parent / "raw" / "usda_nass_crop_progress" / "crop_progress.parquet",
    )
    _cp_found = False
    for cp_path in crop_progress_candidates:
        if not cp_path.exists():
            continue
        try:
            cp_w = read_table(cp_path, date_col="Date")
            cp_daily = _crop_progress_weekly_to_daily(out_df["Date"], cp_w)
            out_df = out_df.merge(cp_daily, on="Date", how="left")
            log.info("features_crop_progress_added", path=str(cp_path), n=len(cp_daily.columns) - 1)
            _cp_found = True
            break
        except Exception as e:
            log.warning("features_crop_progress_failed", path=str(cp_path), error=str(e))
    if not _cp_found:
        out_df["condition_gd_ex_pct"] = np.nan
        for col in [
            "crop_ge_pct",
            "crop_ge_pct_vs_last_year",
            "crop_ge_5y_avg_deviation",
            "crop_ge_zscore_seasonal",
            "crop_planted_pct",
            "crop_silked_pct",
            "crop_mature_pct",
            "crop_harvested_pct",
            "crop_condition_momentum_2w",
            "crop_condition_available",
            "crop_ge_pct_filled",
        ]:
            out_df[col] = np.nan
        log.warning("features_crop_progress_missing_schema_only")

    # 10) EIA Ethanol (weekly → daily, pub lag 6 days, shift(1))
    eia_path = interim_dir / "eia_ethanol.parquet"
    if eia_path.exists():
        try:
            eia_w = read_table(eia_path, date_col="Date")
            eia_daily = _eia_weekly_to_daily(out_df["Date"], eia_w)
            out_df = out_df.merge(eia_daily, on="Date", how="left")
            log.info("features_eia_ethanol_added", path=str(eia_path), n=len(eia_daily.columns) - 1)
        except Exception as e:
            log.warning("features_eia_ethanol_failed", path=str(eia_path), error=str(e))
    else:
        out_df["ethanol_production_kbd"] = np.nan
        out_df["ethanol_stocks_kbbl"] = np.nan
        log.warning("features_eia_ethanol_missing_schema_only")

    # 10b) Macro FRED (fedfunds, CPI, real rate) — shift(1) applied
    macro_fred_path = interim_dir / "macro_fred.parquet"
    if macro_fred_path.exists():
        try:
            mf = read_table(macro_fred_path, date_col="Date")
            mf_daily = (
                mf.set_index("Date")
                .reindex(out_df["Date"])
                .ffill()
                .shift(1)
                .reset_index()
                .rename(columns={"index": "Date"})
            )
            out_df = out_df.merge(mf_daily, on="Date", how="left")
            log.info("features_macro_fred_added", n=mf.shape[1] - 1)
        except Exception as e:
            log.warning("features_macro_fred_failed", error=str(e))

    # 10c) ENSO / ONI NOAA (monthly climate regime → daily, shift(1))
    enso_path = interim_dir / "enso_oni.parquet"
    if enso_path.exists():
        try:
            from mais.collect.enso import build_enso_features

            enso_m = read_table(enso_path, date_col="Date")
            enso_daily = build_enso_features(enso_m, out_df["Date"])
            out_df = out_df.merge(enso_daily, on="Date", how="left")
            log.info("features_enso_added", path=str(enso_path), n=len(enso_daily.columns) - 1)
        except Exception as e:
            log.warning("features_enso_failed", path=str(enso_path), error=str(e))
    else:
        for col in [
            "enso_oni_index",
            "enso_regime",
            "enso_lag3_oni",
            "enso_accumulated_6m",
            "enso_el_nino_flag",
            "enso_la_nina_flag",
        ]:
            out_df[col] = np.nan
        log.warning("features_enso_missing_schema_only")

    # 11) Futures curve spreads — real contracts if diagnostic/source available
    curve_path = interim_dir / "futures_curve.parquet"
    if curve_path.exists():
        try:
            curve = read_table(curve_path, date_col="Date")
            spot = (
                db[["Date", "corn_close"]].merge(out_df[["Date"]], on="Date", how="right")["corn_close"]
                if "corn_close" in db.columns
                else None
            )
            curve_daily = build_curve_spread_features(curve, spot=spot)
            out_df = out_df.merge(curve_daily, on="Date", how="left")
            log.info("features_curve_spreads_added", path=str(curve_path), n=len(curve_daily.columns) - 1)
        except Exception as e:
            log.warning("features_curve_spreads_failed", path=str(curve_path), error=str(e))
    else:
        for col in [
            "curve_zh_spread",
            "curve_kn_spread",
            "curve_nz_spread",
            "curve_contango_flag",
            "curve_zh_spread_ma20",
            "curve_zh_spread_zscore",
            "curve_backwardation_flag",
        ]:
            out_df[col] = np.nan
        log.warning("features_curve_spreads_missing_schema_only")

    # 11a) Futures curve proxy — derived from existing market + COT data
    try:
        _add_curve_proxies(out_df, db=db)
        log.info("features_curve_proxies_added")
    except Exception as e:
        log.warning("features_curve_proxies_failed", error=str(e))

    # 11b) Inter-commodity spread features (V3-06)
    try:
        _add_spread_features(out_df, db=db)
        log.info("features_spread_added")
    except Exception as e:
        log.warning("features_spread_failed", error=str(e))

    # 11c) Euronext EMA curve + continuous features, if DATA-MASTER-01 inputs exist.
    try:
        ema_features = build_ema_features(out_df["Date"])
        ema_feature_count = len(ema_features.columns) - 1
        if ema_feature_count > 0:
            out_df = out_df.merge(ema_features, on="Date", how="left")
        log.info("features_ema_added", n=ema_feature_count)
    except Exception as e:
        log.warning("features_ema_failed", error=str(e))

    # 12) Extended macro derived features
    # Real rates, rate change velocity, CPI momentum — from existing macro_fred
    try:
        _add_macro_extended(out_df)
        log.info("features_macro_extended_added")
    except Exception as e:
        log.warning("features_macro_extended_failed", error=str(e))

    # 13) World supply from WASDE world tables
    # Extracts world ending stocks/use if available in wasde.parquet
    fundamentals_path = interim_dir / "wasde.parquet"
    if fundamentals_path.exists():
        try:
            _add_world_supply(out_df, read_table(fundamentals_path, date_col="Date"))
            log.info("features_world_supply_added")
        except Exception as e:
            log.warning("features_world_supply_failed", error=str(e))

    # Final: deduplicate, sort, write
    from mais.utils import dedupe_columns
    out_df = dedupe_columns(out_df).sort_values("Date").reset_index(drop=True)
    write_parquet(out_df, out)
    log.info("features_written", out=str(out), rows=len(out_df), cols=out_df.shape[1])
    return out_df


def build_multi_horizon_targets(
    price_series: pd.Series | pd.DataFrame,
    horizons: list[int] | tuple[int, ...],
    price_col: str = "corn_close",
) -> pd.DataFrame:
    """Build continuous and binary future-return targets for many horizons.

    The feature row at date ``t`` is paired with ``log(price[t + H] / price[t])``.
    No feature is shifted forward; only the target looks ahead by construction.
    """
    if isinstance(price_series, pd.DataFrame):
        if price_col not in price_series.columns:
            raise KeyError(f"{price_col!r} not found in price_series DataFrame")
        price = pd.to_numeric(price_series[price_col], errors="coerce")
        out = pd.DataFrame(index=price_series.index)
        if "Date" in price_series.columns:
            out["Date"] = pd.to_datetime(price_series["Date"]).values
    else:
        price = pd.to_numeric(price_series, errors="coerce")
        out = pd.DataFrame(index=price.index)
        if price.index.name == "Date" or isinstance(price.index, pd.DatetimeIndex):
            out["Date"] = pd.to_datetime(price.index).values

    for horizon in horizons:
        h = int(horizon)
        future_return = np.log(price.shift(-h) / price)
        out[f"y_cont_h{h}"] = future_return.astype(float)
        out[f"y_up_h{h}"] = (future_return > 0.0).astype(float)
        out.loc[future_return.isna(), f"y_up_h{h}"] = np.nan
        out[f"y_up_gt_3pct_h{h}"] = (future_return > 0.03).astype(float)
        out.loc[future_return.isna(), f"y_up_gt_3pct_h{h}"] = np.nan
        out[f"y_down_gt_3pct_h{h}"] = (future_return < -0.03).astype(float)
        out.loc[future_return.isna(), f"y_down_gt_3pct_h{h}"] = np.nan

    return out.reset_index(drop=True)


__all__ = [
    "build_features",
    "build_factors",
    "save_factors",
    "FactorBuildResult",
    "build_multi_horizon_targets",
]

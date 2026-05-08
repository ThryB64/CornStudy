"""Feature engineering modules.

Each sub-module produces a DataFrame indexed by ``Date`` with one or several
columns. ``build_features()`` orchestrates them into the unified parquet at
``data/processed/features.parquet``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.paths import FEATURES_PARQUET, INTERIM_DIR
from mais.utils import get_logger, read_table, write_parquet

from .market import build_market_features
from .weather_belt import build_weather_belt_features
from .surprise import add_surprise_features
from .seasonality import build_seasonality_features
from .factors import build_factors, save_factors, FactorBuildResult

log = get_logger("mais.features")


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

    # 6) FRED macro (monetary policy + inflation)
    macro_path = interim_dir / "macro_fred.parquet"
    if macro_path.exists():
        try:
            macro = read_table(macro_path, date_col="Date")
            # Monthly data: reindex to market dates, forward-fill, shift 1 (anti-leakage)
            macro_reindexed = (
                macro.set_index("Date")
                .reindex(out_df["Date"])
                .ffill()
                .shift(1)
                .reset_index()
                .rename(columns={"index": "Date"})
            )
            out_df = out_df.merge(macro_reindexed, on="Date", how="left")
            log.info("features_macro_fred_added", n=macro.shape[1] - 1)
        except Exception as e:
            log.warning("features_macro_fred_failed", error=str(e))

    # 7) NASS QuickStats (area, yield, production, quarterly stocks) + surprise variants
    quickstats_path = interim_dir / "quickstats.parquet"
    if quickstats_path.exists():
        try:
            qs = read_table(quickstats_path, date_col="Date")
            qs = add_surprise_features(qs, exclude_cols=["Date"])
            # Annual/quarterly data: reindex to market dates, forward-fill, shift 1 (anti-leakage)
            qs_reindexed = (
                qs.set_index("Date")
                .reindex(out_df["Date"])
                .ffill()
                .shift(1)
                .reset_index()
                .rename(columns={"index": "Date"})
            )
            out_df = out_df.merge(qs_reindexed, on="Date", how="left")
            log.info("features_quickstats_added", n=qs.shape[1] - 1)
        except Exception as e:
            log.warning("features_quickstats_failed", error=str(e))

    # 8) Production state shares (geographic concentration)
    prod_path = interim_dir / "production.parquet"
    if prod_path.exists():
        try:
            prod = read_table(prod_path, date_col="Date")
            # Only state-share columns — national aggregates already come from quickstats
            share_cols = [c for c in prod.columns if c.startswith("share_")]
            if share_cols:
                prod_shares = prod[["Date"] + share_cols]
                prod_reindexed = (
                    prod_shares.set_index("Date")
                    .reindex(out_df["Date"])
                    .ffill()
                    .shift(1)
                    .reset_index()
                    .rename(columns={"index": "Date"})
                )
                out_df = out_df.merge(prod_reindexed, on="Date", how="left")
                log.info("features_production_shares_added", n=len(share_cols))
        except Exception as e:
            log.warning("features_production_shares_failed", error=str(e))

    # 9) CFTC COT — weekly speculative positioning (3-day publication lag)
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
            log.info("features_cot_added", n=cot.shape[1] - 1)
        except Exception as e:
            log.warning("features_cot_failed", error=str(e))

    # 10) EIA ethanol — if parquet exists (requires EIA_API_KEY, 6-day lag)
    eia_path = interim_dir / "eia_ethanol.parquet"
    if eia_path.exists():
        try:
            eia = read_table(eia_path, date_col="Date")
            eia = add_surprise_features(eia, exclude_cols=["Date"])
            eia_reindexed = (
                eia.set_index("Date")
                .reindex(out_df["Date"])
                .ffill()
                .shift(1)
                .reset_index()
                .rename(columns={"index": "Date"})
            )
            out_df = out_df.merge(eia_reindexed, on="Date", how="left")
            log.info("features_eia_ethanol_added", n=eia.shape[1] - 1)
        except Exception as e:
            log.warning("features_eia_ethanol_failed", error=str(e))
    else:
        # Ethanol proxy: corn-oil spread as crush margin approximation
        if "corn_close" in db.columns and "oil_close" in db.columns:
            try:
                proxy = pd.DataFrame({"Date": out_df["Date"]})
                corn_p = pd.to_numeric(db.set_index("Date")["corn_close"]
                                       .reindex(out_df["Date"]).ffill(), errors="coerce")
                oil_p = pd.to_numeric(db.set_index("Date")["oil_close"]
                                      .reindex(out_df["Date"]).ffill(), errors="coerce")
                # Corn-to-oil ratio (proxy for ethanol margin): higher oil vs corn = better crush
                proxy["ethanol_proxy_crush_margin"] = (oil_p / corn_p.replace(0, float("nan"))).shift(1)
                out_df = out_df.merge(proxy, on="Date", how="left")
                log.info("features_ethanol_proxy_added")
            except Exception as e:
                log.warning("features_ethanol_proxy_failed", error=str(e))

    # Final: deduplicate, sort, write
    from mais.utils import dedupe_columns
    out_df = dedupe_columns(out_df).sort_values("Date").reset_index(drop=True)
    write_parquet(out_df, out)
    log.info("features_written", out=str(out), rows=len(out_df), cols=out_df.shape[1])
    return out_df


__all__ = ["build_features", "build_factors", "save_factors", "FactorBuildResult"]

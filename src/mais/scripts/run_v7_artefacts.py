"""Génère tous les artefacts manquants pour les tickets V7 déjà codés."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

ARTEFACTS = ROOT / "artefacts" / "v7"
ARTEFACTS.mkdir(parents=True, exist_ok=True)


def load_data():
    df = pd.read_parquet(ROOT / "data/processed/features.parquet")
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index)

    # Add corn_close / ema_close / cbot_close aliases from raw sources
    market_path = ROOT / "data/interim/market.parquet"
    if market_path.exists():
        mk = pd.read_parquet(market_path)
        if "Date" in mk.columns:
            mk = mk.set_index("Date")
        mk.index = pd.to_datetime(mk.index)
        for col in ["corn_close", "wheat_close", "soy_close", "oats_close"]:
            if col in mk.columns and col not in df.columns:
                df[col] = mk[col]
        # cbot_close alias
        if "corn_close" in df.columns:
            df["cbot_close"] = df["corn_close"]

    # Add EMA front close from euronext parquet
    ema_raw_path = ROOT / "data/processed/euronext/ema_front_continuous_raw.parquet"
    if ema_raw_path.exists():
        ema_raw = pd.read_parquet(ema_raw_path)
        if "date" in ema_raw.columns:
            ema_raw["date"] = pd.to_datetime(ema_raw["date"])
            ema_raw = ema_raw.set_index("date")["price"].rename("ema_close")
        elif "Date" in ema_raw.columns:
            ema_raw = ema_raw.set_index("Date")["price"].rename("ema_close")
            ema_raw.index = pd.to_datetime(ema_raw.index)
        else:
            ema_raw = ema_raw["price"].rename("ema_close")
        df["ema_close"] = ema_raw

    # cbot_close_eur alias (CBOT in EUR/t, already available)
    if "cbot_eur_t" in df.columns and "cbot_close_eur" not in df.columns:
        df["cbot_close_eur"] = df["cbot_eur_t"]

    # Derive eurusd from cbot_close + cbot_eur_t
    if "cbot_close" in df.columns and "cbot_eur_t" in df.columns and "eurusd" not in df.columns:
        # cbot_eur_t = cbot_close * 36.744 / eurusd
        # eurusd = cbot_close * 36.744 / cbot_eur_t
        eurusd_derived = (df["cbot_close"] * 36.744) / df["cbot_eur_t"]
        df["eurusd"] = eurusd_derived.replace([np.inf, -np.inf], np.nan)

    # Add EMA targets
    ema_t_path = ROOT / "data/processed/euronext/ema_targets.parquet"
    ema_t = pd.read_parquet(ema_t_path) if ema_t_path.exists() else pd.DataFrame()
    if "Date" in ema_t.columns:
        ema_t = ema_t.set_index("Date")
    if not ema_t.empty:
        ema_t.index = pd.to_datetime(ema_t.index)

    cbot_t = pd.read_parquet(ROOT / "data/processed/targets.parquet")
    if "Date" in cbot_t.columns:
        cbot_t = cbot_t.set_index("Date")
    cbot_t.index = pd.to_datetime(cbot_t.index)

    merged = df.join(ema_t, how="left")
    # Avoid duplicate cols from cbot_t
    new_cols = [c for c in cbot_t.columns if c not in merged.columns]
    merged = merged.join(cbot_t[new_cols], how="left")
    return merged


def run_v7_31(df: pd.DataFrame):
    """V7-31 benchmark_suite artefact."""
    out = ARTEFACTS / "benchmark_suite.json"
    if out.exists():
        print("  V7-31 artefact already exists, skipping")
        return
    from mais.research.benchmark_suite import save_benchmark_suite

    targets = {}
    for col in df.columns:
        if col.startswith("y_up_h") or col.startswith("y_rel_outperform"):
            s = df[col].dropna()
            if len(s) > 200 and 0.2 <= s.mean() <= 0.8:
                targets[col] = s
        if len(targets) >= 8:
            break

    prices = df.get("ema_front_price", df.get("cbot_eur_t"))
    basis = df.get("ema_cbot_basis")
    result = save_benchmark_suite(targets, prices, basis)
    print(f"  V7-31: {result['n_targets']} targets, {len(result['benchmarks'])} benchmarks")


def run_v7_04(df: pd.DataFrame):
    """V7-04 cbot_target_lab artefact."""
    out = ARTEFACTS / "cbot_target_lab.json"
    if out.exists():
        print("  V7-04 artefact already exists, skipping")
        return
    from mais.research.cbot_target_lab_v7 import save_target_lab

    result = save_target_lab(df)
    print(f"  V7-04: {result['n_targets']} targets, {result['n_balanced_targets']} balanced")


def run_v7_39(df: pd.DataFrame):
    """V7-39 data_quality artefact."""
    out = ARTEFACTS / "data_quality_scores.json"
    if out.exists():
        print("  V7-39 artefact already exists, skipping")
        return
    from mais.features.data_quality import save_quality_scores

    result = save_quality_scores(df)
    print(f"  V7-39: mean_quality={result.get('mean_quality', 'N/A'):.3f}")


def run_v7_06(df: pd.DataFrame):
    """V7-06 seasonal_experts artefact."""
    out = ARTEFACTS / "seasonal_experts.json"
    if out.exists():
        print("  V7-06 artefact already exists, skipping")
        return
    from mais.research.seasonal_experts_v7 import save_seasonal_experts

    y_col = "y_rel_outperform_h40" if "y_rel_outperform_h40" in df.columns else "y_up_h20_ema"
    if y_col not in df.columns:
        print(f"  V7-06: target {y_col} not found, skipping")
        return
    y = df[y_col].dropna()
    dates = y.index
    result = save_seasonal_experts(dates, y)
    print(f"  V7-06: {result.get('n_policies', 'N/A')} policies evaluated")


def run_v7_08(df: pd.DataFrame):
    """V7-08 basis_regimes artefact."""
    out = ARTEFACTS / "basis_regimes.json"
    if out.exists():
        print("  V7-08 artefact already exists, skipping")
        return
    from mais.research.basis_regimes_v7 import save_basis_regimes

    result = save_basis_regimes(df)
    print(f"  V7-08: {result['n_dates']} dates, dominant={result['dominant_regime']}")


def run_v7_07(df: pd.DataFrame):
    """V7-07 roll_risk artefact."""
    out = ARTEFACTS / "roll_aware_premium.json"
    if out.exists():
        print("  V7-07 artefact already exists, skipping")
        return
    from mais.features.roll_risk import compute_roll_aware_report

    report = compute_roll_aware_report(df)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"  V7-07: roll_risk computed, n_high_risk={report.get('n_high_risk_days', 'N/A')}")


def run_v7_09(df: pd.DataFrame):
    """V7-09 ema_decomposition artefact."""
    out = ARTEFACTS / "ema_decomposition.json"
    if out.exists():
        print("  V7-09 artefact already exists, skipping")
        return
    from mais.research.ema_decomposition_v7 import save_ema_decomposition

    result = save_ema_decomposition(df)
    print(f"  V7-09: decomposed {result.get('n_obs', 'N/A')} obs")


def run_v7_10(df: pd.DataFrame):
    """V7-10 event_study artefact."""
    out = ARTEFACTS / "event_study.json"
    if out.exists():
        print("  V7-10 artefact already exists, skipping")
        return
    from mais.research.event_study_v7 import save_event_study

    # Use EMA front or basis as price series
    prices = df.get("ema_cbot_basis", df.get("ema_front_price", df.get("cbot_eur_t")))
    if prices is None:
        print("  V7-10: no price series found, skipping")
        return
    result = save_event_study(prices.dropna())
    print(f"  V7-10: {result.get('n_event_types', 'N/A')} event types studied")


def run_v7_17(df: pd.DataFrame):
    """V7-17 inter_commodity artefact."""
    out = ARTEFACTS / "inter_commodity.json"
    if out.exists():
        print("  V7-17 artefact already exists, skipping")
        return
    from mais.features.inter_commodity import run_inter_commodity_analysis

    result = run_inter_commodity_analysis(df)
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"  V7-17: {result.get('n_spreads', 'N/A')} spreads computed")


def run_v7_19(df: pd.DataFrame):
    """V7-19 structural_breaks artefact."""
    out = ARTEFACTS / "structural_breaks.json"
    if out.exists():
        print("  V7-19 artefact already exists, skipping")
        return
    from mais.research.structural_breaks import save_structural_breaks

    result = save_structural_breaks(df)
    print(f"  V7-19: {result.get('n_breaks_tested', 'N/A')} breaks tested")


def run_v7_25(df: pd.DataFrame):
    """V7-25 market_anomalies artefact."""
    out = ARTEFACTS / "market_anomalies.json"
    if out.exists():
        print("  V7-25 artefact already exists, skipping")
        return
    from mais.research.market_anomalies import save_market_anomalies

    col = "corn_logret_1d"
    y_col = "y_up_h20"
    if col not in df.columns or y_col not in df.columns:
        print("  V7-25: missing cols, skipping")
        return
    returns = df[col].dropna()
    y = df[y_col].reindex(returns.index).dropna()
    returns = returns.reindex(y.index)
    result = save_market_anomalies(returns, y)
    print(f"  V7-25: {result.get('n_anomalies_tested', 'N/A')} anomalies tested")


if __name__ == "__main__":
    print("Loading data...")
    df = load_data()
    print(f"Data loaded: {df.shape}")

    print("\nGenerating V7 artefacts...")
    for fn in [run_v7_31, run_v7_04, run_v7_39, run_v7_06, run_v7_08, run_v7_07, run_v7_09, run_v7_10, run_v7_17, run_v7_19, run_v7_25]:
        try:
            print(f"\nRunning {fn.__name__}...")
            fn(df)
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nDone! Artefacts in artefacts/v7/")
    for f in sorted(ARTEFACTS.glob("*.json")):
        print(f"  {f.name}")

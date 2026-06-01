"""Runner V9 — indicateur structurel hybride + validation LOYO + backtest V4 + red team V2."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.indicator.structural_indicator_v9 import (  # noqa: E402
    compute_signals,
    fit_oof_structural,
    run_backtest_v4,
    run_indicator_v9,
    run_loyo,
    run_red_team_v2,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402


def _timed(name, fn, *args, **kwargs):
    print(f"\n[{name}]")
    t0 = time.time()
    r = fn(*args, **kwargs)
    print(f"  -> {name}: verdict={r.get('verdict')} ({time.time() - t0:.1f}s)")
    return r


if __name__ == "__main__":
    print("=" * 60)
    print("V9 — INDICATEUR STRUCTUREL PRIME EMA/CBOT")
    print("=" * 60)

    df = load_master_dataset()
    df = filter_out_holdout(df)
    print(f"master shape (no holdout): {df.shape}")

    ind = _timed("V9-IND-01 indicator", run_indicator_v9, df)
    print(f"  core_metrics: {ind.get('core_metrics')}")
    print(f"  signal_distribution: {ind.get('signal_distribution')}")
    print(f"  evaluation: {ind.get('evaluation')}")
    print(f"  latest snapshot: {ind.get('latest_actionable_snapshot')}")

    loyo = _timed("V9-IND-02 LOYO", run_loyo, df)
    print(f"  summary: {loyo.get('summary')}")

    # Backtest sur les signaux du cœur (réutilise un fit pour cohérence)
    fit = fit_oof_structural(df)
    signals = compute_signals(df, fit["oof_cal"]) if fit["verdict"] == "OK" else None
    bt = _timed("V9-IND-03 backtest V4", run_backtest_v4, df, signals)
    print(f"  n_trades: {bt.get('n_trades')}")
    print(f"  by_cost: {bt.get('by_cost_eur_t_per_leg')}")

    rt = _timed("V9-IND-04 red team V2", run_red_team_v2, df, 100)
    print(f"  p_value: {rt.get('p_value')} | observed_auc: {rt.get('observed_auc_cal')}")

    print("\nDONE V9.")

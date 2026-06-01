"""Runner V14 — indicateur short-only, survival de reversion, robustesse proxy."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v14_short_indicator import (  # noqa: E402
    run_proxy_robustness,
    run_reversion_survival,
    run_short_indicator,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402


def _timed(name, fn, *args):
    print(f"\n[{name}]")
    t0 = time.time()
    r = fn(*args)
    print(f"  -> verdict={r.get('verdict')} ({time.time() - t0:.1f}s)")
    return r


if __name__ == "__main__":
    print("=" * 60)
    print("V14 — INDICATEUR SHORT-ONLY + SURVIVAL + ROBUSTESSE PROXY")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V14-01 short indicator", run_short_indicator, df)
    print(f"  n_signals strict/relaxed: {a.get('n_signals_strict')}/{a.get('n_signals_relaxed')}")
    print(f"  relaxed: {a.get('relaxed_indicator')}")
    print(f"  baseline: {a.get('baseline_short_no_gates')}")
    print(f"  crisis-out: {a.get('leave_all_crises_out')}")
    print(f"  cost5/trade relaxed vs baseline: {a.get('relaxed_cost5_per_trade')} vs {a.get('baseline_cost5_per_trade')}")

    b = _timed("V14-02 reversion survival", run_reversion_survival, df)
    print(f"  median KM: {b.get('median_days_to_reversion_km')} | "
          f"P(<=40/60/90): {b.get('p_revert_by_40d')}/{b.get('p_revert_by_60d')}/{b.get('p_revert_by_90d')}")
    print(f"  by season: {b.get('median_by_season')}")

    c = _timed("V14-04 proxy robustness", run_proxy_robustness, df)
    print(f"  degradation 0->10eur: {c.get('pnl_degradation_0_to_10eur')} | robust: {c.get('edge_robust_to_10eur_noise')}")
    print(f"  results: {c.get('results_by_noise')}")

    print("\nDONE V14.")

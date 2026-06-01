"""Runner V11 — programme discipliné post-review V10."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v11_simplified_program import (  # noqa: E402
    run_basis_change_regression,
    run_cost_aware_decision,
    run_forward_regime_filter,
    run_promote_simplified,
    run_simple_rules_lab_v11,
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
    print("V11 — PROGRAMME DISCIPLINÉ (simplifié / régime / coûts / basis-change / règles)")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V11-01 promote simplified", run_promote_simplified, df)
    print(f"  auc_gain: {a.get('auc_gain')} | {a.get('recommendation')}")
    print(f"  comparison: {a.get('comparison')}")

    b = _timed("V11-02 forward regime filter", run_forward_regime_filter, df)
    print(f"  filtered: {b.get('forward_filtered')}")
    print(f"  baseline: {b.get('forward_baseline_no_filter')}")
    print(f"  chosen: {b.get('regime_chosen_per_year')}")

    c = _timed("V11-03 cost-aware decision", run_cost_aware_decision, df)
    print(f"  results: {c.get('results_by_cost')}")

    d = _timed("V11-04 basis-change regression", run_basis_change_regression, df)
    print(f"  results: {d.get('results_by_horizon')}")
    print(f"  best: {d.get('best_horizon_by_sign_da')}")

    e = _timed("V11-05 simple rules lab", run_simple_rules_lab_v11, df)
    print(f"  tested={e.get('n_rules_tested')} bh_sig={e.get('n_bh_significant_q10')} "
          f"profit_cost5={e.get('n_bh_significant_and_profitable_cost5')}")
    print(f"  survivors: {e.get('bh_significant_profitable_cost5')}")

    print("\nDONE V11.")

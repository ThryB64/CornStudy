"""Runner V13 — indicateur de mean-reversion du basis."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v13_basis_reversion_indicator import (  # noqa: E402
    append_premium_journal,
    run_basis_change_sign_models,
    run_conformal_recalibration,
    run_dynamic_exits,
    run_long_short_separated,
    run_short_rule_strict,
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
    print("V13 — INDICATEUR MEAN-REVERSION DU BASIS")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V13-02 dynamic exits", run_dynamic_exits, df)
    print(f"  short best by PnL: {a.get('best_short_by_mean_pnl')} | by profit/day: {a.get('best_short_by_profit_per_day')}")
    print(f"  short exits: {a.get('short_high_entries_z_gt_1')}")

    b = _timed("V13-03 short rule strict", run_short_rule_strict, df)
    print(f"  n={b.get('n_trades')} loyo years +: {b.get('loyo_years_positive')}/{b.get('loyo_years_evaluable')}")
    print(f"  crisis: {b.get('leave_one_crisis_out')}")
    print(f"  exit_compare: {b.get('exit_compare')}")

    c = _timed("V13-01 conformal recalibration", run_conformal_recalibration, df)
    print(f"  best_alpha: {c.get('best_alpha_config')}")
    print(f"  results: {c.get('results_by_alpha')}")

    d = _timed("V13-05 basis-change sign models", run_basis_change_sign_models, df)
    print(f"  best: {d.get('best_model')} auc={d.get('best_auc')}")
    print(f"  results: {d.get('results')}")

    e = _timed("V13-06 long/short separated", run_long_short_separated, df)
    print(f"  asymmetry: {e.get('asymmetry')}")

    j = append_premium_journal(df)
    print(f"\n[V13-07 journal] {j}")

    print("\nDONE V13.")

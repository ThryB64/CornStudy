"""Runner V12 — mean-reversion anatomy, forward rule validation, conformal abstention, journal."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v12_mean_reversion_lab import (  # noqa: E402
    build_premium_journal,
    evaluate_matured_journal,
    run_conformal_abstention,
    run_forward_rule_validation,
    run_reversion_anatomy,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402


def _timed(name, fn, *args):
    print(f"\n[{name}]")
    t0 = time.time()
    r = fn(*args)
    v = r.get("verdict") if isinstance(r, dict) else "DONE"
    print(f"  -> verdict={v} ({time.time() - t0:.1f}s)")
    return r


if __name__ == "__main__":
    print("=" * 60)
    print("V12 — MEAN-REVERSION LAB + FORWARD VALIDATION + CONFORMAL")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V12-A reversion anatomy", run_reversion_anatomy, df)
    print(f"  reversion_time: {a.get('reversion_time')}")
    print(f"  mae: {a.get('mean_adverse_excursion_eur_t')} | best_exit: {a.get('best_exit_by_mean_pnl')}")
    print(f"  exits: {a.get('exit_strategies')}")

    b = _timed("V12-B forward rule validation", run_forward_rule_validation, df)
    print(f"  robust both halves: {b.get('families_robust_both_halves')}")
    print(f"  results: {b.get('results_by_family')}")

    c = _timed("V12-C conformal abstention", run_conformal_abstention, df)
    print(f"  coverage: {c.get('empirical_interval_coverage')} (target {c.get('target_coverage')})")
    print(f"  DA no-abstention {c.get('sign_da_no_abstention')} (n={c.get('n_no_abstention')}) | "
          f"DA acted {c.get('sign_da_with_abstention')} (n={c.get('n_acted_after_abstention')})")
    print(f"  abstention_improves: {c.get('abstention_improves_da')}")

    journal = build_premium_journal(df)
    print(f"\n[V12-D journal] rows={len(journal)}")
    ev = evaluate_matured_journal(journal, df)
    print(f"  eval: {ev}")

    print("\nDONE V12.")

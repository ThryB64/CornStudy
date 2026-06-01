"""Runner V17 — indicateur research de prime EMA/CBOT (consolidation)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v17_research_indicator import (  # noqa: E402
    compute_indicator_v17,
    generate_daily_report,
    run_failure_analysis,
    run_trade_fiches,
    run_walk_forward_final,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402


def _timed(name, fn, *args):
    print(f"\n[{name}]")
    t0 = time.time()
    r = fn(*args)
    if isinstance(r, dict):
        print(f"  -> verdict={r.get('verdict')} ({time.time() - t0:.1f}s)")
    return r


if __name__ == "__main__":
    print("=" * 60)
    print("V17 — INDICATEUR RESEARCH PRIME EMA/CBOT")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    ind = compute_indicator_v17(df)
    dist = ind["signal"].value_counts().to_dict()
    print(f"\n[V17-01 indicator] distribution: {dist}")
    actionable = ind[~ind["signal"].isin(["NO_SIGNAL"])]
    if len(actionable):
        print(f"  latest: {actionable.index[-1].date()} -> {dict(actionable.iloc[-1])}")

    wf = _timed("V17-04 walk-forward final", run_walk_forward_final, df)
    print(f"  n={wf.get('n_trades')} hit={wf.get('hit_rate')} net_dyn={wf.get('net_pnl_dyncost_total')} "
          f"DD={wf.get('max_drawdown')} years+={wf.get('years_positive')}/{wf.get('years_total')}")

    tf = _timed("V17-05 trade fiches", run_trade_fiches, df)
    print(f"  n={tf.get('n_trades')} win_rate={tf.get('win_rate')} by_tier={tf.get('by_tier')}")
    print(f"  losing trades: {tf.get('losing_trades')}")

    fa = _timed("V17-06 failure analysis", run_failure_analysis, df)
    print(f"  losers profile: {fa.get('profile_losers')}")
    print(f"  warnings: {fa.get('warnings')}")

    print("\n[V17-02 daily report]")
    print(generate_daily_report(df))

    print("\nDONE V17.")

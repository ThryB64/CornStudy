"""Runner V15 — réalisme de l'indicateur short basis-haut."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v15_short_realism import (  # noqa: E402
    run_censored_archaeology,
    run_drawdown_study,
    run_dynamic_cost,
    run_partial_exits,
    run_position_sizing,
    run_season_aware_exits,
    run_strict_portfolio,
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
    print("V15 — RÉALISME INDICATEUR SHORT BASIS-HAUT")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V15-01 season-aware exits", run_season_aware_exits, df)
    print(f"  best net_cost3: {a.get('best_by_net_cost3')} | sa beats z0: {a.get('season_aware_beats_uniform_z0')}")
    print(f"  results: {a.get('results')}")

    b = _timed("V15-02 censored archaeology", run_censored_archaeology, df)
    print(f"  censored {b.get('n_censored')}/{b.get('n_entries')} | vetoes: {b.get('proposed_vetoes')}")
    print(f"  censored profile: {b.get('profile_censored')} | reverted: {b.get('profile_reverted')}")

    c = _timed("V15-03 drawdown study", run_drawdown_study, df)
    print(f"  MAE pct: {c.get('mae_percentiles_eur_t')} | stops: {c.get('stop_loss_tests')}")

    d = _timed("V15-04 partial exits", run_partial_exits, df)
    print(f"  best profit/day: {d.get('best_by_profit_per_day')}")
    print(f"  results: {d.get('results')}")

    e = _timed("V15-05 position sizing", run_position_sizing, df)
    print(f"  bucket: {e.get('pnl_by_entry_z_bucket')} | bigger->bigger edge: {e.get('bigger_anomaly_bigger_edge')}")

    f = _timed("V15-06 dynamic cost", run_dynamic_cost, df)
    print(f"  dyn net {f.get('net_pnl_dynamic_cost')} vs flat3 {f.get('net_pnl_flat_cost3')} | survives: {f.get('survives_dynamic_cost')}")

    g = _timed("V15-07 strict portfolio", run_strict_portfolio, df)
    print(f"  strict: {g.get('strict_one_at_a_time')}")
    print(f"  nonoverlap: {g.get('nonoverlap_40d')} | independent: {g.get('independent_events')}")

    print("\nDONE V15.")

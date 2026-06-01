"""Runner V10 — Market Discovery : 5 expériences de recherche quantitative."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v10_market_discovery import (  # noqa: E402
    run_basis_econometrics,
    run_cost_survival,
    run_feature_attribution,
    run_horizon_sweep,
    run_regime_conditioning,
    run_simplified_model,
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
    print("V10 — MARKET DISCOVERY")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V10-A basis econometrics", run_basis_econometrics, df)
    print(f"  basis_z: {a.get('basis_z')} | rolling: {a.get('rolling_half_life')}")

    b = _timed("V10-B feature attribution", run_feature_attribution, df)
    print(f"  ranking: {b.get('ranking')}")
    print(f"  importance: {b.get('permutation_importance')}")
    print(f"  sign_stable: {b.get('coef_sign_stable')}")

    c = _timed("V10-C horizon sweep", run_horizon_sweep, df)
    print(f"  results: {c.get('results')}")
    print(f"  best: {c.get('best_horizon')} auc={c.get('best_auc')}")

    d = _timed("V10-D cost survival", run_cost_survival, df)
    print(f"  baseline cost5: {d.get('baseline_all_trades_net_pnl_cost5')}")
    print(f"  selectivity: {d.get('selectivity_curve')}")
    print(f"  forward: {d.get('forward_learnable_threshold')}")

    e = _timed("V10-E regime conditioning", run_regime_conditioning, df)
    print(f"  by_regime: {e.get('results_by_regime')}")
    print(f"  best_regime: {e.get('best_regime')} auc={e.get('best_regime_auc')}")

    f = _timed("V10-F simplified model", run_simplified_model, df)
    print(f"  by_subset: {f.get('results_by_subset')}")
    print(f"  best: {f.get('best_subset')} auc={f.get('best_auc')} gain={f.get('auc_gain_vs_6vars')}")

    print("\nDONE V10.")

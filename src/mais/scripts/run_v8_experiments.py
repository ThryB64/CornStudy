"""Runner V8 — exécute le batch d'expériences scientifiques."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v8_experiments import (  # noqa: E402
    run_backtest_v3,
    run_basis_regime_v3,
    run_cbot_lab_plus,
    run_cross_market_v3,
    run_ema_premium_lab_plus,
    run_embargo_robustness,
    run_pcorrect_v3,
    run_red_team,
    run_seasonal_v3,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402


def _timed(name, fn, *args, **kwargs):
    print(f"\n[{name}]")
    t0 = time.time()
    try:
        r = fn(*args, **kwargs)
        dt = time.time() - t0
        verdict = r.get("verdict") or r.get("global_verdict") or "DONE"
        print(f"  → {name}: verdict={verdict} ({dt:.1f}s)")
        return r
    except Exception as e:
        print(f"  → {name}: ERROR {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("V8 EXPERIMENTS — Sprint 2 & 3 batch")
    print("=" * 60)

    print("\nLoading master dataset (no holdout)...")
    df = load_master_dataset()
    df = filter_out_holdout(df)
    print(f"  master shape: {df.shape}")

    _timed("V8-EMBARGO-ROBUSTNESS", run_embargo_robustness, df)
    _timed("V8-CBOT-LAB-PLUS", run_cbot_lab_plus, df)
    _timed("V8-EMA-PREMIUM-LAB-PLUS", run_ema_premium_lab_plus, df)
    _timed("V8-BASIS-REGIME-V3", run_basis_regime_v3, df)
    _timed("V8-SEASONAL-V3", run_seasonal_v3, df)
    _timed("V8-CROSS-MARKET-V3", run_cross_market_v3, df)
    _timed("V8-PCORRECT-V3", run_pcorrect_v3, df)
    _timed("V8-BACKTEST-V3", run_backtest_v3, df)
    _timed("V8-RED-TEAM-PREMIUM", run_red_team, df, n_perms=100)

    print("\nDONE V8 batch.")

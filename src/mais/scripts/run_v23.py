"""Runner V23 — risque drawdown CBOT + reversion conditionnelle au régime + snapshot forecast live."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v23_cbot_risk_and_regime import (  # noqa: E402
    run_cbot_drawdown_risk_module,
    run_live_forecast_snapshot,
    run_regime_conditional_basis,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V23 — RISQUE DRAWDOWN CBOT + RÉGIME BASIS + FORECAST LIVE")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = run_cbot_drawdown_risk_module(df)
    print(f"\n[V23-01 drawdown risk] {a.get('results')}")

    b = run_regime_conditional_basis(df)
    print("\n[V23-02 regime-conditional basis]")
    print(f"  CBOT below trend: {b.get('cbot_below_trend')}")
    print(f"  CBOT above trend: {b.get('cbot_above_trend')}")
    print(f"  hypothesis supported: {b.get('hypothesis_supported')}")

    c = run_live_forecast_snapshot(region="us")
    print(f"\n[V23-03 live forecast] verdict={c.get('verdict')} "
          f"issue={c.get('issue_date')} latest={c.get('weighted_features_latest')}")

    print("\nDONE V23.")

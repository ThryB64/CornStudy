"""Runner V21-IND — indicateur intégré prime + contexte CBOT + chemin de compression."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v21_indicator_integration import (  # noqa: E402
    decompose_compression_path,
    run_integrated_indicator,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V21-IND — INDICATEUR INTÉGRÉ (prime + contexte CBOT)")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    path = decompose_compression_path(df)
    print("\n--- Décomposition du chemin de compression ---")
    print(f"  n_trades: {path.get('n_trades')}")
    print(f"  path distribution: {path.get('path_distribution')}")
    print(f"  via CBOT up: {path.get('share_compression_via_cbot_up')} | "
          f"via EMA down: {path.get('share_compression_via_ema_down')} | both: {path.get('share_both')}")
    print(f"  mean ema_leg: {path.get('mean_ema_leg')} | mean cbot_leg: {path.get('mean_cbot_leg')}")

    out = run_integrated_indicator(df)
    print("\n--- Indicateur intégré ---")
    print(f"  context distribution: {out.get('context_distribution')}")
    print(f"  latest snapshot: {out.get('latest_integrated_snapshot')}")

    print("\nDONE V21-IND.")

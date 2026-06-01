"""Runner V18-LIT — réplication des familles de littérature + matrice de verdicts."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v18_literature_replication import run_replication_summary  # noqa: E402
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V18-LIT — RÉPLICATION LITTÉRATURE → INDICATEUR")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    out = run_replication_summary(df)
    print("\n--- Matrice des verdicts (vs baseline basis_z + month_cos) ---")
    for fam, v in out["matrix"].items():
        print(f"  {fam:14s} verdict={v['verdict']:18s} "
              f"baseline={v['baseline_auc']} augmented={v['augmented_auc']} delta={v['delta_auc']}")
    print(f"\nFamilies to ADD: {out['families_to_add']}")
    print(f"Families WATCHLIST: {out['families_watchlist']}")
    print(f"Decision: {out['decision']}")
    print("\nDONE V18-LIT.")

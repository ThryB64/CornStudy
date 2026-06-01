"""Runner V16 — explication économique du basis."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v16_basis_explanation import (  # noqa: E402
    run_basis_drivers,
    run_basis_fair_value,
    run_curve_structure,
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
    print("V16 — EXPLICATION ÉCONOMIQUE DU BASIS")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = _timed("V16-01 fair value", run_basis_fair_value, df)
    print(f"  fair R²: {a.get('fair_value_oof_r2_mean')}")
    print(f"  AUC compression basis_z={a.get('auc_compression_basis_z')} mispricing={a.get('auc_compression_mispricing')}")
    print(f"  rule basis_z: {a.get('short_rule_basis_z')}")
    print(f"  rule mispricing: {a.get('short_rule_mispricing')}")
    print(f"  mispricing beats basis_z: {a.get('mispricing_beats_basis_z')}")

    b = _timed("V16-02 curve structure", run_curve_structure, df)
    print(f"  results: {b.get('results')}")

    c = _timed("V16-03 basis drivers", run_basis_drivers, df)
    print(f"  R²: {c.get('oof_r2_mean')} | top drivers: {c.get('top_drivers')}")
    print(f"  coefs: {c.get('standardized_coefficients')}")

    print("\nDONE V16.")

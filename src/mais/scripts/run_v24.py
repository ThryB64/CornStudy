"""Runner V24 — audit forensique des données."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v24_data_forensic import run_forensic_summary  # noqa: E402
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V24 — AUDIT FORENSIQUE DES DONNÉES")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    out = run_forensic_summary(df)
    print(json.dumps(out, indent=2, default=str))
    print("\n--- détail conversion + rebuild ---")
    from mais.research.v24_data_forensic import run_conversion_audit, run_minimal_rebuild
    print("conversion:", json.dumps(run_conversion_audit(), indent=2, default=str))
    print("rebuild:", json.dumps(run_minimal_rebuild(), indent=2, default=str))
    print("\nDONE V24.")

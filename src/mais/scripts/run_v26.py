"""Runner V26 — validation source EMA officielle Euronext."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v26_official_ema_validation import run_v26_all  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V26 — SOURCE EMA OFFICIELLE EURONEXT")
    print("=" * 60)
    out = run_v26_all()
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    print("\nDONE V26.")

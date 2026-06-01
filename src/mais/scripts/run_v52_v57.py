"""Runner V52/V54/V56/V57 — substitution MATIF, tension physique, objectif recommandé, magnitude."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v51_weather_extremes import run_v51_extremes  # noqa: E402
from mais.research.v52_matif_substitution import run_v52_matif  # noqa: E402
from mais.research.v54_physical_tension import run_v54_tension  # noqa: E402
from mais.research.v56_target_recommendation import run_v56_target  # noqa: E402
from mais.research.v57_magnitude_buckets import run_v57_buckets  # noqa: E402
from mais.research.v58_casebook_enriched import run_v58_enriched  # noqa: E402
from mais.research.v59_monthly_forward_report import run_v59_report  # noqa: E402
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402


def _show(name, out):
    print(f"\n[{name}] verdict={out.get('verdict')}")
    print(json.dumps(out, indent=2, default=str)[:1100])


if __name__ == "__main__":
    print("=" * 60)
    print("V52/V54/V56/V57 — diagnostics enrichis prime EMA/CBOT")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")
    _show("V51 WEATHER_EXTREMES", run_v51_extremes(df))
    _show("V54 PHYSICAL_TENSION", run_v54_tension(df))
    _show("V56 TARGET_RECOMMENDATION", run_v56_target(df))
    _show("V57 MAGNITUDE_BUCKETS", run_v57_buckets(df))
    _show("V58 CASEBOOK_ENRICHED", run_v58_enriched(df))
    _show("V59 MONTHLY_FORWARD", run_v59_report())
    try:
        _show("V52 MATIF_SUBSTITUTION", run_v52_matif(df))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V52 MATIF] indisponible: {type(e).__name__}: {e}")
    print("\nDONE V52/V54/V56/V57.")

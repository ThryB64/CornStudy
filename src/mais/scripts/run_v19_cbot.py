"""Runner V19-CBOT — lab risque CBOT + interactions COT/WASDE/météo (météo réalisée)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v19_cbot_lab import run_cbot_risk_lab, run_cot_weather_interaction  # noqa: E402
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V19-CBOT — LAB RISQUE + INTERACTIONS (météo réalisée)")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    lab = run_cbot_risk_lab(df)
    print("\n--- Lab risque CBOT (baseline technique vs familles) ---")
    for tgt, r in lab["results"].items():
        if r.get("baseline_auc") is None:
            continue
        line = f"  {tgt:22s} base={r['baseline_auc']} (rate {r.get('base_rate')})"
        for fam in ["weather", "cot", "wasde", "weather+interactions"]:
            if isinstance(r.get(fam), dict):
                line += f" | {fam}:{r[fam]['auc']}({r[fam]['delta']:+})"
        print(line)
    print(f"\nFamilies adding value (delta>0.02): {lab['families_adding_value']}")

    ci = run_cot_weather_interaction(df)
    print("\n--- COT × météo (short covering) ---")
    for t, r in ci["results"].items():
        print(f"  {t:18s} wx_cot={r['auc_wx_cot']} +inter={r['auc_with_interaction']} "
              f"delta={r['delta']} -> {r['verdict']}")

    print("\nDONE V19-CBOT.")

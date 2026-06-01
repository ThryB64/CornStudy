"""Runner V18-WEATHER-DEEP — météo comme warning basis justifié."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mais.research.v18_weather_deep import (  # noqa: E402
    run_weather_basis_justification,
    run_weather_on_trades,
)
from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("V18-WEATHER-DEEP — MÉTÉO = BASIS JUSTIFIÉ ?")
    print("=" * 60)
    df = filter_out_holdout(load_master_dataset())
    print(f"master shape (no holdout): {df.shape}")

    a = run_weather_on_trades(df)
    print(f"\n[trades] verdict={a.get('verdict')} n={a.get('n_trades_with_weather')}")
    print(f"  high stress: {a.get('high_stress_entries')}")
    print(f"  low  stress: {a.get('low_stress_entries')}")
    print(f"  warning useful: {a.get('weather_warning_useful')}")

    b = run_weather_basis_justification(df)
    print(f"\n[justification] verdict={b.get('verdict')}")
    print(f"  corr stress vs basis_change: {b.get('corr_stress_vs_basis_change')}")
    print(f"  compression high/low stress: {b.get('compression_rate_high_stress')} / {b.get('compression_rate_low_stress')}")

    print("\nDONE V18-WEATHER-DEEP.")

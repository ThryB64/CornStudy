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
from mais.research.v60_weather_basis_driver import run_v60_weather_basis  # noqa: E402
from mais.research.v64_adverse_risk_v2 import run_v64_adverse_v2  # noqa: E402
from mais.research.v65_cbot_rebound_engine import run_v65_rebound  # noqa: E402
from mais.research.v70_path_classification import run_v70_paths  # noqa: E402
from mais.research.v71_eu_production_balance import run_v71_eu_production  # noqa: E402
from mais.research.v71b_eu_production_locality import run_v71b_locality  # noqa: E402
from mais.research.v72_survival_reversion import run_v72_survival  # noqa: E402
from mais.research.v77_indicator_synthesis import synthesize_indicator  # noqa: E402
from mais.research.v79_enso_regime import run_v79_enso  # noqa: E402
from mais.research.v80_intercommodity_spreads import run_v80_intercommodity  # noqa: E402
from mais.research.v81_robustness_audit import run_v81_robustness  # noqa: E402
from mais.research.v82_episode_library import run_v82_episodes  # noqa: E402
from mais.research.v86_cbot_support_v2 import run_v86_cbot_support_v2  # noqa: E402
from mais.research.v99_indicator_synthesis_v2 import synthesize_indicator_v2  # noqa: E402
from mais.research.v101_official_synthesis_fix import run_v101_official_synthesis  # noqa: E402
from mais.research.v102_active_signal_monitoring import monitor_active_signal  # noqa: E402
from mais.research.v103_proxy_official_dashboard import run_v103_dashboard  # noqa: E402
from mais.research.v104_compression_start import run_v104_compression_start  # noqa: E402
from mais.research.v105_compression_event_study import run_v105_event_study  # noqa: E402
from mais.research.v106_compression_trigger import run_v106_trigger  # noqa: E402
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
    _show("V60 WEATHER_BASIS_DRIVER", run_v60_weather_basis(df))
    _show("V54 PHYSICAL_TENSION", run_v54_tension(df))
    _show("V56 TARGET_RECOMMENDATION", run_v56_target(df))
    _show("V57 MAGNITUDE_BUCKETS", run_v57_buckets(df))
    _show("V58 CASEBOOK_ENRICHED", run_v58_enriched(df))
    _show("V64 ADVERSE_RISK_V2", run_v64_adverse_v2(df))
    _show("V65 CBOT_REBOUND_ENGINE", run_v65_rebound(df))
    _show("V70 PATH_CLASSIFICATION", run_v70_paths(df))
    try:
        _show("V71 EU_PRODUCTION", run_v71_eu_production(df))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V71 EU_PRODUCTION] indisponible: {type(e).__name__}: {e}")
    try:
        _show("V71b EU_LOCALITY", run_v71b_locality(df))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V71b EU_LOCALITY] indisponible: {type(e).__name__}: {e}")
    _show("V72 SURVIVAL_REVERSION", run_v72_survival(df))
    _show("V77 INDICATOR_SYNTHESIS", synthesize_indicator(df))
    try:
        _show("V79 ENSO_REGIME", run_v79_enso(df, try_network=True))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V79 ENSO] indisponible: {type(e).__name__}: {e}")
    _show("V80 INTERCOMMODITY", run_v80_intercommodity(df))
    _show("V81 ROBUSTNESS", run_v81_robustness(df))
    _show("V82 EPISODE_LIBRARY", run_v82_episodes(df, with_network=False))
    _show("V86 CBOT_SUPPORT_V2", run_v86_cbot_support_v2(df, with_network=False))
    _show("V101 OFFICIAL_SYNTHESIS", run_v101_official_synthesis(df))
    _show("V102 ACTIVE_MONITORING", monitor_active_signal())
    _show("V103 PROXY_OFFICIAL_DASHBOARD", run_v103_dashboard())
    _show("V104 COMPRESSION_START", run_v104_compression_start(df))
    _show("V105 EVENT_STUDY", run_v105_event_study(df, make_png=False))
    _show("V106 COMPRESSION_TRIGGER", run_v106_trigger(df))
    _show("V99 SYNTHESIS_V2", synthesize_indicator_v2(df, with_network=False))
    _show("V59 MONTHLY_FORWARD", run_v59_report())
    try:
        _show("V52 MATIF_SUBSTITUTION", run_v52_matif(df))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V52 MATIF] indisponible: {type(e).__name__}: {e}")
    print("\nDONE V52/V54/V56/V57.")

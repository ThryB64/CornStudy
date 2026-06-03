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
from mais.research.v107_live_context_refresh import run_v107_context_refresh  # noqa: E402
from mais.research.v108_live_basis_reconstruction import run_v108_live_basis  # noqa: E402
from mais.research.v109_ema_curve_live_tension import run_v109_curve_tension  # noqa: E402
from mais.research.v120_basis_econometrics import run_v120_all  # noqa: E402
from mais.research.v121_basis_forecast_model import run_v121_forecast  # noqa: E402
from mais.research.v124_active_monitoring_v2 import monitor_active_signal_v2  # noqa: E402
from mais.research.v125_curve_accumulation import run_v125_curve_accumulation  # noqa: E402
from mais.research.v126_matif_substitution_v2 import run_v126_substitution  # noqa: E402
from mais.research.v129_event_catalyst_library import run_v129_event_library  # noqa: E402
from mais.research.v130_basis_regime_econometrics import run_v130_regime_econometrics  # noqa: E402
from mais.research.v131_target_recommendation_v3 import run_v131_target_v3  # noqa: E402
from mais.research.v132_indicator_synthesis_v3 import run_v132_synthesis  # noqa: E402
from mais.research.v133_monthly_forward_report_v2 import run_v133_monthly_v2  # noqa: E402
from mais.research.v134_data_sourcing_plan import run_v134_sourcing_plan  # noqa: E402
from mais.research.v135_decision_checkpoint import run_v135_checkpoint  # noqa: E402
from mais.research.v136_weather_revision_archive import run_v136_weather_archive  # noqa: E402
from mais.research.v137_event_date_attribution import run_v137_event_dates  # noqa: E402
from mais.research.v138_horizon_estimator import run_v138_horizon  # noqa: E402
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
    _show("V120 BASIS_ECONOMETRICS", run_v120_all(df))
    _show("V121 BASIS_FORECAST", run_v121_forecast(df))
    try:
        _show("V107 CONTEXT_REFRESH", run_v107_context_refresh(try_network=True))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V107] indisponible: {type(e).__name__}: {e}")
    try:
        _show("V108 LIVE_BASIS", run_v108_live_basis(try_network=True))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V108] indisponible: {type(e).__name__}: {e}")
    try:
        _show("V109 CURVE_TENSION", run_v109_curve_tension(try_network=True))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V109] indisponible: {type(e).__name__}: {e}")
    _show("V99 SYNTHESIS_V2", synthesize_indicator_v2(df, with_network=False))
    _show("V124 ACTIVE_MONITORING_V2", monitor_active_signal_v2())
    _show("V125 CURVE_ACCUMULATION", run_v125_curve_accumulation())
    _show("V126 MATIF_SUBSTITUTION_V2", run_v126_substitution())
    _show("V129 EVENT_LIBRARY", run_v129_event_library(df))
    _show("V137 EVENT_DATE_ATTRIBUTION", run_v137_event_dates(df))
    try:
        _show("V136 WEATHER_ARCHIVE", run_v136_weather_archive(try_network=True))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V136] indisponible: {type(e).__name__}: {e}")
    _show("V130 REGIME_ECONOMETRICS", run_v130_regime_econometrics(df))
    _show("V131 TARGET_RECO_V3", run_v131_target_v3(df))
    _show("V138 HORIZON_ESTIMATOR", run_v138_horizon(df))
    _show("V132 INDICATOR_V3", run_v132_synthesis())
    # VNEXT — leading data + premium head
    try:
        from mais.premium.curve_sign_audit import audit_curve_signs
        from mais.premium.euronext_history_probe import probe_history
        from mais.premium.head import build_premium_head
        from mais.research.v_adverse_discriminator import run_v_adverse_discriminator
        from mais.research.v_eu_physical_pressure import run_eu_physical_pressure
        from mais.research.v_event_microstructure import run_v_event_microstructure
        from mais.research.v_forecast_revision_tape import run_v_revision_tape
        from mais.research.v_hazard_compression import run_v_hazard
        from mais.research.v_hierarchical_explanation import run_v_hierarchical
        from mais.research.v_state_transitions import run_v_state_transitions
        _show("VN-A3 CURVE_SIGN_AUDIT", audit_curve_signs())
        _show("VN-C1 EURONEXT_HISTORY_PROBE", probe_history(try_network=True))
        _show("VN-C4 FORECAST_REVISION_TAPE", run_v_revision_tape())
        _show("VN-C3 EU_PHYSICAL_PRESSURE", run_eu_physical_pressure(try_network=True))
        _show("VN-D2 STATE_TRANSITIONS", run_v_state_transitions(df))
        _show("VN-D1 HAZARD_COMPRESSION", run_v_hazard(df))
        _show("VN-D3 ADVERSE_DISCRIMINATOR", run_v_adverse_discriminator())
        _show("VN-D4 HIERARCHICAL_EXPLANATION", run_v_hierarchical(df))
        _show("VN-E2 EVENT_MICROSTRUCTURE", run_v_event_microstructure())
        _show("VN-A1 PREMIUM_HEAD", build_premium_head())
    except Exception as e:  # noqa: BLE001
        print(f"\n[VNEXT] partiel: {type(e).__name__}: {e}")
    _show("V133 MONTHLY_FORWARD_V2", run_v133_monthly_v2())
    _show("V134 DATA_SOURCING_PLAN", run_v134_sourcing_plan())
    _show("V135 DECISION_CHECKPOINT", run_v135_checkpoint())
    _show("V59 MONTHLY_FORWARD", run_v59_report())
    try:
        _show("V52 MATIF_SUBSTITUTION", run_v52_matif(df))
    except Exception as e:  # noqa: BLE001
        print(f"\n[V52 MATIF] indisponible: {type(e).__name__}: {e}")
    print("\nDONE V52/V54/V56/V57.")

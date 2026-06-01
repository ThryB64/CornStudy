"""Collectors download raw data from external sources into ``data/raw/<source>/``.

Each source listed in ``config/sources.yaml`` maps to one module here.
The module exposes a ``download(out_dir: Path, **kwargs) -> Path`` function.

Status
------
Phase 0 ships stubs and a registry; only the collectors marked ``enabled: true``
in ``sources.yaml`` are wired. The rest are NotImplemented placeholders that
make the missing pieces explicit (rather than failing silently like the old
``install_data.sh`` did).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mais.paths import RAW_DIR
from mais.utils import get_logger, load_sources

log = get_logger("mais.collect")

CollectorFn = Callable[[Path, dict], dict | None]


def _registry() -> dict[str, CollectorFn]:
    from . import (
        cftc_cot_collector,
        dce_dalian_collector,
        drought_monitor_collector,
        eia_ethanol_collector,
        enso,
        eu_fundamentals_collector,
        euronext_contracts_daily,
        euronext_ema_collector,
        fas_exports,
        fred_collector,
        futures_curve,
        nass_quickstats_collector,
        openmeteo_collector,
        usda_calendar_collector,
        usda_wasde_collector,
        world_collector,
        yfinance_collector,
    )
    return {
        # market CBOT
        "cbot_corn":  yfinance_collector.download,
        "cbot_wheat": yfinance_collector.download,
        "cbot_soy":   yfinance_collector.download,
        "cbot_oats":  yfinance_collector.download,
        "nymex_crude_wti": yfinance_collector.download,
        "nymex_natgas":    yfinance_collector.download,
        "ice_dxy":         yfinance_collector.download,
        "brent":           yfinance_collector.download,
        "rbob_gasoline":   yfinance_collector.download,
        # macro
        "fred_macro": fred_collector.download,
        # USDA
        "usda_wasde":              usda_wasde_collector.download,
        "usda_nass_crop_progress": nass_quickstats_collector.download,
        "usda_nass_crop_condition": nass_quickstats_collector.download,
        "usda_nass_yield_state":   nass_quickstats_collector.download,
        "usda_fas_export_sales":   fas_exports.download,
        # CFTC + EIA
        "cftc_cot_corn": cftc_cot_collector.download,
        "eia_ethanol":   eia_ethanol_collector.download,
        "enso_oni":      enso.download,
        "futures_curve": futures_curve.download,
        # weather
        "openmeteo_states":   openmeteo_collector.download,
        "us_drought_monitor": drought_monitor_collector.download,
        # world
        "conab_brazil":          world_collector.download,
        "bcr_argentina":         world_collector.download,
        "ukragroconsult":        world_collector.download,
        "noaa_oni":              world_collector.download,
        "brazil_fob_prices":     world_collector.download,
        "brazil_export_inspections": world_collector.download,
        "ukraine_exports":       world_collector.download,
        "asia_tenders":          world_collector.download,
        # Euronext EMA — pivot cible
        "euronext_ema":          euronext_ema_collector.download,
        "euronext_ema_daily":    euronext_contracts_daily.download,
        "euronext_ema_spreads":  eu_fundamentals_collector.download,
        # EU fundamentals
        "eu_cross_assets":       eu_fundamentals_collector.download,
        "ec_mars_bulletin":      eu_fundamentals_collector.download,
        "agreste_france":        eu_fundamentals_collector.download,
        "franceagrimer":         eu_fundamentals_collector.download,
        # Chine
        "dce_dalian_corn":       dce_dalian_collector.download,
        # synthetic
        "usda_calendar": usda_calendar_collector.download,
    }


def run_collector(name: str) -> str:
    cfg = load_sources()
    sources = {s["name"]: s for s in cfg.get("sources", [])}
    if name not in sources:
        return f"unknown source '{name}'"
    src = sources[name]
    if not src.get("enabled", False):
        return "disabled in sources.yaml"
    fn = _registry().get(name)
    if fn is None:
        return "no collector wired"
    out_dir = RAW_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = fn(out_dir, src)
        return f"OK ({result})" if result else "OK"
    except NotImplementedError as e:
        return f"STUB ({e})"
    except Exception as e:
        log.error("collector_failed", name=name, error=str(e))
        return f"FAIL ({e})"


def run_all_collectors() -> dict[str, str]:
    cfg = load_sources()
    return {s["name"]: run_collector(s["name"]) for s in cfg.get("sources", [])}

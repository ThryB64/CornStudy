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

from pathlib import Path
from typing import Callable

from mais.paths import RAW_DIR
from mais.utils import get_logger, load_sources

log = get_logger("mais.collect")

CollectorFn = Callable[[Path, dict], dict | None]


def _registry() -> dict[str, CollectorFn]:
    from . import (
        yfinance_collector,
        fred_collector,
        usda_wasde_collector,
        nass_quickstats_collector,
        fas_export_sales_collector,
        cftc_cot_collector,
        eia_ethanol_collector,
        openmeteo_collector,
        drought_monitor_collector,
        usda_calendar_collector,
        world_collector,
    )
    return {
        # market
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
        "usda_fas_export_sales":   fas_export_sales_collector.download,
        # CFTC + EIA
        "cftc_cot_corn": cftc_cot_collector.download,
        "eia_ethanol":   eia_ethanol_collector.download,
        # weather
        "openmeteo_states":   openmeteo_collector.download,
        "us_drought_monitor": drought_monitor_collector.download,
        # world
        "conab_brazil":     world_collector.download,
        "bcr_argentina":    world_collector.download,
        "ukragroconsult":   world_collector.download,
        "noaa_oni":         world_collector.download,
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
        return f"disabled in sources.yaml"
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

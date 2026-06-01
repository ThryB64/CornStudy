"""V7-01A — Inventaire des proxies EMA disponibles.

Catalogue les sources de données EMA proxy (non-officielle Euronext)
avec statut de disponibilité, lag minimum, et fiabilité.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "ema_proxy_inventory.json"

PROXY_STATUS = {
    "DATA_OK": "Données disponibles et utilisables",
    "DATA_PARTIAL": "Données partielles — couverture < 80% ou lacunes > 30j",
    "DATA_TOO_SPARSE": "Trop peu d'observations pour modèle statistique",
    "DATA_BLOCKED": "Source inaccessible ou format propriétaire",
    "NO_SIGNAL": "Données OK mais signal prédictif absent (AUC ~ 0.5)",
    "SIGNAL_ADDS_VALUE": "Données OK + signal prédictif confirmé en V6/V7",
}


@dataclass
class ProxySource:
    name: str
    description: str
    frequency: str
    lag_days_conservative: int
    coverage_start: str
    coverage_end: str
    status: str
    source_url_hint: str = ""
    features_available: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    v6_used: bool = False
    signal_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "frequency": self.frequency,
            "lag_days_conservative": self.lag_days_conservative,
            "coverage_start": self.coverage_start,
            "coverage_end": self.coverage_end,
            "status": self.status,
            "source_url_hint": self.source_url_hint,
            "features_available": self.features_available,
            "caveats": self.caveats,
            "v6_used": self.v6_used,
            "signal_note": self.signal_note,
        }


EMA_PROXY_INVENTORY: list[ProxySource] = [
    ProxySource(
        name="ema_barchart_proxy",
        description="Prix EMA maïs proxy via Barchart EX-1/EX-2 (non-officiel Euronext)",
        frequency="quotidienne",
        lag_days_conservative=1,
        coverage_start="2010-01-01",
        coverage_end="2024-12-31",
        status="DATA_OK",
        source_url_hint="barchart.com/futures/quotes/EBM*0",
        features_available=[
            "ema_close", "ema_volume", "ema_open_interest",
            "ema_basis_vs_cbot", "ema_roll_spread",
        ],
        caveats=[
            "Proxy non-officiel — données Euronext officielles payantes",
            "Liquidité faible avant 2015 → signaux moins fiables",
            "Roll spread calculé manuellement entre EX-1 et EX-2",
        ],
        v6_used=True,
        signal_note="Basis EMA-CBOT utilisé dans V6 seasonal_expert (AUC 0.982)",
    ),
    ProxySource(
        name="cbot_corn",
        description="Prix maïs CBOT ZC — données officielles CME Group",
        frequency="quotidienne",
        lag_days_conservative=1,
        coverage_start="2000-01-01",
        coverage_end="2024-12-31",
        status="SIGNAL_ADDS_VALUE",
        features_available=[
            "cbot_close", "cbot_volume", "cbot_oi",
            "cbot_roll_yield", "cbot_curve_slope",
        ],
        caveats=["Données US, pas EU — corrélé mais divergences possibles en périodes de crise"],
        v6_used=True,
        signal_note="Variable centrale dans V6 meta_model_h90",
    ),
    ProxySource(
        name="wasde_usda",
        description="WASDE USDA — bilans offre/demande céréales mondiaux",
        frequency="mensuelle",
        lag_days_conservative=1,
        coverage_start="2000-01-01",
        coverage_end="2024-12-31",
        status="SIGNAL_ADDS_VALUE",
        features_available=[
            "wasde_world_corn_prod", "wasde_world_corn_cons",
            "wasde_world_corn_stocks", "wasde_stocks_to_use_ratio",
            "wasde_eu_corn_prod", "wasde_eu_corn_imports",
        ],
        caveats=[
            "Lag minimum = 1 jour (publication mensuelle le 1er vendredi)",
            "Révisions fréquentes — utiliser shift(1) pour éviter leakage",
        ],
        v6_used=True,
        signal_note="Stock-to-use ratio utilisé comme feature fondamentale",
    ),
    ProxySource(
        name="cot_cftc",
        description="COT CFTC — positions des traders sur CBOT maïs",
        frequency="hebdomadaire",
        lag_days_conservative=3,
        coverage_start="2006-01-01",
        coverage_end="2024-12-31",
        status="DATA_OK",
        features_available=[
            "cot_commercial_long", "cot_commercial_short",
            "cot_noncommercial_long", "cot_net_position",
            "cot_open_interest",
        ],
        caveats=["Lag 3 jours ouvrés — publication chaque vendredi pour semaine précédente"],
        v6_used=False,
        signal_note="Non utilisé en V6, candidat V7 phase 1",
    ),
    ProxySource(
        name="eia_ethanol",
        description="EIA — production et stocks éthanol US (corn demand driver)",
        frequency="hebdomadaire",
        lag_days_conservative=4,
        coverage_start="2010-01-01",
        coverage_end="2024-12-31",
        status="DATA_OK",
        features_available=[
            "eia_ethanol_production_kbbl", "eia_ethanol_stocks_kbbl",
            "eia_corn_for_ethanol_weekly",
        ],
        caveats=["Lag 4 jours ouvrés (publication mercredi pour semaine T-1)"],
        v6_used=False,
        signal_note="Demande éthanol = ~40% de la consommation maïs US",
    ),
    ProxySource(
        name="ec_mars_bulletin",
        description="EC MARS — estimations production céréales EU (mensuel)",
        frequency="mensuelle",
        lag_days_conservative=21,
        coverage_start="2001-01-01",
        coverage_end="2024-12-31",
        status="DATA_PARTIAL",
        source_url_hint="mars.ec.europa.eu/MARS/",
        features_available=[
            "mars_corn_yield_eu", "mars_corn_area_eu",
            "mars_biomass_index", "mars_water_stress",
        ],
        caveats=[
            "Lag 14-21 jours (bulletin ~15-20 du mois suivant)",
            "Couverture historique incomplète avant 2005",
            "Format PDF avant 2010 — extraction manuelle requise",
        ],
        v6_used=False,
        signal_note="WAITING_DATA — extraction automatique non implémentée",
    ),
    ProxySource(
        name="franceagrimer_cereales",
        description="FranceAgriMer — bilan offre/demande céréales France",
        frequency="mensuelle",
        lag_days_conservative=30,
        coverage_start="2010-01-01",
        coverage_end="2024-12-31",
        status="DATA_PARTIAL",
        features_available=[
            "fam_corn_production_fr", "fam_corn_exports_fr",
            "fam_corn_stocks_fr",
        ],
        caveats=[
            "Lag variable 7-30 jours",
            "Données historiques en PDF avant 2015",
        ],
        v6_used=False,
        signal_note="WAITING_DATA — scraping mensuel à automatiser",
    ),
    ProxySource(
        name="openmeteo_eu_weather",
        description="Open-Meteo — données météo EU pour zones de production maïs",
        frequency="quotidienne",
        lag_days_conservative=1,
        coverage_start="1990-01-01",
        coverage_end="2024-12-31",
        status="DATA_OK",
        features_available=[
            "temp_max_fr", "temp_min_fr", "precip_fr",
            "temp_max_de", "precip_de",
            "gdd_corn_fr",  # Growing Degree Days
            "drought_index_eu",
        ],
        caveats=["Données réanalysis ERA5 — pas de délai de publication"],
        v6_used=False,
        signal_note="Candidat V7 phase 2 — signal météo pour yield EU",
    ),
    ProxySource(
        name="ukr_grain_exports",
        description="Douanes ukrainiennes — exports céréales hebdomadaires",
        frequency="hebdomadaire",
        lag_days_conservative=14,
        coverage_start="2017-01-01",
        coverage_end="2024-12-31",
        status="DATA_PARTIAL",
        features_available=[
            "ukr_corn_exports_weekly", "ukr_wheat_exports_weekly",
        ],
        caveats=[
            "Données interrompues 2022-2023 (guerre)",
            "Format changeant selon les périodes",
            "WAITING_DATA pour coverage complète",
        ],
        v6_used=False,
        signal_note="WAITING_DATA — source critique pour supply shock EU",
    ),
    ProxySource(
        name="ema_roll_basis_computed",
        description="Basis EMA-CBOT et roll spread calculés à partir des prix proxy",
        frequency="quotidienne",
        lag_days_conservative=1,
        coverage_start="2012-01-01",
        coverage_end="2024-12-31",
        status="SIGNAL_ADDS_VALUE",
        features_available=[
            "ema_cbot_basis_eur", "ema_roll_cost_pct",
            "ema_basis_zscore_252d", "ema_basis_extreme_flag",
        ],
        caveats=[
            "Calculé à partir de données proxy — non officiel",
            "Taux de change EUR/USD requis pour comparaison",
        ],
        v6_used=True,
        signal_note="basis_extreme_flag utilisé dans basis_extreme_h90 (AUC 1.000 sur n=29)",
    ),
]


def get_inventory() -> list[dict[str, Any]]:
    return [s.to_dict() for s in EMA_PROXY_INVENTORY]


def get_sources_by_status(status: str) -> list[dict[str, Any]]:
    return [s.to_dict() for s in EMA_PROXY_INVENTORY if s.status == status]


def save_inventory() -> dict[str, Any]:
    import json
    inventory = get_inventory()
    result = {
        "version": "V7-01A",
        "n_sources": len(inventory),
        "sources": inventory,
        "summary": {
            status: len(get_sources_by_status(status))
            for status in PROXY_STATUS
        },
        "v6_used": [s["name"] for s in inventory if s["v6_used"]],
    }
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    register_experiment(
        experiment_id="V7-01A",
        target="ema_proxy_inventory",
        horizon=0,
        model="audit",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=[],
        metrics={
            "n_sources": len(inventory),
            "n_data_ok": len(get_sources_by_status("DATA_OK")),
            "n_signal_adds_value": len(get_sources_by_status("SIGNAL_ADDS_VALUE")),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result

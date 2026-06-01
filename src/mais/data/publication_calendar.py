"""V7-DATA-CAL — Calendrier officiel des délais de publication par source."""

from __future__ import annotations

PUBLICATION_LAGS: dict[str, tuple[int, int, str, str]] = {
    # source: (lag_min_jours, lag_max_jours, fréquence, notes)
    "wasde": (0, 1, "mensuelle", "Publication 12h00 EST, 1er vendredi du mois"),
    "cot": (3, 3, "hebdomadaire", "COT publié chaque vendredi pour la semaine précédente"),
    "eia_weekly": (4, 4, "hebdomadaire", "EIA publié chaque mercredi matin pour sem-1"),
    "fas_grain": (1, 7, "mensuelle", "FAS WASDE attachment, même jour que WASDE"),
    "ec_mars": (14, 21, "mensuelle", "Bulletin MARS publié ~15-20 du mois suivant"),
    "franceagrimer": (7, 30, "mensuelle", "Bilan offres/demandes céréales, 4 semaines retard"),
    "eurostat_comext": (30, 75, "mensuelle", "T-2 à T-3 mois"),
    "ukraine_exports": (7, 14, "hebdomadaire", "Données douanières ukrainiennes, 1-2 sem"),
    "fob_prices": (1, 3, "quotidien", "Prix FOB Rouen/Ukraine cotés J-1 ou J"),
    "ttf_gas": (1, 1, "quotidien", "Cotation TTF J-1"),
    "ets_carbon": (1, 1, "quotidien", "EUA price J-1"),
    "dap_fertilizer": (1, 3, "hebdomadaire", "DAP price hebdomadaire J-1 à J-3"),
    "nass_crop_progress": (2, 2, "hebdomadaire", "Lundi soir pour la semaine courante"),
    "openmeteo": (1, 1, "quotidien", "Données météo J-1 disponibles"),
    "bdi_freight": (1, 1, "quotidien", "Baltic Dry Index J-1"),
}


def get_lag(source: str, conservative: bool = True) -> int:
    """Retourne le délai officiel (conservateur = max, sinon min) en jours."""
    if source not in PUBLICATION_LAGS:
        raise KeyError(
            f"Source inconnue: '{source}'. "
            f"Sources disponibles: {sorted(PUBLICATION_LAGS)}"
        )
    lag_min, lag_max, _, _ = PUBLICATION_LAGS[source]
    return lag_max if conservative else lag_min


def get_frequency(source: str) -> str:
    """Retourne la fréquence de publication."""
    if source not in PUBLICATION_LAGS:
        raise KeyError(f"Source inconnue: '{source}'")
    return PUBLICATION_LAGS[source][2]


def get_notes(source: str) -> str:
    """Retourne les notes sur la source."""
    if source not in PUBLICATION_LAGS:
        raise KeyError(f"Source inconnue: '{source}'")
    return PUBLICATION_LAGS[source][3]


def all_sources() -> list[str]:
    """Liste toutes les sources documentées."""
    return sorted(PUBLICATION_LAGS.keys())


def minimum_shift(source: str) -> int:
    """Shift minimum requis : max(1, lag_conservateur) — anti-leakage obligatoire."""
    return max(1, get_lag(source, conservative=True))

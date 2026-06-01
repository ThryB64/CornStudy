"""V7-18 — Causalité formelle PCMCI (avec fallback Granger multivarié)."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "pcmci_causality.json"

CANDIDATE_VARIABLES = [
    "cbot_eur_t",
    "ema_close",
    "ema_cbot_basis",
    "cot_mm_long",
    "wasde_ending_stocks",
    "factor_weather_belt_stress",
    "factor_macro_dollar_rates",
    "eurusd",
]

ALTERNATIVE_NAMES = {
    "cbot_eur_t": ["cbot_eur_t", "corn_close", "cbot_close"],
    "ema_close": ["ema_close", "ema_front_price"],
    "ema_cbot_basis": ["ema_cbot_basis"],
    "cot_mm_long": ["cot_mm_long", "cot_mm_net"],
    "wasde_ending_stocks": ["wasde_ending_stocks", "wasde_stocks"],
    "factor_weather_belt_stress": ["factor_weather_belt_stress"],
    "factor_macro_dollar_rates": ["factor_macro_dollar_rates"],
    "eurusd": ["eurusd"],
}


def _select_columns(df: pd.DataFrame, candidates: list[str], alt_map: dict) -> dict[str, str]:
    """Sélectionne les colonnes disponibles avec leurs noms alternatifs."""
    selected: dict[str, str] = {}
    for var in candidates:
        alts = alt_map.get(var, [var])
        for alt in alts:
            if alt in df.columns:
                selected[var] = alt
                break
    return selected


def run_granger_fallback(
    df: pd.DataFrame,
    col_map: dict[str, str],
    max_lag: int = 5,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Test de Granger bivarié comme fallback si tigramite absent."""
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
    except ImportError:
        return {"error": "statsmodels_not_installed"}

    variables = list(col_map.keys())
    series_map = {var: df[col].dropna() for var, col in col_map.items()}

    significant_links: dict[str, list[dict]] = {var: [] for var in variables}
    test_count = 0
    error_count = 0

    for i, target in enumerate(variables):
        for j, source in enumerate(variables):
            if i == j:
                continue
            y_t = series_map[target]
            x_s = series_map[source]
            common_idx = y_t.index.intersection(x_s.index)
            if len(common_idx) < max_lag * 10 + 50:
                continue

            data = pd.DataFrame(
                {"target": y_t.loc[common_idx], "source": x_s.loc[common_idx]}
            ).dropna()

            if len(data) < max_lag * 10 + 50:
                continue

            try:
                results = grangercausalitytests(data.values, maxlag=max_lag, verbose=False)
                test_count += 1
                for lag in range(1, max_lag + 1):
                    if lag in results:
                        pval = float(results[lag][0]["ssr_ftest"][1])
                        if pval < alpha:
                            significant_links[target].append({
                                "source": source,
                                "lag": lag,
                                "p_value": round(pval, 6),
                                "test": "granger_bivariate",
                            })
            except Exception:
                error_count += 1

    return {
        "significant_links": significant_links,
        "n_tests": test_count,
        "n_errors": error_count,
        "method": "granger_bivariate_fallback",
        "note": "PCMCI requires tigramite (not installed); Granger bivariate used as fallback",
    }


def run_pcmci_analysis(
    df: pd.DataFrame,
    variables: list[str],
    max_lag: int = 5,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Causalité PCMCI avec fallback Granger."""
    try:
        from tigramite import data_processing as pp
        from tigramite.independence_tests.parcorr import ParCorr
        from tigramite.pcmci import PCMCI

        col_map = _select_columns(df, variables, ALTERNATIVE_NAMES)
        if len(col_map) < 2:
            return {"error": "not_enough_variables", "available": list(col_map.keys())}

        avail_cols = [col_map[v] for v in col_map]
        data_array = df[avail_cols].dropna().values
        dataframe = pp.DataFrame(data_array, var_names=list(col_map.keys()))
        pcmci = PCMCI(dataframe=dataframe, cond_ind_test=ParCorr())
        results = pcmci.run_pcmci(tau_max=max_lag, alpha_level=alpha)

        significant_links: dict[str, list[dict]] = {}
        var_names = list(col_map.keys())
        for i, target in enumerate(var_names):
            links = []
            for j, source in enumerate(var_names):
                for lag in range(1, max_lag + 1):
                    pval = float(results["p_matrix"][i, j, lag])
                    if pval < alpha:
                        links.append({"source": source, "lag": lag, "p_value": round(pval, 6)})
            significant_links[target] = links

        return {
            "method": "PCMCI",
            "significant_links": significant_links,
            "n_obs": len(data_array),
            "variables": var_names,
            "max_lag": max_lag,
        }

    except ImportError:
        col_map = _select_columns(df, variables, ALTERNATIVE_NAMES)
        return run_granger_fallback(df, col_map, max_lag, alpha)


def _summarize_causality(links: dict[str, list[dict]], variables: list[str]) -> dict[str, Any]:
    """Résumé des relations causales CBOT → EMA."""
    cbot_key = next((v for v in variables if "cbot" in v.lower()), None)
    ema_key = next((v for v in variables if "ema" in v.lower() and "basis" not in v.lower()), None)

    cbot_causes_ema: list[dict] = []
    ema_causes_cbot: list[dict] = []

    if ema_key and cbot_key:
        cbot_causes_ema = [lnk for lnk in links.get(ema_key, []) if lnk["source"] == cbot_key]
        ema_causes_cbot = [lnk for lnk in links.get(cbot_key, []) if lnk["source"] == ema_key]

    return {
        "cbot_causes_ema": cbot_causes_ema,
        "ema_causes_cbot": ema_causes_cbot,
        "cbot_ema_direction": (
            "CBOT_LEADS_EMA" if cbot_causes_ema and not ema_causes_cbot
            else "EMA_LEADS_CBOT" if ema_causes_cbot and not cbot_causes_ema
            else "BIDIRECTIONAL" if cbot_causes_ema and ema_causes_cbot
            else "NO_SIGNIFICANT_CAUSALITY"
        ),
    }


def run_causality_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Analyse complète de causalité sur les variables maïs."""
    variables = list(CANDIDATE_VARIABLES)

    result = run_pcmci_analysis(df, variables, max_lag=5, alpha=0.05)

    sig_links = result.get("significant_links", {})
    avail_vars = [v for v in variables if any(col in df.columns for col in ALTERNATIVE_NAMES.get(v, [v]))]
    summary = _summarize_causality(sig_links, avail_vars)

    n_total_links = sum(len(links) for links in sig_links.values())
    n_variables = len(avail_vars)

    return {
        "version": "V7-18",
        "method": result.get("method", "unknown"),
        "n_variables": n_variables,
        "variables_used": avail_vars,
        "n_obs": result.get("n_obs", 0),
        "n_significant_links": n_total_links,
        "significant_links": sig_links,
        "cbot_ema_causality": summary,
        "n_tests": result.get("n_tests", 0),
        "note": result.get("note", ""),
        "experiment_type": "DESCRIPTIVE_ECONOMIC",
        "verdict": "CAUSALITY_ANALYZED",
    }


def save_causality_analysis(df: pd.DataFrame) -> dict[str, Any]:
    result = run_causality_analysis(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-18",
        target="pcmci_causality",
        horizon=0,
        model=result.get("method", "granger_fallback"),
        cv_protocol="none",
        embargo_days=0,
        n_oof=result.get("n_obs", 0),
        features=result.get("variables_used", []),
        metrics={
            "n_significant_links": result["n_significant_links"],
            "n_variables": result["n_variables"],
            "cbot_ema_direction": result["cbot_ema_causality"].get("cbot_ema_direction"),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result

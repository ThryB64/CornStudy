"""V7-36 — Graphe de causalité économique (synthèse PCMCI + économique)."""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "causality_graph.json"

ECONOMIC_PRIORS = {
    "cbot_eur_t": {"causes": ["ema_close"], "strength": "strong", "basis": "price_transmission"},
    "wasde_ending_stocks": {"causes": ["cbot_eur_t"], "strength": "moderate", "basis": "supply_demand"},
    "factor_weather_belt_stress": {"causes": ["ema_close"], "strength": "moderate", "basis": "eu_production"},
    "eurusd": {"causes": ["ema_close"], "strength": "moderate", "basis": "currency_conversion"},
    "cot_mm_long": {"causes": ["cbot_eur_t"], "strength": "weak", "basis": "positioning"},
}


def build_causality_graph(
    pcmci_results: dict[str, Any],
    econ_priors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if econ_priors is None:
        econ_priors = ECONOMIC_PRIORS

    all_nodes: set[str] = set()
    edges: list[dict] = []
    sig_links = pcmci_results.get("significant_links", {})

    for target, links in sig_links.items():
        all_nodes.add(target)
        for link in links:
            all_nodes.add(link["source"])
            edges.append({
                "from": link["source"],
                "to": target,
                "lag": link.get("lag"),
                "p_value": link.get("p_value"),
                "strength": "statistical",
                "source": pcmci_results.get("method", "granger"),
            })

    # Ajouter les priors économiques
    for source, prior in econ_priors.items():
        for target in prior.get("causes", []):
            all_nodes.add(source)
            all_nodes.add(target)
            edges.append({
                "from": source,
                "to": target,
                "lag": None,
                "p_value": None,
                "strength": prior["strength"],
                "source": "economic_prior",
                "basis": prior.get("basis"),
            })

    # Résumé des relations clés
    cbot_to_ema = [e for e in edges if e["from"] in ("cbot_eur_t", "corn_close") and "ema" in e["to"].lower()]
    ema_to_cbot = [e for e in edges if "ema" in e["from"].lower() and "basis" not in e["from"].lower()
                   and e["to"] in ("cbot_eur_t", "corn_close")]

    return {
        "nodes": sorted(all_nodes),
        "edges": edges,
        "n_nodes": len(all_nodes),
        "n_edges": len(edges),
        "cbot_ema_summary": {
            "cbot_causes_ema": len(cbot_to_ema) > 0,
            "ema_causes_cbot": len(ema_to_cbot) > 0,
            "n_cbot_to_ema_links": len(cbot_to_ema),
            "n_ema_to_cbot_links": len(ema_to_cbot),
        },
    }


def run_causality_graph(pcmci_artefact_path: str | None = None) -> dict[str, Any]:
    pcmci_results: dict[str, Any] = {}
    if pcmci_artefact_path is None:
        pcmci_path = ARTEFACTS_DIR / "v7" / "pcmci_causality.json"
        if pcmci_path.exists():
            import json as _json
            pcmci_results = _json.loads(pcmci_path.read_text())

    graph = build_causality_graph(pcmci_results, ECONOMIC_PRIORS)
    graph.update({"version": "V7-36", "verdict": "CAUSALITY_GRAPH_BUILT"})
    return graph


def save_causality_graph() -> dict[str, Any]:
    result = run_causality_graph()
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-36",
        target="causality_graph",
        horizon=0,
        model="economic_prior_plus_granger",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=list(ECONOMIC_PRIORS.keys()),
        metrics={"n_nodes": result["n_nodes"], "n_edges": result["n_edges"]},
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result

"""V170 / T-DAG — Cartographie causale formelle du marché maïs & identifiabilité (R10).

`docs/CAUSAL_MAP_CORN_MARKET.md` existe en prose ; ici on formalise le DAG (do-calculus léger) :
d-séparation (Bayes-ball) + critère back-door, pour dire QUELLES relations sont identifiables avec
les données du repo et lesquelles sont condamnées au confounding. Le DAG encode les résultats
ÉTABLIS de l'étude, pas des hypothèses neuves :

- GLOBAL_SHOCK (latent) → CBOT et → EMA : le choc mondial commun frappe les deux jambes — c'est
  LUI qui rend le Granger EMA↔CBOT non interprétable causalement (V21, EXP-EMA-STUDY-02).
- WEATHER_US → CBOT (V19/V45 : price-in par anticipation) ; WASDE → CBOT ; COT_LAG → CBOT
  (convention temporelle t-1 → t pour l'acyclicité, publication vendredi V158).
- EU_BALANCE (latent, proxies COMEXT/FranceAgriMer lag 60j) → EMA et → CURVE (V166 maillon B
  TIENT : imports +0.33) ; WEATHER_EU → EU_BALANCE ; WHEAT_EU → EMA (substitution V36/V41).
- LOCAL_PREMIUM_U (latent) → EMA : le résidu local qui survit à macro (V16), substitution (V41),
  parité d'import (V161) et CY (V166).
- BASIS := EMA − f(CBOT, FX) (nœud déterministe) ; BASIS → COMPRESSION ; CBOT → COMPRESSION
  (V21/V105 : la compression vient surtout de la jambe CBOT).

Sorties pré-déclarées : pour chaque effet d'intérêt, IDENTIFIABLE (avec ensemble d'ajustement
back-door observé) / NON_IDENTIFIABLE (confounder latent) / TEMPOREL_SEULEMENT. Descriptif,
aucune donnée touchée, baseline intouchée. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from itertools import chain, combinations
from typing import Any

from mais.paths import ARTEFACTS_DIR

V170_DIR = ARTEFACTS_DIR / "v170"
V170_DIR.mkdir(parents=True, exist_ok=True)

# DAG du marché : parent -> enfants. Latents préfixés U_ (jamais conditionnables).
MARKET_DAG: dict[str, list[str]] = {
    "U_GLOBAL_SHOCK": ["CBOT", "EMA"],
    "WEATHER_US": ["CBOT"],
    "WASDE": ["CBOT"],
    "COT_LAG": ["CBOT"],
    "FX": ["BASIS"],
    "CBOT": ["BASIS", "COMPRESSION"],
    "WEATHER_EU": ["U_EU_BALANCE"],
    "U_EU_BALANCE": ["EMA", "CURVE", "IMPORTS_COMEXT"],
    "WHEAT_EU": ["EMA"],
    "U_LOCAL_PREMIUM": ["EMA"],
    "EMA": ["BASIS"],
    "CURVE": [],
    "IMPORTS_COMEXT": [],
    "BASIS": ["COMPRESSION"],
    "COMPRESSION": [],
}
OBSERVED = {"WEATHER_US", "WASDE", "COT_LAG", "FX", "CBOT", "WEATHER_EU", "WHEAT_EU",
            "EMA", "CURVE", "IMPORTS_COMEXT", "BASIS", "COMPRESSION"}

# Effets interrogés (pré-déclarés)
QUERIES = [
    ("WEATHER_US", "BASIS"), ("WEATHER_EU", "BASIS"), ("CBOT", "BASIS"),
    ("CURVE", "BASIS"), ("WHEAT_EU", "BASIS"), ("COT_LAG", "CBOT"),
    ("EMA", "CBOT"), ("BASIS", "COMPRESSION"), ("U_EU_BALANCE", "BASIS"),
]


def _parents(g: dict[str, list[str]]) -> dict[str, set[str]]:
    p: dict[str, set[str]] = {n: set() for n in g}
    for a, kids in g.items():
        for k in kids:
            p[k].add(a)
    return p


def descendants(g: dict[str, list[str]], x: str) -> set[str]:
    out, stack = set(), list(g.get(x, []))
    while stack:
        n = stack.pop()
        if n not in out:
            out.add(n)
            stack.extend(g.get(n, []))
    return out


def d_separated(g: dict[str, list[str]], x: str, y: str, z: set[str]) -> bool:
    """Bayes-ball : True si x ⊥ y | z dans le DAG g."""
    par = _parents(g)
    anc_z = set(z)
    stack = list(z)
    while stack:
        for p in par[stack.pop()]:
            if p not in anc_z:
                anc_z.add(p)
                stack.append(p)
    # visites (nœud, direction) ; direction 'up' = on arrive depuis un enfant, 'down' = depuis un parent
    visited: set[tuple[str, str]] = set()
    queue: list[tuple[str, str]] = [(x, "up")]
    while queue:
        node, direction = queue.pop()
        if (node, direction) in visited:
            continue
        visited.add((node, direction))
        if node not in z and node == y:
            return False
        if direction == "up" and node not in z:
            queue.extend((p, "up") for p in par[node])
            queue.extend((c, "down") for c in g.get(node, []))
        elif direction == "down":
            if node not in z:
                queue.extend((c, "down") for c in g.get(node, []))
            if node in anc_z:  # collider (ou descendant de z) débloqué
                queue.extend((p, "up") for p in par[node])
    return True


def is_valid_backdoor(g: dict[str, list[str]], x: str, y: str, z: set[str]) -> bool:
    """Critère back-door : z sans descendant de x, et bloque tous les chemins back-door."""
    if z & descendants(g, x) or x in z or y in z:
        return False
    g_no_out = {n: ([] if n == x else kids) for n, kids in g.items()}
    return d_separated(g_no_out, x, y, z)


def find_minimal_backdoor(g: dict[str, list[str]], x: str, y: str,
                          observed: set[str]) -> set[str] | None:
    """Plus petit ensemble d'ajustement OBSERVÉ valide (brute force, graphe petit)."""
    cands = sorted((observed - {x, y}) - descendants(g, x))
    for zs in chain.from_iterable(combinations(cands, r) for r in range(len(cands) + 1)):
        if is_valid_backdoor(g, x, y, set(zs)):
            return set(zs)
    return None


def classify_effect(g: dict[str, list[str]], x: str, y: str,
                    observed: set[str]) -> dict[str, Any]:
    if y not in descendants(g, x):
        return {"effect": f"{x} -> {y}", "status": "NO_CAUSAL_PATH"}
    if x not in observed:
        return {"effect": f"{x} -> {y}", "status": "NOT_IDENTIFIABLE_LATENT_CAUSE",
                "note": "cause latente : seuls ses proxies observés sont utilisables"}
    z = find_minimal_backdoor(g, x, y, observed)
    if z is None:
        return {"effect": f"{x} -> {y}", "status": "NOT_IDENTIFIABLE_CONFOUNDED",
                "note": "aucun ensemble d'ajustement observé ne ferme les back-doors"}
    return {"effect": f"{x} -> {y}", "status": "IDENTIFIABLE",
            "adjustment_set": sorted(z) if z else "∅ (aucun back-door)"}


def run_v170_dag() -> dict[str, Any]:
    effects = [classify_effect(MARKET_DAG, x, y, OBSERVED) for x, y in QUERIES]
    # le point pédagogique central : pourquoi Granger EMA->CBOT n'est pas causal
    granger = d_separated(MARKET_DAG, "EMA", "CBOT", set())
    out = {
        "version": "V170-DAG",
        "verdict": "DAG_FORMALIZED_EFFECTS_CLASSIFIED",
        "n_nodes": len(MARKET_DAG), "n_latent": len(MARKET_DAG) - len(OBSERVED),
        "effects": effects,
        "why_granger_fails": {
            "ema_cbot_marginally_dependent": not granger,
            "mechanism": "U_GLOBAL_SHOCK -> {CBOT, EMA} : fourche latente. EMA et CBOT covarient "
                         "sans qu'aucun ne cause l'autre ; un lead-lag d'agrégation horaire "
                         "(Euronext clôture avant le settlement CBOT) suffit à fabriquer un "
                         "Granger 'significatif' sans causalité (V21, EXP-EMA-STUDY-02).",
        },
        "note": "DAG = résultats établis (V16/V19/V21/V36/V41/V45/V105/V161/V166), pas de "
                "nouvelle hypothèse. Identifiabilité = back-door sur observés du repo. "
                "Convention COT_LAG (t-1) pour l'acyclicité.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V170_DIR / "v170_causal_dag.json").write_text(
        json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    return out

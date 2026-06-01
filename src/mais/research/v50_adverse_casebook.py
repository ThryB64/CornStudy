"""V50 — ADVERSE casebook : archéologie qualitative des trades short-premium perdants.

Plutôt que « le modèle s'est trompé », on documente CHAQUE trade ADVERSE avec son contexte d'entrée et une
RAISON PROBABLE d'échec, dérivée des signatures déjà découvertes (V37 résidu, V40 substitution, V41 CBOT
support, saison, roll, crise). Produit `docs/ADVERSE_CASEBOOK.md`. Descriptif ; ne change pas la règle.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V50_DIR = ARTEFACTS_DIR / "v50"
V50_DIR.mkdir(parents=True, exist_ok=True)
CASEBOOK_MD = ROOT / "docs" / "ADVERSE_CASEBOOK.md"


def _rel(p) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _probable_reason(row) -> str:
    reasons = []
    if row.get("cbot_support") == "LOW":
        reasons.append("CBOT non porteur (pas de rattrapage)")
    if row.get("resid_z") is not None and pd.notna(row.get("resid_z")) and row["resid_z"] < 0:
        reasons.append("prime justifiée par substitution blé/maïs (résidu bas)")
    if row.get("entry_z") is not None and pd.notna(row.get("entry_z")) and row["entry_z"] < 1.5:
        reasons.append("prime seulement modérée (z<1.5)")
    if int(row.get("crisis", 0)) == 1:
        reasons.append("année de crise (2020-2022)")
    if int(row.get("roll_month", 0)) == 1:
        reasons.append("mois de roll")
    return " ; ".join(reasons) if reasons else "indéterminé (à revoir avec courbe officielle / météo)"


def build_casebook(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v32_adverse_path_research import build_adverse_frame
    from mais.research.v37_substitution_residual import substitution_residual
    from mais.research.v41_cbot_support import compute_cbot_support
    adf = build_adverse_frame(df)
    if len(adf) == 0:
        return adf
    entry = pd.to_datetime(adf["entry_date"])
    adf = adf.copy()
    adf["resid_z"] = substitution_residual(df)["basis_residual_z"].reindex(entry).to_numpy()
    adf["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    adverse = adf[adf["adverse"] == 1].copy()
    if len(adverse) == 0:
        return adverse
    adverse["probable_reason"] = adverse.apply(_probable_reason, axis=1)
    return adverse


def run_v50_casebook(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    cases = build_casebook(df)
    if len(cases) == 0:
        return {"version": "V50-ADVERSE-CASEBOOK", "verdict": "NO_ADVERSE"}

    # agrégation des raisons
    reason_counts: dict[str, int] = {}
    for r in cases["probable_reason"]:
        for piece in r.split(" ; "):
            reason_counts[piece] = reason_counts.get(piece, 0) + 1
    reason_counts = dict(sorted(reason_counts.items(), key=lambda kv: -kv[1]))

    lines = ["# ADVERSE casebook — trades short-premium perdants",
             "", "Archéologie qualitative (V50). Descriptif, anti-leakage, règle figée inchangée. "
             "`RESEARCH_ONLY_NOT_TRADING`.", "",
             f"{len(cases)} trades ADVERSE documentés (le basis s'est écarté au lieu de se comprimer).", "",
             "## Raisons probables (fréquence)", ""]
    for r, c in reason_counts.items():
        lines.append(f"- {c}× — {r}")
    lines += ["", "## Fiches", "",
              "| entrée | z | basis | résidu_z | CBOT_support | durée | MAE | raison probable |",
              "|---|---:|---:|---:|---|---:|---:|---|"]
    for _, c in cases.sort_values("entry_date").iterrows():
        lines.append(
            f"| {c['entry_date']} | {c.get('entry_z')} | "
            f"{round(float(c['basis_level']),1) if pd.notna(c.get('basis_level')) else 'NA'} | "
            f"{round(float(c['resid_z']),2) if pd.notna(c.get('resid_z')) else 'NA'} | "
            f"{c.get('cbot_support')} | {int(c['duration_days']) if pd.notna(c.get('duration_days')) else 'NA'} | "
            f"{round(float(c['pnl']),1) if pd.notna(c.get('pnl')) else 'NA'} | {c['probable_reason']} |")
    lines += ["", "## Lecture", "",
              "Les ADVERSE se concentrent sur des primes modérées/justifiées et/ou un CBOT non porteur — "
              "cohérent V37/V40/V41. Le casebook sert à reconnaître ces contextes AVANT l'entrée (warning), "
              "pas à filtrer durement (anti sur-filtrage V15)."]
    CASEBOOK_MD.write_text("\n".join(lines), encoding="utf-8")

    out = {
        "version": "V50-ADVERSE-CASEBOOK",
        "n_adverse": int(len(cases)),
        "reason_counts": reason_counts,
        "casebook_path": _rel(CASEBOOK_MD),
        "verdict": "CASEBOOK_BUILT",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    cases.to_parquet(V50_DIR / "adverse_cases.parquet", index=False)
    (V50_DIR / "v50_casebook.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

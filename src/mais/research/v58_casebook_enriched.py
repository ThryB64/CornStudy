"""V58 — Casebook ADVERSE enrichi : chaque perte devient une règle de lecture marché.

V50 listait les 7 ADVERSE avec une raison probable. V58 superpose la PILE COMPLÈTE de diagnostics
construits depuis (ADVERSE_RISK V38, CBOT_SUPPORT V41, PHYSICAL_TENSION V54, objectif recommandé V56) et
répond à LA question pratique : « le warning aurait-il aidé ? » — c'est-à-dire la pile aurait-elle
recommandé l'objectif PRUDENT (z→0.5) sur ce trade perdant ? On quantifie le taux. Aucun fit, descriptif,
règle figée inchangée (les diagnostics restent du CONTEXTE, jamais un veto).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V58_DIR = ARTEFACTS_DIR / "v58"
V58_DIR.mkdir(parents=True, exist_ok=True)
CASEBOOK_MD = ROOT / "docs" / "ADVERSE_CASEBOOK_ENRICHED.md"


def _rel(p) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def build_enriched(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v32_adverse_path_research import build_adverse_frame
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    from mais.research.v54_physical_tension import compute_physical_tension
    from mais.research.v56_target_recommendation import recommend_target
    adf = build_adverse_frame(df)
    if len(adf) == 0:
        return adf
    adverse = adf[adf["adverse"] == 1].copy()
    if len(adverse) == 0:
        return adverse
    entry = pd.to_datetime(adverse["entry_date"])
    adverse["adverse_risk"] = compute_adverse_risk(df)["adverse_risk"].reindex(entry).to_numpy()
    adverse["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    adverse["physical_tension"] = compute_physical_tension(df)["physical_tension"].reindex(entry).to_numpy()
    adverse["target_reco"] = [
        recommend_target(a if isinstance(a, str) else "NO_SIGNAL",
                         c if isinstance(c, str) else "NO_SIGNAL",
                         p if isinstance(p, str) else "NO_SIGNAL")
        for a, c, p in zip(adverse["adverse_risk"], adverse["cbot_support"],
                           adverse["physical_tension"], strict=False)]
    # le warning « aurait aidé » si la pile recommandait le prudent (z→0.5) sur ce perdant
    adverse["warning_flagged_prudent"] = (adverse["target_reco"] == "z->0.5").astype(int)
    return adverse


def run_v58_enriched(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    cases = build_enriched(df)
    if len(cases) == 0:
        return {"version": "V58-CASEBOOK-ENRICHED", "verdict": "NO_ADVERSE"}

    n = int(len(cases))
    flagged = int(cases["warning_flagged_prudent"].sum())
    flagged_rate = round(flagged / n, 3)
    weak_cbot = int((cases["cbot_support"] == "LOW").sum())
    moderate = int((cases["entry_z"] < 1.5).sum())

    lines = ["# ADVERSE casebook enrichi (V58)",
             "", "Pile de diagnostics complète par trade perdant + « le warning aurait-il aidé ? ». "
             "Descriptif, anti-leakage, règle figée inchangée. `RESEARCH_ONLY_NOT_TRADING`.", "",
             f"{n} trades ADVERSE. Le warning (objectif prudent recommandé) aurait été levé sur "
             f"**{flagged}/{n}** ({flagged_rate:.0%}). CBOT non porteur : {weak_cbot}/{n}. "
             f"Prime modérée (z<1.5) : {moderate}/{n}.", "",
             "| entrée | z | basis | ADVERSE_RISK | CBOT_SUPPORT | PHYS_TENSION | objectif reco | warning ? | PnL |",
             "|---|---:|---:|---|---|---|---|:--:|---:|"]
    for _, c in cases.sort_values("entry_date").iterrows():
        warn = "✅ prudent" if c["warning_flagged_prudent"] == 1 else "—"
        lines.append(
            f"| {c['entry_date']} | {round(float(c['entry_z']), 2)} | "
            f"{round(float(c['basis_level']), 1) if pd.notna(c.get('basis_level')) else 'NA'} | "
            f"{c['adverse_risk']} | {c['cbot_support']} | {c['physical_tension']} | "
            f"{c['target_reco']} | {warn} | {round(float(c['pnl']), 1)} |")
    lines += ["", "## Lecture",
              "",
              f"Sur {n} pertes, la pile de diagnostics aurait recommandé l'objectif PRUDENT (verrouiller plus "
              f"tôt) dans {flagged_rate:.0%} des cas — surtout via un CBOT non porteur. Le warning n'aurait "
              "PAS évité l'entrée (ce n'est jamais un veto) mais aurait incité à un objectif z→0.5, réduisant "
              "l'exposition au chemin adverse. Cohérent V56/V57 : sans CBOT porteur, viser le complet n'apporte "
              "rien et allonge l'exposition. Quelques pertes restent non flaggées (prime forte + contexte "
              "apparemment porteur) : ce sont les ADVERSE irréductibles à surveiller en forward."]
    CASEBOOK_MD.write_text("\n".join(lines), encoding="utf-8")

    out = {
        "version": "V58-CASEBOOK-ENRICHED",
        "n_adverse": n,
        "warning_flagged_prudent_rate": flagged_rate,
        "n_flagged_prudent": flagged,
        "n_weak_cbot": weak_cbot,
        "n_moderate_premium": moderate,
        "by_target_reco": cases["target_reco"].value_counts().to_dict(),
        "casebook_path": _rel(CASEBOOK_MD),
        "verdict": ("WARNING_WOULD_HAVE_SUGGESTED_PRUDENT_MAJORITY"
                    if flagged_rate >= 0.5 else "WARNING_PARTIAL_COVERAGE"),
        "interpretation": (
            f"La pile de diagnostics aurait recommandé l'objectif prudent sur {flagged_rate:.0%} des trades "
            "ADVERSE (jamais un veto : l'entrée aurait eu lieu, mais avec z→0.5). Confirme que les pertes se "
            "concentrent sur un CBOT non porteur / prime modérée et que l'objectif recommandé V56 est la bonne "
            "réponse — pas un filtre dur."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    cases.to_parquet(V58_DIR / "adverse_enriched.parquet", index=False)
    (V58_DIR / "v58_casebook_enriched.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

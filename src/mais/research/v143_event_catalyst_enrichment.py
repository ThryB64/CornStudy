"""V143 — Enrichissement du catalogue d'événements : fusion V129 (catalyseur) + V137 (date USDA) + COT.

V129 attribue un catalyseur par épisode ; V137 ajoute le chevauchement d'un rapport USDA exact. V143 FUSIONNE
les deux par épisode (clé = peak_date) et raffine la classe avec le positionnement COT : si le managed-money
net a fortement augmenté pendant l'épisode (short-covering), on ajoute la classe COT_SHORT_COVERING.

Classes finales : CBOT_WEATHER, CBOT_WASDE, CBOT_GRAIN_STOCKS, COT_SHORT_COVERING, EU_BALANCE_UPDATE,
CURVE_RELAXATION, UNKNOWN. DESCRIPTIF ex-post, jamais une feature. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "event_catalyst_enrichment"
V_DIR.mkdir(parents=True, exist_ok=True)
V129_LIB = ROOT / "data" / "research" / "event_catalyst_library.parquet"
V137_LIB = ARTEFACTS_DIR / "v137" / "event_date_attribution.parquet"
ENRICHED = ROOT / "data" / "research" / "event_catalyst_enriched.parquet"
COT_SHORT_COVER = 0.25  # hausse normalisée du MM net pendant l'épisode


def run_v143_enrichment() -> dict[str, Any]:
    if not V129_LIB.exists():
        return {"version": "V143-EVENT-ENRICHMENT", "verdict": "NO_V129_LIBRARY"}
    lib = pd.read_parquet(V129_LIB)
    lib["peak_date"] = pd.to_datetime(lib["peak_date"]).astype(str)
    merged = lib.copy()

    if V137_LIB.exists():
        v137 = pd.read_parquet(V137_LIB)
        v137["peak_date"] = pd.to_datetime(v137["peak_date"]).astype(str)
        merged = merged.merge(v137[["peak_date", "report_label"]], on="peak_date", how="left")
    else:
        merged["report_label"] = None

    def _final(row):
        cat = row.get("catalyst")
        rep = row.get("report_label")
        # COT short-covering prioritaire si la hausse MM net est forte (V129 f_cot_net_change_norm)
        cot_chg = row.get("f_cot_net_change_norm")
        if cot_chg is not None and pd.notna(cot_chg) and float(cot_chg) >= COT_SHORT_COVER and \
                str(cat).startswith("CBOT"):
            return "COT_SHORT_COVERING"
        if isinstance(rep, str) and rep.startswith("CBOT_"):
            return rep  # date USDA exacte (CBOT_WASDE/GRAIN_STOCKS) raffine V129
        return cat

    merged["catalyst_final"] = merged.apply(_final, axis=1)
    ENRICHED.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(ENRICHED, index=False)
    counts = merged["catalyst_final"].value_counts().to_dict()

    out = {
        "version": "V143-EVENT-ENRICHMENT",
        "verdict": "EVENT_ENRICHMENT_BUILT",
        "n_episodes": int(len(merged)),
        "catalyst_final_counts": {str(k): int(v) for k, v in counts.items()},
        "v137_merged": bool(V137_LIB.exists()),
        "interpretation": (
            f"{len(merged)} épisodes, catalyseurs FINAUX (V129 ∪ V137 dates exactes ∪ COT short-covering) : "
            f"{counts}. Fusion descriptive ex-post : comprendre POURQUOI la prime a tourné, jamais un signal."),
        "note": "Clé de fusion = peak_date. COT_SHORT_COVERING si Δ MM net normalisé ≥0.25 sur un épisode CBOT.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "v143_enrichment.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

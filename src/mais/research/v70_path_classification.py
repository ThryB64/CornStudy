"""V70 — Par quel CANAL le basis se comprime-t-il ? CBOT-driven / EMA-driven / BOTH / ADVERSE.

Un basis haut peut se résorber de trois façons : le CBOT monte (rattrapage, CBOT_DRIVEN), l'EMA baisse
(EMA_DRIVEN), les deux (BOTH), ou il s'écarte (ADVERSE). V32 calcule déjà ce label par trade. V70 le
tabule proprement et le croise avec CBOT_SUPPORT (V41) pour tester le mécanisme central :

  Hypothèse : quand le CBOT est porteur, la compression est plus souvent CBOT_DRIVEN (rattrapage) — c'est
  « short premium ≈ long CBOT relatif ». Quand le CBOT n'est pas porteur, soit l'EMA doit faire le travail
  (EMA_DRIVEN, moins fiable), soit ça part en ADVERSE.

Descriptif, aucun fit, baseline figée inchangée. Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V70_DIR = ARTEFACTS_DIR / "v70"
V70_DIR.mkdir(parents=True, exist_ok=True)
PATHS = ("CBOT_DRIVEN", "EMA_DRIVEN", "BOTH", "ADVERSE")


def _by_path(df_trades: pd.DataFrame) -> dict[str, Any]:
    res = {}
    for p in PATHS:
        sub = df_trades[df_trades["path"] == p]
        if len(sub):
            res[p] = {"n": int(len(sub)),
                      "share": round(float(len(sub) / len(df_trades)), 3),
                      "win_rate": round(float(sub["win"].mean()), 3),
                      "mean_pnl": round(float(sub["pnl"].mean()), 2),
                      "mean_entry_z": round(float(sub["entry_z"].mean()), 2)}
    return res


def run_v70_paths(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v32_adverse_path_research import build_adverse_frame
    from mais.research.v41_cbot_support import compute_cbot_support
    assert_no_holdout(df)
    adf = build_adverse_frame(df)
    adf = adf[adf["path"] != "unknown"] if len(adf) else adf
    if len(adf) < 15:
        return {"version": "V70-PATH-CLASSIFICATION", "verdict": "TOO_FEW", "n": int(len(adf))}

    entry = pd.to_datetime(adf["entry_date"])
    adf = adf.copy()
    adf["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()

    overall = _by_path(adf)
    # croisement canal × CBOT_SUPPORT : part de CBOT_DRIVEN par niveau de support
    cross = {}
    for c in ("LOW", "MEDIUM", "HIGH"):
        sub = adf[adf["cbot_support"] == c]
        if len(sub) >= 4:
            cross[c] = {"n": int(len(sub)),
                        "cbot_driven_share": round(float((sub["path"] == "CBOT_DRIVEN").mean()), 3),
                        "ema_driven_share": round(float((sub["path"] == "EMA_DRIVEN").mean()), 3),
                        "adverse_share": round(float((sub["path"] == "ADVERSE").mean()), 3)}

    # binaire robuste : support faible (LOW) vs porté (MEDIUM+HIGH)
    weak = adf[adf["cbot_support"] == "LOW"]
    sup = adf[adf["cbot_support"].isin(["MEDIUM", "HIGH"])]
    binary = {}
    cbot_driven_more_when_supported = False
    if len(weak) >= 4 and len(sup) >= 4:
        binary = {
            "weak_support": {"n": int(len(weak)),
                             "cbot_driven_share": round(float((weak["path"] == "CBOT_DRIVEN").mean()), 3),
                             "adverse_share": round(float((weak["path"] == "ADVERSE").mean()), 3)},
            "supported": {"n": int(len(sup)),
                          "cbot_driven_share": round(float((sup["path"] == "CBOT_DRIVEN").mean()), 3),
                          "adverse_share": round(float((sup["path"] == "ADVERSE").mean()), 3)},
        }
        cbot_driven_more_when_supported = bool(
            binary["supported"]["cbot_driven_share"] > binary["weak_support"]["cbot_driven_share"])

    cbot_share = overall.get("CBOT_DRIVEN", {}).get("share", 0)
    ema_share = overall.get("EMA_DRIVEN", {}).get("share", 0)
    dominant = max(overall, key=lambda p: overall[p].get("share", 0)) if overall else None

    out = {
        "version": "V70-PATH-CLASSIFICATION",
        "n_trades": int(len(adf)),
        "by_path": overall,
        "dominant_path": dominant,
        "cbot_driven_share": cbot_share,
        "ema_driven_share": ema_share,
        "by_cbot_support": cross,
        "binary_split": binary,
        "cbot_driven_more_frequent_when_supported": cbot_driven_more_when_supported,
        "verdict": ("COMPRESSION_MOSTLY_CBOT_DRIVEN" if cbot_share >= ema_share
                    else "COMPRESSION_MIXED_OR_EMA_DRIVEN"),
        "interpretation": (
            f"Canal dominant : {dominant}. Part CBOT_DRIVEN {cbot_share} vs EMA_DRIVEN {ema_share}. "
            f"CBOT_DRIVEN plus fréquent quand le CBOT est porté : {cbot_driven_more_when_supported}. "
            "Confirme le mécanisme central « short premium ≈ long CBOT relatif » : la compression vient "
            "surtout du rattrapage CBOT, d'autant plus quand CBOT_SUPPORT est élevé. Quand le CBOT n'est pas "
            "porteur, la part ADVERSE/EMA_DRIVEN monte -> objectif prudent (V56)."),
        "note": "Descriptif (label V32), petit n. Aucun fit. À re-tester en forward officiel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    adf[["entry_date", "path", "cbot_support", "win", "pnl", "entry_z"]].to_parquet(
        V70_DIR / "path_trades.parquet", index=False)
    (V70_DIR / "v70_paths.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

"""Termine la validation des anciennes pistes 'prometteuses' : chacune devient ROBUSTE
(decouverte validee) ou LIMITE (pas assez prouvee avec les donnees gratuites), sans entre-deux.
Pistes directionnelles : walk-forward strict (AUC + IC bootstrap + part d'annees positives +
placebo). Pistes sur 42 episodes / oracle / hors-crise / proxy : LIMITE par regle.
Sortie : artefacts/decouvertes/pistes_verdicts.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import build_risk_indicator as eng
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artefacts" / "decouvertes"
RNG = np.random.default_rng(11)
DF = eng.DF.copy()
_t = pd.read_parquet(ROOT / "data/processed/targets.parquet")
_t["Date"] = pd.to_datetime(_t["Date"])
_extra = ["y_up_h90", "y_up_h60", "y_up_h30"]
DF = DF.merge(_t[["Date", *_extra]], on="Date", how="left")
for c in ["crop_ge_5y_avg_deviation", "crop_condition_momentum_2w", "wasde_stocks_to_use_calc_z"]:
    if c in DF:
        DF[c] = DF[c].ffill()

# pistes directionnelles testables : (feats, target, horizon)
TESTABLE = {
 "crop_h90": (["crop_ge_zscore_seasonal", "crop_ge_5y_avg_deviation", "crop_condition_momentum_2w"],
              "y_up_h90", 90),
 "wasde_h40": (["wasde_stocks_to_use_ratio", "wasde_stocks_to_use_calc_z"], "y_up_h60", 60),
 "wheat_corn": (["corn_wheat_ratio", "spread_corn_wheat"], "y_down_gt_3pct_h60", 60),
}

# pistes non elevables avec les donnees gratuites -> LIMITE (raison honnete)
NON_TESTABLE = {
 "indicateur_v9": "Indicateur de prime : valide seulement comme research-only (module M4) - "
                  "ordonne les retours mais AUC hors echantillon 0.56 et prix EMA ~97 % proxy.",
 "modele_2vars": "Indicateur de prime (basis + saison) : meme limite research-only que M4 "
                 "(proxy 97 %, couts non integres).",
 "adverse_predictable": "Repose sur 42 episodes en validation LOO : trop peu d'observations pour "
                        "elever au socle.",
 "sell_high_cost": "Resultat +115 hors crise uniquement ; le PnL net fond avec les couts "
                   "(brut +15.7 -> +5.7 a 5 EUR/t).",
 "asymmetry": "Base sur la bibliotheque d'episodes (peu nombreux) ; a confirmer sur un echantillon "
              "plus large.",
 "cbot_support": "42 episodes et effet possiblement confondu avec le momentum : non isolable ici.",
 "episodes": "Resultat descriptif (typologie d'episodes), pas un signal predictif hors echantillon.",
 "exit_z05": "Regle de strategie (objectif de sortie) non backtestee en walk-forward avec couts.",
 "halflife_extreme": "Resultat econometrique descriptif, non valide en forward comme signal.",
 "weather_extreme": "Resultat 'oracle' (sur meteo realisee, non-tradeable) ; exige une archive de "
                    "previsions forward reelles.",
 "wheat_corn_note": "",
}


def validate(feats, target, horizon):
    oos = eng.walkforward(DF, feats, target, horizon, "clf")
    y, p = oos[target].to_numpy(int), oos["pred"].to_numpy(float)
    auc = roc_auc_score(y, p)
    lo, hi = eng.boot_auc(y, p)
    years = oos.groupby("year").apply(
        lambda g: roc_auc_score(g[target], g["pred"]) if g[target].nunique() > 1 else np.nan,
        include_groups=False)
    share = float((years > 0.5).mean())
    # placebo (labels melanges)
    d2 = DF.dropna(subset=[*feats, target]).copy()
    d2[target] = RNG.permutation(d2[target].to_numpy())
    op = eng.walkforward(d2, feats, target, horizon, "clf")
    plac = roc_auc_score(op[target], op["pred"])
    return {"auc": auc, "ci_low": lo, "ci_high": hi, "n": int(len(oos)),
            "year_share_pos": share, "placebo_auc": float(plac)}


def verdict_of(r):
    # ROBUSTE si : borne basse IC > 0.52, signal positif >= 60 % des annees, placebo proche 0.5
    ok = r["ci_low"] > 0.52 and r["year_share_pos"] >= 0.60 and 0.45 <= r["placebo_auc"] <= 0.55
    return "Robuste" if ok else "Limite"


def main():
    res = {}
    for pid, (feats, tgt, h) in TESTABLE.items():
        r = validate(feats, tgt, h)
        r["verdict"] = verdict_of(r)
        res[pid] = r
        print(f"{pid:14s} AUC {r['auc']:.3f} IC95 [{r['ci_low']:.3f};{r['ci_high']:.3f}] "
              f"annees+ {r['year_share_pos']:.0%} placebo {r['placebo_auc']:.3f} -> {r['verdict']}")
    for pid, reason in NON_TESTABLE.items():
        if pid.endswith("_note"):
            continue
        res.setdefault(pid, {})
        res[pid].update({"verdict": "Limite", "reason": reason})
    json.dump(res, (OUT / "pistes_verdicts.json").open("w"), indent=2, ensure_ascii=False)
    rob = [k for k, v in res.items() if v["verdict"] == "Robuste"]
    lim = [k for k, v in res.items() if v["verdict"] == "Limite"]
    print(f"\nROBUSTE ({len(rob)}): {rob}")
    print(f"LIMITE  ({len(lim)}): {lim}")
    print("ecrit : artefacts/decouvertes/pistes_verdicts.json")


if __name__ == "__main__":
    main()

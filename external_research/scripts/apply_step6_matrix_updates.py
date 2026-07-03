"""Étape 6 — ajoute les colonnes de synthèse finale aux matrices maîtresses.

Source de vérité = final_experiment_verdicts.csv. Merge non destructif (pandas gère le
quoting). Colonnes ajoutées : final_verdict, final_reason, integrate_in_main_study,
step7_action. Les lignes sans expérience exécutée gardent des champs vides.
"""
from pathlib import Path

import pandas as pd

M = Path(__file__).resolve().parents[1] / "matrices"
fev = pd.read_csv(M / "final_experiment_verdicts.csv")
keys = fev[["experiment_id", "final_verdict", "reason",
            "integrate_in_main_study", "recommended_action"]].rename(
    columns={"reason": "final_reason", "recommended_action": "step7_action"})

NEW = ["final_verdict", "final_reason", "integrate_in_main_study", "step7_action"]


def update(path: Path, id_col: str):
    df = pd.read_csv(path, dtype=str)
    df = df.drop(columns=[c for c in NEW if c in df.columns])  # idempotent
    out = df.merge(keys, left_on=id_col, right_on="experiment_id", how="left")
    if "experiment_id" in df.columns:
        out = out.drop(columns=[c for c in ["experiment_id_y"] if c in out.columns])
        out = out.rename(columns={"experiment_id_x": "experiment_id"})
    elif "experiment_id" in out.columns and id_col != "experiment_id":
        out = out.drop(columns=["experiment_id"])
    out[NEW] = out[NEW].fillna("")
    out.to_csv(path, index=False)
    n = (out["final_verdict"] != "").sum()
    print(f"{path.name}: {len(out)} lignes, {n} avec verdict final")


update(M / "experiment_candidates.csv", "experiment_id")
update(M / "ideas_matrix.csv", "experiment_id")

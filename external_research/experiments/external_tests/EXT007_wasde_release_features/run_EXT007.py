"""EXT007 — Features de rapports WASDE (niveaux publies + calendrier).

Source unique : vintage EXT026 (available_from = publication+1BD). Cible :
log-retour CBOT t->t+h. BASE marche seul vs BASE+WASDE.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import wasde_utils as WU  # noqa: E402

EXP, DIRN = "EXT007", "EXT007_wasde_release_features"


def main():
    feats, fdict = WU.release_features()
    cols = list(feats.columns)
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    feats.dropna(how="all").to_csv(out / "wasde_release_features.csv")
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    # dictionnaire au nom demande
    import pandas as pd
    pd.DataFrame([{"feature": k, "description": v} for k, v in fdict.items()]).to_csv(
        out / "wasde_feature_dictionary.csv", index=False)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()

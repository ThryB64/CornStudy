"""EXT008 — Proxys de surprise WASDE (revisions M-M-1, SANS consensus analystes).

Terminologie volontairement prudente : wasde_revision_proxy. La vraie surprise
de marche (vs attentes analystes) n'est pas disponible.
Cible : log-retour CBOT t->t+h. BASE marche seul vs BASE+revisions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import wasde_utils as WU  # noqa: E402

EXP, DIRN = "EXT008", "EXT008_wasde_surprise_proxy"


def main():
    feats, fdict = WU.revision_proxy_features()
    cols = list(feats.columns)
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    feats.dropna(how="all").to_csv(out / "wasde_surprise_proxy_features.csv")
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()

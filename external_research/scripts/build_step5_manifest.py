"""Étape 5 bis — manifeste de l'effet de la correction target_date.

Compare, par horizon, l'ensemble d'évaluation sous l'ancienne règle (cible datée
`index + h jours calendaires`, buggy) et la nouvelle (`index[i+h]`, vraie ligne de
marché). Isolé sur le calendrier marché seul pour ne mesurer QUE la fuite holdout,
indépendamment des NaN de features propres à chaque expérience.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "external_research" / "experiments" / "external_tests" / "_common"))
import ext_harness as H  # noqa: E402

HOLDOUT = H.HOLDOUT_START
EVAL = pd.Timestamp("2008-01-01")


def main():
    idx = H.load_market().index
    rows = []
    for h in [5, 20, 40, 90]:
        true_tgt = H.target_dates_from_index(idx, h)          # index[i+h]
        cal_tgt = pd.Series(idx + pd.to_timedelta(h, "D"), index=idx)  # buggy
        base = (idx >= EVAL) & (idx < HOLDOUT)
        # cible définie (non-NaT) requise dans les deux cas
        defined = true_tgt.notna().to_numpy()
        buggy = base & defined & (cal_tgt < HOLDOUT).to_numpy()
        fixed = base & defined & (true_tgt < HOLDOUT).to_numpy()
        removed = buggy & ~fixed
        dec_before = idx[buggy].max()
        dec_after = idx[fixed].max()
        # vraie date cible de la dernière décision conservée après correction
        true_tgt_max_after = true_tgt[idx[fixed].max()]
        # vraie date cible de la dernière décision de l'ancien set (montre la fuite)
        true_tgt_max_before = true_tgt[dec_before]
        rows.append(dict(
            horizon=h,
            n_before=int(buggy.sum()),
            n_after=int(fixed.sum()),
            n_removed=int(removed.sum()),
            max_decision_date_before=dec_before.date(),
            max_decision_date_after=dec_after.date(),
            true_target_date_max_before=true_tgt_max_before.date(),
            true_target_date_max_after=true_tgt_max_after.date(),
            holdout_2024_excluded=bool((true_tgt[fixed] < HOLDOUT).all()),
        ))
    out = pd.DataFrame(rows)
    dest = ROOT / "external_research" / "results" / "external_tests" / "step5_sample_manifest_corrected.csv"
    out.to_csv(dest, index=False)
    print(out.to_string(index=False))
    print(f"\n-> {dest}")


if __name__ == "__main__":
    main()

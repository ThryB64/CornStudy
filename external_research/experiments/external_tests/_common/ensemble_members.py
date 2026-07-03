"""Membres directionnels communs pour EXT014 (BMA) et EXT050 (stacking)."""
from __future__ import annotations

import ext_harness as H
import ext_harness_dir as D
import features_p2 as F
import pandas as pd

MEMBER_SPECS = {
    "market_only": D.BASE_COLS,
    "market_wasde": D.BASE_COLS + ["s2u_z", "s2u_pctile", "s2u_slow_chg"],
    "market_crop": D.BASE_COLS + ["cond_gd_ex_anom", "cond_dev5y", "cond_poor_vp"],
}


def member_predictions(h: int) -> pd.DataFrame:
    """Retourne un DataFrame index=dates : prob de chaque membre + y_true.
    Chaque membre est déjà OOS (walk-forward), donc empilable sans fuite."""
    mkt = H.load_market()
    df, wcols, ccols, _ = F.build_p2_dataset()
    fam = df.reindex(mkt.index).ffill()
    X = mkt.join(fam[wcols + ccols])
    r = D.logret_target(mkt["corn_close"], h)
    out = None
    for name, cols in MEMBER_SPECS.items():
        res = D.walk_forward_clf(X, r, cols, h)
        s = pd.DataFrame({name: res["prob_up"], "y_true": res["y_true"]},
                         index=pd.DatetimeIndex(res["dates"]))
        out = s if out is None else out.join(s[[name]], how="inner")
    # membre random-walk (sans skill) = taux de base expandant, lagué
    rw = out["y_true"].expanding().mean().shift(1).fillna(0.5)
    out["rw_baserate"] = rw
    return out

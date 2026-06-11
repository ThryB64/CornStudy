"""V168 / T-SUBBASKET — Panier de substitution élargi vs ratio blé/maïs seul.

Hypothèse (R8) : la prime EMA est co-déterminée par le complexe céréales fourragères, pas seulement
le blé. Un panier (blé/maïs + avoine/maïs + soja/maïs, CBOT) devrait capturer le soutien de
substitution mieux que wheat_corn_z seul (V36/V41, séparateur ADVERSE 0.653).

Panier ÉQUIPONDÉRÉ figé ex-ante (aucune optimisation de poids), z expandant identique à V38
(min_periods=120). Orge et maïs Black Sea : DATA_BLOCKED (aucune série gratuite en repo). Le ratio
MATIF EBM/EMA (V52/V126) rejoindra le panier en FORWARD quand le journal aura >=150 observations.

Trois tests pré-déclarés contre l'incumbent wheat_corn_z, à périmètre identique :
  A. explication du NIVEAU du basis (corr, complet + 2 moitiés) ;
  B. séparation ADVERSE à l'entrée sur les 42 épisodes V82 (AUC univarié direction-ignorée) ;
  C. vitesse de compression (Spearman entre z à l'entrée et jours vers z0.5, épisodes non censurés).

Critères GO déclarés AVANT lecture : GO si le panier bat le blé seul sur >=2 tests avec marge
(corr +0.03, AUC +0.02, rho +0.05) ; NO_GO si 0 test gagné ; WATCHLIST sinon. n=42 -> DESCRIPTIF,
aucun fit multivarié, baseline z>1 intouchée. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V168_DIR = ARTEFACTS_DIR / "v168"
V168_DIR.mkdir(parents=True, exist_ok=True)
EPISODES = ROOT / "data" / "research" / "high_basis_episodes.parquet"
MATIF_HISTORY = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"

COMPONENTS = [("wheat_close", "wheat_corn_z"), ("oats_close", "oats_corn_z"),
              ("soy_close", "soy_corn_z")]
MIN_COMPONENTS = 2
MATIF_MIN_OBS = 150
MARGIN_CORR, MARGIN_AUC, MARGIN_RHO = 0.03, 0.02, 0.05


def expanding_ratio_z(num: pd.Series, den: pd.Series, min_periods: int = 120) -> pd.Series:
    """z expandant du ratio num/den, identique à V38 (_wheat_corn_ratio_z)."""
    ratio = pd.to_numeric(num, errors="coerce") / pd.to_numeric(den, errors="coerce")
    mu = ratio.expanding(min_periods=min_periods).mean()
    sd = ratio.expanding(min_periods=min_periods).std()
    return (ratio - mu) / sd


def build_basket(df: pd.DataFrame) -> pd.DataFrame:
    """Composants z + basket_z équipondéré (>=2 composants requis par date)."""
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    out = pd.DataFrame(index=df.index)
    for col, name in COMPONENTS:
        if col in df.columns:
            out[name] = expanding_ratio_z(df[col], corn)
    comp = [c for _, c in COMPONENTS if c in out.columns]
    enough = out[comp].notna().sum(axis=1) >= MIN_COMPONENTS
    out["basket_z"] = out[comp].mean(axis=1).where(enough)
    return out


def _sep_auc(x: pd.Series, y: pd.Series) -> float | None:
    """AUC univarié direction-ignorée (cadre VN-D3) : |AUC-0.5|+0.5."""
    m = x.notna() & y.notna()
    if m.sum() < 15 or y[m].nunique() < 2:
        return None
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return None
    auc = roc_auc_score(y[m].astype(int), x[m])
    return round(float(max(auc, 1 - auc)), 3)


def _halves_corr(basis: pd.Series, z: pd.Series) -> dict[str, float | None]:
    al = pd.concat([basis, z], axis=1).dropna()
    if len(al) < 100:
        return {"full": None, "h1": None, "h2": None}
    mid = len(al) // 2
    return {"full": round(float(al.iloc[:, 0].corr(al.iloc[:, 1])), 3),
            "h1": round(float(al.iloc[:mid, 0].corr(al.iloc[:mid, 1])), 3),
            "h2": round(float(al.iloc[mid:, 0].corr(al.iloc[mid:, 1])), 3)}


def _matif_forward_status() -> dict[str, Any]:
    if not MATIF_HISTORY.exists():
        return {"available": False, "n_obs": 0}
    hist = pd.read_parquet(MATIF_HISTORY)
    return {"available": True, "n_obs": int(len(hist)),
            "joins_basket_at": MATIF_MIN_OBS,
            "status": "FORWARD_ACCUMULATING" if len(hist) < MATIF_MIN_OBS else "READY"}


def run_v168_basket(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    basket = build_basket(df)
    if basket["basket_z"].notna().sum() < 300:
        return {"version": "V168-SUBBASKET", "verdict": "DATA_INSUFFICIENT"}
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    wc_z = basket.get("wheat_corn_z")

    # A — explication du niveau du basis
    corr_basket = _halves_corr(basis, basket["basket_z"])
    corr_wheat = _halves_corr(basis, wc_z)
    a_win = (corr_basket["full"] is not None and corr_wheat["full"] is not None
             and abs(corr_basket["full"]) >= abs(corr_wheat["full"]) + MARGIN_CORR
             and np.sign(corr_basket["h1"]) == np.sign(corr_basket["h2"]))

    # B — séparation ADVERSE à l'entrée (épisodes V82, n=42)
    b_block: dict[str, Any] = {"available": EPISODES.exists()}
    b_win = False
    if EPISODES.exists():
        ep = pd.read_parquet(EPISODES)
        entry = pd.to_datetime(ep["entry_date"])
        bz_entry = basket["basket_z"].reindex(entry).to_numpy()
        wz_entry = basket["wheat_corn_z"].reindex(entry).to_numpy()
        y = pd.to_numeric(ep["adverse"], errors="coerce")
        auc_basket = _sep_auc(pd.Series(bz_entry), y)
        auc_wheat = _sep_auc(pd.Series(wz_entry), y)
        auc_wheat_stored = _sep_auc(pd.to_numeric(ep.get("wheat_corn_z"), errors="coerce"), y)
        b_block.update({"n_episodes": int(len(ep)), "n_adverse": int(y.sum()),
                        "auc_basket": auc_basket, "auc_wheat_recomputed": auc_wheat,
                        "auc_wheat_stored_v82": auc_wheat_stored})
        b_win = (auc_basket is not None and auc_wheat is not None
                 and auc_basket >= auc_wheat + MARGIN_AUC)

        # C — vitesse de compression (non censurés seulement, censure rapportée)
        z05 = pd.to_datetime(ep.get("exit_z05_date"), errors="coerce")
        days = (z05 - entry).dt.days
        unc = days.notna()
        c_block: dict[str, Any] = {"n_uncensored": int(unc.sum()), "n_censored": int((~unc).sum())}
        c_win = False
        if unc.sum() >= 15:
            dd = days[unc].astype(float)
            rho_basket = pd.Series(bz_entry)[unc.to_numpy()].corr(dd.reset_index(drop=True),
                                                                  method="spearman")
            rho_wheat = pd.Series(wz_entry)[unc.to_numpy()].corr(dd.reset_index(drop=True),
                                                                 method="spearman")
            c_block.update({"rho_basket_days_to_z05": round(float(rho_basket), 3),
                            "rho_wheat_days_to_z05": round(float(rho_wheat), 3)})
            c_win = abs(rho_basket) >= abs(rho_wheat) + MARGIN_RHO
        b_block["speed"] = c_block
    else:
        c_win = False

    wins = int(a_win) + int(b_win) + int(c_win)
    verdict = ("GO_BASKET_BEATS_WHEAT" if wins >= 2
               else "NO_GO_WHEAT_SUFFICIENT" if wins == 0 else "WATCHLIST_MIXED")
    out = {
        "version": "V168-SUBBASKET",
        "verdict": verdict,
        "tests_won_by_basket": {"a_level_corr": bool(a_win), "b_adverse_auc": bool(b_win),
                                "c_compression_speed": bool(c_win), "total": wins},
        "basket": {"components": [c for _, c in COMPONENTS if c in basket.columns],
                   "weights": "equal_fixed_ex_ante", "n_days": int(basket["basket_z"].notna().sum())},
        "a_level_explanation": {"corr_basis_basket": corr_basket, "corr_basis_wheat": corr_wheat},
        "b_adverse_separation": b_block,
        "matif_ebm_forward": _matif_forward_status(),
        "data_blocked": ["orge (aucune série gratuite)", "maïs Black Sea (BCD illiquide/payant)"],
        "note": "Panier équipondéré figé ex-ante, z expandant V38, n=42 épisodes -> DESCRIPTIF. "
                "Aucun fit multivarié, aucun changement de seuil, baseline z>1 intouchée.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V168_DIR / "v168_substitution_basket.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

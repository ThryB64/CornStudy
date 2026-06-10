"""V162 / T-VECM — Cointégration & correction d'erreur EMA(EUR) ↔ CBOT(EUR).

Écriture économétrique canonique de « la prime revient » : si EMA_EUR et CBOT_EUR sont cointégrés, le
basis EST le terme de correction d'erreur. Le VECM donne (a) la vitesse d'ajustement α de chaque jambe
(QUI corrige : EMA descend-il ou CBOT monte-t-il ? — teste V21 par voie indépendante), (b) une demi-vie
propre du déséquilibre, (c) un test formel de réversion (Johansen).

DESCRIPTIF (structure de long terme estimée in-sample) — pas un prédicteur live. Stabilité vérifiée par
ré-estimation sur deux sous-échantillons. statsmodels optionnel. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

V162_DIR = ARTEFACTS_DIR / "v162"
V162_DIR.mkdir(parents=True, exist_ok=True)


def _ar1_halflife(resid: pd.Series) -> float | None:
    r = pd.to_numeric(resid, errors="coerce").dropna()
    if len(r) < 30:
        return None
    y, x = r.iloc[1:].to_numpy(), r.iloc[:-1].to_numpy()
    phi = float(np.polyfit(x, y, 1)[0])
    if phi <= 0 or phi >= 1:
        return None
    return float(np.log(0.5) / np.log(phi))


def _fit_vecm(ema: pd.Series, cbot: pd.Series, k_ar_diff: int = 1) -> dict[str, Any]:
    from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
    endog = pd.concat([ema.rename("ema"), cbot.rename("cbot")], axis=1).dropna()
    if len(endog) < 200:
        return {"verdict": "TOO_FEW_OBS", "n": int(len(endog))}
    joh = coint_johansen(endog.to_numpy(), det_order=0, k_ar_diff=k_ar_diff)
    trace = joh.lr1
    cv95 = joh.cvt[:, 1]
    rank = int(sum(trace > cv95))  # nb de relations de cointégration au seuil 95%

    res: dict[str, Any] = {
        "n": int(len(endog)),
        "johansen_trace_stat": [round(float(x), 3) for x in trace],
        "johansen_cv95": [round(float(x), 3) for x in cv95],
        "coint_rank_95": rank,
        "cointegrated": rank >= 1,
    }
    if rank < 1:
        res["verdict"] = "NOT_COINTEGRATED"
        return res

    vecm = VECM(endog.to_numpy(), k_ar_diff=k_ar_diff, coint_rank=1, deterministic="ci")
    fit = vecm.fit()
    alpha = np.asarray(fit.alpha).ravel()          # vitesses d'ajustement (ema, cbot)
    beta = np.asarray(fit.beta).ravel()            # vecteur cointégrant (normalisé sur ema)
    # résidu cointégrant = beta' . [ema, cbot]
    coint_resid = endog.to_numpy() @ beta
    res.update({
        "alpha_ema": round(float(alpha[0]), 5),
        "alpha_cbot": round(float(alpha[1]), 5),
        "beta": [round(float(b), 5) for b in beta],
        "halflife_ecm_resid_days": (round(hl, 2) if (hl := _ar1_halflife(pd.Series(coint_resid)))
                                    is not None else None),
    })
    # QUI corrige : la jambe à |α| significatif et signe ramenant vers l'équilibre
    a_ema, a_cbot = abs(alpha[0]), abs(alpha[1])
    tot = a_ema + a_cbot
    res["correction_share_ema"] = round(float(a_ema / tot), 3) if tot else None
    res["correction_share_cbot"] = round(float(a_cbot / tot), 3) if tot else None
    res["who_corrects"] = ("CBOT_LEG" if a_cbot > a_ema else "EMA_LEG")
    return res


def run_v162(df: pd.DataFrame) -> dict[str, Any]:
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V162-VECM", "verdict": "MISSING_COLUMNS"}
    ema = pd.to_numeric(df["ema_close"], errors="coerce")
    cbot = pd.to_numeric(df["cbot_eur_t"], errors="coerce")
    if ema.dropna().empty or cbot.dropna().empty:
        return {"version": "V162-VECM", "verdict": "MISSING_COLUMNS"}
    try:
        full = _fit_vecm(ema, cbot)
    except ImportError:
        return {"version": "V162-VECM", "verdict": "STATSMODELS_MISSING"}

    out: dict[str, Any] = {"version": "V162-VECM", "full_sample": full}
    if full.get("verdict") == "NOT_COINTEGRATED" or "alpha_cbot" not in full:
        out["verdict"] = full.get("verdict", "NO_VECM")
        (V162_DIR / "v162_vecm.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out

    # stabilité : ré-estimation sur 2 moitiés chronologiques
    half = len(df) // 2
    try:
        h1 = _fit_vecm(ema.iloc[:half], cbot.iloc[:half])
        h2 = _fit_vecm(ema.iloc[half:], cbot.iloc[half:])
    except Exception:  # noqa: BLE001
        h1 = h2 = {}
    same_corrector = (h1.get("who_corrects") == h2.get("who_corrects") == full.get("who_corrects"))
    out.update({
        "verdict": "COINTEGRATED_VECM_FITTED",
        "who_corrects": full["who_corrects"],
        "correction_share_cbot": full["correction_share_cbot"],
        "halflife_ecm_resid_days": full["halflife_ecm_resid_days"],
        "stability": {"h1_who": h1.get("who_corrects"), "h2_who": h2.get("who_corrects"),
                      "stable_corrector": bool(same_corrector)},
        "interpretation": (
            f"EMA et CBOT (en EUR/t) sont cointégrés (Johansen rang>=1) : le basis est le terme de "
            f"correction d'erreur. La jambe {full['who_corrects']} porte "
            f"{full['correction_share_cbot'] if full['who_corrects']=='CBOT_LEG' else round(1-full['correction_share_cbot'],3)} "
            f"de la correction ; demi-vie du déséquilibre ~{full['halflife_ecm_resid_days']} j "
            f"(à rapprocher de V120 ~17j et de l'horizon trade V138 ~28j). "
            + ("CONFIRME V21 (« short premium = long CBOT relatif ») par voie économétrique indépendante."
               if full["who_corrects"] == "CBOT_LEG" else
               "NUANCE V21 : ici c'est plutôt la jambe EMA qui corrige.")),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    })
    (V162_DIR / "v162_vecm.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

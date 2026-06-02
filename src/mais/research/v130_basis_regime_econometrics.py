"""V130 — Économétrie du basis par RÉGIMES : la demi-vie de réversion dépend-elle du contexte ?

V120/V121 ont établi que le basis_z est mean-reverting (AR1 φ≈0.96, demi-vie ≈17 j) et que c'est le NIVEAU
qu'on exploite. Ici on raffine : la vitesse de réversion change-t-elle selon le tier, PHYSICAL_TENSION,
CBOT_SUPPORT, ou le ratio blé/maïs ? On estime un AR(1) conditionnel par régime (φ → demi-vie = -ln2/lnφ),
un TAR (seuil sur basis_z : la réversion est-elle plus rapide quand z est haut ?), et, si statsmodels le
permet, un Markov-switching 2 régimes.

Garde-fous : ex-crise possible, comparaison AIC vs AR1 linéaire, rejet si gain marginal. assert_no_holdout.
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V130_DIR = ARTEFACTS_DIR / "v130"
V130_DIR.mkdir(parents=True, exist_ok=True)
TAR_THRESHOLD = 1.5


def _halflife(phi: float) -> float | None:
    if phi is None or not (0.0 < phi < 1.0):
        return None
    return round(float(-np.log(2) / np.log(phi)), 1)


def _ar1(x_prev: np.ndarray, x_cur: np.ndarray) -> dict[str, Any]:
    if len(x_prev) < 30:
        return {"n": int(len(x_prev)), "phi": None, "half_life_days": None}
    a, b = np.polyfit(x_prev, x_cur, 1)  # x_cur ≈ a*x_prev + b
    resid = x_cur - (a * x_prev + b)
    sse = float(np.sum(resid ** 2))
    n = len(x_prev)
    aic = n * np.log(sse / n + 1e-12) + 2 * 2
    return {"n": int(n), "phi": round(float(a), 4), "half_life_days": _halflife(a), "aic": round(aic, 1)}


def conditional_halflife(df: pd.DataFrame, regime: pd.Series, label: str) -> dict[str, Any]:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    r = regime.reindex(z.index)
    out = {}
    pair = pd.DataFrame({"prev": z.shift(1), "cur": z, "reg_prev": r.shift(1)}).dropna()
    for g in sorted(pair["reg_prev"].dropna().unique()):
        sub = pair[pair["reg_prev"] == g]
        out[str(g)] = _ar1(sub["prev"].to_numpy(), sub["cur"].to_numpy())
    return {"by": label, "regimes": out}


def _tier_regime(df: pd.DataFrame) -> pd.Series:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    def t(v):
        if pd.isna(v) or v < 1.0:
            return "NO_SIGNAL"
        if v < 1.5:
            return "MODERATE"
        return "STRONG" if v < 2.0 else "EXTREME"
    return z.map(t)


def tar_model(df: pd.DataFrame, threshold: float = TAR_THRESHOLD) -> dict[str, Any]:
    """AR(1) à seuil : φ distinct selon basis_z >= seuil ou non, vs AR1 linéaire (AIC)."""
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    pair = pd.DataFrame({"prev": z.shift(1), "cur": z}).dropna()
    lin = _ar1(pair["prev"].to_numpy(), pair["cur"].to_numpy())
    hi = pair[pair["prev"] >= threshold]
    lo = pair[pair["prev"] < threshold]
    ar_hi = _ar1(hi["prev"].to_numpy(), hi["cur"].to_numpy())
    ar_lo = _ar1(lo["prev"].to_numpy(), lo["cur"].to_numpy())
    aic_tar = (ar_hi.get("aic") or 0) + (ar_lo.get("aic") or 0)
    tar_better = bool(ar_hi.get("aic") is not None and ar_lo.get("aic") is not None
                      and lin.get("aic") is not None and aic_tar < lin["aic"] - 4)
    return {"threshold": threshold, "linear_ar1": lin, "above_threshold": ar_hi, "below_threshold": ar_lo,
            "tar_beats_linear_aic": tar_better}


def markov_switching(df: pd.DataFrame) -> dict[str, Any]:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").dropna()
    if len(z) < 300:
        return {"available": False, "reason": "série trop courte"}
    try:
        from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression
    except ImportError:
        return {"available": False, "reason": "statsmodels indisponible"}
    try:
        mod = MarkovAutoregression(z.to_numpy(), k_regimes=2, order=1, switching_ar=True)
        res = mod.fit(maxiter=100, disp=False)
        params = dict(zip(getattr(mod, "param_names", []), np.asarray(res.params), strict=False))
        phis = [round(float(params[k]), 4) for k in ("ar.L1[0]", "ar.L1[1]") if k in params]
        if not phis:
            return {"available": False, "reason": "params AR non identifiés"}
        return {"available": True, "n_regimes": 2, "regime_ar1_phi": phis,
                "regime_half_life_days": [_halflife(p) for p in phis],
                "aic": round(float(res.aic), 1)}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"{type(exc).__name__}: {str(exc)[:60]}"}


def run_v130_regime_econometrics(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    if z.notna().sum() < 300:
        return {"version": "V130-REGIME-ECONOMETRICS", "verdict": "NO_DATA"}

    by_tier = conditional_halflife(df, _tier_regime(df), "tier")
    cond = {"tier": by_tier}
    try:
        from mais.research.v54_physical_tension import compute_physical_tension
        pt = compute_physical_tension(df)["physical_tension"]
        cond["physical_tension"] = conditional_halflife(df, pt, "physical_tension")["regimes"]
    except Exception:  # noqa: BLE001
        pass
    try:
        from mais.research.v41_cbot_support import compute_cbot_support
        cs = compute_cbot_support(df)["cbot_support"]
        cond["cbot_support"] = conditional_halflife(df, cs, "cbot_support")["regimes"]
    except Exception:  # noqa: BLE001
        pass

    tar = tar_model(df)
    ms = markov_switching(df)

    # demi-vie par tier (signaux actifs) -> apport pour l'horizon V27
    tier_hl = {k: v.get("half_life_days") for k, v in by_tier["regimes"].items() if k != "NO_SIGNAL"}
    valid_hl = {k: v for k, v in tier_hl.items() if v is not None}
    spread_hl = (max(valid_hl.values()) - min(valid_hl.values())) if len(valid_hl) >= 2 else None
    differs = bool(spread_hl is not None and spread_hl >= 5)
    verdict = "ADD_TO_HORIZON_ESTIMATE" if differs else "WATCHLIST"

    out = {
        "version": "V130-REGIME-ECONOMETRICS",
        "verdict": verdict,
        "half_life_by_tier": tier_hl,
        "half_life_spread_days": round(spread_hl, 1) if spread_hl is not None else None,
        "conditional": cond,
        "tar": tar,
        "markov_switching": ms,
        "interpretation": (
            f"Demi-vie de réversion par tier : {tier_hl}. "
            + (f"Elle DIFFÈRE nettement selon le tier (écart {round(spread_hl,1)} j) -> affiner l'horizon "
               "saisonnier de V27 par tier." if differs else
               "Pas d'écart franc selon le tier -> garder l'horizon V27 ; WATCHLIST.")
            + f" TAR (seuil {TAR_THRESHOLD}) bat le linéaire (AIC) : {tar['tar_beats_linear_aic']} "
            f"(φ>seuil {tar['above_threshold'].get('phi')} vs φ<seuil {tar['below_threshold'].get('phi')}). "
            f"Markov-switching : {'dispo' if ms.get('available') else 'indispo'} "
            f"({ms.get('regime_ar1_phi') if ms.get('available') else ms.get('reason')})."),
        "note": "AR(1) conditionnel + TAR + Markov (statsmodels optionnel). Garde-fou overfit : AIC, rejet si "
                "gain marginal. CONTEXTE pour l'horizon, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V130_DIR / "v130_regime_econometrics.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def regime_econometrics_report_block() -> str:
    artefact = V130_DIR / "v130_regime_econometrics.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("version") != "V130-REGIME-ECONOMETRICS" or s.get("verdict") == "NO_DATA":
        return ""
    return (
        "### Demi-vie de réversion par régime (V130)\n"
        f"- Demi-vie par tier : {s['half_life_by_tier']} (écart {s['half_life_spread_days']} j)\n"
        f"- TAR bat linéaire : {s['tar']['tar_beats_linear_aic']} · Markov : "
        f"{'dispo' if s['markov_switching'].get('available') else 'indispo'}\n"
        f"- **{s['verdict']}**. CONTEXTE pour l'horizon, jamais un veto. RESEARCH_ONLY_NOT_TRADING.\n"
    )

"""V169 / T-BAYES — Survie bayésienne hiérarchique du time-to-z0.5 (R9).

Avec 42 épisodes, les point-estimates par sous-groupe (n=4..29) sont fragiles. On fournit des
postérieurs honnêtes via partial pooling : Weibull hiérarchique avec censure à droite pour le
time-to-z0.5, et logit hiérarchique pour le win-rate. Paramétrisation non centrée :
log lambda_g = mu + tau*eta_g. Priors faiblement informatifs : mu ~ N(log 30, 1.5^2),
tau ~ HalfNormal(1), log k ~ N(0, 0.5^2) ; win-rate : mu_p ~ N(0, 1.5^2), tau_p ~ HalfNormal(1).

Inférence : random-walk Metropolis numpy (pymc absent — refus de dépendance lourde pour n=42),
4 chaînes, adaptation du pas pendant le burn-in, split-Rhat rapporté. Questions PRÉ-DÉCLARÉES :
Q1 P(médiane EXTREME < médiane MODERATE) ; Q2 P(jul_aug plus lent que apr_jun) (V167) ;
Q3 largeur des intervalles crédibles win-rate par groupe (anti sur-interprétation des n petits).

Descriptif, baseline z>1 intouchée, aucun seuil modifié. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V169_DIR = ARTEFACTS_DIR / "v169"
V169_DIR.mkdir(parents=True, exist_ok=True)
EPISODES = ROOT / "data" / "research" / "high_basis_episodes.parquet"

N_CHAINS = 4
N_DRAWS = 24000
N_BURN = 8000
TIER_SHORT = {"SHORT_PREMIUM_MODERATE": "MODERATE", "SHORT_PREMIUM_STRONG": "STRONG",
              "SHORT_PREMIUM_EXTREME": "EXTREME"}


def _metropolis(logpost, dim: int, seed: int, n_draws: int = N_DRAWS,
                n_burn: int = N_BURN) -> np.ndarray:
    """RWM avec adaptation du pas (cible ~0.25) pendant le burn-in. Retourne (n_draws-n_burn, dim)."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 0.1, dim)
    lp = logpost(x)
    scale = 0.3
    out = np.empty((n_draws - n_burn, dim))
    acc = 0
    for i in range(n_draws):
        prop = x + rng.normal(0, scale, dim)
        lp_prop = logpost(prop)
        if np.log(rng.uniform()) < lp_prop - lp:
            x, lp = prop, lp_prop
            acc += 1
        if i < n_burn and i > 0 and i % 200 == 0:
            rate = acc / (i + 1)
            scale *= np.exp(0.5 * (rate - 0.25))
        if i >= n_burn:
            out[i - n_burn] = x
    return out


def _split_rhat(chains: list[np.ndarray]) -> float:
    """Split-Rhat max sur les dimensions (diagnostic de convergence rapporté, pas caché)."""
    halves = []
    for c in chains:
        mid = len(c) // 2
        halves += [c[:mid], c[mid:]]
    arr = np.stack(halves)  # (m, n, dim)
    n = arr.shape[1]
    means = arr.mean(axis=1)
    w = arr.var(axis=1, ddof=1).mean(axis=0)
    b = n * means.var(axis=0, ddof=1)
    var_hat = (n - 1) / n * w + b / n
    return float(np.sqrt(var_hat / w).max())


def _weibull_logpost_factory(t: np.ndarray, censored: np.ndarray, gidx: np.ndarray, n_g: int):
    """theta = [mu, log_tau, log_k, eta_1..eta_G] (non centré)."""
    def logpost(theta: np.ndarray) -> float:
        mu, log_tau, log_k = theta[0], theta[1], theta[2]
        eta = theta[3:]
        tau, k = np.exp(log_tau), np.exp(log_k)
        if k > 50 or tau > 50:
            return -np.inf
        lam = np.exp(mu + tau * eta)[gidx]
        z = (t / lam) ** k
        ll = np.where(censored, -z,
                      np.log(k) - k * np.log(lam) + (k - 1) * np.log(t) - z).sum()
        lp = (-0.5 * ((mu - np.log(30.0)) / 1.5) ** 2
              - 0.5 * (tau / 1.0) ** 2 + log_tau          # HalfNormal(1) + jacobien
              - 0.5 * (log_k / 0.5) ** 2
              - 0.5 * (eta ** 2).sum())
        return float(ll + lp)
    return logpost, 3 + n_g


def _logit_logpost_factory(win: np.ndarray, gidx: np.ndarray, n_g: int):
    """theta = [mu_p, log_tau_p, eta_1..eta_G]."""
    def logpost(theta: np.ndarray) -> float:
        mu, log_tau = theta[0], theta[1]
        eta = theta[2:]
        tau = np.exp(log_tau)
        if tau > 50:
            return -np.inf
        logit_p = (mu + tau * eta)[gidx]
        ll = (win * logit_p - np.log1p(np.exp(logit_p))).sum()
        lp = (-0.5 * (mu / 1.5) ** 2 - 0.5 * (tau / 1.0) ** 2 + log_tau
              - 0.5 * (eta ** 2).sum())
        return float(ll + lp)
    return logpost, 2 + n_g


def _ci(x: np.ndarray) -> dict[str, float]:
    return {"median": round(float(np.median(x)), 2),
            "ci5": round(float(np.percentile(x, 5)), 2),
            "ci95": round(float(np.percentile(x, 95)), 2)}


def fit_survival(t: np.ndarray, censored: np.ndarray, groups: pd.Series) -> dict[str, Any]:
    """Postérieurs des médianes de survie par groupe (jours vers z0.5), partial pooling."""
    labels = sorted(groups.unique())
    gidx = groups.map({g: i for i, g in enumerate(labels)}).to_numpy()
    logpost, dim = _weibull_logpost_factory(t, censored, gidx, len(labels))
    chains = [_metropolis(logpost, dim, seed=s) for s in range(N_CHAINS)]
    rhat = _split_rhat(chains)
    draws = np.concatenate(chains)
    mu, tau, k = draws[:, 0], np.exp(draws[:, 1]), np.exp(draws[:, 2])
    out: dict[str, Any] = {"rhat_max": round(rhat, 3), "k_shape": _ci(k),
                           "pooled_median_days": _ci(np.exp(mu) * np.log(2) ** (1 / k))}
    med = {}
    for i, g in enumerate(labels):
        lam_g = np.exp(mu + tau * draws[:, 3 + i])
        med[g] = lam_g * np.log(2) ** (1 / k)
        out[g] = {"n": int((gidx == i).sum()), "n_censored": int(censored[gidx == i].sum()),
                  "median_days_posterior": _ci(med[g])}
    out["_median_draws"] = med
    return out


def fit_winrate(win: np.ndarray, groups: pd.Series) -> dict[str, Any]:
    labels = sorted(groups.unique())
    gidx = groups.map({g: i for i, g in enumerate(labels)}).to_numpy()
    logpost, dim = _logit_logpost_factory(win, gidx, len(labels))
    chains = [_metropolis(logpost, dim, seed=100 + s) for s in range(N_CHAINS)]
    draws = np.concatenate(chains)
    mu, tau = draws[:, 0], np.exp(draws[:, 1])
    out: dict[str, Any] = {"rhat_max": round(_split_rhat(chains), 3),
                           "pooled_winrate": _ci(1 / (1 + np.exp(-mu)))}
    for i, g in enumerate(labels):
        p_g = 1 / (1 + np.exp(-(mu + tau * draws[:, 2 + i])))
        raw = win[gidx == i].mean()
        out[g] = {"n": int((gidx == i).sum()), "raw_winrate": round(float(raw), 3),
                  "posterior": _ci(p_g),
                  "ci_width": round(float(np.percentile(p_g, 95) - np.percentile(p_g, 5)), 3)}
    return out


def run_v169_bayes() -> dict[str, Any]:
    if not EPISODES.exists():
        return {"version": "V169-BAYES", "verdict": "NO_EPISODES"}
    ep = pd.read_parquet(EPISODES)
    entry = pd.to_datetime(ep["entry_date"])
    z05 = pd.to_datetime(ep["exit_z05_date"], errors="coerce")
    exit_d = pd.to_datetime(ep["exit_date"])
    censored = z05.isna().to_numpy()
    t = np.where(censored, (exit_d - entry).dt.days, (z05 - entry).dt.days).astype(float)
    t = np.clip(t, 1.0, None)
    win = pd.to_numeric(ep["win"], errors="coerce").fillna(0).to_numpy(dtype=float)
    tier = ep["tier"].map(TIER_SHORT).fillna("OTHER")
    season = ep["season"].astype(str)

    surv_tier = fit_survival(t, censored, tier)
    surv_season = fit_survival(t, censored, season)
    win_tier = fit_winrate(win, tier)

    # Questions pré-déclarées
    mt, ms = surv_tier.pop("_median_draws"), surv_season.pop("_median_draws")
    q1 = (round(float((mt["EXTREME"] < mt["MODERATE"]).mean()), 3)
          if "EXTREME" in mt and "MODERATE" in mt else None)
    q2 = (round(float((ms["jul_aug"] > ms["apr_jun"]).mean()), 3)
          if "jul_aug" in ms and "apr_jun" in ms else None)
    widths = {g: v["ci_width"] for g, v in win_tier.items()
              if isinstance(v, dict) and "ci_width" in v}

    out = {
        "version": "V169-BAYES",
        "verdict": "POSTERIORS_DELIVERED_DESCRIPTIVE",
        "n_episodes": int(len(ep)), "n_censored": int(censored.sum()),
        "survival_by_tier": surv_tier,
        "survival_by_season": surv_season,
        "winrate_by_tier": win_tier,
        "predeclared_questions": {
            "q1_p_extreme_faster_than_moderate": q1,
            "q2_p_summer_slower_than_spring": q2,
            "q3_winrate_ci_widths": widths,
        },
        "model": "Weibull hiérarchique censure droite + logit hiérarchique, non centré, "
                 "RWM numpy 4 chaînes (pymc absent), priors faiblement informatifs",
        "note": "Partial pooling = les groupes à n petit sont tirés vers le pool ; les CrI larges "
                "sont la réponse honnête au n=42. Aucun seuil modifié, baseline intouchée.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V169_DIR / "v169_bayes_survival.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

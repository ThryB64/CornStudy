"""V172 / T-OVERFIT — Défense anti-data-snooping (Bailey & López de Prado).

Avec ~42 trades et des dizaines de variantes explorées, le win rate brut peut être sur-ajusté. Ce module
fournit la batterie minimale exigée par les deux audits AVANT de marquer un résultat « VALIDÉ » :

  - PSR  : Probabilistic Sharpe Ratio (corrige skew/kurtosis et la taille d'échantillon).
  - DSR  : Deflated Sharpe Ratio (corrige en plus le nombre d'essais via le Sharpe max attendu).
  - PBO  : Probability of Backtest Overfitting (CSCV) — proba que la config best in-sample soit
           sous la médiane out-of-sample.

Aucune dépendance lourde (statsmodels optionnel) : on utilise scipy.stats.norm.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from itertools import combinations
from typing import Any

import numpy as np

try:
    from scipy.stats import norm
    _NORM_CDF = norm.cdf
    _NORM_PPF = norm.ppf
except ImportError:  # fallback sans scipy
    import math

    def _NORM_CDF(x):  # noqa: N802
        return 0.5 * (1.0 + math.erf(np.asarray(x) / math.sqrt(2.0)))

    def _NORM_PPF(p):  # noqa: N802
        # approx d'Acklam, suffisante pour nos usages
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188771972e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
             3.754408661907416e+00]
        p = float(p)
        plow, phigh = 0.02425, 1 - 0.02425
        if p < plow:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        if p > phigh:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

EULER_GAMMA = 0.5772156649015329


def sharpe_stats(returns: np.ndarray) -> dict[str, float]:
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    n = len(r)
    if n < 3 or r.std(ddof=1) == 0:
        return {"n": n, "sharpe": 0.0, "skew": 0.0, "kurt": 3.0}
    mu, sd = r.mean(), r.std(ddof=1)
    z = (r - mu) / sd
    skew = float((z**3).mean())
    kurt = float((z**4).mean())
    return {"n": n, "sharpe": float(mu / sd), "skew": skew, "kurt": kurt}


def probabilistic_sharpe_ratio(sharpe: float, n: int, skew: float, kurt: float,
                               sharpe_benchmark: float = 0.0) -> float:
    """PSR : P(SR_vrai > sharpe_benchmark). Sharpe par observation (non annualisé)."""
    if n < 3:
        return float("nan")
    denom = np.sqrt(max(1e-12, 1.0 - skew * sharpe + (kurt - 1.0) / 4.0 * sharpe**2))
    return float(_NORM_CDF((sharpe - sharpe_benchmark) * np.sqrt(n - 1) / denom))


def expected_max_sharpe(var_sr_trials: float, n_trials: int) -> float:
    """Sharpe max attendu sous n_trials essais indépendants (variance des SR donnée)."""
    if n_trials < 2 or var_sr_trials <= 0:
        return 0.0
    sigma = np.sqrt(var_sr_trials)
    e1 = _NORM_PPF(1.0 - 1.0 / n_trials)
    e2 = _NORM_PPF(1.0 - 1.0 / (n_trials * np.e))
    return float(sigma * ((1.0 - EULER_GAMMA) * e1 + EULER_GAMMA * e2))


def deflated_sharpe_ratio(returns: np.ndarray, n_trials: int,
                          var_sr_trials: float | None = None,
                          trial_sharpes: np.ndarray | None = None) -> dict[str, Any]:
    """DSR = PSR avec benchmark = Sharpe max attendu sous n_trials. Survit si DSR > 0.95 (ou > 0.5 mini)."""
    st = sharpe_stats(returns)
    if trial_sharpes is not None and len(np.asarray(trial_sharpes)) >= 2:
        var_sr = float(np.var(np.asarray(trial_sharpes, dtype=float), ddof=1))
    elif var_sr_trials is not None:
        var_sr = float(var_sr_trials)
    else:
        # défaut conservateur : variance inter-essais ~ 1/(n-1) (hypothèse SR nul, bruit d'estimation)
        var_sr = 1.0 / max(2, st["n"] - 1)
    sr_star = expected_max_sharpe(var_sr, n_trials)
    dsr = probabilistic_sharpe_ratio(st["sharpe"], st["n"], st["skew"], st["kurt"], sharpe_benchmark=sr_star)
    return {
        "sharpe_per_obs": round(st["sharpe"], 4), "n": st["n"],
        "skew": round(st["skew"], 3), "kurt": round(st["kurt"], 3),
        "n_trials": n_trials, "var_sr_trials": round(var_sr, 5),
        "expected_max_sharpe": round(sr_star, 4),
        "deflated_sharpe_ratio": round(float(dsr), 4),
        "survives": bool(dsr > 0.95),
    }


def pbo_cscv(perf_matrix: np.ndarray, n_splits: int = 10) -> dict[str, Any]:
    """PBO par Combinatorially Symmetric Cross-Validation.

    perf_matrix : (T observations) x (N stratégies) de rendements par période.
    Retourne PBO = fraction des partitions où la stratégie best-IS est sous la médiane OOS.
    """
    mat = np.asarray(perf_matrix, dtype=float)
    n_obs, n_strat = mat.shape
    if n_strat < 2 or n_obs < n_splits or n_splits % 2 != 0:
        return {"verdict": "SKIP", "reason": "matrice trop petite ou n_splits impair",
                "T": n_obs, "N": n_strat}
    # découpe en n_splits blocs contigus de tailles ~égales
    idx = np.array_split(np.arange(n_obs), n_splits)
    blocks = list(range(n_splits))
    lambdas = []
    for is_combo in combinations(blocks, n_splits // 2):
        is_rows = np.concatenate([idx[b] for b in is_combo])
        oos_rows = np.concatenate([idx[b] for b in blocks if b not in is_combo])
        def _sharpe(rows, _m=mat):
            sub = _m[rows]
            mu = sub.mean(axis=0)
            sd = sub.std(axis=0, ddof=1)
            sd[sd == 0] = np.nan
            return mu / sd
        sr_is = _sharpe(is_rows)
        sr_oos = _sharpe(oos_rows)
        if np.all(np.isnan(sr_is)):
            continue
        n_star = int(np.nanargmax(sr_is))
        # rang relatif OOS de la stratégie best-IS (0 = pire, 1 = meilleure)
        valid = ~np.isnan(sr_oos)
        if valid.sum() < 2 or np.isnan(sr_oos[n_star]):
            continue
        rank = (sr_oos[valid] < sr_oos[n_star]).sum() / (valid.sum() - 1)
        omega = min(max(rank, 1e-6), 1 - 1e-6)
        lambdas.append(np.log(omega / (1 - omega)))
    if not lambdas:
        return {"verdict": "SKIP", "reason": "aucune partition exploitable"}
    lambdas = np.array(lambdas)
    pbo = float((lambdas < 0).mean())
    return {
        "verdict": "OVERFIT_LIKELY" if pbo > 0.5 else "ROBUST",
        "pbo": round(pbo, 4), "n_partitions": len(lambdas),
        "median_logit": round(float(np.median(lambdas)), 4),
        "n_strategies": n_strat, "n_splits": n_splits,
    }


def reality_check_spa(perf_matrix: np.ndarray, n_boot: int = 2000, seed: int = 0) -> dict[str, Any]:
    """White Reality Check + Hansen SPA (recentrage consistant) sur un univers de stratégies.

    perf_matrix : (T périodes) x (N stratégies) de performance relative au benchmark (0 = nul).
    H0 : la MEILLEURE stratégie n'a pas de performance supérieure une fois corrigé du data-snooping.
    Retourne les p-values RC (White) et SPA_c (Hansen). p > 0.05 => pas significatif après recherche.
    """
    mat = np.asarray(perf_matrix, dtype=float)
    n, k = mat.shape
    if n < 8 or k < 2:
        return {"verdict": "SKIP", "reason": "univers trop petit", "T": n, "N": k}
    fbar = np.nanmean(mat, axis=0)
    sd = np.nanstd(mat, axis=0, ddof=1)
    sd[sd == 0] = np.nan
    sqrt_n = np.sqrt(n)
    v_white = float(np.nanmax(sqrt_n * fbar))
    v_spa = float(np.nanmax(sqrt_n * fbar / sd))  # studentisé (Hansen)
    # seuil de recentrage Hansen (écarte les très mauvaises stratégies de la nulle)
    thresh = -np.sqrt(2.0 * np.log(np.log(n))) * sd / sqrt_n
    keep = fbar >= thresh
    rng = np.random.default_rng(seed)
    cnt_white = cnt_spa = 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)  # bootstrap i.i.d. sur les périodes
        boot = mat[idx]
        fboot = np.nanmean(boot, axis=0)
        centered = sqrt_n * (fboot - fbar)
        if np.nanmax(centered) >= v_white:
            cnt_white += 1
        stud = np.where(keep, centered / sd, -np.inf)
        if np.nanmax(stud) >= v_spa:
            cnt_spa += 1
    p_white = cnt_white / n_boot
    p_spa = cnt_spa / n_boot
    best = int(np.nanargmax(fbar))
    return {
        "verdict": "SIGNIFICANT_AFTER_SNOOPING" if p_spa <= 0.05 else "NOT_SIGNIFICANT_AFTER_SNOOPING",
        "p_reality_check_white": round(p_white, 4),
        "p_spa_hansen": round(p_spa, 4),
        "best_strategy_index": best,
        "best_mean_perf": round(float(fbar[best]), 5),
        "n_periods": n, "n_strategies": k, "n_boot": n_boot,
    }


def run_overfitting_pack(returns: np.ndarray, n_trials: int,
                         perf_matrix: np.ndarray | None = None,
                         trial_sharpes: np.ndarray | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "version": "V172-OVERFITTING-PACK",
        "deflated_sharpe": deflated_sharpe_ratio(returns, n_trials, trial_sharpes=trial_sharpes),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    if perf_matrix is not None:
        out["pbo"] = pbo_cscv(perf_matrix)
        out["reality_check_spa"] = reality_check_spa(perf_matrix)
    dsr_ok = out["deflated_sharpe"]["survives"]
    pbo_ok = (out.get("pbo", {}).get("pbo", 1.0) < 0.5) if perf_matrix is not None else None
    out["overall"] = ("SURVIVES" if dsr_ok and (pbo_ok in (True, None)) else "REQUALIFY_EXPLORATORY")
    try:
        from mais.audit.data_truth import AUDIT_DIR
        (AUDIT_DIR / "overfitting_pack.json").write_text(json.dumps(out, indent=2, default=str),
                                                         encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return out

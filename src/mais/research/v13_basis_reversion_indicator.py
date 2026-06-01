"""V13 — Indicateur de mean-reversion du basis : sorties dynamiques, short strict, conformal, signe.

Suite V12. Thèse : la prime EMA/CBOT se comprend comme une mean-reversion du basis, surtout côté
compression (basis haut -> short premium). V13 affine l'exécution : quand sortir, quelle règle tient
strictement, comment s'abstenir par incertitude, et comment prédire le signe du basis_change.

- run_dynamic_exits        : compare H40/50/60, z->0.5, z->0, time-stops, stop-loss (PnL, MAE, profit/jour).
- run_short_rule_strict    : valide short basis_z>1 en LOYO + leave-one-crisis-out + saison/régime/coût.
- run_conformal_recalibration : alpha 0.10/0.15/0.20 + comparaison des méthodes d'abstention.
- run_basis_change_sign_models : signe du basis_change (logistic+z², isotonic, HistGB monotone).
- run_long_short_separated : modèles séparés compression (haut) vs rebond (bas) -> asymétrie.
- append_premium_journal   : journal append-only (V13-07), sans réécriture.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from mais.meta.cqr import _finite_sample_residual_quantile
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V13_DIR = ARTEFACTS_DIR / "v13"
V13_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
CRISIS_YEARS = (2020, 2021, 2022)


# ---------------------------------------------------------------------------
# Simulateur de trade : entrée basis extrême -> sortie selon règle
# ---------------------------------------------------------------------------

def _simulate_trade(ema, cbot, bz, i, side, rule, max_h=160):
    """Retourne (pnl_eur_t, holding_days_idx, mae_eur_t) pour un trade depuis l'indice i.

    rule : 'h40'/'h50'/'h60' (temps) ; 'z0.5'/'z0' (niveau) ; 'z0_max90'/'z0_max120' ;
           'sl10'/'sl15'/'sl20' (stop-loss + sortie z0).
    """
    n = len(ema)
    e0, c0, z0 = ema[i], cbot[i], bz[i]
    if np.isnan(e0) or np.isnan(c0) or np.isnan(z0):
        return np.nan, np.nan, np.nan
    sgn = np.sign(z0)
    mae = 0.0
    last_pnl, last_t = np.nan, np.nan
    sl_map = {"sl10": -10.0, "sl15": -15.0, "sl20": -20.0}
    for t in range(1, max_h + 1):
        j = i + t
        if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
            continue
        pnl = side * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0
        mae = min(mae, pnl)
        last_pnl, last_t = pnl, t
        zt = bz[j]
        if rule == "h40" and t >= 40:
            return pnl, t, mae
        if rule == "h50" and t >= 50:
            return pnl, t, mae
        if rule == "h60" and t >= 60:
            return pnl, t, mae
        if rule == "z0.5" and not np.isnan(zt) and abs(zt) < 0.5:
            return pnl, t, mae
        if rule == "z0" and not np.isnan(zt) and zt * sgn <= 0:
            return pnl, t, mae
        if rule == "z0_max90" and ((not np.isnan(zt) and zt * sgn <= 0) or t >= 90):
            return pnl, t, mae
        if rule == "z0_max120" and ((not np.isnan(zt) and zt * sgn <= 0) or t >= 120):
            return pnl, t, mae
        if rule in sl_map and (pnl <= sl_map[rule] or (not np.isnan(zt) and zt * sgn <= 0)):
            return pnl, t, mae
    return last_pnl, last_t, mae


def _entries_nonoverlap(df, mask, max_h=160):
    """Indices d'entrée non-overlap : on n'ouvre pas un nouveau trade tant que <40j du précédent."""
    idx = np.where(mask.values)[0]
    dates = df.index
    kept, last = [], None
    for i in idx:
        d = dates[i]
        if last is None or (d - last).days >= HORIZON:
            kept.append(i)
            last = d
    return kept


def _exit_metrics(df, entries, side_fn, rule):
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
    pnls, days, maes = [], [], []
    for i in entries:
        side = side_fn(bz[i])
        p, t, m = _simulate_trade(ema, cbot, bz, i, side, rule)
        if not np.isnan(p):
            pnls.append(p)
            days.append(t)
            maes.append(m)
    if len(pnls) < 6:
        return {"n": len(pnls)}
    pnls, days, maes = np.array(pnls), np.array(days), np.array(maes)
    return {
        "n": int(len(pnls)),
        "mean_pnl_eur_t": round(float(pnls.mean()), 2),
        "hit_rate": round(float((pnls > 0).mean()), 4),
        "mean_holding_days": round(float(days.mean()), 1),
        "median_holding_days": round(float(np.median(days)), 1),
        "mean_mae_eur_t": round(float(maes.mean()), 2),
        "p90_adverse_excursion_eur_t": round(float(np.quantile(maes, 0.10)), 2),
        "profit_per_day_held": round(float(pnls.sum() / max(days.sum(), 1)), 4),
        "net_pnl_cost3_total": round(float((pnls - 6).sum()), 1),
    }


# ---------------------------------------------------------------------------
# V13-02 — Sorties dynamiques
# ---------------------------------------------------------------------------

def run_dynamic_exits(df: pd.DataFrame) -> dict[str, Any]:
    """Compare les règles de sortie sur entrées basis extrême (|z|>1.5) et short basis-haut (z>1)."""
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "ema_cbot_basis_zscore_52w" not in df.columns:
        return {"version": "V13-02-DYNAMIC-EXITS", "verdict": "MISSING_DATA"}
    bz = df["ema_cbot_basis_zscore_52w"]
    rules = ["h40", "h50", "h60", "z0.5", "z0", "z0_max90", "z0_max120", "sl10", "sl15", "sl20"]

    def side_fn(z):
        return 1.0 if z < 0 else -1.0

    extreme = _entries_nonoverlap(df, (bz.abs() > 1.5))
    short_high = _entries_nonoverlap(df, (bz > 1.0))
    out_extreme = {r: _exit_metrics(df, extreme, side_fn, r) for r in rules}
    out_short = {r: _exit_metrics(df, short_high, lambda z: -1.0, r) for r in rules}

    def _best(d):
        valid = {k: v for k, v in d.items() if v.get("profit_per_day_held") is not None}
        if not valid:
            return None, None
        best_ppd = max(valid.items(), key=lambda kv: kv[1]["profit_per_day_held"])[0]
        best_pnl = max(valid.items(), key=lambda kv: kv[1]["mean_pnl_eur_t"])[0]
        return best_ppd, best_pnl

    bppd_e, bpnl_e = _best(out_extreme)
    bppd_s, bpnl_s = _best(out_short)
    out = {
        "version": "V13-02-DYNAMIC-EXITS",
        "extreme_entries_abs_z_gt_1.5": out_extreme,
        "short_high_entries_z_gt_1": out_short,
        "best_extreme_by_profit_per_day": bppd_e,
        "best_extreme_by_mean_pnl": bpnl_e,
        "best_short_by_profit_per_day": bppd_s,
        "best_short_by_mean_pnl": bpnl_s,
        "interpretation": (
            "profit_per_day_held arbitre capital immobilisé vs PnL : une sortie au niveau gagne plus mais "
            "immobilise plus longtemps. La meilleure règle dépend de la métrique (PnL total vs efficacité capital)."
        ),
        "verdict": "DYNAMIC_EXITS_DONE",
    }
    (V13_DIR / "dynamic_exits.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V13-03 — Validation stricte du short basis-haut
# ---------------------------------------------------------------------------

def run_short_rule_strict(df: pd.DataFrame) -> dict[str, Any]:
    """Valide short basis_z>1 : LOYO, leave-one-crisis-out, saison/régime, coûts, sorties."""
    assert_no_holdout(df)
    bz = df["ema_cbot_basis_zscore_52w"]
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bzv = bz.values
    entries = _entries_nonoverlap(df, (bz > 1.0))

    # PnL par trade pour sortie z0 (sortie de référence) et H40
    trades = []
    for i in entries:
        p_z0, t_z0, _ = _simulate_trade(ema, cbot, bzv, i, -1.0, "z0")
        p_h40, _, _ = _simulate_trade(ema, cbot, bzv, i, -1.0, "h40")
        if np.isnan(p_z0) or np.isnan(p_h40):
            continue
        trades.append({"year": df.index[i].year, "month": df.index[i].month,
                       "pnl_z0": p_z0, "pnl_h40": p_h40})
    tdf = pd.DataFrame(trades)
    if len(tdf) < 15:
        return {"version": "V13-03-SHORT-STRICT", "verdict": "TOO_FEW", "n": int(len(tdf))}

    def _summary(sub, col="pnl_z0"):
        if len(sub) < 5:
            return {"n": int(len(sub))}
        g = sub[col].values
        return {"n": int(len(sub)), "hit_rate": round(float((g > 0).mean()), 4),
                "mean_pnl": round(float(g.mean()), 2),
                "net_cost1": round(float((g - 2).sum()), 1),
                "net_cost3": round(float((g - 6).sum()), 1),
                "net_cost5": round(float((g - 10).sum()), 1)}

    # LOYO (par année)
    loyo = {str(y): _summary(tdf[tdf["year"] == y]) for y in sorted(tdf["year"].unique())}
    years_pos = sum(1 for v in loyo.values() if v.get("mean_pnl", -1) > 0 and v.get("n", 0) >= 5)
    years_eval = sum(1 for v in loyo.values() if v.get("n", 0) >= 5)

    # leave-one-crisis-out + leave-all-crises-out
    crisis = {f"exclude_{y}": _summary(tdf[tdf["year"] != y]) for y in CRISIS_YEARS}
    crisis["exclude_all_crises"] = _summary(tdf[~tdf["year"].isin(CRISIS_YEARS)])

    # par saison
    seasons = {"jan_mar": [1, 2, 3], "apr_jun": [4, 5, 6], "jul_aug": [7, 8],
               "sep_nov": [9, 10, 11], "dec": [12]}
    by_season = {s: _summary(tdf[tdf["month"].isin(mm)]) for s, mm in seasons.items()}

    # sortie z0 vs h40 global
    exit_compare = {"exit_z0": _summary(tdf, "pnl_z0"), "exit_h40": _summary(tdf, "pnl_h40")}

    robust = (years_pos / years_eval >= 0.6 if years_eval else False) and all(
        crisis[k].get("mean_pnl", -1) > 0 for k in crisis if crisis[k].get("n", 0) >= 5
    )
    out = {
        "version": "V13-03-SHORT-STRICT",
        "rule": "short if basis_z > 1, exit z0 (ref)",
        "n_trades": int(len(tdf)),
        "loyo_by_year": loyo,
        "loyo_years_positive": years_pos,
        "loyo_years_evaluable": years_eval,
        "leave_one_crisis_out": crisis,
        "by_season": by_season,
        "exit_compare": exit_compare,
        "verdict": "SHORT_RULE_ROBUST" if robust else "SHORT_RULE_PARTIAL",
        "note": "Spread proxy exploratoire, sortie z0 optimiste (mécanique). Research-only.",
    }
    (V13_DIR / "short_rule_strict.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Helpers basis_change
# ---------------------------------------------------------------------------

def _basis_change_frame(df: pd.DataFrame, h: int):
    basis = df["ema_cbot_basis"]
    x = pd.DataFrame({
        "basis_z": df.get("ema_cbot_basis_zscore_52w"),
        "month_cos": np.cos(2 * np.pi * df.index.month / 12),
        "month_sin": np.sin(2 * np.pi * df.index.month / 12),
        "eurusd": df.get("eurusd"),
    }, index=df.index)
    target = basis.shift(-h) - basis
    keep = target.notna() & x.notna().all(axis=1)
    return x.loc[keep], target.loc[keep]


# ---------------------------------------------------------------------------
# V13-01 — Recalibration de l'abstention conforme
# ---------------------------------------------------------------------------

def run_conformal_recalibration(df: pd.DataFrame, h: int = HORIZON) -> dict[str, Any]:
    """Teste alpha 0.10/0.15/0.20 et compare les méthodes d'abstention sur le signe du basis_change."""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V13-01-CONFORMAL-RECAL", "verdict": "MISSING_BASIS"}
    x, y = _basis_change_frame(df, h)
    if len(x) < 300:
        return {"version": "V13-01-CONFORMAL-RECAL", "verdict": "INSUFFICIENT", "n": int(len(x))}
    dates = x.index
    means, stds = x.mean(), x.std().replace(0, 1)
    xs = (x - means) / stds
    bz = x["basis_z"].values

    results = {}
    for alpha in (0.10, 0.15, 0.20):
        point = np.full(len(x), np.nan)
        hw = np.full(len(x), np.nan)
        for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
            train_end = dates[tr[-1]]
            te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=h)])
            if len(tr) < 120 or len(te_p) < 10:
                continue
            cut = int(len(tr) * 0.7)
            fit_idx, cal_idx = tr[:cut], tr[cut:]
            if len(cal_idx) < 30:
                continue
            reg = Ridge(alpha=1.0).fit(xs.iloc[fit_idx], y.iloc[fit_idx])
            q = _finite_sample_residual_quantile(np.abs(y.iloc[cal_idx].values - reg.predict(xs.iloc[cal_idx])), alpha)
            point[te_p] = reg.predict(xs.iloc[te_p])
            hw[te_p] = q
        v = ~np.isnan(point)
        if v.sum() < 50:
            results[f"alpha_{alpha}"] = {"verdict": "NO_OOF"}
            continue
        lo, hi = point - hw, point + hw
        yv = y.values
        cov = float(((yv[v] >= lo[v]) & (yv[v] <= hi[v])).mean())
        excl0 = (lo > 0) | (hi < 0)
        sgn_pred, sgn_true = np.sign(point), np.sign(yv)

        def _da(mask, v=v, sgn_pred=sgn_pred, sgn_true=sgn_true):
            m = v & mask
            return (round(float((sgn_pred[m] == sgn_true[m]).mean()), 4), int(m.sum())) if m.sum() >= 20 else (None, int(m.sum()))

        da_all, n_all = _da(np.ones(len(point), dtype=bool))
        da_conf, n_conf = _da(excl0)
        da_conf_short, n_conf_short = _da(excl0 & (bz > 1.0))
        results[f"alpha_{alpha}"] = {
            "empirical_coverage": round(cov, 4), "target_coverage": round(1 - alpha, 4),
            "da_all": da_all, "n_all": n_all,
            "da_conformal_excl0": da_conf, "n_conformal": n_conf,
            "da_conformal_and_short": da_conf_short, "n_conformal_short": n_conf_short,
        }

    # meilleure config : couverture proche cible ET da_conformal élevée
    best = None
    for k, v in results.items():
        if "empirical_coverage" not in v or v.get("da_conformal_excl0") is None:
            continue
        score = v["da_conformal_excl0"] - abs(v["empirical_coverage"] - v["target_coverage"])
        if best is None or score > best[1]:
            best = (k, score)
    out = {
        "version": "V13-01-CONFORMAL-RECAL",
        "results_by_alpha": results,
        "best_alpha_config": best[0] if best else None,
        "interpretation": (
            "On cherche la couverture la plus proche de la cible avec la meilleure DA conforme. "
            "da_conformal_and_short combine incertitude + côté robuste (short basis-haut)."
        ),
        "verdict": "CONFORMAL_RECALIBRATED",
    }
    (V13_DIR / "conformal_recalibration.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V13-05 — Modèles de signe du basis_change
# ---------------------------------------------------------------------------

def _oof_sign(x: pd.DataFrame, y_sign: pd.Series, embargo: int, model: str):
    dates = x.index
    means, stds = x.mean(), x.std().replace(0, 1)
    xs = (x - means) / stds
    oof = np.full(len(x), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo)])
        if len(tr) < 100 or len(te_p) < 10 or y_sign.iloc[tr].nunique() < 2:
            continue
        if model == "logistic":
            clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
            clf.fit(xs.iloc[tr], y_sign.iloc[tr])
            oof[te_p] = clf.predict_proba(xs.iloc[te_p])[:, 1]
        elif model == "isotonic_basisz":
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(x["basis_z"].iloc[tr].values, y_sign.iloc[tr].values)
            oof[te_p] = iso.predict(x["basis_z"].iloc[te_p].values)
        elif model == "histgb_monotonic":
            from sklearn.ensemble import HistGradientBoostingClassifier
            # basis_z attendu monotone décroissant pour P(basis monte) -> contrainte -1 sur basis_z
            mono = [-1 if c == "basis_z" else 0 for c in x.columns]
            clf = HistGradientBoostingClassifier(max_depth=3, max_iter=150, l2_regularization=1.0,
                                                 monotonic_cst=mono, random_state=42)
            clf.fit(x.iloc[tr], y_sign.iloc[tr])
            oof[te_p] = clf.predict_proba(x.iloc[te_p])[:, 1]
    v = ~np.isnan(oof)
    if v.sum() < 30 or len(np.unique(y_sign.values[v])) < 2:
        return None
    return {"auc": round(float(roc_auc_score(y_sign.values[v], oof[v])), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(
                y_sign.values[v], (oof[v] > 0.5).astype(int))), 4),
            "n_oof": int(v.sum())}


def run_basis_change_sign_models(df: pd.DataFrame, h: int = HORIZON) -> dict[str, Any]:
    """Prédit le signe du basis_change_h avec modèles simples (z², interactions, isotonic, HistGB monotone)."""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V13-05-SIGN-MODELS", "verdict": "MISSING_BASIS"}
    x, target = _basis_change_frame(df, h)
    y_sign = (target > 0).astype(int)

    feature_sets = {
        "linear_2var": x[["basis_z", "month_cos"]],
        "linear_4var": x[["basis_z", "month_cos", "month_sin", "eurusd"]],
        "with_z2_interaction": x.assign(
            basis_z2=x["basis_z"] ** 2,
            z_x_mcos=x["basis_z"] * x["month_cos"],
        )[["basis_z", "month_cos", "basis_z2", "z_x_mcos"]],
    }
    results = {}
    for fname, xf in feature_sets.items():
        for model in ("logistic", "histgb_monotonic"):
            r = _oof_sign(xf, y_sign, h, model)
            if r:
                results[f"{fname}__{model}"] = r
    iso = _oof_sign(x[["basis_z"]], y_sign, h, "isotonic_basisz")
    if iso:
        results["basisz_only__isotonic"] = iso

    best = max(results.items(), key=lambda kv: kv[1]["auc"]) if results else (None, {})
    out = {
        "version": "V13-05-SIGN-MODELS",
        "horizon": h,
        "results": results,
        "best_model": best[0],
        "best_auc": best[1].get("auc"),
        "interpretation": (
            "Si with_z2_interaction ou histgb_monotonic battent linear_2var -> non-linéarité utile sur le "
            "signe ; sinon le linéaire 2 vars suffit (cohérent avec la simplicité V10/V11)."
        ),
        "verdict": "SIGN_MODELS_DONE",
    }
    (V13_DIR / "basis_change_sign_models.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V13-06 — Modèles long/short séparés
# ---------------------------------------------------------------------------

def run_long_short_separated(df: pd.DataFrame, h: int = HORIZON) -> dict[str, Any]:
    """Deux modèles : compression (basis haut -> baisse) vs rebond (basis bas -> hausse). Asymétrie."""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V13-06-LONG-SHORT", "verdict": "MISSING_BASIS"}
    x, target = _basis_change_frame(df, h)
    y_sign = (target > 0).astype(int)
    bz = x["basis_z"]

    def _eval_subset(submask, expected):
        xs = x.loc[submask, ["basis_z", "month_cos", "eurusd"]]
        ys = y_sign.loc[submask]
        if len(xs) < 120 or ys.nunique() < 2:
            return {"n": int(len(xs)), "verdict": "INSUFFICIENT"}
        r = _oof_sign(xs, ys, h, "logistic")
        if r is None:
            return {"n": int(len(xs)), "verdict": "NO_OOF"}
        # base rate du sous-ensemble (compression attendue si basis haut -> base_rate bas)
        r["base_rate_basis_up"] = round(float(ys.mean()), 4)
        r["expected_direction"] = expected
        return r

    short_side = _eval_subset(bz > 0.5, "compression (basis_change < 0)")
    long_side = _eval_subset(bz < -0.5, "rebound (basis_change > 0)")
    out = {
        "version": "V13-06-LONG-SHORT",
        "short_premium_model_basis_high": short_side,
        "long_premium_model_basis_low": long_side,
        "asymmetry": {
            "short_auc": short_side.get("auc"),
            "long_auc": long_side.get("auc"),
            "short_better": bool((short_side.get("auc") or 0) > (long_side.get("auc") or 0)),
        },
        "interpretation": (
            "Confirme l'asymétrie V12 : le modèle de compression (basis haut) doit être plus fiable que "
            "le modèle de rebond (basis bas). Deux modèles, deux niveaux de confiance."
        ),
        "verdict": "LONG_SHORT_SEPARATED_DONE",
    }
    (V13_DIR / "long_short_separated.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V13-07 — Journal append-only
# ---------------------------------------------------------------------------

def append_premium_journal(df: pd.DataFrame, journal_path=None) -> dict[str, Any]:
    """Ajoute (append-only) les nouvelles lignes de signal au journal, sans jamais réécrire l'existant."""
    from mais.research.v12_mean_reversion_lab import build_premium_journal
    if journal_path is None:
        journal_path = ARTEFACTS_DIR / "v13" / "premium_journal.parquet"
    journal_path = journal_path if hasattr(journal_path, "exists") else __import__("pathlib").Path(journal_path)

    new = build_premium_journal(df)
    if new.empty:
        return {"verdict": "EMPTY", "n_total": 0}
    new = new.reset_index().rename(columns={"index": "date", new.index.name or "index": "date"})
    if "date" not in new.columns:
        new.insert(0, "date", build_premium_journal(df).index)

    if journal_path.exists():
        existing = pd.read_parquet(journal_path)
        known = set(pd.to_datetime(existing["date"]))
        fresh = new[~pd.to_datetime(new["date"]).isin(known)]
        combined = pd.concat([existing, fresh], ignore_index=True)
        n_added = int(len(fresh))
    else:
        combined = new
        n_added = int(len(new))
    combined.to_parquet(journal_path, index=False)
    return {"verdict": "APPENDED", "n_added": n_added, "n_total": int(len(combined)),
            "path": str(journal_path)}

"""V11 — Programme discipliné : modèle simplifié, régime forward, cost-aware, basis-change, règles.

Suite directe de la review V10. Principe : pas de meta-model, pas de H90, pas de prédiction d'EMA brut.
On consolide le signal compris (basis mean-reverting + saison) et on attaque honnêtement le mur des coûts.

- run_promote_simplified   : valide basis_z+month_cos vs 6 vars (OOF/LOYO/red team/backtest).
- run_forward_regime_filter: filtre régime CBOT appris sur train, appliqué forward (anti post-hoc).
- run_cost_aware_decision  : ne trade que si edge attendu (appris forward) > coût + marge.
- run_basis_change_regression : prédit directement basis_change_h (objet économique), pas une classe.
- run_simple_rules_lab_v11 : règles basis_z × saison × régime, p-values binomiales + correction BH.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from mais.indicator.structural_indicator_v9 import (
    HORIZON,
    SIMPLIFIED_FEATURES,
    STRUCTURAL_FEATURES,
    compute_signals,
    fit_oof_structural,
    run_loyo,
    run_red_team_v2,
)
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v10_market_discovery import _rel_target

V11_DIR = ARTEFACTS_DIR / "v11"
V11_DIR.mkdir(parents=True, exist_ok=True)


def _benjamini_hochberg(pvals: list[float], q: float = 0.10) -> list[bool]:
    """Renvoie le masque des hypothèses retenues sous contrôle FDR à q."""
    m = len(pvals)
    if m == 0:
        return []
    order = np.argsort(pvals)
    thresh = np.array([(i + 1) / m * q for i in range(m)])
    sorted_p = np.array(pvals)[order]
    passed_sorted = sorted_p <= thresh
    # plus grand k tel que p_(k) <= k/m*q ; tout en-dessous est retenu
    kmax = np.where(passed_sorted)[0].max() + 1 if passed_sorted.any() else 0
    keep_sorted = np.zeros(m, dtype=bool)
    keep_sorted[:kmax] = True
    keep = np.zeros(m, dtype=bool)
    keep[order] = keep_sorted
    return keep.tolist()


def _spread_pnl(df: pd.DataFrame, h: int = HORIZON):
    ema_ret = df["ema_close"].pct_change(h).shift(-h)
    cbot_ret = df["cbot_eur_t"].pct_change(h).shift(-h)
    return (ema_ret - cbot_ret), df["ema_close"]


def _nonoverlap_idx(dates: pd.DatetimeIndex, h: int = HORIZON) -> list:
    kept, last = [], None
    for d in dates:
        if last is None or (d - last).days >= h:
            kept.append(d)
            last = d
    return kept


# ---------------------------------------------------------------------------
# V11-01 — Promotion du modèle simplifié
# ---------------------------------------------------------------------------

def run_promote_simplified(df: pd.DataFrame) -> dict[str, Any]:
    """Valide basis_z+month_cos vs 6 vars sur toute la batterie : OOF, LOYO, red team, backtest."""
    assert_no_holdout(df)
    comparison = {}
    for name, feats in [("model_6var", STRUCTURAL_FEATURES), ("model_2var_simplified", SIMPLIFIED_FEATURES)]:
        fit = fit_oof_structural(df, features=feats)
        if fit["verdict"] != "OK":
            comparison[name] = {"verdict": fit["verdict"]}
            continue
        signals = compute_signals(df, fit["oof_cal"])
        # backtest spread sur signaux
        spread, price = _spread_pnl(df)
        side = pd.Series(0, index=df.index)
        side[signals["signal"] == "LONG_PREMIUM"] = 1
        side[signals["signal"] == "SHORT_PREMIUM"] = -1
        active = (side != 0) & spread.notna() & price.notna()
        kept = _nonoverlap_idx(df.index[active.values])
        gross = (spread.loc[kept] * side.loc[kept] * price.loc[kept]).values
        bt = {}
        for c in [0, 1, 2, 3, 5, 8]:
            net = gross - 2 * c
            bt[f"cost_{c}"] = round(float(net.sum()), 1)
        loyo = run_loyo(df, features=feats)
        rt = run_red_team_v2(df, n_perms=100, features=feats)
        comparison[name] = {
            "n_features": len(feats),
            "auc_cal": fit["metrics"].get("auc_cal"),
            "balanced_accuracy": fit["metrics"].get("balanced_accuracy"),
            "top20_da": fit["metrics"].get("top20_da"),
            "ece_cal": fit["metrics"].get("ece_cal"),
            "n_trades": len(kept),
            "backtest_net_pnl": bt,
            "loyo_verdict": loyo["verdict"],
            "loyo_mean_auc": loyo["summary"].get("mean_auc"),
            "red_team_p": rt.get("p_value"),
        }

    s6 = comparison.get("model_6var", {})
    s2 = comparison.get("model_2var_simplified", {})
    better = (
        s2.get("auc_cal", 0) > s6.get("auc_cal", 0)
        and s2.get("loyo_verdict") == "LOYO_STABLE"
        and (s2.get("red_team_p") or 1) <= 0.05
    )
    out = {
        "version": "V11-01-PROMOTE-SIMPLIFIED",
        "comparison": comparison,
        "auc_gain": (round(s2.get("auc_cal", 0) - s6.get("auc_cal", 0), 4)
                     if s2.get("auc_cal") and s6.get("auc_cal") else None),
        "verdict": "PROMOTE_SIMPLIFIED" if better else "KEEP_6VAR",
        "recommendation": (
            "Le modèle 2 variables (basis_z + month_cos) devient le cœur de l'indicateur."
            if better else "Conserver le modèle 6 variables."
        ),
    }
    (V11_DIR / "promote_simplified.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V11-02 — Filtre de régime CBOT en forward (anti post-hoc)
# ---------------------------------------------------------------------------

def _regime_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    macd = df.get("corn_macd_hist")
    vol = df.get("corn_realized_vol_20")
    masks = {"none": pd.Series(True, index=df.index)}
    if macd is not None:
        masks["uptrend"] = macd > 0
    if vol is not None:
        exp_med = vol.expanding(min_periods=200).median()
        masks["low_vol"] = vol <= exp_med
    if macd is not None and vol is not None:
        masks["uptrend_low_vol"] = (macd > 0) & (vol <= vol.expanding(min_periods=200).median())
    return masks


def run_forward_regime_filter(df: pd.DataFrame) -> dict[str, Any]:
    """Apprend le meilleur régime sur années passées, l'applique forward. Teste si V10-E tient."""
    assert_no_holdout(df)
    fit = fit_oof_structural(df, features=SIMPLIFIED_FEATURES)
    if fit["verdict"] != "OK":
        return {"version": "V11-02-FORWARD-REGIME", "verdict": fit["verdict"]}
    proba = fit["oof_cal"]
    y = _rel_target(df, HORIZON)
    spread, price = _spread_pnl(df)
    masks = _regime_masks(df)

    # trades candidats (cœur simplifié, deadband implicite via |p-0.5|>0.06 comme l'indicateur)
    side = pd.Series(0, index=df.index)
    side[proba > 0.56] = 1
    side[proba < 0.44] = -1
    base_active = (side != 0) & spread.notna() & price.notna() & proba.notna()

    years = sorted(df.index[base_active.values].year.unique())
    cost = 3  # coût de référence pour l'apprentissage du régime
    chosen, kept_dates, kept_regime = [], [], []
    for yr in years:
        train_mask = base_active & (df.index.year < yr)
        if df.index[train_mask.values].year.nunique() < 4:
            continue
        # net PnL par régime sur le passé (non-overlap)
        best_reg, best_net = "none", -1e18
        for rname, rmask in masks.items():
            sel = train_mask & rmask.reindex(df.index).fillna(False)
            kd = _nonoverlap_idx(df.index[sel.values])
            if len(kd) < 8:
                continue
            net = float((spread.loc[kd] * side.loc[kd] * price.loc[kd] - 2 * cost).sum())
            if net > best_net:
                best_net, best_reg = net, rname
        chosen.append((yr, best_reg))
        # appliquer le régime choisi à l'année test
        test_sel = base_active & (df.index.year == yr) & masks[best_reg].reindex(df.index).fillna(False)
        kd = _nonoverlap_idx(df.index[test_sel.values])
        kept_dates.extend(kd)
        kept_regime.extend([best_reg] * len(kd))

    # baseline forward : aucun filtre (régime none) sur les mêmes années test
    base_kd = []
    for yr in years:
        if df.index[(base_active & (df.index.year < yr)).values].year.nunique() < 4:
            continue
        base_kd.extend(_nonoverlap_idx(df.index[(base_active & (df.index.year == yr)).values]))

    def _metrics(dates):
        if len(dates) < 8:
            return {"n_trades": len(dates)}
        g = (spread.loc[dates] * side.loc[dates] * price.loc[dates]).values
        yy = (y.loc[dates] > 0.5).astype(int).values
        pp = (side.loc[dates] > 0).astype(int).values
        da = float((pp == yy).mean()) if len(np.unique(yy)) > 1 else None
        return {
            "n_trades": len(dates),
            "directional_accuracy": round(da, 4) if da else None,
            "net_pnl_cost2": round(float((g - 4).sum()), 1),
            "net_pnl_cost3": round(float((g - 6).sum()), 1),
            "net_pnl_cost5": round(float((g - 10).sum()), 1),
            "hit_rate": round(float((g > 0).mean()), 4),
        }

    filtered = _metrics(kept_dates)
    baseline = _metrics(base_kd)
    helps = (filtered.get("net_pnl_cost3", -1e9) > baseline.get("net_pnl_cost3", -1e9))
    out = {
        "version": "V11-02-FORWARD-REGIME",
        "regime_chosen_per_year": [{"year": int(y_), "regime": r} for y_, r in chosen],
        "forward_filtered": filtered,
        "forward_baseline_no_filter": baseline,
        "regime_filter_helps_forward": bool(helps),
        "verdict": "REGIME_FILTER_HELPS_FORWARD" if helps else "REGIME_FILTER_POST_HOC_ONLY",
        "note": "Régime appris uniquement sur années passées (forward strict). Coûts proxy, research-only.",
    }
    (V11_DIR / "forward_regime_filter.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V11-03 — Couche de décision cost-aware
# ---------------------------------------------------------------------------

def run_cost_aware_decision(df: pd.DataFrame) -> dict[str, Any]:
    """Ne trade que si l'edge brut attendu (appris forward via buckets de confiance) > coût + marge."""
    assert_no_holdout(df)
    fit = fit_oof_structural(df, features=SIMPLIFIED_FEATURES)
    if fit["verdict"] != "OK":
        return {"version": "V11-03-COST-AWARE", "verdict": fit["verdict"]}
    proba = fit["oof_cal"]
    spread, price = _spread_pnl(df)
    side = pd.Series(0, index=df.index)
    side[proba > 0.5] = 1
    side[proba < 0.5] = -1
    conf = (proba - 0.5).abs() * 2.0
    active = (side != 0) & spread.notna() & price.notna() & proba.notna()
    kept = _nonoverlap_idx(df.index[active.values])
    trades = pd.DataFrame({
        "date": kept,
        "year": [d.year for d in kept],
        "conf": conf.loc[kept].values,
        "gross": (spread.loc[kept] * side.loc[kept] * price.loc[kept]).values,
    })
    if len(trades) < 20:
        return {"version": "V11-03-COST-AWARE", "verdict": "TOO_FEW_TRADES", "n": int(len(trades))}

    years = sorted(trades["year"].unique())
    results = {}
    for cost, margin in [(3, 2.0), (5, 3.0)]:
        threshold = 2 * cost + margin
        kept_rows = []
        for yr in years:
            past = trades[trades["year"] < yr]
            if past["year"].nunique() < 4 or len(past) < 15:
                continue
            # edge attendu par bucket de confiance (quartiles appris sur le passé)
            qs = past["conf"].quantile([0.25, 0.5, 0.75]).values
            def _bucket(c, qs=qs):
                return int(np.searchsorted(qs, c))
            past = past.assign(b=past["conf"].map(_bucket))
            exp_edge = past.groupby("b")["gross"].mean()
            cur = trades[trades["year"] == yr].copy()
            cur["b"] = cur["conf"].map(_bucket)
            cur["exp_edge"] = cur["b"].map(exp_edge).fillna(-1e9)
            kept_rows.append(cur[cur["exp_edge"] > threshold])
        gated = pd.concat(kept_rows) if kept_rows else trades.iloc[:0]
        # comparaison : tous les trades (mêmes années test) sans gating
        all_test = trades[trades["year"].isin(
            [yr for yr in years if trades[trades["year"] < yr]["year"].nunique() >= 4]
        )]
        results[f"cost_{cost}"] = {
            "edge_threshold_eur_t": threshold,
            "gated_n_trades": int(len(gated)),
            "gated_net_pnl": round(float((gated["gross"] - 2 * cost).sum()), 1) if len(gated) else 0.0,
            "gated_hit_rate": round(float((gated["gross"] > 0).mean()), 4) if len(gated) else None,
            "ungated_n_trades": int(len(all_test)),
            "ungated_net_pnl": round(float((all_test["gross"] - 2 * cost).sum()), 1),
            "gating_improves": bool(
                (float((gated["gross"] - 2 * cost).sum()) if len(gated) else -1e9)
                > float((all_test["gross"] - 2 * cost).sum())
            ),
        }
    any_positive_cost5 = results.get("cost_5", {}).get("gated_net_pnl", -1) > 0
    out = {
        "version": "V11-03-COST-AWARE",
        "results_by_cost": results,
        "verdict": "COST_AWARE_BREAKS_WALL" if any_positive_cost5 else "COST_WALL_PERSISTS",
        "note": "Edge attendu appris uniquement sur années passées. Spread proxy, research-only.",
    }
    (V11_DIR / "cost_aware_decision.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V11-04 — Régression directe du basis change
# ---------------------------------------------------------------------------

def run_basis_change_regression(df: pd.DataFrame) -> dict[str, Any]:
    """Prédit basis_change_h (EUR/t) directement, plutôt qu'une classe up/down."""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V11-04-BASIS-CHANGE", "verdict": "MISSING_BASIS"}
    basis = df["ema_cbot_basis"]
    feats = ["basis_z", "month_cos", "eurusd"]
    x_all = df.reindex(columns=[]).assign(
        basis_z=df.get("ema_cbot_basis_zscore_52w"),
        month_cos=np.cos(2 * np.pi * df.index.month / 12),
        eurusd=df.get("eurusd"),
    )
    results = {}
    for h in (20, 30, 40, 60):
        target = basis.shift(-h) - basis
        keep = target.notna() & x_all.notna().all(axis=1)
        x, y = x_all.loc[keep], target.loc[keep]
        if len(x) < 200:
            results[f"h{h}"] = {"verdict": "INSUFFICIENT", "n": int(len(x))}
            continue
        dates = x.index
        means, stds = x.mean(), x.std().replace(0, 1)
        xs = (x - means) / stds
        oof = np.full(len(x), np.nan)
        for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
            train_end = dates[tr[-1]]
            te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=h)])
            if len(tr) < 80 or len(te_p) < 10:
                continue
            r = Ridge(alpha=1.0).fit(xs.iloc[tr], y.iloc[tr])
            oof[te_p] = r.predict(xs.iloc[te_p])
        v = ~np.isnan(oof)
        if v.sum() < 30:
            results[f"h{h}"] = {"verdict": "NO_OOF"}
            continue
        sign_da = float((np.sign(oof[v]) == np.sign(y.values[v])).mean())
        results[f"h{h}"] = {
            "n_oof": int(v.sum()),
            "r2": round(float(r2_score(y.values[v], oof[v])), 4),
            "mae_eur_t": round(float(mean_absolute_error(y.values[v], oof[v])), 3),
            "sign_directional_accuracy": round(sign_da, 4),
        }
    valid = {k: v for k, v in results.items() if "r2" in v}
    best = max(valid.items(), key=lambda kv: kv[1]["sign_directional_accuracy"]) if valid else (None, {})
    out = {
        "version": "V11-04-BASIS-CHANGE",
        "features": feats,
        "results_by_horizon": results,
        "best_horizon_by_sign_da": best[0],
        "interpretation": (
            "La régression du basis change est un objet économique direct : un sign-DA > 0.55 indique "
            "qu'on prédit la direction du mouvement de prime mieux que le hasard, sans passer par une classe."
        ),
        "verdict": "BASIS_CHANGE_REGRESSION_DONE",
    }
    (V11_DIR / "basis_change_regression.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V11-05 — Lab exhaustif de règles basis_z × saison × régime (BH corrigé)
# ---------------------------------------------------------------------------

def run_simple_rules_lab_v11(df: pd.DataFrame) -> dict[str, Any]:
    """Règles basis_z par saison/régime, hit rate vs 0.5 (binomial), correction BH FDR q=0.10."""
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V11-05-RULES-LAB", "verdict": "MISSING_PRICES"}
    spread, price = _spread_pnl(df)
    bz = df.get("ema_cbot_basis_zscore_52w")
    months = pd.Series(df.index.month, index=df.index)
    macd = df.get("corn_macd_hist", pd.Series(np.nan, index=df.index))

    seasons = {"all": months.notna(), "jan_mar": months.isin([1, 2, 3]),
               "apr_jun": months.isin([4, 5, 6]), "jul_aug": months.isin([7, 8]),
               "sep_nov": months.isin([9, 10, 11]), "dec": months == 12}
    regimes = {"any": pd.Series(True, index=df.index), "uptrend": macd > 0, "downtrend": macd <= 0}
    thresholds = [(-2, 1), (-1.5, 1), (-1, 1), (1, -1), (1.5, -1), (2, -1)]

    rules = []
    for thr, sidekind in thresholds:
        cond_base = (bz < thr) if sidekind == 1 else (bz > thr)
        for sname, smask in seasons.items():
            for rname, rmask in regimes.items():
                active = (cond_base & smask & rmask.reindex(df.index).fillna(False)
                          & spread.notna() & price.notna() & bz.notna())
                kd = _nonoverlap_idx(df.index[active.values])
                if len(kd) < 8:
                    continue
                g = (spread.loc[kd] * sidekind * price.loc[kd]).values
                wins = int((g > 0).sum())
                p = binomtest(wins, len(kd), 0.5, alternative="greater").pvalue
                rules.append({
                    "rule": f"basis_z{'<' if sidekind == 1 else '>'}{thr}_{sname}_{rname}",
                    "side": "long" if sidekind == 1 else "short",
                    "season": sname, "regime": rname, "threshold": thr,
                    "n_trades": len(kd), "hit_rate": round(wins / len(kd), 4),
                    "net_pnl_cost1": round(float((g - 2).sum()), 1),
                    "net_pnl_cost3": round(float((g - 6).sum()), 1),
                    "net_pnl_cost5": round(float((g - 10).sum()), 1),
                    "p_value": round(float(p), 4),
                })

    pvals = [r["p_value"] for r in rules]
    keep = _benjamini_hochberg(pvals, q=0.10)
    for r, k in zip(rules, keep, strict=False):
        r["bh_significant"] = bool(k)
    survivors = [r for r in rules if r["bh_significant"]]
    survivors_cost5 = [r for r in survivors if r["net_pnl_cost5"] > 0]
    rules_sorted = sorted(rules, key=lambda r: r["p_value"])

    out = {
        "version": "V11-05-RULES-LAB",
        "n_rules_tested": len(rules),
        "n_bh_significant_q10": len(survivors),
        "n_bh_significant_and_profitable_cost5": len(survivors_cost5),
        "top_rules_by_pvalue": rules_sorted[:12],
        "bh_significant_profitable_cost5": survivors_cost5,
        "interpretation": (
            "Seules les règles survivant à BH FDR q=0.10 ET profitables à coût 5 €/t sont des candidates "
            "économiques sérieuses. Le reste est probablement du bruit multi-test."
        ),
        "verdict": ("STABLE_RULES_FOUND" if survivors_cost5 else "NO_RULE_SURVIVES_COST_AND_FDR"),
    }
    (V11_DIR / "simple_rules_lab_v11.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

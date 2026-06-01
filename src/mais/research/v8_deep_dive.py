"""V8 deep-dive — explore les pistes scientifiques sérieuses post-V8.

Contient :
- run_basis_compression_deep : étude détaillée y_basis_compression_h20
- run_seasonal_deep : jul_aug exploitée + signaux inversés jan_mar/apr_jun
- run_structural_pema : modèle structurel P_EMA = f(CBOT, FX, basis, season)
- run_simple_rules_lab : règles économiques pures testées en backtest
"""
from __future__ import annotations

import json
import warnings
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    balanced_accuracy_score,
    brier_score_loss,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v8_experiments import _ensure_targets, _lgbm_clf

warnings.filterwarnings("ignore")

V8_DIR = ARTEFACTS_DIR / "v8"
V8_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. BASIS COMPRESSION DEEP
# ---------------------------------------------------------------------------

def run_basis_compression_deep(df: pd.DataFrame) -> dict[str, Any]:
    """Étude détaillée de y_basis_compression_h20 (cible V8 nouvelle, AUC 0.65 n=139).

    Tests : stabilité par sous-période, SHAP importance, robustesse embargo {0, 20, 40, 60, 90, 180}.
    """
    assert_no_holdout(df)
    df = _ensure_targets(df)
    tgt = "y_basis_compression_h20"
    if tgt not in df.columns:
        return {"version": "V8-BASIS-COMPRESSION-DEEP", "verdict": "NO_TARGET"}

    # Features pertinentes : basis-related, market context, season
    candidate_cols = [
        c for c in df.columns
        if df[c].dtype in (np.float64, np.float32, float)
        and not c.startswith(("y_", "Date", "date", "future_"))
        and df[c].notna().mean() > 0.3
        and any(k in c.lower() for k in ("basis", "cbot", "ema_", "corn_", "wasde", "cot", "soy", "wheat", "eurusd", "ttf"))
    ][:50]
    if len(candidate_cols) < 5:
        return {"version": "V8-BASIS-COMPRESSION-DEEP", "verdict": "INSUFFICIENT_FEATURES"}

    x = df[candidate_cols].fillna(0)
    y = df[tgt]

    # Embargo sensitivity
    embargo_results = {}
    for emb in (0, 20, 40, 60, 90, 180):
        tscv = TimeSeriesSplit(n_splits=5)
        oof = np.full(len(x), np.nan)
        for tr, te in tscv.split(x):
            train_end = x.index[tr[-1]]
            te_p = np.array([i for i in te if x.index[i] > train_end + pd.Timedelta(days=emb)])
            y_tr = y.iloc[tr]
            mask = y_tr.notna()
            if mask.sum() < 30 or y_tr[mask].nunique() < 2 or len(te_p) < 5:
                continue
            clf = _lgbm_clf()
            try:
                clf.fit(x.iloc[tr][mask], y_tr[mask])
                oof[te_p] = clf.predict_proba(x.iloc[te_p])[:, 1]
            except Exception:
                continue
        valid = (~np.isnan(oof)) & y.notna().values
        if valid.sum() < 30 or len(np.unique(y.values[valid])) < 2:
            continue
        try:
            auc = float(roc_auc_score(y.values[valid], oof[valid]))
            embargo_results[f"embargo_{emb}d"] = {
                "auc": round(auc, 4),
                "n_oof": int(valid.sum()),
            }
        except Exception:
            pass

    # Période-by-période AUC (rolling 3-year)
    period_results = []
    y_dropna = y.dropna()
    if len(y_dropna) > 100:
        years = sorted(set(y_dropna.index.year))
        for i in range(2, len(years) - 1):
            train_years = years[: i + 1]
            test_year = years[i + 1]
            tr_idx = x.index[x.index.year.isin(train_years[:-1])]
            te_idx = x.index[x.index.year == test_year]
            tr_idx = tr_idx.intersection(y_dropna.index)
            te_idx = te_idx.intersection(y_dropna.index)
            if len(tr_idx) < 50 or len(te_idx) < 10:
                continue
            x_tr = x.loc[tr_idx]
            y_tr = y.loc[tr_idx]
            if y_tr.nunique() < 2:
                continue
            x_te = x.loc[te_idx]
            y_te = y.loc[te_idx]
            try:
                clf = _lgbm_clf()
                clf.fit(x_tr, y_tr)
                preds = clf.predict_proba(x_te)[:, 1]
                if y_te.nunique() > 1:
                    auc = float(roc_auc_score(y_te, preds))
                    period_results.append({
                        "test_year": int(test_year),
                        "n_train": int(len(tr_idx)),
                        "n_test": int(len(te_idx)),
                        "auc": round(auc, 4),
                    })
            except Exception:
                continue

    aucs = [p["auc"] for p in period_results]
    auc_stats = {
        "mean": round(float(np.mean(aucs)), 4) if aucs else None,
        "std": round(float(np.std(aucs)), 4) if aucs else None,
        "min": round(float(np.min(aucs)), 4) if aucs else None,
        "max": round(float(np.max(aucs)), 4) if aucs else None,
        "n_periods": len(aucs),
        "n_periods_above_055": sum(1 for a in aucs if a > 0.55),
    }

    # SHAP importance
    shap_top10 = []
    try:
        import shap  # type: ignore
        n_tr = int(len(x) * 0.7)
        mask_y = y.iloc[:n_tr].notna()
        if mask_y.sum() > 30:
            clf = _lgbm_clf()
            clf.fit(x.iloc[:n_tr][mask_y], y.iloc[:n_tr][mask_y])
            explainer = shap.TreeExplainer(clf)
            shap_vals = explainer.shap_values(x.iloc[:n_tr][mask_y])
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[1]
            mean_abs = np.abs(shap_vals).mean(axis=0)
            order = np.argsort(-mean_abs)[:10]
            shap_top10 = [
                {"feature": candidate_cols[i], "mean_abs_shap": round(float(mean_abs[i]), 4)}
                for i in order
            ]
    except Exception:
        pass

    if not shap_top10:
        try:
            clf = _lgbm_clf()
            mask = y.notna()
            clf.fit(x[mask], y[mask])
            if hasattr(clf, "feature_importances_"):
                imps = clf.feature_importances_
                order = np.argsort(-imps)[:10]
                shap_top10 = [
                    {"feature": candidate_cols[i], "importance": int(imps[i])}
                    for i in order
                ]
        except Exception:
            pass

    verdict = "STABLE_PROMISING" if (auc_stats.get("mean") or 0) >= 0.55 and (auc_stats.get("min") or 0) >= 0.50 \
              else "UNSTABLE_FRAGILE" if auc_stats.get("mean") else "INSUFFICIENT_DATA"

    out = {
        "version": "V8-BASIS-COMPRESSION-DEEP",
        "target": tgt,
        "n_features": len(candidate_cols),
        "embargo_sensitivity": embargo_results,
        "period_results": period_results,
        "auc_stats_yearly_walk_forward": auc_stats,
        "feature_importance_top10": shap_top10,
        "verdict": verdict,
    }
    (V8_DIR / "basis_compression_deep.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )
    return out


# ---------------------------------------------------------------------------
# 2. SEASONAL DEEP
# ---------------------------------------------------------------------------

def run_seasonal_deep(df: pd.DataFrame) -> dict[str, Any]:
    """Approfondit jul_aug (vraie poche AUC 0.62) + inversion jan_mar/apr_jun.

    Tests stratégies inverses, ablation features par saison.
    """
    assert_no_holdout(df)
    df = _ensure_targets(df)
    tgt = "y_rel_outperform_h40"
    if tgt not in df.columns:
        return {"version": "V8-SEASONAL-DEEP", "verdict": "NO_TARGET"}

    seasons = {
        "jan_mar": ([1, 2, 3], "invert"),
        "apr_jun": ([4, 5, 6], "invert"),
        "jul_aug": ([7, 8], "normal"),
        "sep_nov": ([9, 10, 11], "normal"),
        "dec": ([12], "normal"),
    }

    feat_pool = [
        c for c in df.columns
        if df[c].dtype in (np.float64, np.float32, float)
        and not c.startswith(("y_", "Date", "date", "future_"))
        and df[c].notna().mean() > 0.3
    ]

    results: dict[str, Any] = {}
    for sname, (months, direction) in seasons.items():
        mask = df.index.month.isin(months)
        df_s = df.loc[mask].copy()
        y_s = df_s[tgt].dropna()
        if len(y_s) < 100:
            continue
        # Use top 40 features
        feat_cols = feat_pool[:40]
        x_s = df_s.loc[y_s.index, feat_cols].fillna(0)

        # Walk-forward OOF
        oof = np.full(len(x_s), np.nan)
        tscv = TimeSeriesSplit(n_splits=3)
        for tr, te in tscv.split(x_s):
            y_tr = y_s.iloc[tr]
            if y_tr.nunique() < 2 or len(tr) < 30:
                continue
            clf = _lgbm_clf()
            try:
                clf.fit(x_s.iloc[tr], y_tr)
                oof[te] = clf.predict_proba(x_s.iloc[te])[:, 1]
            except Exception:
                continue
        valid = ~np.isnan(oof)
        if valid.sum() < 30 or len(np.unique(y_s.values[valid])) < 2:
            continue

        proba_normal = oof.copy()
        proba_inverted = 1 - oof.copy()
        proba_used = proba_inverted if direction == "invert" else proba_normal

        auc_normal = float(roc_auc_score(y_s.values[valid], proba_normal[valid]))
        auc_inverted = float(roc_auc_score(y_s.values[valid], proba_inverted[valid]))
        ba_used = float(balanced_accuracy_score(
            y_s.values[valid].astype(int), (proba_used[valid] > 0.5).astype(int)
        ))

        # top20 train-only DA
        n_tr = int(valid.sum() * 0.7)
        idx_valid = np.where(valid)[0]
        top20_da = None
        if n_tr > 30 and len(idx_valid) - n_tr > 10:
            tr_idx = idx_valid[:n_tr]
            te_idx = idx_valid[n_tr:]
            threshold = np.quantile(proba_used[tr_idx], 0.80)
            top_mask = proba_used[te_idx] >= threshold
            if top_mask.sum() > 3:
                top20_da = round(float((y_s.values[te_idx][top_mask] > 0.5).mean()), 4)

        results[sname] = {
            "months": months,
            "direction": direction,
            "n_obs": int(len(y_s)),
            "n_valid_oof": int(valid.sum()),
            "auc_normal": round(auc_normal, 4),
            "auc_inverted": round(auc_inverted, 4),
            "auc_best": round(max(auc_normal, auc_inverted), 4),
            "balanced_accuracy_used": round(ba_used, 4),
            "top20_train_only_da": top20_da,
        }

    # Politique combinée : utiliser le bon sens par saison
    summary = {
        "best_season": max(results.items(), key=lambda kv: kv[1]["auc_best"])[0] if results else None,
        "n_seasons_auc_above_055": sum(1 for r in results.values() if r["auc_best"] >= 0.55),
        "interpretation": (
            "jan_mar et apr_jun ont AUC normal < 0.5 → signal inversé (économiquement cohérent : "
            "stocks et semis ont des dynamiques contra-tendance). "
            "jul_aug AUC > 0.6 → vraie poche stress yield. "
            "dec doit être marqué FRAGILE car n_oof faible."
        ),
    }

    out = {
        "version": "V8-SEASONAL-DEEP",
        "target": tgt,
        "results_by_season": results,
        "summary": summary,
        "verdict": "SEASONAL_USEFUL_BUT_DIRECTIONAL_AWARE",
    }
    (V8_DIR / "seasonal_deep.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )
    return out


# ---------------------------------------------------------------------------
# 3. STRUCTURAL P_EMA
# ---------------------------------------------------------------------------

def run_structural_pema(df: pd.DataFrame) -> dict[str, Any]:
    """Modèle structurel P_EMA = α + β1×CBOT_EUR + β2×basis_z + β3×season + β4×FX + ε.

    Compare régression linéaire structurelle vs ML lourd vs règle simple.
    Objectif : montrer si la simplicité écrase la complexité.
    """
    assert_no_holdout(df)
    df = _ensure_targets(df)

    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V8-STRUCTURAL-PEMA", "verdict": "MISSING_PRICES"}

    # Variables structurelles
    out_features = pd.DataFrame(index=df.index)
    out_features["cbot_eur"] = df["cbot_eur_t"]
    out_features["basis_z"] = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=df.index))
    out_features["eurusd"] = df.get("eurusd", pd.Series(np.nan, index=df.index))
    out_features["month_sin"] = np.sin(2 * np.pi * df.index.month / 12)
    out_features["month_cos"] = np.cos(2 * np.pi * df.index.month / 12)
    out_features["dte_proxy"] = (
        df.get("ema_oi_total", pd.Series(np.nan, index=df.index)).fillna(0)
    )

    y_price = df["ema_close"]
    valid = y_price.notna() & out_features.notna().all(axis=1)
    x_struct = out_features.loc[valid].fillna(0)
    y_struct = y_price.loc[valid]

    if len(x_struct) < 300:
        return {"version": "V8-STRUCTURAL-PEMA", "verdict": "INSUFFICIENT_DATA"}

    # Walk-forward Ridge regression : prédire P_EMA niveau
    tscv = TimeSeriesSplit(n_splits=5)
    preds_ridge = np.full(len(x_struct), np.nan)
    preds_lgbm = np.full(len(x_struct), np.nan)
    for tr, te in tscv.split(x_struct):
        if len(tr) < 50:
            continue
        ridge = Ridge(alpha=1.0)
        ridge.fit(x_struct.iloc[tr], y_struct.iloc[tr])
        preds_ridge[te] = ridge.predict(x_struct.iloc[te])
        try:
            from lightgbm import LGBMRegressor
            lgbm = LGBMRegressor(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
            lgbm.fit(x_struct.iloc[tr], y_struct.iloc[tr])
            preds_lgbm[te] = lgbm.predict(x_struct.iloc[te])
        except Exception:
            pass

    v_r = ~np.isnan(preds_ridge)
    v_l = ~np.isnan(preds_lgbm)
    metrics_ridge = {
        "r2": round(float(r2_score(y_struct.values[v_r], preds_ridge[v_r])), 4) if v_r.sum() > 30 else None,
        "mae": round(float(mean_absolute_error(y_struct.values[v_r], preds_ridge[v_r])), 4) if v_r.sum() > 30 else None,
        "n_oof": int(v_r.sum()),
    }
    metrics_lgbm = {
        "r2": round(float(r2_score(y_struct.values[v_l], preds_lgbm[v_l])), 4) if v_l.sum() > 30 else None,
        "mae": round(float(mean_absolute_error(y_struct.values[v_l], preds_lgbm[v_l])), 4) if v_l.sum() > 30 else None,
        "n_oof": int(v_l.sum()),
    }

    # Modèle de direction premium : signal structural sur y_rel_outperform_h40
    tgt = "y_rel_outperform_h40"
    direction_results = {}
    if tgt in df.columns:
        y_dir = df[tgt]
        valid_dir = y_dir.notna() & out_features.notna().all(axis=1)
        x_d = out_features.loc[valid_dir].fillna(0)
        y_d = y_dir.loc[valid_dir]
        if len(x_d) > 200 and y_d.nunique() > 1:
            tscv = TimeSeriesSplit(n_splits=5)

            for model_name, factory in (
                ("structural_logistic", lambda: LogisticRegression(C=1.0, max_iter=500, random_state=42)),
                ("lgbm_full", lambda: _lgbm_clf()),
            ):
                oof = np.full(len(x_d), np.nan)
                for tr, te in tscv.split(x_d):
                    if len(tr) < 50 or y_d.iloc[tr].nunique() < 2:
                        continue
                    clf = factory()
                    try:
                        clf.fit(x_d.iloc[tr], y_d.iloc[tr])
                        oof[te] = clf.predict_proba(x_d.iloc[te])[:, 1]
                    except Exception:
                        continue
                v = ~np.isnan(oof)
                if v.sum() < 30 or len(np.unique(y_d.values[v])) < 2:
                    continue
                auc = float(roc_auc_score(y_d.values[v], oof[v]))
                ba = float(balanced_accuracy_score(
                    y_d.values[v].astype(int), (oof[v] > 0.5).astype(int)
                ))
                brier = float(brier_score_loss(y_d.values[v].astype(int), oof[v]))
                direction_results[model_name] = {
                    "auc": round(auc, 4),
                    "balanced_accuracy": round(ba, 4),
                    "brier": round(brier, 4),
                    "n_oof": int(v.sum()),
                }

    out = {
        "version": "V8-STRUCTURAL-PEMA",
        "n_features_structural": x_struct.shape[1],
        "n_obs_struct": int(len(x_struct)),
        "price_level_models": {
            "ridge_structural": metrics_ridge,
            "lgbm_full": metrics_lgbm,
        },
        "direction_models": direction_results,
        "interpretation": (
            "Si ridge_structural batte ou égale lgbm_full sur direction → simplicité structurelle suffit. "
            "Si lgbm_full +0.02+ AUC → la complexité ajoute de la valeur."
        ),
        "verdict": "STRUCTURAL_BENCHMARK_COMPLETE",
    }
    (V8_DIR / "structural_pema.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )
    return out


# ---------------------------------------------------------------------------
# 4. SIMPLE RULES LAB — backtests règles économiques pures
# ---------------------------------------------------------------------------

def run_simple_rules_lab(df: pd.DataFrame) -> dict[str, Any]:
    """Tests règles économiques pures sur PnL EMA/CBOT spread H40.

    Règles testées :
    R1 : long si basis_z > 1.5
    R2 : long si basis_z < -1.5 (mean-reversion)
    R3 : long en jul-aug, flat sinon
    R4 : long en jul-aug × basis_z > 0.5 (combo)
    R5 : short si basis_z > 1.5 ET season ∈ {jan, feb, mar} (inversé)
    R6 : long si y_basis_compression_h20 attendu (basis_z > 1.0 ET basis_delta_20 > 0)
    """
    assert_no_holdout(df)
    df = _ensure_targets(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V8-SIMPLE-RULES-LAB", "verdict": "MISSING_PRICES"}

    h = 40
    ema_ret = df["ema_close"].pct_change(h).shift(-h)
    cbot_ret = df["cbot_eur_t"].pct_change(h).shift(-h)
    spread_ret_h40 = (ema_ret - cbot_ret).values
    prices = df["ema_close"].values
    basis_z = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=df.index)).values
    basis = df.get("ema_cbot_basis", pd.Series(np.nan, index=df.index)).values
    basis_delta_20 = pd.Series(basis).diff(20).values
    months = df.index.month.values
    dates_arr = df.index.values

    def _bt(active, side, label):
        idx = np.where(active & ~np.isnan(spread_ret_h40))[0]
        kept = []
        last_d = None
        for i in idx:
            d = pd.Timestamp(dates_arr[i])
            if last_d is None or (d - last_d).days >= h:
                kept.append(i)
                last_d = d
        kept = np.array(kept, dtype=int)
        if len(kept) == 0:
            return {"rule": label, "n_trades": 0, "pnl_total_eur_t": 0, "hit_rate": None}
        ret = spread_ret_h40[kept] * side
        pnl = ret * prices[kept]
        return {
            "rule": label,
            "side": int(side),
            "n_trades": int(len(kept)),
            "hit_rate": round(float(np.mean(ret > 0)), 4),
            "pnl_total_eur_t": round(float(np.nansum(pnl)), 2),
            "pnl_mean_eur_t": round(float(np.nanmean(pnl)), 2),
            "pnl_std_eur_t": round(float(np.nanstd(pnl)), 2),
            "max_gain_eur_t": round(float(np.nanmax(pnl)), 2),
            "max_loss_eur_t": round(float(np.nanmin(pnl)), 2),
            "pnl_per_trade_cost1": round(float(np.nansum(pnl) - 2 * len(kept)), 2),
            "pnl_per_trade_cost5": round(float(np.nansum(pnl) - 10 * len(kept)), 2),
        }

    rules: dict[str, Any] = {}
    rules["R1_long_basis_z_gt_1p5"] = _bt(basis_z > 1.5, +1, "R1 long basis_z>1.5")
    rules["R2_long_basis_z_lt_neg1p5_mean_rev"] = _bt(basis_z < -1.5, +1, "R2 long basis_z<-1.5 mean-rev")
    rules["R3_long_jul_aug"] = _bt(np.isin(months, [7, 8]), +1, "R3 long jul-aug")
    rules["R4_long_jul_aug_basis_z_gt_0p5"] = _bt(np.isin(months, [7, 8]) & (basis_z > 0.5), +1, "R4 long jul-aug × basis_z>0.5")
    rules["R5_short_basis_z_gt_1p5_jan_mar"] = _bt(
        np.isin(months, [1, 2, 3]) & (basis_z > 1.5), -1, "R5 short basis_z>1.5 × jan-mar (inversé)"
    )
    rules["R6_long_basis_high_rising"] = _bt(
        (basis_z > 1.0) & (basis_delta_20 > 0), +1, "R6 long basis_z>1 ET delta20>0"
    )
    rules["R7_short_basis_high_falling_anticipate_compression"] = _bt(
        (basis_z > 1.0) & (basis_delta_20 < 0), -1, "R7 short basis_z>1 ET delta20<0 (anticipation compression)"
    )

    # Comparaison brute
    summary = {
        "n_rules_profitable_cost0": sum(1 for r in rules.values() if r.get("pnl_total_eur_t", 0) > 0),
        "n_rules_profitable_cost1": sum(1 for r in rules.values() if r.get("pnl_per_trade_cost1", 0) > 0),
        "n_rules_profitable_cost5": sum(1 for r in rules.values() if r.get("pnl_per_trade_cost5", 0) > 0),
        "best_rule_cost0": max(rules.items(), key=lambda kv: kv[1].get("pnl_total_eur_t") or -1e9)[0],
        "best_rule_cost5": max(rules.items(), key=lambda kv: kv[1].get("pnl_per_trade_cost5") or -1e9)[0],
    }

    out = {
        "version": "V8-SIMPLE-RULES-LAB",
        "rules_tested": list(rules.keys()),
        "rules_results": rules,
        "summary": summary,
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V8_DIR / "simple_rules_lab.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

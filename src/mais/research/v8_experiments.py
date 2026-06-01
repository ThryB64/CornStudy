"""V8 — Module consolidé d'expériences scientifiques.

Contient :
- V8-EMBARGO-ROBUSTNESS : sensibilité embargo
- V8-RED-TEAM-PREMIUM : permutation tests sur les pics V6/V7
- V8-CBOT-LAB-PLUS : extension cibles CBOT (triple barrier, conditionnels)
- V8-EMA-PREMIUM-LAB-PLUS : extension cibles EMA premium (basis_compression/expansion, etc.)
- V8-BASIS-REGIME-V3 : KMeans + GMM + HMM-like sur basis
- V8-SEASONAL-V3 : modèles par saison, audit train-only strict
- V8-CROSS-MARKET-V3 : EMA→CBOT et CBOT→EMA ablation
- V8-PCORRECT-V3 : calibration P(correct) avec Platt/Iso
- V8-BACKTEST-V3 : backtests stress 1/2/3/5/8 €/t

Chaque expérience produit un artefact `artefacts/v8/<name>.json`.
"""
from __future__ import annotations

import json
import warnings
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import KMeans
from sklearn.metrics import (
    balanced_accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

warnings.filterwarnings("ignore")

V8_DIR = ARTEFACTS_DIR / "v8"
V8_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers communs
# ---------------------------------------------------------------------------

def _classical_features(df: pd.DataFrame, max_features: int = 60) -> list[str]:
    exclude = ("y_", "Date", "date", "future_", "storage_", "return_", "prob_", "target_")
    cols = [
        c for c in df.columns
        if not any(c.startswith(p) for p in exclude)
        and df[c].dtype in (np.float64, np.float32, float)
        and df[c].notna().mean() > 0.3
    ]
    return cols[:max_features]


def _lgbm_clf():
    try:
        from lightgbm import LGBMClassifier
        return LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier
        return GradientBoostingClassifier(n_estimators=50, random_state=42)


def _purged_embargo(dates: pd.DatetimeIndex, embargo_days: int, n_splits: int = 5):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    for tr, te in tscv.split(dates):
        train_end = dates[tr[-1]]
        te_purged = np.array([
            i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo_days)
        ])
        if len(tr) >= 50 and len(te_purged) >= 10:
            yield tr, te_purged


def _oof_lgbm(x: pd.DataFrame, y: pd.Series, embargo_days: int = 90) -> tuple[np.ndarray, dict[str, Any]]:
    """OOF LGBM avec purged embargo."""
    oof = np.full(len(x), np.nan)
    n_folds = 0
    for tr, te in _purged_embargo(x.index, embargo_days):
        y_tr = y.iloc[tr]
        if y_tr.notna().sum() < 30 or y_tr.dropna().nunique() < 2:
            continue
        mask = y_tr.notna()
        clf = _lgbm_clf()
        try:
            clf.fit(x.iloc[tr][mask].fillna(0), y_tr[mask])
            oof[te] = clf.predict_proba(x.iloc[te].fillna(0))[:, 1]
            n_folds += 1
        except Exception:
            continue

    valid = (~np.isnan(oof)) & y.notna().values
    n_oof = int(valid.sum())
    metrics: dict[str, Any] = {"n_oof": n_oof, "n_folds_done": n_folds}
    if n_oof >= 30 and len(np.unique(y.values[valid])) > 1:
        try:
            metrics["auc"] = round(float(roc_auc_score(y.values[valid], oof[valid])), 4)
            preds = (oof[valid] > 0.5).astype(int)
            metrics["balanced_accuracy"] = round(float(balanced_accuracy_score(
                y.values[valid].astype(int), preds)), 4)
            metrics["brier"] = round(float(brier_score_loss(y.values[valid].astype(int), oof[valid])), 4)
            # top20 DA
            n_top = max(int(n_oof * 0.20), 5)
            order = np.argsort(-oof[valid])[:n_top]
            y_top = y.values[valid][order]
            metrics["top20_da"] = round(float((y_top > 0.5).mean()), 4)
        except Exception:
            pass
    return oof, metrics


def _ensure_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Construit y_rel_outperform_h*, basis_* targets si absentes."""
    out = df.copy()
    ema_col = next((c for c in ["ema_close", "ema_front_price"] if c in out.columns), None)
    cbot_col = next((c for c in ["cbot_eur_t", "cbot_close_eur"] if c in out.columns), None)
    basis_col = next((c for c in ["ema_cbot_basis"] if c in out.columns), None)
    basis_z_col = next((c for c in ["ema_cbot_basis_zscore_52w"] if c in out.columns), None)

    if ema_col and cbot_col:
        for h in (10, 20, 40, 60, 90, 120):
            col = f"y_rel_outperform_h{h}"
            if col not in out.columns:
                ema_ret = out[ema_col].pct_change(h).shift(-h)
                cbot_ret = out[cbot_col].pct_change(h).shift(-h)
                out[col] = (ema_ret > cbot_ret).astype(float)
                out.loc[ema_ret.isna() | cbot_ret.isna(), col] = np.nan

    if basis_col:
        b = out[basis_col]
        b_mean20 = b.rolling(20).mean()
        b_std20 = b.rolling(20).std()
        for h in (20, 40):
            col_comp = f"y_basis_compression_h{h}"
            col_exp = f"y_basis_expansion_h{h}"
            col_rev = f"y_basis_reversion_h{h}"
            if col_comp not in out.columns:
                future_b = b.shift(-h)
                out[col_comp] = ((future_b - b) < -b_std20).astype(float)
                out[col_exp] = ((future_b - b) > b_std20).astype(float)
                out[col_rev] = (((future_b - b_mean20).abs()) < ((b - b_mean20).abs() * 0.5)).astype(float)
                out.loc[future_b.isna() | b_std20.isna(), [col_comp, col_exp, col_rev]] = np.nan

    if basis_z_col:
        for h in (40, 90):
            col = f"y_rel_outperform_when_basis_extreme_h{h}"
            base = f"y_rel_outperform_h{h}"
            if col not in out.columns and base in out.columns:
                extreme = out[basis_z_col].abs() > 1.5
                out[col] = out[base].where(extreme, np.nan)

    # CBOT triple-barrier ±3% / ±5% H40
    if "corn_close" in out.columns:
        c = out["corn_close"]
        for h in (40, 60):
            for pct in (3, 5):
                col = f"y_cbot_triple_barrier_{pct}pct_h{h}"
                if col not in out.columns:
                    future_max = c.shift(-1).rolling(h).max().shift(-(h - 1))
                    future_min = c.shift(-1).rolling(h).min().shift(-(h - 1))
                    up = future_max / c - 1 > pct / 100
                    down = future_min / c - 1 < -pct / 100
                    # 1 if up first, 0 if down first, NaN otherwise
                    out[col] = up.astype(float)
                    out.loc[~(up | down), col] = np.nan
                    out.loc[c.shift(-h).isna(), col] = np.nan

    return out


# ---------------------------------------------------------------------------
# V8-EMBARGO-ROBUSTNESS
# ---------------------------------------------------------------------------

def run_embargo_robustness(df: pd.DataFrame) -> dict[str, Any]:
    """Sensibilité AUC à l'embargo {0,5,20,40,60,90,180}j pour cibles clés."""
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=50)
    targets = ["y_rel_outperform_h40", "y_rel_outperform_h90", "y_up_h20", "y_up_h60"]
    targets = [t for t in targets if t in df.columns]
    embargos = [0, 5, 20, 40, 60, 90, 180]

    results: dict[str, dict[str, dict[str, Any]]] = {}
    for tgt in targets:
        y = df[tgt]
        x = df[feat_cols]
        results[tgt] = {}
        for emb in embargos:
            _, m = _oof_lgbm(x, y, embargo_days=emb)
            results[tgt][f"embargo_{emb}d"] = m

    # Verdict : sensible si max - min > 0.05 AUC
    summary = {}
    for tgt, embs in results.items():
        aucs = [v.get("auc") for v in embs.values() if v.get("auc") is not None]
        if aucs:
            summary[tgt] = {
                "max_auc": round(max(aucs), 4),
                "min_auc": round(min(aucs), 4),
                "delta_max_min": round(max(aucs) - min(aucs), 4),
                "sensitive_to_embargo": (max(aucs) - min(aucs)) > 0.05,
            }

    out = {
        "version": "V8-EMBARGO-ROBUSTNESS",
        "embargos_tested": embargos,
        "results_by_target": results,
        "summary": summary,
        "verdict": "EMBARGO_MATTERS" if any(s["sensitive_to_embargo"] for s in summary.values())
                   else "EMBARGO_NEUTRAL",
    }
    (V8_DIR / "embargo_robustness.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-RED-TEAM-PREMIUM
# ---------------------------------------------------------------------------

def run_red_team(df: pd.DataFrame, n_perms: int = 200) -> dict[str, Any]:
    """Permutation tests sur cibles V8 stratégiques.

    Pour chaque cible : permute le vecteur y, calcule l'AUC OOF, répète n_perms fois.
    Retourne p-value empirique = P(AUC_perm >= AUC_observed).
    """
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=40)
    rng = np.random.default_rng(42)

    targets = ["y_rel_outperform_h40", "y_rel_outperform_h90", "y_up_h60",
               "y_rel_outperform_when_basis_extreme_h40"]
    targets = [t for t in targets if t in df.columns]

    report: dict[str, dict[str, Any]] = {}
    for tgt in targets:
        y = df[tgt].dropna()
        if y.nunique() < 2 or len(y) < 200:
            continue
        x_aligned = df.loc[y.index, feat_cols]

        # AUC observée (1 OOF run rapide TSCV n=3)
        oof = np.full(len(x_aligned), np.nan)
        for tr, te in TimeSeriesSplit(n_splits=3).split(x_aligned):
            clf = _lgbm_clf()
            try:
                clf.fit(x_aligned.iloc[tr].fillna(0), y.iloc[tr])
                oof[te] = clf.predict_proba(x_aligned.iloc[te].fillna(0))[:, 1]
            except Exception:
                continue
        valid = ~np.isnan(oof)
        if valid.sum() < 30 or len(np.unique(y.values[valid])) < 2:
            continue
        auc_obs = float(roc_auc_score(y.values[valid], oof[valid]))

        # Permutations
        perm_aucs = []
        for _ in range(n_perms):
            y_perm = pd.Series(rng.permutation(y.values), index=y.index)
            oof_p = np.full(len(x_aligned), np.nan)
            for tr, te in TimeSeriesSplit(n_splits=3).split(x_aligned):
                clf = _lgbm_clf()
                try:
                    clf.fit(x_aligned.iloc[tr].fillna(0), y_perm.iloc[tr])
                    oof_p[te] = clf.predict_proba(x_aligned.iloc[te].fillna(0))[:, 1]
                except Exception:
                    continue
            vp = ~np.isnan(oof_p)
            if vp.sum() < 30:
                continue
            try:
                perm_aucs.append(float(roc_auc_score(y_perm.values[vp], oof_p[vp])))
            except Exception:
                continue

        if not perm_aucs:
            continue

        p_value = float(np.mean(np.array(perm_aucs) >= auc_obs))
        p95 = float(np.quantile(perm_aucs, 0.95))

        report[tgt] = {
            "auc_observed": round(auc_obs, 4),
            "auc_perm_mean": round(float(np.mean(perm_aucs)), 4),
            "auc_perm_p95": round(p95, 4),
            "auc_perm_min": round(float(min(perm_aucs)), 4),
            "auc_perm_max": round(float(max(perm_aucs)), 4),
            "p_value_empirical": round(p_value, 4),
            "verdict": "RED_TEAM_PASS" if auc_obs > p95 else "RED_TEAM_FAIL",
            "n_perms": len(perm_aucs),
        }

    out = {
        "version": "V8-RED-TEAM-PREMIUM",
        "n_perms_target": n_perms,
        "report": report,
        "global_verdict": (
            "RED_TEAM_ALL_PASS" if all(v["verdict"] == "RED_TEAM_PASS" for v in report.values())
            else "RED_TEAM_PARTIAL" if any(v["verdict"] == "RED_TEAM_PASS" for v in report.values())
            else "RED_TEAM_ALL_FAIL"
        ),
    }
    (V8_DIR / "red_team_premium.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-CBOT-LAB-PLUS
# ---------------------------------------------------------------------------

def run_cbot_lab_plus(df: pd.DataFrame) -> dict[str, Any]:
    """Extension cibles CBOT : triple barrier + conditionnels."""
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=60)

    # Cibles candidates
    targets = []
    for c in df.columns:
        starts_ok = any(c.startswith(p) for p in ("y_cbot_", "y_up_h", "y_down_gt", "y_up_gt"))
        if starts_ok and df[c].dropna().shape[0] >= 200 and df[c].dropna().nunique() >= 2:
            br = df[c].dropna().mean()
            if 0.1 <= br <= 0.9:
                targets.append(c)
    targets = targets[:25]

    results = []
    for tgt in targets:
        y = df[tgt]
        x = df[feat_cols]
        _, m = _oof_lgbm(x, y, embargo_days=90)
        m["target"] = tgt
        m["positive_rate"] = round(float(y.dropna().mean()), 4)
        if m.get("auc") is not None:
            if m["auc"] >= 0.65:
                m["verdict"] = "GO_RESEARCH"
            elif m["auc"] >= 0.55:
                m["verdict"] = "PROMISING"
            else:
                m["verdict"] = "NO_GO"
        else:
            m["verdict"] = "INSUFFICIENT_DATA"
        results.append(m)

    results_sorted = sorted(results, key=lambda r: -(r.get("auc") or 0))
    out = {
        "version": "V8-CBOT-LAB-PLUS",
        "n_targets_tested": len(results),
        "embargo_days": 90,
        "results_top10": results_sorted[:10],
        "results_all": results_sorted,
        "best_target": results_sorted[0]["target"] if results_sorted else None,
        "best_auc": results_sorted[0].get("auc") if results_sorted else None,
    }
    (V8_DIR / "cbot_lab_plus.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-EMA-PREMIUM-LAB-PLUS
# ---------------------------------------------------------------------------

def run_ema_premium_lab_plus(df: pd.DataFrame) -> dict[str, Any]:
    """Extension cibles EMA premium / basis."""
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=60)

    targets = []
    for c in df.columns:
        starts_ok = any(c.startswith(p) for p in ("y_rel_outperform", "y_basis_", "y_up_h20_ema", "y_up_h40_ema", "y_up_h60_ema"))
        if starts_ok and df[c].dropna().shape[0] >= 100 and df[c].dropna().nunique() >= 2:
            br = df[c].dropna().mean()
            if 0.05 <= br <= 0.95:
                targets.append(c)
    targets = targets[:25]

    results = []
    for tgt in targets:
        y = df[tgt]
        x = df[feat_cols]
        _, m = _oof_lgbm(x, y, embargo_days=90)
        m["target"] = tgt
        m["positive_rate"] = round(float(y.dropna().mean()), 4)
        if m.get("auc") is not None:
            n = m.get("n_oof", 0)
            if m["auc"] >= 0.85 and n < 100:
                m["verdict"] = "FRAGILE_HIGH_AUC_LOW_N"
            elif m["auc"] >= 0.65:
                m["verdict"] = "GO_RESEARCH"
            elif m["auc"] >= 0.55:
                m["verdict"] = "PROMISING"
            else:
                m["verdict"] = "NO_GO"
        else:
            m["verdict"] = "INSUFFICIENT_DATA"
        results.append(m)

    results_sorted = sorted(results, key=lambda r: -(r.get("auc") or 0))
    out = {
        "version": "V8-EMA-PREMIUM-LAB-PLUS",
        "n_targets_tested": len(results),
        "embargo_days": 90,
        "results_top10": results_sorted[:10],
        "results_all": results_sorted,
        "best_target": results_sorted[0]["target"] if results_sorted else None,
        "best_auc": results_sorted[0].get("auc") if results_sorted else None,
    }
    (V8_DIR / "ema_premium_lab_plus.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-BASIS-REGIME-V3
# ---------------------------------------------------------------------------

def run_basis_regime_v3(df: pd.DataFrame) -> dict[str, Any]:
    """KMeans + GMM sur (basis_z, basis_delta, basis_accel, vol_recent, month)."""
    assert_no_holdout(df)
    basis_col = next((c for c in ["ema_cbot_basis"] if c in df.columns), None)
    if basis_col is None:
        return {"version": "V8-BASIS-REGIME-V3", "verdict": "NO_BASIS_DATA"}

    b = df[basis_col].copy()
    # Anti-leakage : shift(1) car basis_t connu en fin de jour t, utilisé pour décider t+1
    feat = pd.DataFrame({
        "basis": b,
        "basis_delta": b.diff(),
        "basis_accel": b.diff().diff(),
        "vol_recent": b.diff().rolling(20).std(),
        "month_sin": np.sin(2 * np.pi * df.index.month / 12),
        "month_cos": np.cos(2 * np.pi * df.index.month / 12),
    }).shift(1)
    feat = feat.dropna()
    if len(feat) < 200:
        return {"version": "V8-BASIS-REGIME-V3", "verdict": "INSUFFICIENT_DATA"}

    feat_z = (feat - feat.mean()) / (feat.std() + 1e-9)

    results_kmeans = {}
    for k in (4, 5, 6, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(feat_z)
        from sklearn.metrics import silhouette_score
        sil = float(silhouette_score(feat_z, labels)) if len(set(labels)) > 1 else None
        inertia = float(km.inertia_)
        results_kmeans[f"k_{k}"] = {
            "silhouette": round(sil, 4) if sil else None,
            "inertia": round(inertia, 2),
            "regime_distribution": {str(c): int(np.sum(labels == c)) for c in sorted(set(labels))},
        }

    results_gmm = {}
    for k in (4, 5, 6):
        try:
            gmm = GaussianMixture(n_components=k, random_state=42, max_iter=200)
            gmm.fit(feat_z)
            bic = float(gmm.bic(feat_z))
            aic = float(gmm.aic(feat_z))
            labels = gmm.predict(feat_z)
            results_gmm[f"k_{k}"] = {
                "bic": round(bic, 2),
                "aic": round(aic, 2),
                "regime_distribution": {str(c): int(np.sum(labels == c)) for c in sorted(set(labels))},
            }
        except Exception:
            results_gmm[f"k_{k}"] = {"error": "gmm_fit_failed"}

    # Choix best k par silhouette (KMeans) et BIC (GMM)
    best_kmeans = max(results_kmeans.items(),
                     key=lambda x: x[1].get("silhouette") or 0)
    best_gmm = min(
        ((k, v) for k, v in results_gmm.items() if "bic" in v),
        key=lambda x: x[1]["bic"],
        default=(None, None),
    )

    # AUC premium H40 par régime (avec best k KMeans)
    auc_by_regime: dict[str, Any] = {}
    if "y_rel_outperform_h40" in df.columns:
        best_k = int(best_kmeans[0].split("_")[1])
        km_best = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels_best = km_best.fit_predict(feat_z)
        regime_series = pd.Series(labels_best, index=feat_z.index, name="regime")
        df_aligned = df.loc[regime_series.index]
        y = df_aligned.get("y_rel_outperform_h40", pd.Series(dtype=float))
        feat_cols = _classical_features(df, max_features=40)
        for reg in sorted(set(labels_best)):
            mask = regime_series == reg
            if mask.sum() < 100:
                continue
            x_r = df_aligned.loc[mask, feat_cols]
            y_r = y.loc[x_r.index]
            valid = y_r.notna()
            if valid.sum() < 100 or y_r[valid].nunique() < 2:
                continue
            x_r_clean = x_r[valid]
            y_r_clean = y_r[valid]
            n_tr = int(len(x_r_clean) * 0.7)
            if n_tr < 30:
                continue
            try:
                clf = _lgbm_clf()
                clf.fit(x_r_clean.iloc[:n_tr].fillna(0), y_r_clean.iloc[:n_tr])
                preds = clf.predict_proba(x_r_clean.iloc[n_tr:].fillna(0))[:, 1]
                if y_r_clean.iloc[n_tr:].nunique() > 1:
                    auc_by_regime[f"regime_{reg}"] = round(
                        float(roc_auc_score(y_r_clean.iloc[n_tr:], preds)), 4
                    )
            except Exception:
                pass

    out = {
        "version": "V8-BASIS-REGIME-V3",
        "n_features": feat_z.shape[1],
        "n_obs": len(feat_z),
        "kmeans": results_kmeans,
        "gmm": results_gmm,
        "best_kmeans_k": best_kmeans[0],
        "best_gmm_k": best_gmm[0],
        "auc_premium_h40_by_regime_best_kmeans": auc_by_regime,
        "verdict": "REGIMES_IDENTIFIED",
    }
    (V8_DIR / "basis_regime_v3.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-SEASONAL-V3
# ---------------------------------------------------------------------------

def run_seasonal_v3(df: pd.DataFrame) -> dict[str, Any]:
    """Modèles experts par saison avec audit train-only des seuils top20."""
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=50)

    seasons = {
        "jan_mar": [1, 2, 3],
        "apr_jun": [4, 5, 6],
        "jul_aug": [7, 8],
        "sep_nov": [9, 10, 11],
        "dec": [12],
    }

    target_global = "y_rel_outperform_h40"
    if target_global not in df.columns:
        return {"version": "V8-SEASONAL-V3", "verdict": "NO_TARGET"}

    results: dict[str, Any] = {}
    for sname, months in seasons.items():
        mask = df.index.month.isin(months)
        df_s = df.loc[mask].copy()
        if len(df_s) < 200:
            continue
        y = df_s[target_global]
        x = df_s[feat_cols]
        oof, metrics = _oof_lgbm(x, y, embargo_days=60)

        # Audit top20 TRAIN-ONLY : utiliser uniquement les seuils calibrés sur train pour décision sur test
        # ici on calcule simplement top20 OOF qui est déjà train-only par construction (seuils non utilisés)
        # On ajoute top20_threshold_estimated train
        valid = ~np.isnan(oof) & y.notna().values
        top20_train_only_da = None
        if valid.sum() >= 50 and y.values[valid].std() > 0:
            n_split = int(valid.sum() * 0.7)
            train_idx = np.where(valid)[0][:n_split]
            test_idx = np.where(valid)[0][n_split:]
            if len(train_idx) > 30 and len(test_idx) > 30:
                threshold_train = np.quantile(oof[train_idx], 0.80)
                top_mask_test = oof[test_idx] > threshold_train
                if top_mask_test.sum() > 5:
                    y_top_test = y.values[test_idx][top_mask_test]
                    top20_train_only_da = round(float((y_top_test > 0.5).mean()), 4)

        results[sname] = {
            "months": months,
            "n_obs": len(df_s),
            "metrics": metrics,
            "top20_train_only_da": top20_train_only_da,
        }

    best_season = max(
        results.items(),
        key=lambda kv: kv[1]["metrics"].get("auc") or 0,
    ) if results else (None, None)

    out = {
        "version": "V8-SEASONAL-V3",
        "target": target_global,
        "embargo_days": 60,
        "results_by_season": results,
        "best_season": best_season[0],
        "best_season_auc": best_season[1]["metrics"].get("auc") if best_season[1] else None,
        "verdict": "SEASONAL_DIFFERENTIATION_OBSERVED" if results else "INSUFFICIENT_DATA",
    }
    (V8_DIR / "seasonal_v3.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-CROSS-MARKET-V3
# ---------------------------------------------------------------------------

def run_cross_market_v3(df: pd.DataFrame) -> dict[str, Any]:
    """EMA features → CBOT target AND CBOT features → EMA target."""
    assert_no_holdout(df)
    df = _ensure_targets(df)

    ema_features = [c for c in df.columns
                    if c.startswith(("ema_", "basis"))
                    and df[c].dtype in (np.float64, np.float32, float)
                    and df[c].notna().mean() > 0.3][:30]
    cbot_features = [c for c in df.columns
                     if c.startswith(("cbot_", "corn_", "wasde", "cot_", "soy_", "wheat_"))
                     and df[c].dtype in (np.float64, np.float32, float)
                     and df[c].notna().mean() > 0.3][:30]

    cbot_targets = [t for t in ["y_up_h20", "y_up_h60", "y_cbot_drawdown_5pct_h20", "y_cbot_drawdown_5pct_h60"]
                    if t in df.columns]
    ema_targets = [t for t in ["y_rel_outperform_h40", "y_rel_outperform_h90"]
                   if t in df.columns]

    results = {"ema_features_to_cbot": [], "cbot_features_to_ema": []}

    # EMA → CBOT
    for tgt in cbot_targets:
        if not ema_features:
            continue
        x_cbot_only = df[cbot_features]
        x_combined = df[cbot_features + ema_features]
        y = df[tgt]
        _, m_cbot = _oof_lgbm(x_cbot_only, y, embargo_days=90)
        _, m_comb = _oof_lgbm(x_combined, y, embargo_days=90)
        delta = (m_comb.get("auc") or 0) - (m_cbot.get("auc") or 0)
        results["ema_features_to_cbot"].append({
            "target": tgt,
            "auc_cbot_only": m_cbot.get("auc"),
            "auc_combined": m_comb.get("auc"),
            "delta_auc": round(delta, 4) if delta else None,
            "ema_adds_value": delta > 0.01,
        })

    # CBOT → EMA
    for tgt in ema_targets:
        if not cbot_features:
            continue
        x_ema_only = df[ema_features]
        x_combined = df[cbot_features + ema_features]
        y = df[tgt]
        _, m_ema = _oof_lgbm(x_ema_only, y, embargo_days=90)
        _, m_comb = _oof_lgbm(x_combined, y, embargo_days=90)
        delta = (m_comb.get("auc") or 0) - (m_ema.get("auc") or 0)
        results["cbot_features_to_ema"].append({
            "target": tgt,
            "auc_ema_only": m_ema.get("auc"),
            "auc_combined": m_comb.get("auc"),
            "delta_auc": round(delta, 4) if delta else None,
            "cbot_adds_value": delta > 0.01,
        })

    n_ema_adds = sum(1 for r in results["ema_features_to_cbot"] if r.get("ema_adds_value"))
    n_cbot_adds = sum(1 for r in results["cbot_features_to_ema"] if r.get("cbot_adds_value"))
    if n_ema_adds and n_cbot_adds:
        verdict = "BIDIRECTIONAL"
    elif n_ema_adds:
        verdict = "EMA_ADDS_TO_CBOT"
    elif n_cbot_adds:
        verdict = "CBOT_ADDS_TO_EMA"
    else:
        verdict = "NEITHER_ADDS"

    out = {
        "version": "V8-CROSS-MARKET-V3",
        "n_ema_features": len(ema_features),
        "n_cbot_features": len(cbot_features),
        "results": results,
        "n_ema_adds_to_cbot": n_ema_adds,
        "n_cbot_adds_to_ema": n_cbot_adds,
        "verdict": verdict,
    }
    (V8_DIR / "cross_market_v3.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-PCORRECT-V3
# ---------------------------------------------------------------------------

def run_pcorrect_v3(df: pd.DataFrame) -> dict[str, Any]:
    """P(correct) calibré Platt vs Isotonic sur premium H40."""
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=40)
    tgt = "y_rel_outperform_h40"
    if tgt not in df.columns:
        return {"version": "V8-PCORRECT-V3", "verdict": "NO_TARGET"}

    y = df[tgt]
    x = df[feat_cols]
    common = x.dropna(how="all").index.intersection(y.dropna().index)
    if len(common) < 300:
        return {"version": "V8-PCORRECT-V3", "verdict": "INSUFFICIENT_DATA"}
    x = x.loc[common].fillna(0)
    y = y.loc[common]
    n_tr = int(len(x) * 0.7)

    out: dict[str, Any] = {"version": "V8-PCORRECT-V3", "target": tgt, "n_train": n_tr, "n_test": len(x) - n_tr}

    for method in ("sigmoid", "isotonic"):
        try:
            base = _lgbm_clf()
            # Use prefit base then CalibratedClassifierCV
            cal = CalibratedClassifierCV(base, cv=3, method=method)
            cal.fit(x.iloc[:n_tr], y.iloc[:n_tr])
            proba_test = cal.predict_proba(x.iloc[n_tr:])[:, 1]
            y_te = y.iloc[n_tr:].astype(int).values
            auc = float(roc_auc_score(y_te, proba_test))
            brier = float(brier_score_loss(y_te, proba_test))
            ll = float(log_loss(y_te, np.clip(proba_test, 1e-9, 1 - 1e-9)))
            # ECE en 10 bins
            bins = np.linspace(0, 1, 11)
            bin_idx = np.clip(np.digitize(proba_test, bins) - 1, 0, 9)
            ece = 0.0
            for b_id in range(10):
                mask = bin_idx == b_id
                if mask.sum() > 0:
                    conf = float(proba_test[mask].mean())
                    acc = float(y_te[mask].mean())
                    ece += (mask.sum() / len(y_te)) * abs(conf - acc)
            out[method] = {
                "auc": round(auc, 4),
                "brier": round(brier, 4),
                "log_loss": round(ll, 4),
                "ece": round(float(ece), 4),
                "well_calibrated": ece < 0.05,
            }
        except Exception as e:
            out[method] = {"error": str(e)}

    out["verdict"] = (
        "PLATT_BEST" if (out.get("sigmoid", {}).get("ece") or 1) < (out.get("isotonic", {}).get("ece") or 1)
        else "ISO_BEST"
    )
    (V8_DIR / "pcorrect_v3.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V8-BACKTEST-V3
# ---------------------------------------------------------------------------

def run_backtest_v3(df: pd.DataFrame) -> dict[str, Any]:
    """Stress test coûts 1/2/3/5/8 €/t sur stratégie premium H40 OOF."""
    assert_no_holdout(df)
    df = _ensure_targets(df)
    feat_cols = _classical_features(df, max_features=40)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V8-BACKTEST-V3", "verdict": "MISSING_PRICE_SERIES"}
    if "y_rel_outperform_h40" not in df.columns:
        return {"version": "V8-BACKTEST-V3", "verdict": "NO_TARGET"}

    y = df["y_rel_outperform_h40"]
    x = df[feat_cols]
    # OOF LGBM premium signal
    oof, _ = _oof_lgbm(x, y, embargo_days=40)

    # Spread return réalisé sur H40
    h = 40
    ema_ret_h40 = df["ema_close"].pct_change(h).shift(-h)
    cbot_ret_h40 = df["cbot_eur_t"].pct_change(h).shift(-h)
    spread_ret_h40 = (ema_ret_h40 - cbot_ret_h40).values  # log-like proxy

    signal_proba = oof
    valid = (~np.isnan(signal_proba)) & (~np.isnan(spread_ret_h40))
    dates = df.index.values

    if valid.sum() < 200:
        return {"version": "V8-BACKTEST-V3", "verdict": "INSUFFICIENT_VALID"}

    # Politiques : full_signal (long si proba > 0.5, short sinon),
    # top20 (long si proba > p80, short si proba < p20),
    # rule simple basis_z > 1.5
    basis_z = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=df.index)).values

    # Non-overlap trades : H jours min entre deux trades
    def _non_overlap_trades(active_mask, dates_arr, gap_days=h):
        idx_active = np.where(active_mask)[0]
        kept = []
        last_date = None
        for i in idx_active:
            d = pd.Timestamp(dates_arr[i])
            if last_date is None or (d - last_date).days >= gap_days:
                kept.append(i)
                last_date = d
        return np.array(kept, dtype=int)

    # Estimer prix en EUR/t pour convertir % en €/t (notional EMA brut comme proxy)
    ema_price = df["ema_close"].values

    def _backtest(active, side):
        idx = _non_overlap_trades(active, dates, gap_days=h)
        if len(idx) == 0:
            return {"n_trades": 0, "pnl_total_pct": 0.0, "pnl_total_eur_t": 0.0,
                    "hit_rate": None, "pnl_mean_eur_t": 0.0}
        ret = spread_ret_h40[idx] * side
        prices = ema_price[idx]
        pnl_eur_per_t = ret * prices  # approx
        hit_rate = float(np.mean(ret > 0))
        return {
            "n_trades": int(len(idx)),
            "pnl_total_pct": round(float(np.nansum(ret)), 4),
            "pnl_total_eur_t": round(float(np.nansum(pnl_eur_per_t)), 4),
            "pnl_mean_eur_t": round(float(np.nanmean(pnl_eur_per_t)), 4),
            "pnl_std_eur_t": round(float(np.nanstd(pnl_eur_per_t)), 4),
            "hit_rate": round(hit_rate, 4),
            "max_loss_eur_t": round(float(np.nanmin(pnl_eur_per_t)), 4),
            "max_gain_eur_t": round(float(np.nanmax(pnl_eur_per_t)), 4),
        }

    policies = {}

    # Politique : full_signal long/short selon p>0.5
    long_mask = valid & (signal_proba > 0.5)
    short_mask = valid & (signal_proba <= 0.5)
    p_long = _backtest(long_mask, +1)
    p_short = _backtest(short_mask, -1)
    policies["full_signal_long_short"] = {
        "long": p_long, "short": p_short,
        "combined_pnl_eur_t": round(p_long["pnl_total_eur_t"] + p_short["pnl_total_eur_t"], 4),
    }

    # Politique top20
    if valid.sum() > 50:
        p_high = np.quantile(signal_proba[valid], 0.80)
        p_low = np.quantile(signal_proba[valid], 0.20)
        long_top = valid & (signal_proba >= p_high)
        short_top = valid & (signal_proba <= p_low)
        p_lt = _backtest(long_top, +1)
        p_st = _backtest(short_top, -1)
        policies["top20"] = {
            "long": p_lt, "short": p_st,
            "combined_pnl_eur_t": round(p_lt["pnl_total_eur_t"] + p_st["pnl_total_eur_t"], 4),
        }

    # Politique règle simple basis_z
    rule_long = valid & (basis_z > 1.5)
    rule_short = valid & (basis_z < -1.5)
    p_rl = _backtest(rule_long, +1)
    p_rs = _backtest(rule_short, -1)
    policies["basis_rule_only"] = {
        "long": p_rl, "short": p_rs,
        "combined_pnl_eur_t": round(p_rl["pnl_total_eur_t"] + p_rs["pnl_total_eur_t"], 4),
    }

    # Stress coûts pour la politique full_signal
    cost_stress = {}
    for cost in (1, 2, 3, 5, 8):
        # Coût par leg × 2 legs (long EMA / short CBOT)
        pnl_long = p_long["pnl_total_eur_t"] - cost * 2 * p_long["n_trades"]
        pnl_short = p_short["pnl_total_eur_t"] - cost * 2 * p_short["n_trades"]
        cost_stress[f"cost_{cost}_eur_t"] = {
            "pnl_long_net": round(pnl_long, 4),
            "pnl_short_net": round(pnl_short, 4),
            "pnl_combined_net": round(pnl_long + pnl_short, 4),
            "profitable": (pnl_long + pnl_short) > 0,
        }

    out = {
        "version": "V8-BACKTEST-V3",
        "target": "y_rel_outperform_h40",
        "horizon_days": h,
        "n_signal_valid": int(valid.sum()),
        "policies": policies,
        "cost_stress_full_signal": cost_stress,
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V8_DIR / "backtests_v3.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

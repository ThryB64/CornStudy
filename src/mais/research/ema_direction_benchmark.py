"""NB-EMA-08 — Benchmark directionnel EMA : walk-forward multi-feature × multi-cible."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from mais.paths import ARTEFACTS_DIR, EMA_FRONT_ADJUSTED, FEATURES_PARQUET, TARGETS_PARQUET
from mais.research.ema_utils import (
    benjamini_hochberg,
    binary_target_from_condition,
    binary_target_from_future_return,
    bootstrap_ci,
    crop_year,
    direction_accuracy,
)

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_direction_benchmark.json"
_MIN_TRAIN_YEARS = 3
_N_BOOTSTRAP = 1000

_FEATURE_SETS: dict[str, list[str]] = {
    "cbot_only": ["corn_logret_1d", "corn_logret_5d", "corn_logret_20d", "corn_realized_vol_20", "corn_realized_vol_60"],
    "basis_only": ["ema_cbot_basis", "ema_cbot_basis_zscore_52w"],
    "ema_technical_only": ["ema_spread_f0_f1", "ema_curve_slope_3", "ema_roll_yield_ann", "ema_oi_total", "ema_liquidity_shift"],
    "cbot_basis": ["corn_logret_1d", "corn_logret_5d", "corn_logret_20d", "corn_realized_vol_20", "ema_cbot_basis", "ema_cbot_basis_zscore_52w"],
    "cbot_ema_combined": ["corn_logret_1d", "corn_logret_5d", "corn_realized_vol_20", "ema_cbot_basis", "ema_spread_f0_f1", "ema_roll_yield_ann"],
    "cbot_eu_macro": ["corn_logret_1d", "corn_logret_5d", "corn_realized_vol_20", "ema_cbot_basis", "fedfunds_level_zscore", "fedfunds_z24"],
    "all_selected": ["corn_logret_1d", "corn_logret_5d", "corn_logret_20d", "corn_realized_vol_20", "ema_cbot_basis", "ema_cbot_basis_zscore_52w", "ema_spread_f0_f1", "ema_curve_slope_3", "ema_roll_yield_ann", "fedfunds_level_zscore"],
}


def _build_ema_targets(adj: pd.DataFrame) -> pd.DataFrame:
    adj = adj.copy().sort_values("date").reset_index(drop=True)
    price = adj.set_index("date")["adjusted_price"]
    out = pd.DataFrame({"Date": price.index})
    for h in [20, 40]:
        fut_ret = price.pct_change(h).shift(-h)
        out[f"y_up_h{h}_ema_adj"] = binary_target_from_future_return(fut_ret)
    return out.reset_index(drop=True)


def _build_basis_reversion_target(feats: pd.DataFrame) -> pd.Series:
    basis = feats["ema_cbot_basis"]
    mu = basis.mean()
    fut_basis = basis.shift(-20)
    current_above = basis > mu
    reverts = current_above & (fut_basis < mu) | (~current_above) & (fut_basis > mu)
    return binary_target_from_condition(
        reverts,
        basis.notna() & fut_basis.notna(),
    ).rename("y_up_h20_basis_reversion")


def _merge_dataset(feats: pd.DataFrame, ema_targets: pd.DataFrame, targets_cbot: pd.DataFrame) -> pd.DataFrame:
    feats = feats.copy()
    feats["Date"] = pd.to_datetime(feats["Date"])
    ema_targets["Date"] = pd.to_datetime(ema_targets["Date"])
    targets_cbot["Date"] = pd.to_datetime(targets_cbot["Date"])
    df = feats.merge(ema_targets, on="Date", how="left")
    tgt_cols = ["Date"] + [c for c in ["y_up_h20", "y_up_h40"] if c in targets_cbot.columns]
    df = df.merge(targets_cbot[tgt_cols], on="Date", how="left")
    df["y_up_h20_basis_reversion"] = _build_basis_reversion_target(df)
    df["crop_year"] = df["Date"].apply(crop_year)
    return df.sort_values("Date").reset_index(drop=True)


def _walk_forward_cv(df: pd.DataFrame, feature_cols: list[str], target_col: str) -> list[dict]:
    cys = sorted(df["crop_year"].unique())
    results = []
    for i in range(_MIN_TRAIN_YEARS, len(cys)):
        train_cys = cys[:i]
        test_cy = cys[i]
        train = df[df["crop_year"].isin(train_cys)]
        test = df[df["crop_year"] == test_cy]
        x_tr = train[feature_cols].values
        y_tr = train[target_col].values
        x_te = test[feature_cols].values
        y_te = test[target_col].values
        valid = ~(np.isnan(x_tr).any(axis=1) | np.isnan(y_tr.astype(float)))
        valid_te = ~(np.isnan(x_te).any(axis=1) | np.isnan(y_te.astype(float)))
        if valid.sum() < 50 or valid_te.sum() < 10:
            continue
        valid_np = valid.values if hasattr(valid, "values") else valid
        valid_te_np = valid_te.values if hasattr(valid_te, "values") else valid_te
        x_tr, y_tr = x_tr[valid_np], y_tr[valid_np]
        x_te, y_te = x_te[valid_te_np], y_te[valid_te_np]
        if len(np.unique(y_tr)) < 2:
            continue
        clf = HistGradientBoostingClassifier(max_iter=100, random_state=42)
        try:
            clf.fit(x_tr, y_tr)
            y_pred = clf.predict(x_te)
            da = direction_accuracy(y_te * 2 - 1, y_pred * 2 - 1)
            try:
                y_prob = clf.predict_proba(x_te)[:, 1]
                from sklearn.metrics import roc_auc_score
                auc = float(roc_auc_score(y_te, y_prob))
            except Exception:
                auc = float("nan")
            results.append({"crop_year": int(test_cy), "n_test": int(len(y_te)), "da": float(da), "auc": auc})
        except Exception:
            pass
    return results


def _aggregate_cv(cv_results: list[dict], feature_set: str, target: str) -> dict:
    if not cv_results:
        return {"feature_set": feature_set, "target": target, "error": "no_folds"}
    das = np.array([r["da"] for r in cv_results if not np.isnan(r["da"])])
    aucs = np.array([r["auc"] for r in cv_results if not np.isnan(r["auc"])])
    if len(das) == 0:
        return {"feature_set": feature_set, "target": target, "error": "no_valid_das"}

    da_mean = float(np.mean(das))
    ci = bootstrap_ci(das, np.mean, n_draws=_N_BOOTSTRAP)

    # p-value (one-sided test: DA > 0.5)
    # Using normal approximation: z = (DA_mean - 0.5) / (std / sqrt(n))
    n = len(das)
    std = float(np.std(das))
    z = (da_mean - 0.5) / (std / np.sqrt(max(n, 1)) + 1e-12)
    from scipy.stats import norm
    p_val = float(1 - norm.cdf(z))

    go_minimal = da_mean > 0.55 and (len(aucs) == 0 or float(np.mean(aucs)) > 0.55) and ci["ci_lo"] > 0.50
    go_pro = ci["ci_lo"] > 0.55

    return {
        "feature_set": feature_set,
        "target": target,
        "n_folds": n,
        "da_mean": da_mean,
        "da_std": std,
        "da_ci_lo": ci["ci_lo"],
        "da_ci_hi": ci["ci_hi"],
        "auc_mean": float(np.mean(aucs)) if len(aucs) else float("nan"),
        "p_value_da_gt_05": p_val,
        "verdict_go_minimal": go_minimal,
        "verdict_go_professional": go_pro,
    }


def build_direction_benchmark() -> dict:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    targets_cbot = pd.read_parquet(TARGETS_PARQUET)
    targets_cbot["Date"] = pd.to_datetime(targets_cbot["Date"])
    adj = pd.read_parquet(EMA_FRONT_ADJUSTED)
    adj["date"] = pd.to_datetime(adj["date"])

    ema_targets = _build_ema_targets(adj)
    df = _merge_dataset(feats, ema_targets, targets_cbot)

    target_cols = ["y_up_h20", "y_up_h40", "y_up_h20_ema_adj", "y_up_h40_ema_adj", "y_up_h20_basis_reversion"]

    all_results = []
    for fs_name, feat_cols in _FEATURE_SETS.items():
        avail = [c for c in feat_cols if c in df.columns]
        if len(avail) < 1:
            continue
        for tgt in target_cols:
            if tgt not in df.columns:
                continue
            cv = _walk_forward_cv(df, avail, tgt)
            agg = _aggregate_cv(cv, fs_name, tgt)
            all_results.append(agg)

    # BH correction
    valid_results = [r for r in all_results if "p_value_da_gt_05" in r]
    p_vals = [r["p_value_da_gt_05"] for r in valid_results]
    bh_rejected = benjamini_hochberg(p_vals, alpha=0.05)
    for r, rej in zip(valid_results, bh_rejected, strict=False):
        r["bh_significant"] = bool(rej)

    n_go = sum(r.get("verdict_go_minimal", False) for r in all_results)
    n_go_pro = sum(r.get("verdict_go_professional", False) for r in all_results)
    best = max((r for r in all_results if "da_mean" in r), key=lambda x: x["da_mean"], default=None)

    return {
        "n_combinations": len(all_results),
        "feature_sets": list(_FEATURE_SETS.keys()),
        "targets": target_cols,
        "results": all_results,
        "summary": {
            "n_go_minimal": n_go,
            "n_go_professional": n_go_pro,
            "best_da_mean": best.get("da_mean") if best else None,
            "best_feature_set": best.get("feature_set") if best else None,
            "best_target": best.get("target") if best else None,
            "overall_verdict": "GO_SIGNAL" if n_go > 0 else "NO_GO",
        },
    }


def save_direction_benchmark(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_direction_benchmark()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        if isinstance(obj, bool):
            return bool(obj)
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_direction_benchmark()
    print(f"Direction benchmark saved → {out}")

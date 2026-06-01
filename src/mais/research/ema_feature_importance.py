"""NB-EMA-10 — Importance des features EMA : permutation importance et corrélations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, TARGETS_PARQUET
from mais.research.ema_utils import crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_feature_importance.json"
_MIN_TRAIN_YEARS = 3

_CANDIDATE_FEATURES = [
    "corn_logret_1d", "corn_logret_5d", "corn_logret_20d",
    "corn_realized_vol_20", "corn_realized_vol_60",
    "ema_cbot_basis", "ema_cbot_basis_zscore_52w",
    "ema_spread_f0_f1", "ema_curve_slope_3", "ema_roll_yield_ann",
    "ema_oi_total", "ema_liquidity_shift",
    "fedfunds_level_zscore", "fedfunds_z24",
]


def _build_dataset(feats: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    feats = feats[feats["ema_front_price"].notna()].copy()
    feats["Date"] = pd.to_datetime(feats["Date"])
    targets["Date"] = pd.to_datetime(targets["Date"])
    df = feats.merge(targets[["Date", "y_up_h20"]], on="Date", how="left")
    df["crop_year"] = df["Date"].apply(crop_year)
    return df.sort_values("Date").reset_index(drop=True)


def _permutation_importance(x_arr: np.ndarray, y: np.ndarray, clf, feat_names: list[str], n_repeats: int = 10) -> dict:
    from sklearn.metrics import accuracy_score
    baseline = accuracy_score(y, clf.predict(x_arr))
    importances = []
    for j in range(x_arr.shape[1]):
        scores = []
        for _ in range(n_repeats):
            x_perm = x_arr.copy()
            np.random.shuffle(x_perm[:, j])
            scores.append(accuracy_score(y, clf.predict(x_perm)))
        importances.append(float(baseline - np.mean(scores)))
    ranked = sorted(zip(feat_names, importances, strict=False), key=lambda x: -x[1])
    return {"baseline_accuracy": float(baseline), "importances": {f: float(v) for f, v in ranked}}


def _mutual_info_importance(df: pd.DataFrame, feat_cols: list[str]) -> dict:
    """Mutual information calculée feature par feature pour gérer les NaN indépendamment."""
    from sklearn.feature_selection import mutual_info_classif
    result = {}
    for f in feat_cols:
        sub = df[[f, "y_up_h20"]].dropna()
        if len(sub) < 50 or len(sub["y_up_h20"].unique()) < 2:
            result[f] = {"importance": float("nan"), "n": int(len(sub))}
            continue
        x_feat = sub[[f]].to_numpy(dtype=float)
        y = sub["y_up_h20"].to_numpy(dtype=float)
        # Filter out inf values
        finite_mask = np.isfinite(x_feat[:, 0]) & np.isfinite(y)
        if finite_mask.sum() < 50 or len(np.unique(y[finite_mask])) < 2:
            result[f] = {"importance": float("nan"), "n": int(finite_mask.sum())}
            continue
        mi = mutual_info_classif(x_feat[finite_mask], y[finite_mask], random_state=42)
        result[f] = {"importance": float(mi[0]), "n": int(finite_mask.sum())}
    return result


def _spearman_corr_with_target(df: pd.DataFrame, feat_cols: list[str], target: str) -> dict:
    result = {}
    for f in feat_cols:
        sub = df[[f, target]].dropna()
        if len(sub) < 30:
            result[f] = float("nan")
            continue
        try:
            from scipy.stats import spearmanr
            r, p = spearmanr(sub[f], sub[target])
            result[f] = {"spearman_r": float(r), "p_value": float(p)}
        except ImportError:
            result[f] = float(np.corrcoef(sub[f], sub[target])[0, 1])
    return result


def build_feature_importance() -> dict:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    targets = pd.read_parquet(TARGETS_PARQUET)
    targets["Date"] = pd.to_datetime(targets["Date"])

    avail_feats = [f for f in _CANDIDATE_FEATURES if f in feats.columns]
    df = _build_dataset(feats, targets)

    mi_imp = _mutual_info_importance(df, avail_feats)
    spearman = _spearman_corr_with_target(df, avail_feats, "y_up_h20")

    ranked = sorted(mi_imp.items(), key=lambda x: -(x[1]["importance"] if not np.isnan(x[1]["importance"]) else -999))
    top5 = [{"feature": f, **v} for f, v in ranked[:5]]

    return {
        "candidate_features": avail_feats,
        "mutual_info_importance": mi_imp,
        "spearman_correlation_with_y_up_h20": spearman,
        "top5_features": top5,
        "key_findings": {
            "top_feature": ranked[0][0] if ranked else None,
            "top_feature_importance": ranked[0][1]["importance"] if ranked else float("nan"),
            "n_features_positive_importance": sum(1 for _, v in ranked if not np.isnan(v["importance"]) and v["importance"] > 0),
        },
    }


def save_feature_importance(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_feature_importance()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_feature_importance()
    print(f"Feature importance saved → {out}")

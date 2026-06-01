"""NB2-06 — Importance robuste des features EMA : OOF, année, ablations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT, TARGETS_PARQUET
from mais.research.ema_utils import crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_feature_importance_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_FEATURE_IMPORTANCE_V2.md"

_CANDIDATES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "ema_front_return_5d_adjusted",
    "ema_oi_total",
    "ema_volume_total",
    "ema_spread_f0_f1",
    "ema_curve_slope_3",
    "corn_logret_20d",
    "corn_realized_vol_20",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
    "fedfunds_z24",
]

_FAMILIES = {
    "basis": ["ema_cbot_basis", "ema_cbot_basis_zscore_52w"],
    "ema_technical": ["ema_front_vol_20d_adjusted", "ema_front_return_5d_adjusted"],
    "liquidity": ["ema_oi_total", "ema_volume_total"],
    "curve": ["ema_spread_f0_f1", "ema_curve_slope_3"],
    "cbot_technical": ["corn_logret_20d", "corn_realized_vol_20"],
    "energy_proxy": ["corn_gas_ratio"],
    "macro_fedfunds": ["fedfunds_level_zscore", "fedfunds_z24"],
}


def _dataset() -> tuple[pd.DataFrame, list[str]]:
    feats = pd.read_parquet(FEATURES_PARQUET)
    targets = pd.read_parquet(TARGETS_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    targets["Date"] = pd.to_datetime(targets["Date"])
    df = feats.merge(targets[["Date", "y_up_h20"]], on="Date", how="inner")
    df = df[df["ema_cbot_basis"].notna()].copy()
    df["crop_year"] = df["Date"].apply(crop_year)
    features = [c for c in _CANDIDATES if c in df.columns and df[c].notna().sum() >= 50]
    return df.sort_values("Date").reset_index(drop=True), features


def _mi_spearman(df: pd.DataFrame, features: list[str]) -> list[dict]:
    rows = []
    for feature in features:
        sub = df[[feature, "y_up_h20"]].dropna()
        if len(sub) < 50 or sub["y_up_h20"].nunique() < 2:
            continue
        mi = mutual_info_classif(sub[[feature]], sub["y_up_h20"], random_state=42)[0]
        rho = sub[feature].corr(sub["y_up_h20"], method="spearman")
        rows.append({"feature": feature, "n": int(len(sub)), "mutual_info": float(mi), "spearman": float(rho)})
    return sorted(rows, key=lambda r: r["mutual_info"], reverse=True)


def _prepare_xy(data: pd.DataFrame, features: list[str]):
    sub = data[["y_up_h20", *features]].replace([np.inf, -np.inf], np.nan).dropna()
    return sub[features], sub["y_up_h20"]


def _fit_model(train: pd.DataFrame, features: list[str]):
    x_train, y_train = _prepare_xy(train, features)
    if len(x_train) < 100 or y_train.nunique() < 2:
        return None
    model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
    model.fit(x_train, y_train)
    return model


def _permutation_oof(df: pd.DataFrame, features: list[str]) -> dict:
    crop_years = sorted(df["crop_year"].unique())
    rows = []
    for idx in range(3, len(crop_years)):
        train = df[df["crop_year"].isin(crop_years[:idx])]
        test = df[df["crop_year"] == crop_years[idx]]
        model = _fit_model(train, features)
        if model is None:
            continue
        x_test, y_test = _prepare_xy(test, features)
        if len(x_test) < 30 or y_test.nunique() < 2:
            continue
        perm = permutation_importance(model, x_test, y_test, n_repeats=5, random_state=42, scoring="roc_auc")
        pred = model.predict(x_test)
        try:
            auc = float(roc_auc_score(y_test, model.predict_proba(x_test)[:, 1]))
        except Exception:
            auc = float("nan")
        for feature, imp, std in zip(features, perm.importances_mean, perm.importances_std, strict=False):
            rows.append({
                "crop_year": int(crop_years[idx]),
                "feature": feature,
                "permutation_auc_drop": float(imp),
                "std": float(std),
                "fold_auc": auc,
                "fold_da": float(accuracy_score(y_test, pred)),
            })
    summary = []
    if rows:
        frame = pd.DataFrame(rows)
        for feature, sub in frame.groupby("feature"):
            summary.append({
                "feature": feature,
                "mean_permutation_auc_drop": float(sub["permutation_auc_drop"].mean()),
                "std_permutation_auc_drop": float(sub["permutation_auc_drop"].std()),
                "n_years": int(sub["crop_year"].nunique()),
                "mean_fold_auc": float(sub["fold_auc"].mean()),
            })
    return {
        "by_year": rows,
        "summary": sorted(summary, key=lambda r: r["mean_permutation_auc_drop"], reverse=True),
    }


def _fedfunds_audit(df: pd.DataFrame, features: list[str]) -> dict:
    fed_cols = [c for c in ["fedfunds_level_zscore", "fedfunds_z24"] if c in features]
    if not fed_cols:
        return {"status": "missing"}
    full = _permutation_oof(df, features)
    no_crisis = df[~df["Date"].dt.year.isin([2021, 2022])]
    no_crisis_res = _permutation_oof(no_crisis, features)
    def _extract(res):
        return {
            row["feature"]: row["mean_permutation_auc_drop"]
            for row in res.get("summary", [])
            if row["feature"] in fed_cols
        }
    return {
        "status": "suspect_temporal_proxy",
        "full_sample_importance": _extract(full),
        "excluding_2021_2022_importance": _extract(no_crisis_res),
        "conclusion": "fedfunds_level_zscore peut capter le régime temporel 2021-2022 ; causalité EMA non confirmée.",
    }


def _family_ablation(df: pd.DataFrame, features: list[str]) -> list[dict]:
    crop_years = sorted(df["crop_year"].unique())
    rows = []
    for family, family_cols in _FAMILIES.items():
        cols = [c for c in family_cols if c in features]
        if not cols:
            rows.append({"family": family, "status": "missing"})
            continue
        base_cols = features
        ablated_cols = [c for c in features if c not in cols]
        fold_rows = []
        for idx in range(3, len(crop_years)):
            train = df[df["crop_year"].isin(crop_years[:idx])]
            test = df[df["crop_year"] == crop_years[idx]]
            full_model = _fit_model(train, base_cols)
            ablated_model = _fit_model(train, ablated_cols)
            if full_model is None or ablated_model is None:
                continue
            x_full, y_test = _prepare_xy(test, base_cols)
            x_abl, y_abl = _prepare_xy(test, ablated_cols)
            common = x_full.index.intersection(x_abl.index).intersection(y_test.index).intersection(y_abl.index)
            if len(common) < 30 or y_test.loc[common].nunique() < 2:
                continue
            try:
                auc_full = roc_auc_score(y_test.loc[common], full_model.predict_proba(x_full.loc[common])[:, 1])
                auc_abl = roc_auc_score(y_test.loc[common], ablated_model.predict_proba(x_abl.loc[common])[:, 1])
            except Exception:
                continue
            fold_rows.append(float(auc_full - auc_abl))
        rows.append({
            "family": family,
            "features": cols,
            "mean_delta_auc_full_minus_ablated": float(np.mean(fold_rows)) if fold_rows else float("nan"),
            "n_folds": len(fold_rows),
            "status": "available",
        })
    return rows


def _weekly_importance(df: pd.DataFrame, features: list[str]) -> dict:
    weekly = df.set_index("Date")[[*features, "y_up_h20"]].resample("W-FRI").last().dropna().reset_index()
    weekly["crop_year"] = weekly["Date"].apply(crop_year)
    return _permutation_oof(weekly, features)


def build_feature_importance_v2() -> dict:
    df, features = _dataset()
    mi = _mi_spearman(df, features)
    perm = _permutation_oof(df, features)
    family = _family_ablation(df, features)
    weekly = _weekly_importance(df, features)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target": "y_up_h20",
        "n_rows": int(len(df)),
        "features_used": features,
        "mi_spearman": mi,
        "permutation_oof": perm,
        "importance_by_year": perm["by_year"],
        "fedfunds_audit": _fedfunds_audit(df, features),
        "family_ablation_oof": family,
        "weekly_importance": weekly,
        "key_findings": {
            "top_mi_feature": mi[0]["feature"] if mi else None,
            "top_oof_permutation_feature": perm["summary"][0]["feature"] if perm["summary"] else None,
            "fedfunds_status": "suspect_temporal_proxy",
            "n_features": len(features),
        },
    }


def _json_default(obj):
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


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA FEATURE IMPORTANCE V2",
        "",
        "> Importance OOF et par année. Source EMA exploratoire/proxy.",
        "",
        "## Résultats",
        "",
        f"- Features testées : {k['n_features']}",
        f"- Top MI : {k['top_mi_feature']}",
        f"- Top permutation OOF : {k['top_oof_permutation_feature']}",
        "",
        "## Fed Funds",
        "",
        data["fedfunds_audit"]["conclusion"],
        "",
        "## Limite",
        "",
        "Les familles EU avancées absentes du master features sont marquées manquantes dans les ablations.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_feature_importance_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_feature_importance_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_feature_importance_v2()
    print(f"Feature importance v2 saved -> {out}")

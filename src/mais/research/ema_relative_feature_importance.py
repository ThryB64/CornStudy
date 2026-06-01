"""EMA-NEXT-03 — Importance des features sur EMA/CBOT relatif H40/H90."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import build_relative_frame
from mais.research.ema_utils import crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_feature_importance.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_FEATURE_IMPORTANCE.md"
_HORIZONS = (40, 90)
_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]
_FAMILIES = {
    "basis": ["ema_cbot_basis", "ema_cbot_basis_zscore_52w"],
    "ema_technical": ["ema_front_vol_20d_adjusted"],
    "cbot_technical": ["corn_realized_vol_20", "corn_logret_20d"],
    "macro_energy": ["corn_gas_ratio", "fedfunds_level_zscore"],
}


def _prepare_frame(horizon: int) -> tuple[pd.DataFrame, list[str], str]:
    df = build_relative_frame((horizon,)).sort_values("Date").reset_index(drop=True)
    df["crop_year"] = df["Date"].apply(crop_year)
    feature_cols = [col for col in _FEATURES if col in df.columns]
    for col in feature_cols:
        df[f"{col}_lag1"] = df[col].shift(1)
    lag_cols = [f"{col}_lag1" for col in feature_cols]
    target = f"y_ema_outperforms_cbot_h{horizon}"
    keep = ["Date", "crop_year", target, *lag_cols]
    work = df[keep].replace([np.inf, -np.inf], np.nan).dropna(subset=[target, *lag_cols])
    return work, lag_cols, target


def _oof_predictions(
    horizon: int,
    *,
    drop_base_features: set[str] | None = None,
    permute_base_feature: str | None = None,
    seed: int = 17,
) -> pd.DataFrame:
    work, lag_cols, target = _prepare_frame(horizon)
    drop_lags = {f"{col}_lag1" for col in (drop_base_features or set())}
    model_cols = [col for col in lag_cols if col not in drop_lags]
    if not model_cols:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    years = sorted(work["crop_year"].unique())
    preds = []
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])].copy()
        if len(train) < 100 or len(test) < 20 or train[target].nunique() < 2:
            continue
        model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
        model.fit(train[model_cols], train[target])
        test_x = test[model_cols].copy()
        if permute_base_feature:
            perm_col = f"{permute_base_feature}_lag1"
            if perm_col in test_x.columns:
                test_x[perm_col] = rng.permutation(test_x[perm_col].to_numpy())
        prob = model.predict_proba(test_x)[:, 1]
        out = test[["Date", "crop_year", target]].rename(columns={target: "y_true"}).copy()
        out["prob"] = prob
        out["y_pred"] = (prob >= 0.5).astype(float)
        out["confidence"] = np.abs(prob - 0.5)
        preds.append(out)
    return pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()


def _metrics(pred: pd.DataFrame) -> dict:
    if pred.empty or pred["y_true"].nunique() < 2:
        return {"status": "SKIPPED", "n": int(len(pred))}
    top_n = max(1, int(len(pred) * 0.20))
    top = pred.nlargest(top_n, "confidence")
    y = pred["y_true"].astype(float)
    y_pred = pred["y_pred"].astype(float)
    return {
        "status": "OK",
        "n": int(len(pred)),
        "da": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, pred["prob"])),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
    }


def _horizon_importance(horizon: int) -> dict:
    baseline_pred = _oof_predictions(horizon)
    baseline = _metrics(baseline_pred)
    permutation = []
    for feature in _FEATURES:
        pred = _oof_predictions(horizon, permute_base_feature=feature)
        row = {"feature": feature, **_metrics(pred)}
        row["delta_auc"] = float((baseline.get("auc") or 0.0) - (row.get("auc") or 0.0))
        row["delta_balanced_accuracy"] = float(
            (baseline.get("balanced_accuracy") or 0.0) - (row.get("balanced_accuracy") or 0.0)
        )
        permutation.append(row)
    permutation = sorted(permutation, key=lambda row: (row.get("delta_auc", -999), row.get("delta_balanced_accuracy", -999)), reverse=True)

    family_ablation = []
    for family, features in _FAMILIES.items():
        pred = _oof_predictions(horizon, drop_base_features=set(features))
        row = {"family": family, "dropped_features": features, **_metrics(pred)}
        row["delta_auc"] = float((baseline.get("auc") or 0.0) - (row.get("auc") or 0.0))
        row["delta_balanced_accuracy"] = float(
            (baseline.get("balanced_accuracy") or 0.0) - (row.get("balanced_accuracy") or 0.0)
        )
        family_ablation.append(row)
    family_ablation = sorted(family_ablation, key=lambda row: row.get("delta_auc", -999), reverse=True)
    return {
        "horizon": int(horizon),
        "baseline": baseline,
        "permutation_importance": permutation,
        "family_ablation": family_ablation,
        "top_feature": permutation[0]["feature"] if permutation else None,
        "top_family": family_ablation[0]["family"] if family_ablation else None,
    }


def build_relative_feature_importance() -> dict:
    results = [_horizon_importance(horizon) for horizon in _HORIZONS]
    h40 = next(row for row in results if row["horizon"] == 40)
    h90 = next(row for row in results if row["horizon"] == 90)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target_family": "relative_ema_outperformance",
        "horizons": list(_HORIZONS),
        "results": results,
        "key_findings": {
            "h40_top_feature": h40.get("top_feature"),
            "h40_top_family": h40.get("top_family"),
            "h90_top_feature": h90.get("top_feature"),
            "h90_top_family": h90.get("top_family"),
            "interpretation": _interpretation(h40, h90),
        },
    }


def _interpretation(h40: dict, h90: dict) -> str:
    families = {h40.get("top_family"), h90.get("top_family")}
    if "basis" in families:
        return "Le basis reste le driver le plus robuste de la performance relative EMA/CBOT."
    return "Le signal relatif ne semble pas uniquement porte par le basis dans cette permutation OOF."


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


def _fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(data: dict, path: Path) -> None:
    lines = [
        "# EMA RELATIVE FEATURE IMPORTANCE",
        "",
        "> Importance OOF sur `relative_ema_outperformance_h40/h90`.",
        "",
        "## Verdict",
        "",
        f"- H40 top feature : `{data['key_findings']['h40_top_feature']}`",
        f"- H40 top family : `{data['key_findings']['h40_top_family']}`",
        f"- H90 top feature : `{data['key_findings']['h90_top_feature']}`",
        f"- H90 top family : `{data['key_findings']['h90_top_family']}`",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
    ]
    for result in data["results"]:
        lines += [
            f"## H{result['horizon']}",
            "",
            f"- Baseline AUC : {_fmt(result['baseline'].get('auc'))}",
            f"- Baseline balanced accuracy : {_fmt(result['baseline'].get('balanced_accuracy'))}",
            "",
            "| Feature | Δ AUC permutation | Δ balanced acc. |",
            "|---|---:|---:|",
        ]
        for row in result["permutation_importance"]:
            lines.append(
                f"| {row['feature']} | {_fmt(row.get('delta_auc'))} | {_fmt(row.get('delta_balanced_accuracy'))} |"
            )
        lines += [
            "",
            "| Famille retirée | Δ AUC ablation | Δ balanced acc. |",
            "|---|---:|---:|",
        ]
        for row in result["family_ablation"]:
            lines.append(
                f"| {row['family']} | {_fmt(row.get('delta_auc'))} | {_fmt(row.get('delta_balanced_accuracy'))} |"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_feature_importance(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_feature_importance()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_feature_importance()
    print(f"Relative feature importance saved -> {out}")

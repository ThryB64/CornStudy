"""V6-02 — Cross-target OOF prediction factory and meta-features."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.experiment_registry_v6 import make_record, save_registry
from mais.research.target_labs_v6 import build_target_frames_v6

_OUTPUT_DIR = ARTEFACTS_DIR / "v6"
_PRED_OUTPUT = _OUTPUT_DIR / "cross_target_oof_predictions_v6.parquet"
_META_OUTPUT = _OUTPUT_DIR / "meta_features_v6.parquet"
_MANIFEST_OUTPUT = _OUTPUT_DIR / "cross_target_oof_v6.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "CROSS_TARGET_OOF_V6.md"
_MIN_TRAIN = 140
_MIN_TEST = 20

_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
    "drought_composite",
    "crop_ge_pct",
    "cot_mm_net",
    "cot_mm_net_zscore",
]

_AUX_TARGETS = {
    "ema": [
        "y_rel_outperform_h40",
        "y_rel_outperform_h90",
        "y_rel_outperform_h120",
        "y_rel_outperform_when_basis_extreme_h40",
        "y_rel_outperform_when_basis_extreme_h90",
        "y_rel_large_outperform_h90",
        "y_rel_large_underperform_h90",
    ],
    "cbot": [
        "y_cbot_up_h20",
        "y_cbot_up_h60",
        "y_cbot_drawdown_5pct_h20",
        "y_cbot_drawdown_5pct_h60",
        "y_cbot_large_down_3pct_h90",
        "y_cbot_rally_5pct_h40",
    ],
}


def _present(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [col for col in cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]


def _models() -> dict[str, object]:
    return {
        "logistic": LogisticRegression(max_iter=600, class_weight="balanced", solver="liblinear"),
        "histgb": HistGradientBoostingClassifier(max_iter=80, learning_rate=0.04, max_leaf_nodes=15, random_state=17),
    }


def _oof_one(frame: pd.DataFrame, *, market: str, target: str, model_name: str) -> pd.DataFrame:
    features = _present(frame, _FEATURES)
    work = frame[["Date", "crop_year", target, *features]].copy()
    for col in features:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{col}_lag1" for col in features]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target, *lag_cols])
    rows = []
    years = sorted(work["crop_year"].unique())
    for fold, idx in enumerate(range(3, len(years)), start=1):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if len(train) < _MIN_TRAIN or len(test) < _MIN_TEST or train[target].nunique() < 2 or test[target].nunique() < 2:
            continue
        model = _models()[model_name]
        model.fit(train[lag_cols], train[target])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        out = test[["Date", "crop_year", target]].rename(columns={target: "y_true"}).copy()
        out["market"] = market
        out["target_name"] = target
        out["model_name"] = model_name
        out["pred_proba"] = prob
        out["pred_label"] = (prob >= 0.5).astype(float)
        out["confidence"] = np.abs(prob - 0.5)
        out["fold"] = fold
        out["train_start"] = train["Date"].min()
        out["train_end"] = train["Date"].max()
        out["test_start"] = test["Date"].min()
        out["test_end"] = test["Date"].max()
        out["is_oof"] = True
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_oof_predictions_v6() -> pd.DataFrame:
    frames = build_target_frames_v6()
    rows = []
    for market, targets in _AUX_TARGETS.items():
        frame = frames[market]
        for target in targets:
            if target not in frame.columns:
                continue
            for model_name in _models():
                pred = _oof_one(frame, market=market, target=target, model_name=model_name)
                if not pred.empty:
                    rows.append(pred)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_meta_features_v6(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    pred = build_oof_predictions_v6() if predictions is None else predictions.copy()
    if pred.empty:
        return pd.DataFrame()
    pred["feature_name"] = "pred_" + pred["market"] + "_" + pred["target_name"] + "_" + pred["model_name"]
    wide = pred.pivot_table(index="Date", columns="feature_name", values="pred_proba", aggfunc="last").reset_index()
    pred_wide = wide.set_index("Date")
    rel_cols = [col for col in pred_wide.columns if "ema_y_rel_" in col]
    cbot_cols = [col for col in pred_wide.columns if "cbot_y_cbot_" in col]
    meta = wide.copy()
    meta["meta_mean_rel_signal"] = pred_wide[rel_cols].mean(axis=1).to_numpy() if rel_cols else np.nan
    meta["meta_std_rel_signal"] = pred_wide[rel_cols].std(axis=1).to_numpy() if rel_cols else np.nan
    meta["meta_mean_cbot_signal"] = pred_wide[cbot_cols].mean(axis=1).to_numpy() if cbot_cols else np.nan
    meta["meta_signal_entropy"] = _entropy(pred_wide).to_numpy()
    meta["meta_max_confidence"] = (pred_wide - 0.5).abs().max(axis=1).to_numpy()
    meta["meta_n_models_bullish"] = (pred_wide >= 0.55).sum(axis=1).to_numpy()
    meta["meta_n_models_bearish"] = (pred_wide <= 0.45).sum(axis=1).to_numpy()
    if rel_cols:
        h40_cols = [col for col in rel_cols if "h40" in col]
        h90_cols = [col for col in rel_cols if "h90" in col]
        meta["meta_h40_h90_agreement"] = (
            ((pred_wide[h40_cols].mean(axis=1) >= 0.5) == (pred_wide[h90_cols].mean(axis=1) >= 0.5)).astype(float).to_numpy()
            if h40_cols and h90_cols
            else np.nan
        )
    return meta.replace([np.inf, -np.inf], np.nan)


def _entropy(frame: pd.DataFrame) -> pd.Series:
    clipped = frame.clip(1e-6, 1 - 1e-6)
    ent = -(clipped * np.log(clipped) + (1 - clipped) * np.log(1 - clipped))
    return ent.mean(axis=1)


def _prediction_metrics(pred: pd.DataFrame) -> list[dict]:
    rows = []
    for (market, target, model), group in pred.groupby(["market", "target_name", "model_name"]):
        if group["y_true"].nunique() < 2:
            continue
        rows.append({
            "market": market,
            "target": target,
            "model": model,
            "n": int(len(group)),
            "auc": float(roc_auc_score(group["y_true"], group["pred_proba"])),
            "da": float(accuracy_score(group["y_true"], group["pred_label"])),
            "balanced_accuracy": float(balanced_accuracy_score(group["y_true"], group["pred_label"])),
        })
    return rows


@lru_cache(maxsize=1)
def build_cross_target_oof_v6() -> dict:
    pred = build_oof_predictions_v6()
    meta = build_meta_features_v6(pred)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pred.to_parquet(_PRED_OUTPUT, index=False)
    meta.to_parquet(_META_OUTPUT, index=False)
    metrics = _prediction_metrics(pred)
    best = max(metrics, key=lambda row: row["auc"], default={})
    records = [
        make_record(
            experiment_id=f"V6-02-{row['market']}-{row['target']}-{row['model']}",
            feature_set="cross_target_oof",
            target=row["target"],
            horizon=row["target"].rsplit("_h", 1)[-1] if "_h" in row["target"] else "NA",
            model=row["model"],
            cv_protocol="crop_year_oof",
            metrics={k: row[k] for k in ("auc", "balanced_accuracy", "da")},
            verdict="PROMISING" if row["auc"] >= 0.70 else "WATCHLIST" if row["auc"] >= 0.60 else "NO_GO",
            artefact_paths=[str(_PRED_OUTPUT), str(_META_OUTPUT)],
        )
        for row in metrics
    ]
    registry = save_registry(records) if records else {}
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "OOF prediction factory for auxiliary CBOT and EMA premium targets.",
        "prediction_rows": int(len(pred)),
        "meta_rows": int(len(meta)),
        "prediction_path": str(_PRED_OUTPUT),
        "meta_feature_path": str(_META_OUTPUT),
        "metrics": metrics,
        "registry": registry,
        "key_findings": {
            "n_prediction_series": int(pred.groupby(["market", "target_name", "model_name"]).ngroups) if not pred.empty else 0,
            "n_meta_columns": int(len(meta.columns)) if not meta.empty else 0,
            "best_oof_target": best.get("target"),
            "best_oof_model": best.get("model"),
            "best_oof_auc": best.get("auc"),
            "interpretation": "OOF auxiliary predictions are ready for meta-models; no in-sample predictions are used.",
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


def _write_doc(data: dict, path: Path) -> None:
    lines = [
        "# CROSS TARGET OOF V6",
        "",
        "> Predictions OOF de cibles auxiliaires EMA/CBOT, transformees en meta-features.",
        "",
        f"- Prediction rows : {data['prediction_rows']}",
        f"- Meta rows : {data['meta_rows']}",
        f"- Series OOF : {data['key_findings']['n_prediction_series']}",
        f"- Meta columns : {data['key_findings']['n_meta_columns']}",
        f"- Best OOF : `{data['key_findings'].get('best_oof_target')}` / `{data['key_findings'].get('best_oof_model')}` AUC {data['key_findings'].get('best_oof_auc')}",
        "",
        "## Metrics",
        "",
        "| Market | Target | Model | n | AUC | DA | BA |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in data["metrics"]:
        lines.append(
            f"| {row['market']} | `{row['target']}` | {row['model']} | {row['n']} | "
            f"{row['auc']:.3f} | {row['da']:.3f} | {row['balanced_accuracy']:.3f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_cross_target_oof_v6(output_path: Path | None = None) -> Path:
    path = output_path or _MANIFEST_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_cross_target_oof_v6()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_doc(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_cross_target_oof_v6()
    print(f"Cross-target OOF V6 saved -> {out}")

"""V6-03 — Premium meta-model, confidence and abstention experiments."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    matthews_corrcoef,
    roc_auc_score,
)

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.cross_target_oof_v6 import _META_OUTPUT, build_cross_target_oof_v6
from mais.research.experiment_registry_v6 import make_record, save_registry
from mais.research.target_labs_v6 import build_target_frames_v6

_OUTPUT_DIR = ARTEFACTS_DIR / "v6"
_OUTPUT = _OUTPUT_DIR / "meta_model_premium_v6.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "META_MODEL_PREMIUM_V6.md"
_TARGETS = [
    "y_rel_outperform_h40",
    "y_rel_outperform_h90",
    "y_rel_outperform_when_basis_extreme_h40",
    "y_rel_outperform_when_basis_extreme_h90",
]
_CLASSIC = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]
_MIN_TRAIN = 120
_MIN_TEST = 20


def _load_meta() -> pd.DataFrame:
    if not _META_OUTPUT.exists():
        build_cross_target_oof_v6()
    return pd.read_parquet(_META_OUTPUT)


def build_meta_model_frame() -> pd.DataFrame:
    frames = build_target_frames_v6()
    ema = frames["ema"].copy()
    meta = _load_meta()
    ema["Date"] = pd.to_datetime(ema["Date"])
    meta["Date"] = pd.to_datetime(meta["Date"])
    return ema.merge(meta, on="Date", how="inner")


def _present(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [col for col in cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]


def _unique(cols: list[str]) -> list[str]:
    return list(dict.fromkeys(cols))


def _feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    classic = _present(df, _CLASSIC)
    meta = [col for col in df.columns if col.startswith(("pred_", "meta_")) and pd.api.types.is_numeric_dtype(df[col])]
    basis_rule = _present(df, ["ema_cbot_basis_zscore_52w"])
    return {
        "classic": classic,
        "meta_only": meta,
        "classic_plus_meta": _unique([*classic, *meta]),
        "meta_plus_basis": _unique([*meta, *basis_rule]),
        "full_stack": _unique([*classic, *meta, *basis_rule]),
    }


def _oof(df: pd.DataFrame, target: str, features: list[str]) -> pd.DataFrame:
    work = df[["Date", "crop_year", "month", target, *features]].copy()
    for col in features:
        if col.startswith(("pred_", "meta_")):
            work[f"{col}_x"] = work[col]
        else:
            work[f"{col}_x"] = work[col].shift(1)
    x_cols = [f"{col}_x" for col in features]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target])
    rows = []
    years = sorted(work["crop_year"].unique())
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if len(train) < _MIN_TRAIN or len(test) < _MIN_TEST or train[target].nunique() < 2 or test[target].nunique() < 2:
            continue
        fold_cols = [
            col
            for col in x_cols
            if train[col].notna().sum() >= min(60, max(20, int(len(train) * 0.15)))
            and test[col].notna().sum() > 0
            and train[col].nunique(dropna=True) > 1
        ]
        if not fold_cols:
            continue
        medians = train[fold_cols].median(numeric_only=True).fillna(0.0)
        x_train = train[fold_cols].fillna(medians)
        x_test = test[fold_cols].fillna(medians)
        model = LogisticRegression(max_iter=700, class_weight="balanced", solver="liblinear")
        model.fit(x_train, train[target])
        prob = model.predict_proba(x_test)[:, 1]
        out = test[["Date", "crop_year", "month", target]].rename(columns={target: "y_true"}).copy()
        out["prob"] = prob
        out["y_pred"] = (prob >= 0.5).astype(float)
        out["confidence"] = np.abs(prob - 0.5)
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _ece(y: pd.Series, prob: pd.Series, bins: int = 10) -> float:
    frame = pd.DataFrame({"y": y.astype(float), "prob": prob.astype(float)})
    frame["bin"] = pd.cut(frame["prob"], bins=np.linspace(0, 1, bins + 1), include_lowest=True)
    total = len(frame)
    err = 0.0
    for _, group in frame.groupby("bin", observed=False):
        if group.empty:
            continue
        err += len(group) / total * abs(group["y"].mean() - group["prob"].mean())
    return float(err)


def _metrics(pred: pd.DataFrame, *, target: str, feature_set: str) -> dict:
    if pred.empty or pred["y_true"].nunique() < 2:
        return {"target": target, "feature_set": feature_set, "status": "SKIPPED", "n": int(len(pred))}
    y = pred["y_true"].astype(float)
    y_pred = pred["y_pred"].astype(float)
    top20 = pred.nlargest(max(1, int(len(pred) * 0.20)), "confidence")
    top40 = pred.nlargest(max(1, int(len(pred) * 0.40)), "confidence")
    return {
        "target": target,
        "feature_set": feature_set,
        "status": "OK",
        "n": int(len(pred)),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, pred["prob"])),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "mcc": float(matthews_corrcoef(y, y_pred)),
        "brier": float(brier_score_loss(y, pred["prob"])),
        "ece": _ece(y, pred["prob"]),
        "top20_da": float(accuracy_score(top20["y_true"], top20["y_pred"])),
        "top40_da": float(accuracy_score(top40["y_true"], top40["y_pred"])),
    }


def _abstention(pred: pd.DataFrame) -> list[dict]:
    if pred.empty:
        return []
    policies = {
        "all": pd.Series(True, index=pred.index),
        "top40_confidence": pred["confidence"] >= pred["confidence"].quantile(0.60),
        "top20_confidence": pred["confidence"] >= pred["confidence"].quantile(0.80),
        "avoid_roll_proxy_months": ~pred["month"].isin([2, 5, 7, 10]),
    }
    rows = []
    for name, mask in policies.items():
        sub = pred[mask].copy()
        if len(sub) < 20 or sub["y_true"].nunique() < 2:
            rows.append({"policy": name, "status": "SKIPPED", "n": int(len(sub)), "coverage": float(len(sub) / len(pred))})
            continue
        rows.append({
            "policy": name,
            "status": "OK",
            "n": int(len(sub)),
            "coverage": float(len(sub) / len(pred)),
            "da": float(accuracy_score(sub["y_true"], sub["y_pred"])),
            "balanced_accuracy": float(balanced_accuracy_score(sub["y_true"], sub["y_pred"])),
            "auc": float(roc_auc_score(sub["y_true"], sub["prob"])),
        })
    return rows


@lru_cache(maxsize=1)
def build_meta_model_premium_v6() -> dict:
    df = build_meta_model_frame()
    feature_sets = _feature_sets(df)
    results = []
    predictions = {}
    for target in _TARGETS:
        if target not in df.columns:
            continue
        for name, features in feature_sets.items():
            pred = _oof(df, target, features)
            predictions[(target, name)] = pred
            results.append(_metrics(pred, target=target, feature_set=name))
    ok = [row for row in results if row["status"] == "OK"]
    base_lookup = {(row["target"], row["feature_set"]): row for row in ok}
    enriched = []
    for row in results:
        out = dict(row)
        base = base_lookup.get((row["target"], "classic"))
        if row.get("status") == "OK" and base:
            out["delta_auc_vs_classic"] = float(row["auc"] - base["auc"])
            out["delta_top20_vs_classic"] = float(row["top20_da"] - base["top20_da"])
        enriched.append(out)
    best_context = max(ok, key=lambda row: (row["auc"], row["top20_da"]), default={})
    robust = [row for row in ok if row["n"] >= 300]
    best_robust = max(robust, key=lambda row: (row["auc"], row["top20_da"]), default=best_context)
    gain_candidates = [
        row
        for row in enriched
        if row.get("status") == "OK" and row.get("feature_set") != "classic" and row.get("delta_auc_vs_classic") is not None
    ]
    best_gain = max(gain_candidates, key=lambda row: (row.get("delta_auc_vs_classic", -999), row["auc"]), default={})
    best_pred = predictions.get((best_robust.get("target"), best_robust.get("feature_set")), pd.DataFrame())
    abstention = _abstention(best_pred)
    records = [
        make_record(
            experiment_id=f"V6-03-{row['target']}-{row['feature_set']}",
            feature_set=row["feature_set"],
            target=row["target"],
            horizon=row["target"].rsplit("_h", 1)[-1] if "_h" in row["target"] else "NA",
            model="logistic_meta",
            cv_protocol="crop_year_oof_meta",
            metrics={k: row[k] for k in ("auc", "balanced_accuracy", "top20_da", "ece") if k in row},
            verdict="PROMISING" if row.get("auc", 0) >= 0.72 else "WATCHLIST" if row.get("auc", 0) >= 0.62 else "NO_GO",
            artefact_paths=["artefacts/v6/meta_model_premium_v6.json"],
        )
        for row in ok
    ]
    registry = save_registry(records) if records else {}
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Premium meta-models using classic features and strict OOF meta-features.",
        "results": enriched,
        "abstention_on_best": abstention,
        "registry": registry,
        "key_findings": {
            "best_target": best_robust.get("target"),
            "best_feature_set": best_robust.get("feature_set"),
            "best_auc": best_robust.get("auc"),
            "best_balanced_accuracy": best_robust.get("balanced_accuracy"),
            "best_top20_da": best_robust.get("top20_da"),
            "best_ece": best_robust.get("ece"),
            "best_n": best_robust.get("n"),
            "best_context_target": best_context.get("target"),
            "best_context_feature_set": best_context.get("feature_set"),
            "best_context_auc": best_context.get("auc"),
            "best_context_n": best_context.get("n"),
            "best_gain_target": best_gain.get("target"),
            "best_gain_feature_set": best_gain.get("feature_set"),
            "best_gain_delta_auc_vs_classic": best_gain.get("delta_auc_vs_classic"),
            "interpretation": _interpretation(best_robust, enriched),
        },
    }


def _interpretation(best: dict, rows: list[dict]) -> str:
    max_delta = max((row.get("delta_auc_vs_classic", -999) for row in rows if row.get("status") == "OK"), default=0)
    if max_delta >= 0.02:
        return "OOF meta-features materially improve at least one premium target."
    if best.get("feature_set") in {"meta_only", "classic_plus_meta", "full_stack", "meta_plus_basis"}:
        return "Meta-features are competitive, but gains over classic features are modest."
    return "Classic/basis features remain hard to beat; keep meta-features as auxiliary confidence inputs."


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
        "# META MODEL PREMIUM V6",
        "",
        "> Meta-model premium utilisant uniquement des meta-features OOF.",
        "",
        f"- Best target : `{data['key_findings'].get('best_target')}`",
        f"- Best set : `{data['key_findings'].get('best_feature_set')}`",
        f"- Best n : {data['key_findings'].get('best_n')}",
        f"- Best AUC : {data['key_findings'].get('best_auc')}",
        f"- Best top20 : {data['key_findings'].get('best_top20_da')}",
        f"- Best contexte étroit : `{data['key_findings'].get('best_context_target')}` "
        f"(n={data['key_findings'].get('best_context_n')}, AUC={data['key_findings'].get('best_context_auc')})",
        f"- Meilleur gain meta vs classic : `{data['key_findings'].get('best_gain_target')}` "
        f"+{data['key_findings'].get('best_gain_delta_auc_vs_classic')} AUC",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
        "## Results",
        "",
        "| Target | Set | n | AUC | dAUC | BA | Top20 | ECE |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| `{row['target']}` | `{row['feature_set']}` | {row.get('n', 0)} | "
            f"{row.get('auc', float('nan')):.3f} | {row.get('delta_auc_vs_classic', float('nan')):.3f} | "
            f"{row.get('balanced_accuracy', float('nan')):.3f} | {row.get('top20_da', float('nan')):.3f} | "
            f"{row.get('ece', float('nan')):.3f} |"
        )
    lines += ["", "## Abstention best model", "", "| Policy | n | Coverage | DA | AUC | BA |", "|---|---:|---:|---:|---:|---:|"]
    for row in data["abstention_on_best"]:
        lines.append(
            f"| `{row['policy']}` | {row.get('n', 0)} | {row.get('coverage', float('nan')):.3f} | "
            f"{row.get('da', float('nan')):.3f} | {row.get('auc', float('nan')):.3f} | {row.get('balanced_accuracy', float('nan')):.3f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_meta_model_premium_v6(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_meta_model_premium_v6()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_doc(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_meta_model_premium_v6()
    print(f"Meta model premium V6 saved -> {out}")

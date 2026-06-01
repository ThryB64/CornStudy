"""EMA-V5-03 — Hierarchical CBOT + EU premium experiment."""

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
    matthews_corrcoef,
    roc_auc_score,
)

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_cross_data_interactions_v5 import build_interaction_frame
from mais.research.ema_utils import binary_target_from_future_return, bootstrap_ci

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_hierarchical_cbot_premium_v5.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_HIERARCHICAL_CBOT_PREMIUM_V5.md"
_HORIZONS = (40, 90)
_MIN_TRAIN = 120
_MIN_TEST = 20

_DIRECT_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
    "x_basis_cbot_momentum",
    "x_basis_cbot_vol",
    "x_basis_ema_vol",
    "x_basis_month_sin",
    "x_basis_month_cos",
]
_CBOT_FEATURES = [
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]
_PREMIUM_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "x_basis_cbot_momentum",
    "x_basis_cbot_vol",
    "x_basis_ema_vol",
    "x_basis_month_sin",
    "x_basis_month_cos",
]


def build_hierarchical_frame() -> pd.DataFrame:
    """Build direct EMA, CBOT and premium targets on the same date frame."""
    df = build_interaction_frame().copy()
    for horizon in _HORIZONS:
        df[f"y_ema_up_h{horizon}"] = binary_target_from_future_return(df[f"ema_return_h{horizon}"])
        df[f"y_cbot_up_h{horizon}"] = binary_target_from_future_return(df[f"cbot_eur_return_h{horizon}"])
    return df


def _present(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [col for col in cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]


def _lagged(work: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, list[str]]:
    out = work.copy()
    for col in features:
        out[f"{col}_lag1"] = out[col].shift(1)
    return out, [f"{col}_lag1" for col in features]


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str], target: str) -> tuple[np.ndarray, np.ndarray]:
    model = LogisticRegression(max_iter=600, class_weight="balanced", solver="liblinear")
    model.fit(train[features], train[target])
    return model.predict_proba(train[features])[:, 1], model.predict_proba(test[features])[:, 1]


def _choose_weight(y_train: pd.Series, cbot_prob: np.ndarray, premium_prob: np.ndarray) -> float:
    best_weight = 0.5
    best_score = -np.inf
    for weight in np.linspace(0.1, 0.9, 9):
        score = weight * cbot_prob + (1.0 - weight) * premium_prob
        pred = (score >= 0.5).astype(float)
        metric = balanced_accuracy_score(y_train, pred)
        if metric > best_score:
            best_weight = float(weight)
            best_score = float(metric)
    return best_weight


def _oof_horizon(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    y_ema = f"y_ema_up_h{horizon}"
    y_cbot = f"y_cbot_up_h{horizon}"
    y_premium = f"y_rel_outperform_h{horizon}"
    direct_features = _present(df, _DIRECT_FEATURES)
    cbot_features = _present(df, _CBOT_FEATURES)
    premium_features = _present(df, _PREMIUM_FEATURES)
    needed = list(
        dict.fromkeys(["Date", "crop_year", "month", y_ema, y_cbot, y_premium, *direct_features, *cbot_features, *premium_features])
    )
    work = df[needed].copy()
    work, direct_lag = _lagged(work, direct_features)
    work, cbot_lag = _lagged(work, cbot_features)
    work, premium_lag = _lagged(work, premium_features)
    all_lag = sorted({*direct_lag, *cbot_lag, *premium_lag})
    work = work[["Date", "crop_year", "month", y_ema, y_cbot, y_premium, *all_lag]]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[y_ema, y_cbot, y_premium, *all_lag])

    rows = []
    years = sorted(work["crop_year"].unique())
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if (
            len(train) < _MIN_TRAIN
            or len(test) < _MIN_TEST
            or train[y_ema].nunique() < 2
            or train[y_cbot].nunique() < 2
            or train[y_premium].nunique() < 2
            or test[y_ema].nunique() < 2
        ):
            continue
        direct_train, direct_test = _fit_predict(train, test, direct_lag, y_ema)
        cbot_train, cbot_test = _fit_predict(train, test, cbot_lag, y_cbot)
        premium_train, premium_test = _fit_predict(train, test, premium_lag, y_premium)
        learned_weight = _choose_weight(train[y_ema], cbot_train, premium_train)

        out = test[["Date", "crop_year", "month", y_ema]].rename(columns={y_ema: "y_true"}).copy()
        out["direct_ema"] = direct_test
        out["cbot_only"] = cbot_test
        out["premium_only"] = premium_test
        out["hierarchical_fixed"] = 0.60 * cbot_test + 0.40 * premium_test
        out["hierarchical_train_weighted"] = learned_weight * cbot_test + (1.0 - learned_weight) * premium_test
        out["train_weight_cbot"] = learned_weight
        out["horizon"] = int(horizon)
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _score_frame(pred: pd.DataFrame, model_name: str) -> pd.DataFrame:
    out = pred[["Date", "crop_year", "month", "horizon", "y_true", model_name]].copy()
    out = out.rename(columns={model_name: "prob"})
    out["y_pred"] = (out["prob"] >= 0.5).astype(float)
    out["confidence"] = (out["prob"] - 0.5).abs()
    return out


def _metrics(pred: pd.DataFrame, model_name: str, horizon: int) -> dict:
    if pred.empty or pred["y_true"].nunique() < 2:
        return {
            "model": model_name,
            "horizon": int(horizon),
            "status": "SKIPPED",
            "n": int(len(pred)),
        }
    y = pred["y_true"].astype(float)
    y_pred = pred["y_pred"].astype(float)
    correct = y.eq(y_pred).astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=250)
    top = pred.nlargest(max(1, int(len(pred) * 0.20)), "confidence")
    annual = (
        pred.assign(correct=correct)
        .groupby("crop_year")
        .agg(n=("correct", "size"), da=("correct", "mean"))
        .reset_index()
    )
    return {
        "model": model_name,
        "horizon": int(horizon),
        "status": "OK",
        "n": int(len(pred)),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, pred["prob"])),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "mcc": float(matthews_corrcoef(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
        "ci95_da_lo": ci["ci_lo"],
        "ci95_da_hi": ci["ci_hi"],
        "annual_stability_share_da_ge_53": float((annual["da"] >= 0.53).mean()),
    }


@lru_cache(maxsize=1)
def build_hierarchical_cbot_premium_v5() -> dict:
    df = build_hierarchical_frame()
    rows = []
    weights = {}
    for horizon in _HORIZONS:
        pred = _oof_horizon(df, horizon)
        if not pred.empty:
            weights[str(horizon)] = {
                "mean_train_weight_cbot": float(pred["train_weight_cbot"].mean()),
                "min_train_weight_cbot": float(pred["train_weight_cbot"].min()),
                "max_train_weight_cbot": float(pred["train_weight_cbot"].max()),
            }
        for model_name in [
            "direct_ema",
            "cbot_only",
            "premium_only",
            "hierarchical_fixed",
            "hierarchical_train_weighted",
        ]:
            rows.append(_metrics(_score_frame(pred, model_name) if not pred.empty else pred, model_name, horizon))

    ok = [row for row in rows if row.get("status") == "OK"]
    best = max(ok, key=lambda row: (row["auc"], row["balanced_accuracy"]), default={})
    direct = {
        row["horizon"]: row
        for row in ok
        if row["model"] == "direct_ema"
    }
    enriched = []
    for row in rows:
        out = dict(row)
        base = direct.get(row["horizon"])
        if row.get("status") == "OK" and base:
            out["delta_auc_vs_direct"] = float(row["auc"] - base["auc"])
            out["delta_balanced_accuracy_vs_direct"] = float(row["balanced_accuracy"] - base["balanced_accuracy"])
        enriched.append(out)

    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Hierarchical EMA direction experiment: CBOT global component + EU premium component.",
        "target": "absolute EMA direction, evaluated only as a diagnostic target",
        "results": enriched,
        "train_weight_summary": weights,
        "key_findings": {
            "best_model": best.get("model"),
            "best_horizon": best.get("horizon"),
            "best_auc": best.get("auc"),
            "best_balanced_accuracy": best.get("balanced_accuracy"),
            "best_top20_da": best.get("top20_da"),
            "interpretation": _interpretation(best),
        },
    }


def _interpretation(best: dict) -> str:
    model = best.get("model")
    if model and model.startswith("hierarchical"):
        return "The hierarchical CBOT + premium architecture improves the raw EMA diagnostic target."
    if model == "premium_only":
        return "The premium component remains more informative than direct EMA modelling for this diagnostic."
    if model == "cbot_only":
        return "The global CBOT component dominates absolute EMA direction in this diagnostic."
    return "Direct EMA direction remains difficult; keep premium-relative targets central."


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
    key = data["key_findings"]
    lines = [
        "# EMA HIERARCHICAL CBOT PREMIUM V5",
        "",
        "> Diagnostic : EMA absolu = composante CBOT mondiale + composante prime europeenne.",
        "",
        "## Verdict",
        "",
        f"- Meilleur modele : `{key.get('best_model')}`",
        f"- Horizon : H{key.get('best_horizon')}",
        f"- AUC : {_fmt(key.get('best_auc'))}",
        f"- Balanced accuracy : {_fmt(key.get('best_balanced_accuracy'))}",
        f"- Top20 DA : {_fmt(key.get('best_top20_da'))}",
        f"- Lecture : {key['interpretation']}",
        "",
        "## Resultats",
        "",
        "| Modele | H | n | DA | AUC | Bal. acc | dAUC vs direct | dBal vs direct | Top20 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| `{row['model']}` | {row['horizon']} | {row.get('n', 0)} | {_fmt(row.get('da'))} | "
            f"{_fmt(row.get('auc'))} | {_fmt(row.get('balanced_accuracy'))} | "
            f"{_fmt(row.get('delta_auc_vs_direct'))} | {_fmt(row.get('delta_balanced_accuracy_vs_direct'))} | "
            f"{_fmt(row.get('top20_da'))} |"
        )
    lines += [
        "",
        "## Limites",
        "",
        "- La direction EMA absolue reste une cible diagnostic, pas le coeur de l'etude.",
        "- La source EMA reste exploratoire/proxy.",
        "- Les poids hierarchiques sont calibres uniquement sur train mais restent simples.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_hierarchical_cbot_premium_v5(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_hierarchical_cbot_premium_v5()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_hierarchical_cbot_premium_v5()
    print(f"EMA hierarchical CBOT premium V5 saved -> {out}")

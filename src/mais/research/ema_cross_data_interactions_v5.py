"""EMA-V5-02 — Cross-data interaction experiments for the EMA premium signal."""

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
from mais.research.ema_target_lab_v5 import build_target_frame
from mais.research.ema_utils import bootstrap_ci

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_cross_data_interactions_v5.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_CROSS_DATA_INTERACTIONS_V5.md"
_HORIZONS = (40, 90)
_MIN_TRAIN = 120
_MIN_TEST = 20
_MIN_EVAL = 80

_BASE_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]


def _zscore(series: pd.Series) -> pd.Series:
    std = series.expanding(min_periods=120).std().shift(1)
    mean = series.expanding(min_periods=120).mean().shift(1)
    return (series - mean) / std.replace(0, np.nan)


def build_interaction_frame() -> pd.DataFrame:
    """Build current-known cross-data interactions for premium targets."""
    df = build_target_frame(_HORIZONS).copy()
    z = df["ema_cbot_basis_zscore_52w"]
    month_angle = 2.0 * np.pi * df["month"] / 12.0
    df["month_sin"] = np.sin(month_angle)
    df["month_cos"] = np.cos(month_angle)

    if "corn_logret_20d" in df:
        df["x_basis_cbot_momentum"] = z * df["corn_logret_20d"]
    if "corn_realized_vol_20" in df:
        df["x_basis_cbot_vol"] = z * df["corn_realized_vol_20"]
    if "ema_front_vol_20d_adjusted" in df:
        df["x_basis_ema_vol"] = z * df["ema_front_vol_20d_adjusted"]
    if "corn_gas_ratio" in df:
        df["x_basis_energy_ratio"] = z * df["corn_gas_ratio"]
    if "fedfunds_level_zscore" in df:
        df["x_basis_macro_rate"] = z * df["fedfunds_level_zscore"]
    df["x_basis_month_sin"] = z * df["month_sin"]
    df["x_basis_month_cos"] = z * df["month_cos"]

    weather_cols = [
        col
        for col in df.columns
        if col.startswith("eu_") and any(token in col for token in ("gdd", "heat", "precip", "rain"))
    ]
    if weather_cols:
        weather = pd.concat([_zscore(df[col]) for col in weather_cols], axis=1).mean(axis=1)
        df["eu_weather_stress_score"] = weather
        df["x_basis_eu_weather_stress"] = z * weather

    wasde_cols = [col for col in df.columns if col.startswith(("wasde_eu_", "wasde_ukraine_"))]
    numeric_wasde = [col for col in wasde_cols if pd.api.types.is_numeric_dtype(df[col])]
    if numeric_wasde:
        wasde = pd.concat([_zscore(df[col]) for col in numeric_wasde[:8]], axis=1).mean(axis=1)
        df["eu_wasde_balance_score"] = wasde
        df["x_basis_eu_wasde_balance"] = z * wasde

    return df.replace([np.inf, -np.inf], np.nan)


def _present(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [col for col in cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]


def _feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    base = _present(df, _BASE_FEATURES)
    market_cross = _present(
        df,
        [
            "x_basis_cbot_momentum",
            "x_basis_cbot_vol",
            "x_basis_ema_vol",
            "x_basis_energy_ratio",
            "x_basis_macro_rate",
        ],
    )
    season_cross = _present(df, ["month_sin", "month_cos", "x_basis_month_sin", "x_basis_month_cos"])
    eu_cross = _present(
        df,
        [
            "eu_weather_stress_score",
            "x_basis_eu_weather_stress",
            "eu_wasde_balance_score",
            "x_basis_eu_wasde_balance",
        ],
    )
    return {
        "base": base,
        "base_plus_market_cross": [*base, *market_cross],
        "base_plus_season_cross": [*base, *season_cross],
        "base_plus_eu_cross": [*base, *eu_cross],
        "all_cross": [*base, *market_cross, *season_cross, *eu_cross],
    }


def _target_names(horizon: int) -> list[str]:
    return [
        f"y_rel_outperform_h{horizon}",
        f"y_rel_outperform_when_basis_extreme_h{horizon}",
        f"y_rel_large_outperform_h{horizon}",
        f"y_rel_large_underperform_h{horizon}",
    ]


def _oof(df: pd.DataFrame, target: str, features: list[str]) -> pd.DataFrame:
    work = df[["Date", "crop_year", "month", target, *features]].copy()
    for col in features:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{col}_lag1" for col in features]
    work = work[["Date", "crop_year", "month", target, *lag_cols]]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target, *lag_cols])
    rows = []
    years = sorted(work["crop_year"].unique())
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if (
            len(train) < _MIN_TRAIN
            or len(test) < _MIN_TEST
            or train[target].nunique() < 2
            or test[target].nunique() < 2
        ):
            continue
        model = LogisticRegression(max_iter=600, class_weight="balanced", solver="liblinear")
        model.fit(train[lag_cols], train[target])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        out = test[["Date", "crop_year", "month", target]].copy()
        out = out.rename(columns={target: "y_true"})
        out["prob"] = prob
        out["y_pred"] = (prob >= 0.5).astype(float)
        out["confidence"] = np.abs(prob - 0.5)
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _metrics(pred: pd.DataFrame, *, target: str, horizon: int, feature_set: str, n_features: int) -> dict:
    if len(pred) < _MIN_EVAL or pred["y_true"].nunique() < 2:
        return {
            "target": target,
            "horizon": int(horizon),
            "feature_set": feature_set,
            "n_features": int(n_features),
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
        "target": target,
        "horizon": int(horizon),
        "feature_set": feature_set,
        "n_features": int(n_features),
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


def _add_deltas(rows: list[dict]) -> list[dict]:
    base_by_target = {
        (row["target"], row["horizon"]): row
        for row in rows
        if row.get("status") == "OK" and row["feature_set"] == "base"
    }
    out = []
    for row in rows:
        enriched = dict(row)
        base = base_by_target.get((row["target"], row["horizon"]))
        if row.get("status") == "OK" and base:
            enriched["delta_auc_vs_base"] = float(row["auc"] - base["auc"])
            enriched["delta_balanced_accuracy_vs_base"] = float(row["balanced_accuracy"] - base["balanced_accuracy"])
            enriched["delta_top20_da_vs_base"] = float(row["top20_da"] - base["top20_da"])
        out.append(enriched)
    return out


@lru_cache(maxsize=1)
def build_cross_data_interactions_v5() -> dict:
    df = build_interaction_frame()
    feature_sets = _feature_sets(df)
    rows = []
    for horizon in _HORIZONS:
        for target in _target_names(horizon):
            for name, features in feature_sets.items():
                pred = _oof(df, target, features)
                rows.append(
                    _metrics(
                        pred,
                        target=target,
                        horizon=horizon,
                        feature_set=name,
                        n_features=len(features),
                    )
                )
    rows = _add_deltas(rows)
    ok = [row for row in rows if row.get("status") == "OK"]
    non_base = [row for row in ok if row["feature_set"] != "base"]
    best_delta = max(non_base, key=lambda row: row.get("delta_auc_vs_base", -np.inf), default={})
    best_overall = max(ok, key=lambda row: (row["auc"], row["balanced_accuracy"]), default={})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Cross-data interactions for EMA premium and alternative relative targets.",
        "feature_sets": dict(feature_sets),
        "results": rows,
        "key_findings": {
            "n_results": int(len(rows)),
            "n_ok": int(len(ok)),
            "best_overall_target": best_overall.get("target"),
            "best_overall_feature_set": best_overall.get("feature_set"),
            "best_overall_auc": best_overall.get("auc"),
            "best_overall_balanced_accuracy": best_overall.get("balanced_accuracy"),
            "best_delta_target": best_delta.get("target"),
            "best_delta_feature_set": best_delta.get("feature_set"),
            "best_delta_auc_vs_base": best_delta.get("delta_auc_vs_base"),
            "best_delta_balanced_accuracy_vs_base": best_delta.get("delta_balanced_accuracy_vs_base"),
            "interpretation": _interpretation(best_delta),
        },
    }


def _interpretation(best_delta: dict) -> str:
    delta = best_delta.get("delta_auc_vs_base")
    if delta is None:
        return "No valid cross-data improvement was measured."
    if delta >= 0.02:
        return "Cross-data interactions add meaningful OOF value for at least one premium target."
    if delta > 0:
        return "Cross-data interactions add mild value; keep only if stable in later tests."
    return "Cross-data interactions do not improve the base premium model in this run."


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
        "# EMA CROSS DATA INTERACTIONS V5",
        "",
        "> Test OOF des croisements basis x marche, saison, meteo EU et WASDE quand les colonnes existent.",
        "",
        "## Verdict",
        "",
        f"- Meilleur overall : `{key.get('best_overall_target')}` / `{key.get('best_overall_feature_set')}`",
        f"- AUC overall : {_fmt(key.get('best_overall_auc'))}",
        f"- Balanced accuracy overall : {_fmt(key.get('best_overall_balanced_accuracy'))}",
        f"- Meilleur delta : `{key.get('best_delta_target')}` / `{key.get('best_delta_feature_set')}`",
        f"- Delta AUC vs base : {_fmt(key.get('best_delta_auc_vs_base'))}",
        f"- Delta balanced accuracy vs base : {_fmt(key.get('best_delta_balanced_accuracy_vs_base'))}",
        f"- Lecture : {key['interpretation']}",
        "",
        "## Feature sets",
        "",
    ]
    for name, cols in data["feature_sets"].items():
        lines.append(f"- `{name}` : {len(cols)} features")
    lines += [
        "",
        "## Resultats",
        "",
        "| Target | H | Set | n | AUC | dAUC | Bal. acc | dBal | Top20 |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| `{row['target']}` | {row['horizon']} | `{row['feature_set']}` | {row.get('n', 0)} | "
            f"{_fmt(row.get('auc'))} | {_fmt(row.get('delta_auc_vs_base'))} | "
            f"{_fmt(row.get('balanced_accuracy'))} | {_fmt(row.get('delta_balanced_accuracy_vs_base'))} | "
            f"{_fmt(row.get('top20_da'))} |"
        )
    lines += [
        "",
        "## Limites",
        "",
        "- Source EMA proxy.",
        "- Les croisements sont des hypotheses economiques, pas des preuves causales.",
        "- Les colonnes EU/WASDE ne sont utilisees que si elles existent dans le master features.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_cross_data_interactions_v5(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_cross_data_interactions_v5()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_cross_data_interactions_v5()
    print(f"EMA cross-data interactions V5 saved -> {out}")

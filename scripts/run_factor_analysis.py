#!/usr/bin/env python3
"""Generate factors.parquet and docs/FACTOR_ANALYSIS_REPORT.md."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.features import build_factors, save_factors
from mais.paths import FEATURES_PARQUET, PROCESSED_DIR, TARGETS_PARQUET


HORIZONS = [5, 10, 20, 30]
MAIN_PROTOCOL = "rolling_expanding_6m"


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    y = y_true.astype(float).values
    pred = np.asarray(y_pred, dtype=float)
    mse = mean_squared_error(y, pred)
    return {
        "rmse": float(np.sqrt(mse)),
        "mae": float(mean_absolute_error(y, pred)),
        "r2": float(r2_score(y, pred)),
        "da": float(np.mean(np.sign(pred) == np.sign(y))),
        "n": int(len(y)),
    }


def _temporal_splits(df: pd.DataFrame, protocol: str) -> list[tuple[str, np.ndarray, np.ndarray]]:
    n = len(df)
    if n < 500:
        cut = max(50, int(0.8 * n))
        return [("holdout_20", np.arange(0, cut), np.arange(cut, n))]

    if protocol == "holdout_20":
        cut = int(0.8 * n)
        return [("holdout_20", np.arange(0, cut), np.arange(cut, n))]

    if protocol == "rolling_expanding_6m":
        initial = int(0.60 * n)
        test_size = 126
        step = 126
        splits = []
        start = initial
        i = 1
        while start < n:
            end = min(start + test_size, n)
            if end - start >= 40:
                splits.append((f"roll_{i:02d}", np.arange(0, start), np.arange(start, end)))
            start += step
            i += 1
        return splits

    raise ValueError(f"Unknown temporal protocol: {protocol}")


def _clean_matrix(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    X_train = train[cols].replace([np.inf, -np.inf], np.nan)
    X_test = test[cols].replace([np.inf, -np.inf], np.nan)
    med = X_train.median(numeric_only=True)
    X_train = X_train.fillna(med).fillna(0.0)
    X_test = X_test.fillna(med).fillna(0.0)
    return X_train, X_test


def _fit_ridge(
    train: pd.DataFrame,
    test: pd.DataFrame,
    cols: list[str],
    ycol: str,
) -> tuple[np.ndarray, np.ndarray]:
    X_train, X_test = _clean_matrix(train, test, cols)
    model = Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
    model.fit(X_train.values, train[ycol].astype(float).values)
    return model.predict(X_test.values), model.named_steps["ridge"].coef_


def _evaluate_protocol(
    work: pd.DataFrame,
    raw_cols: list[str],
    factor_cols: list[str],
    ycol: str,
    protocol: str,
) -> dict[str, Any]:
    splits = _temporal_splits(work, protocol)
    collected: dict[str, list[pd.DataFrame]] = {
        "baseline_zero_return": [],
        "raw_features_ridge": [],
        "factor_model_ridge": [],
    }

    split_meta: list[dict[str, Any]] = []
    for split_name, train_idx, test_idx in splits:
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        if train[ycol].notna().sum() < 250 or test[ycol].notna().sum() < 20:
            continue

        y_test = test[ycol].astype(float)
        dates = test["Date"].values
        split_meta.append(
            {
                "split": split_name,
                "train_start": str(pd.to_datetime(train["Date"]).min().date()),
                "train_end": str(pd.to_datetime(train["Date"]).max().date()),
                "test_start": str(pd.to_datetime(test["Date"]).min().date()),
                "test_end": str(pd.to_datetime(test["Date"]).max().date()),
                "test_rows": int(len(test)),
            }
        )

        baseline = np.zeros(len(test))
        pred_raw, _ = _fit_ridge(train, test, raw_cols, ycol)
        pred_fac, _ = _fit_ridge(train, test, factor_cols, ycol)

        for model_name, pred in [
            ("baseline_zero_return", baseline),
            ("raw_features_ridge", pred_raw),
            ("factor_model_ridge", pred_fac),
        ]:
            collected[model_name].append(
                pd.DataFrame(
                    {
                        "Date": dates,
                        "split": split_name,
                        "y_true": y_test.values,
                        "y_pred": pred,
                    }
                )
            )

    metrics: dict[str, dict[str, float]] = {}
    for model_name, frames in collected.items():
        if not frames:
            metrics[model_name] = {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "da": np.nan, "n": 0}
            continue
        pred_df = pd.concat(frames, ignore_index=True)
        metrics[model_name] = _metrics(pred_df["y_true"], pred_df["y_pred"].values)

    return {
        "metrics": metrics,
        "splits": split_meta,
        "n_splits": len(split_meta),
        "test_start": split_meta[0]["test_start"] if split_meta else None,
        "test_end": split_meta[-1]["test_end"] if split_meta else None,
    }


def _coef_importance(
    work: pd.DataFrame,
    cols: list[str],
    ycol: str,
) -> dict[str, float]:
    _, train_idx, test_idx = _temporal_splits(work, "holdout_20")[0]
    train = work.iloc[train_idx].copy()
    test = work.iloc[test_idx].copy()
    _, coef = _fit_ridge(train, test, cols, ycol)
    return {c: abs(float(v)) for c, v in zip(cols, coef)}


def _build_family_map(raw_features: pd.DataFrame) -> dict[str, str]:
    from mais.features.factors import _family_of

    return {c: _family_of(c) for c in raw_features.columns if c != "Date"}


def _share_by_family(values: dict[str, float], family_map: dict[str, str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for col, value in values.items():
        fam = family_map.get(col, "others")
        out[fam] = out.get(fam, 0.0) + abs(float(value))
    total = sum(out.values()) or 1.0
    return {k: v / total for k, v in sorted(out.items(), key=lambda kv: kv[1], reverse=True)}


def _wasde_surprise_model_r2(work: pd.DataFrame, raw_cols: list[str], ycol: str) -> float:
    cols = [c for c in raw_cols if c.startswith("wasde_") and "surprise" in c]
    if not cols:
        return float("nan")
    d = work[["Date", ycol] + cols].dropna(subset=[ycol]).copy()
    if len(d) < 500:
        return float("nan")
    result = _evaluate_custom_feature_set(d, cols, ycol, MAIN_PROTOCOL)
    return float(result.get("r2", np.nan))


def _evaluate_custom_feature_set(
    work: pd.DataFrame,
    cols: list[str],
    ycol: str,
    protocol: str,
) -> dict[str, float]:
    preds: list[pd.DataFrame] = []
    for split_name, train_idx, test_idx in _temporal_splits(work, protocol):
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        if train[ycol].notna().sum() < 250 or test[ycol].notna().sum() < 20:
            continue
        pred, _ = _fit_ridge(train, test, cols, ycol)
        preds.append(pd.DataFrame({"y_true": test[ycol].values, "y_pred": pred, "split": split_name}))
    if not preds:
        return {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "da": np.nan, "n": 0}
    pred_df = pd.concat(preds, ignore_index=True)
    return _metrics(pred_df["y_true"], pred_df["y_pred"].values)


def _summer_weather_effect(work: pd.DataFrame, factor_cols: list[str], ycol: str) -> dict[str, float]:
    wcols = [c for c in factor_cols if "weather" in c]
    if not wcols:
        return {"summer_abs_corr_mean": np.nan, "non_summer_abs_corr_mean": np.nan}
    month = pd.to_datetime(work["Date"]).dt.month
    is_summer = month.isin([6, 7, 8])
    cors_s: list[float] = []
    cors_n: list[float] = []
    for c in wcols:
        cs = work.loc[is_summer, c].corr(work.loc[is_summer, ycol])
        cn = work.loc[~is_summer, c].corr(work.loc[~is_summer, ycol])
        if pd.notna(cs):
            cors_s.append(abs(float(cs)))
        if pd.notna(cn):
            cors_n.append(abs(float(cn)))
    return {
        "summer_abs_corr_mean": float(np.mean(cors_s)) if cors_s else float("nan"),
        "non_summer_abs_corr_mean": float(np.mean(cors_n)) if cors_n else float("nan"),
    }


def _factor_vs_raw_sentence(h: int, rolling: dict[str, dict[str, float]]) -> str:
    b = rolling["baseline_zero_return"]
    r = rolling["raw_features_ridge"]
    f = rolling["factor_model_ridge"]
    rmse_delta_raw = (f["rmse"] / r["rmse"] - 1.0) * 100 if r["rmse"] else np.nan
    rmse_delta_base = (f["rmse"] / b["rmse"] - 1.0) * 100 if b["rmse"] else np.nan
    da_delta_raw = f["da"] - r["da"]
    return (
        f"Sur J+{h}, le modèle factoriel est {rmse_delta_raw:+.1f}% en RMSE vs features brutes "
        f"et {rmse_delta_base:+.1f}% vs zéro-retour; son hit-rate directionnel est "
        f"{da_delta_raw:+.3f} vs brut."
    )


def _economic_reading(
    h: int,
    comparison: dict[str, Any],
    family_importance: dict[str, float],
    top_factors: list[tuple[str, float]],
    weather: dict[str, float],
    wasde_r2: float,
) -> list[str]:
    rolling = comparison[h][MAIN_PROTOCOL]["metrics"]
    top_fam = list(family_importance.items())[:3]
    top_fac = ", ".join(f"`{name}`" for name, _ in top_factors[:3])
    fam_txt = ", ".join(f"{fam} ({share:.0%})" for fam, share in top_fam)
    ws = weather.get("summer_abs_corr_mean", np.nan)
    wn = weather.get("non_summer_abs_corr_mean", np.nan)
    weather_txt = (
        "davantage concentrée en été"
        if pd.notna(ws) and pd.notna(wn) and ws > wn
        else "faiblement concentrée sur l'été"
    )
    return [
        _factor_vs_raw_sentence(h, rolling),
        f"Lecture économique dominante: {fam_txt}. Les facteurs les plus actifs sont {top_fac}.",
        (
            f"La contribution météo est {weather_txt} "
            f"(corrélation absolue moyenne été {ws:.3f} vs hors été {wn:.3f})."
        ),
        f"Le bloc WASDE-surprises seul a un R2 rolling de {wasde_r2:.3f}.",
    ]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if pd.isna(obj):
        return None
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run() -> None:
    if not FEATURES_PARQUET.exists() or not TARGETS_PARQUET.exists():
        raise FileNotFoundError("Need features.parquet and targets.parquet first.")

    features = pd.read_parquet(FEATURES_PARQUET)
    targets = pd.read_parquet(TARGETS_PARQUET)

    factor_result = build_factors(features, targets)
    factors_path, factors_meta_path = save_factors(factor_result)
    factors = factor_result.factors
    meta = factor_result.metadata

    df = features.merge(factors, on="Date", how="inner").merge(targets, on="Date", how="inner")
    df = df.sort_values("Date").reset_index(drop=True)

    raw_cols = [c for c in features.columns if c != "Date" and pd.api.types.is_numeric_dtype(features[c])]
    factor_cols = [c for c in factors.columns if c != "Date" and pd.api.types.is_numeric_dtype(factors[c])]
    family_map = _build_family_map(features)
    factor_family = meta.get("factor_family", {})

    comparison: dict[int, dict[str, Any]] = {}
    family_importance: dict[int, dict[str, float]] = {}
    factor_family_importance: dict[int, dict[str, float]] = {}
    top_factors_by_h: dict[int, list[tuple[str, float]]] = {}
    summer_weather_effect: dict[int, dict[str, float]] = {}
    wasde_surprise_r2: dict[int, float] = {}

    for h in HORIZONS:
        ycol = f"y_logret_h{h}"
        if ycol not in df.columns:
            continue
        work = df[["Date"] + raw_cols + factor_cols + [ycol]].dropna(subset=[ycol]).copy()
        comparison[h] = {}
        for protocol in ["holdout_20", MAIN_PROTOCOL]:
            comparison[h][protocol] = _evaluate_protocol(work, raw_cols, factor_cols, ycol, protocol)

        raw_coef = _coef_importance(work, raw_cols, ycol)
        fac_coef = _coef_importance(work, factor_cols, ycol)
        family_importance[h] = _share_by_family(raw_coef, family_map)
        factor_family_importance[h] = _share_by_family(fac_coef, factor_family)
        top_factors_by_h[h] = sorted(fac_coef.items(), key=lambda kv: kv[1], reverse=True)[:12]
        summer_weather_effect[h] = _summer_weather_effect(work, factor_cols, ycol)
        wasde_surprise_r2[h] = _wasde_surprise_model_r2(work, raw_cols, ycol)

    report_path = Path("docs/FACTOR_ANALYSIS_REPORT.md")
    lines: list[str] = []
    lines.append("# Rapport d'analyse factorielle")
    lines.append("")
    lines.append(f"- Généré le: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`")
    lines.append(f"- Features source: `{FEATURES_PARQUET}`")
    lines.append(f"- Facteurs: `{factors_path}`")
    lines.append(f"- Métadonnées: `{factors_meta_path}`")
    lines.append("")

    lines.append("## 1) Synthèse")
    lines.append("")
    lines.append(
        f"- Univers brut: **{meta['n_input_features']}** features, dont "
        f"**{meta['n_candidate_features']}** candidates avec couverture suffisante."
    )
    lines.append(
        f"- Vue factorielle: **{meta['n_factor_columns']}** facteurs synthétiques "
        f"construits depuis **{meta['n_selected_components']}** composants économiques."
    )
    lines.append(
        "- Les facteurs sont construits sans utiliser les targets; les targets servent seulement "
        "à l'évaluation temporelle et aux diagnostics."
    )
    lines.append("")

    lines.append("## 2) Familles économiques")
    lines.append("")
    lines.append("| Famille | Features brutes | Composants utilisés | Facteurs | Variables laissées hors recettes |")
    lines.append("|---|---:|---:|---:|---:|")
    fams = meta["families"]
    selected = meta["selected_by_family"]
    unused = meta["unused_by_family"]
    for fam in fams:
        n_factors = sum(1 for f in factor_cols if factor_family.get(f) == fam)
        lines.append(
            f"| `{fam}` | {len(fams[fam])} | {len(selected.get(fam, []))} | "
            f"{n_factors} | {len(unused.get(fam, []))} |"
        )
    lines.append("")

    lines.append("## 3) Définition des facteurs")
    lines.append("")
    lines.append("| Facteur | Famille | Composants | Lecture économique |")
    lines.append("|---|---|---:|---|")
    descriptions = meta.get("factor_descriptions", {})
    components = meta.get("factor_components", {})
    for fac in factor_cols:
        fam = factor_family.get(fac, "others")
        desc = descriptions.get(fac, "")
        lines.append(f"| `{fac}` | `{fam}` | {len(components.get(fac, {}))} | {desc} |")
    lines.append("")

    lines.append("## 4) Protocole de comparaison")
    lines.append("")
    lines.append("- Modèles comparés: `baseline_zero_return`, `raw_features_ridge`, `factor_model_ridge`.")
    lines.append("- Même cible, mêmes dates et mêmes splits pour les trois modèles.")
    lines.append("- Prétraitement: médiane apprise sur train uniquement, `StandardScaler` et `Ridge(alpha=1)`.")
    lines.append("- `holdout_20`: dernier 20% de l'historique en test.")
    lines.append("- `rolling_expanding_6m`: train expanding, fenêtres test d'environ 6 mois.")
    lines.append("")

    lines.append("## 5) Résultats par horizon")
    lines.append("")
    lines.append("| Horizon | Protocole | Modèle | RMSE | MAE | R2 | DA | N test |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|")
    for h in HORIZONS:
        if h not in comparison:
            continue
        for protocol in ["holdout_20", MAIN_PROTOCOL]:
            metrics = comparison[h][protocol]["metrics"]
            for model_name, m in metrics.items():
                lines.append(
                    f"| J+{h} | `{protocol}` | `{model_name}` | {m['rmse']:.5f} | "
                    f"{m['mae']:.5f} | {m['r2']:.5f} | {m['da']:.3f} | {int(m['n'])} |"
                )
    lines.append("")

    lines.append("## 6) Robustesse économique")
    lines.append("")
    lines.append("| Horizon | Splits rolling | Fenêtre test rolling | RMSE facteur vs brut | DA facteur vs brut | RMSE facteur vs naïf |")
    lines.append("|---:|---:|---|---:|---:|---:|")
    for h in HORIZONS:
        if h not in comparison:
            continue
        roll = comparison[h][MAIN_PROTOCOL]
        m = roll["metrics"]
        raw = m["raw_features_ridge"]
        fac = m["factor_model_ridge"]
        base = m["baseline_zero_return"]
        rmse_vs_raw = (fac["rmse"] / raw["rmse"] - 1.0) if raw["rmse"] else np.nan
        rmse_vs_base = (fac["rmse"] / base["rmse"] - 1.0) if base["rmse"] else np.nan
        da_vs_raw = fac["da"] - raw["da"]
        period = f"{roll['test_start']} -> {roll['test_end']}"
        lines.append(
            f"| J+{h} | {roll['n_splits']} | {period} | {rmse_vs_raw:+.1%} | "
            f"{da_vs_raw:+.3f} | {rmse_vs_base:+.1%} |"
        )
    lines.append("")
    lines.append(
        "Lecture: la baseline zéro-retour reste dure à battre en RMSE sur des rendements courts, "
        "ce qui signale une espérance de retour faible et bruitée. L'intérêt des facteurs se juge "
        "donc aussi sur la stabilité, le hit-rate directionnel et la lisibilité économique."
    )
    lines.append("")

    lines.append("## 7) Importance par famille")
    lines.append("")
    for h in HORIZONS:
        if h not in family_importance:
            continue
        lines.append(f"### J+{h}")
        lines.append("")
        lines.append("| Famille brute | Part coefficient Ridge |")
        lines.append("|---|---:|")
        for fam, score in family_importance[h].items():
            lines.append(f"| `{fam}` | {score:.3f} |")
        lines.append("")
        lines.append("| Famille factorielle | Part coefficient Ridge |")
        lines.append("|---|---:|")
        for fam, score in factor_family_importance[h].items():
            lines.append(f"| `{fam}` | {score:.3f} |")
        lines.append("")

    lines.append("## 8) Lecture par horizon")
    lines.append("")
    for h in HORIZONS:
        if h not in comparison:
            continue
        lines.append(f"### J+{h}")
        lines.append("")
        for sentence in _economic_reading(
            h,
            comparison,
            family_importance[h],
            top_factors_by_h[h],
            summer_weather_effect[h],
            wasde_surprise_r2[h],
        ):
            lines.append(f"- {sentence}")
        lines.append("")

    lines.append("## 9) Facteurs dominants")
    lines.append("")
    for h in HORIZONS:
        if h not in top_factors_by_h:
            continue
        lines.append(f"### J+{h}")
        lines.append("")
        lines.append("| Facteur | Coefficient absolu standardisé |")
        lines.append("|---|---:|")
        for fac, score in top_factors_by_h[h][:10]:
            lines.append(f"| `{fac}` | {score:.5f} |")
        lines.append("")

    lines.append("## 10) Conclusion et prochaine étape")
    lines.append("")
    lines.append(
        f"- La vue factorielle est maintenant plus petite, stable et lisible que les "
        f"{meta['n_input_features']} features brutes."
    )
    lines.append("- À ce stade, les facteurs ne doivent pas être jugés comme une promesse de RMSE: ils servent surtout à expliquer les familles de risque qui déplacent le prix.")
    lines.append("- Prochaine expérimentation incrémentale: ajouter une seule source prioritaire (`EIA ethanol`), relancer ce rapport, mesurer le gain marginal, puis seulement ensuite tester `CFTC COT` et `USDA Crop Progress`.")
    lines.append("- Après chaque source: relancer `features`, `targets`, `audit`, `train`, `stack`, `backtest`, `validate_outputs.py`, puis ce rapport.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "comparison": comparison,
        "family_importance": family_importance,
        "factor_family_importance": factor_family_importance,
        "top_factors_by_horizon": top_factors_by_h,
        "summer_weather_effect": summer_weather_effect,
        "wasde_surprise_r2": wasde_surprise_r2,
        "factors_shape": [int(factors.shape[0]), int(factors.shape[1])],
        "factor_columns": factor_cols,
    }
    (PROCESSED_DIR / "factor_analysis_summary.json").write_text(
        json.dumps(summary, indent=2, default=_json_default),
        encoding="utf-8",
    )

    print(f"Wrote {factors_path}")
    print(f"Wrote {factors_meta_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    run()

"""Controlled oracle analysis for maize direction research.

Oracle variables intentionally look into the future. They are only written to
research artefacts and must never enter production features or factors.
"""

from __future__ import annotations

import re
from contextlib import suppress
from dataclasses import dataclass
from datetime import date
from typing import Any

import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROCESSED_DIR, PROJECT_ROOT, TARGETS_PARQUET
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.oracle_analysis")

STUDY_DIR = ARTEFACTS_DIR / "professional_study"
ORACLE_ANALYSIS_PARQUET = STUDY_DIR / "oracle_analysis.parquet"
REPORT_PATH = PROJECT_ROOT / "docs" / "PROFESSIONAL_STUDY_REPORT.md"
EXPERIMENT_INDEX = PROJECT_ROOT / "notebooks" / "corn_study" / "EXPERIMENT_INDEX.md"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "corn_study" / "experiments" / "oracle_analysis.ipynb"
NOTEBOOK_EXPORT = PROJECT_ROOT / "notebooks" / "corn_study" / "exports" / "oracle_analysis.html"

OOT_CUTOFF = pd.Timestamp("2022-12-31")
TARGET_COL = "y_up_h20"
HORIZON = 20
MIN_TEST_OBS = 50


@dataclass(frozen=True)
class OracleSpec:
    name: str
    source: str
    economic_expectation: str


ORACLE_SPECS = [
    OracleSpec("oracle_weather_stress_h20", "future factor_weather_belt_stress", "positive stress should be bullish"),
    OracleSpec("oracle_heat_days_h20", "future wx_belt_heat_days_30", "more heat should be bullish"),
    OracleSpec("oracle_rain_deficit_h20", "future negative wx_belt_prcp_30_anom_z", "more deficit should be bullish"),
    OracleSpec("oracle_cot_mm_net_h10", "future cot_mm_net / cot_mm_net_pct_oi", "more managed-money net long should be bullish"),
    OracleSpec("oracle_condition_change_h20", "future crop condition change", "better condition should be bearish"),
    OracleSpec("oracle_drought_h20", "future drought_composite", "more drought should be bullish"),
    OracleSpec("oracle_realized_vol_h20", "target realized_vol_h20", "more volatility is directional only if asymmetric"),
    OracleSpec("oracle_wasde_ending_stocks_surprise", "next WASDE ending stocks via bfill", "higher stocks should be bearish"),
]


def build_oracle_variables(
    features: pd.DataFrame,
    factors: pd.DataFrame,
    targets: pd.DataFrame,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """Create future-aware variables in an isolated DataFrame."""
    feat = _normalize(features)
    fac = _normalize(factors)
    tgt = _normalize(targets)
    df = feat.merge(fac, on="Date", how="left").merge(tgt, on="Date", how="left")
    out = pd.DataFrame({"Date": df["Date"]})

    if "factor_weather_belt_stress" in df.columns:
        out["oracle_weather_stress_h20"] = df["factor_weather_belt_stress"].shift(-horizon)
    if "wx_belt_heat_days_30" in df.columns:
        out["oracle_heat_days_h20"] = df["wx_belt_heat_days_30"].shift(-horizon)
    if "wx_belt_prcp_30_anom_z" in df.columns:
        out["oracle_rain_deficit_h20"] = -df["wx_belt_prcp_30_anom_z"].shift(-horizon)
    elif "wx_belt_prcp_mm_anom_z" in df.columns:
        out["oracle_rain_deficit_h20"] = -df["wx_belt_prcp_mm_anom_z"].shift(-horizon)

    if "cot_mm_net_pct_oi" in df.columns:
        out["oracle_cot_mm_net_h10"] = df["cot_mm_net_pct_oi"].shift(-10)
    elif "cot_mm_net" in df.columns:
        out["oracle_cot_mm_net_h10"] = _expanding_z(df["cot_mm_net"]).shift(-10)

    if "condition_gd_ex_pct" in df.columns:
        out["oracle_condition_change_h20"] = df["condition_gd_ex_pct"].shift(-horizon) - df["condition_gd_ex_pct"]
    if "drought_composite" in df.columns:
        out["oracle_drought_h20"] = df["drought_composite"].shift(-horizon)
    if "realized_vol_h20" in df.columns:
        out["oracle_realized_vol_h20"] = df["realized_vol_h20"]
    if "wasde_ending_stocks" in df.columns:
        out["oracle_wasde_ending_stocks_surprise"] = _next_wasde_surprise(df)

    oracle_cols = [c for c in out.columns if c.startswith("oracle_")]
    out.loc[out.index[-horizon:], oracle_cols] = np.nan
    _assert_oracle_isolated(out, feat, fac)
    log.info("oracle_variables_built", rows=len(out), n_oracle=len(oracle_cols), cols=oracle_cols)
    return out


def run_oracle_analysis(
    features: pd.DataFrame | None = None,
    factors: pd.DataFrame | None = None,
    targets: pd.DataFrame | None = None,
    *,
    target_col: str = TARGET_COL,
    horizon: int = HORIZON,
    save_output: bool = True,
) -> pd.DataFrame:
    """Benchmark each oracle variable against the factor-only baseline."""
    if features is None:
        features = pd.read_parquet(FEATURES_PARQUET)
    if factors is None:
        factors = pd.read_parquet(PROCESSED_DIR / "factors.parquet")
    if targets is None:
        targets = pd.read_parquet(TARGETS_PARQUET)

    features = _normalize(features)
    factors = _normalize(factors)
    targets = _normalize(targets)
    if target_col not in targets.columns:
        raise KeyError(f"Missing target column: {target_col}")

    oracle_df = build_oracle_variables(features, factors, targets, horizon=horizon)
    factor_cols = [c for c in factors.columns if c != "Date" and pd.api.types.is_numeric_dtype(factors[c])]
    data = (
        factors.merge(targets[["Date", target_col]], on="Date", how="inner")
        .merge(oracle_df, on="Date", how="left")
        .sort_values("Date")
        .reset_index(drop=True)
    )
    data = data[data["Date"] <= OOT_CUTOFF].reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    for spec in ORACLE_SPECS:
        if spec.name not in data.columns:
            rows.append(_missing_row(spec, target_col, "source column unavailable"))
            continue
        work = data[["Date", target_col, *factor_cols, spec.name]].dropna(subset=[target_col, spec.name])
        if len(work) < 800 or int(work[target_col].nunique()) < 2:
            rows.append(_missing_row(spec, target_col, "insufficient observations"))
            continue
        metrics = _benchmark_one_oracle(work, factor_cols, spec.name, target_col)
        rows.append({
            "oracle_var": spec.name,
            "target": target_col,
            "da_without": metrics["da_without"],
            "da_with": metrics["da_with"],
            "delta_da": metrics["delta_da"],
            "auc_without": metrics["auc_without"],
            "auc_with": metrics["auc_with"],
            "brier_without": metrics["brier_without"],
            "brier_with": metrics["brier_with"],
            "n_obs": int(len(work)),
            "n_test": metrics["n_test"],
            "n_folds": metrics["n_folds"],
            "priority": _priority(metrics["delta_da"]),
            "oracle_coef": metrics["oracle_coef"],
            "economic_expectation": spec.economic_expectation,
            "economic_coherence": _economic_coherence(spec.name, metrics["oracle_coef"]),
            "source": spec.source,
            "status": "ok",
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNAVAILABLE": 3}
        result["_priority_order"] = result["priority"].map(order).fillna(9)
        result = result.sort_values(["_priority_order", "delta_da", "n_obs"], ascending=[True, False, False])
        result = result.drop(columns=["_priority_order"]).reset_index(drop=True)

    if save_output:
        STUDY_DIR.mkdir(parents=True, exist_ok=True)
        write_parquet(result, ORACLE_ANALYSIS_PARQUET)
        _update_report(result)
        _update_experiment_index(result)
        _write_notebook(result)

    log.info("oracle_analysis_done", rows=len(result), target=target_col)
    return result


def _benchmark_one_oracle(
    work: pd.DataFrame,
    factor_cols: list[str],
    oracle_col: str,
    target_col: str,
) -> dict[str, Any]:
    splits = _walk_splits(len(work), horizon=HORIZON)
    baseline_frames = []
    oracle_frames = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        train = work.iloc[train_idx]
        test = work.iloc[test_idx]
        pred_base, score_base, _ = _fit_predict(train, test, factor_cols, target_col)
        pred_oracle, score_oracle, coef = _fit_predict(train, test, [*factor_cols, oracle_col], target_col, oracle_col)
        baseline_frames.append(_fold_frame(test, fold, target_col, pred_base, score_base, coef=np.nan))
        oracle_frames.append(_fold_frame(test, fold, target_col, pred_oracle, score_oracle, coef=coef))

    base = pd.concat(baseline_frames, ignore_index=True)
    oracle = pd.concat(oracle_frames, ignore_index=True)
    mb = _classification_metrics(base["y_true"], base["y_pred"], base["y_score"])
    mo = _classification_metrics(oracle["y_true"], oracle["y_pred"], oracle["y_score"])
    coef_values = oracle["oracle_coef"].dropna()
    oracle_coef = float(coef_values.mean()) if len(coef_values) else np.nan
    return {
        "da_without": mb["da"],
        "da_with": mo["da"],
        "delta_da": mo["da"] - mb["da"],
        "auc_without": mb["auc"],
        "auc_with": mo["auc"],
        "brier_without": mb["brier"],
        "brier_with": mo["brier"],
        "n_test": int(len(oracle)),
        "n_folds": int(oracle["fold"].nunique()),
        "oracle_coef": oracle_coef,
    }


def _fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    cols: list[str],
    target_col: str,
    oracle_col: str | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    x_train = train[cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[cols].replace([np.inf, -np.inf], np.nan)
    y_train = train[target_col].astype(int).values
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, C=0.7, random_state=42)),
    ])
    pipe.fit(x_train, y_train)
    proba = pipe.predict_proba(x_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    coef = np.nan
    if oracle_col is not None:
        model = pipe.named_steps["model"]
        idx = cols.index(oracle_col)
        coef = float(model.coef_[0][idx])
    return pred, proba, coef


def _fold_frame(
    test: pd.DataFrame,
    fold: int,
    target_col: str,
    pred: np.ndarray,
    score: np.ndarray,
    coef: float,
) -> pd.DataFrame:
    return pd.DataFrame({
        "Date": test["Date"].values,
        "fold": fold,
        "y_true": test[target_col].astype(int).values,
        "y_pred": pred,
        "y_score": score,
        "oracle_coef": coef,
    })


def _classification_metrics(y_true: pd.Series, y_pred: pd.Series, y_score: pd.Series) -> dict[str, float]:
    y = y_true.astype(int).values
    pred = y_pred.astype(int).values
    score = np.clip(y_score.astype(float).values, 0.0, 1.0)
    out = {
        "da": float(accuracy_score(y, pred)),
        "brier": float(brier_score_loss(y, score)),
        "auc": np.nan,
    }
    with suppress(ValueError):
        out["auc"] = float(roc_auc_score(y, score))
    return out


def _walk_splits(n: int, horizon: int) -> list[tuple[np.ndarray, np.ndarray]]:
    start = int(n * 0.60)
    remaining = n - start
    test_size = max(80, remaining // 5)
    splits = []
    for i in range(5):
        test_start = start + i * test_size
        test_end = n if i == 4 else min(n, test_start + test_size)
        train_end = max(1, test_start - max(horizon, 10))
        if test_end - test_start >= MIN_TEST_OBS and train_end >= 500:
            splits.append((np.arange(0, train_end), np.arange(test_start, test_end)))
    if not splits:
        raise ValueError(f"no valid walk-forward split for n={n}")
    return splits


def _next_wasde_surprise(df: pd.DataFrame) -> pd.Series:
    daily = df[["Date", "wasde_ending_stocks"]].copy()
    daily = daily.dropna(subset=["wasde_ending_stocks"]).drop_duplicates("Date")
    # Reconstruct report points from changed values, then bfill to intentionally
    # represent knowledge of the next report. This bfill is oracle-only.
    changes = daily["wasde_ending_stocks"].ne(daily["wasde_ending_stocks"].shift(1))
    if "is_wasde_day" in df.columns:
        wasde_day = pd.to_numeric(df.loc[daily.index, "is_wasde_day"], errors="coerce").fillna(0).astype(bool)
        changes = changes | wasde_day.values
    monthly = daily.loc[changes, ["Date", "wasde_ending_stocks"]].set_index("Date")["wasde_ending_stocks"]
    daily_index = pd.DatetimeIndex(df["Date"])
    next_report = monthly.reindex(daily_index).bfill()
    current_report = monthly.reindex(daily_index).ffill()
    return pd.Series(next_report.values - current_report.values, index=df.index)


def _assert_oracle_isolated(oracle_df: pd.DataFrame, features: pd.DataFrame, factors: pd.DataFrame) -> None:
    oracle_cols = [c for c in oracle_df.columns if c.startswith("oracle_")]
    feature_cols = set(features.columns)
    factor_cols = set(factors.columns)
    contaminated = [c for c in oracle_cols if c in feature_cols or c in factor_cols]
    if contaminated:
        raise AssertionError(f"Oracle variable detected in production inputs: {contaminated}")


def _missing_row(spec: OracleSpec, target_col: str, reason: str) -> dict[str, Any]:
    return {
        "oracle_var": spec.name,
        "target": target_col,
        "da_without": np.nan,
        "da_with": np.nan,
        "delta_da": np.nan,
        "auc_without": np.nan,
        "auc_with": np.nan,
        "brier_without": np.nan,
        "brier_with": np.nan,
        "n_obs": 0,
        "n_test": 0,
        "n_folds": 0,
        "priority": "UNAVAILABLE",
        "oracle_coef": np.nan,
        "economic_expectation": spec.economic_expectation,
        "economic_coherence": reason,
        "source": spec.source,
        "status": reason,
    }


def _priority(delta_da: float) -> str:
    if pd.isna(delta_da):
        return "UNAVAILABLE"
    if float(delta_da) > 0.03:
        return "HIGH"
    if float(delta_da) > 0.01:
        return "MEDIUM"
    return "LOW"


def _economic_coherence(oracle_var: str, coef: float) -> str:
    if pd.isna(coef):
        return "not estimated"
    positive_bullish = {
        "oracle_weather_stress_h20",
        "oracle_heat_days_h20",
        "oracle_rain_deficit_h20",
        "oracle_cot_mm_net_h10",
        "oracle_drought_h20",
    }
    negative_bullish = {
        "oracle_condition_change_h20",
        "oracle_wasde_ending_stocks_surprise",
    }
    if oracle_var in positive_bullish:
        return "coherent" if coef > 0 else "counterintuitive"
    if oracle_var in negative_bullish:
        return "coherent" if coef < 0 else "counterintuitive"
    return "directional sign not predefined"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"])
    return out.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def _expanding_z(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce").astype(float)
    mean = x.expanding(min_periods=252).mean().shift(1)
    sd = x.expanding(min_periods=252).std().shift(1)
    return ((x - mean) / sd.replace(0, np.nan)).clip(-5, 5)


def _update_report(result: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else "# Étude professionnelle du prix du maïs CBOT\n"
    marker = "\n## Oracle Analysis\n"
    if marker in text:
        text = text.split(marker)[0].rstrip()

    lines = [text.rstrip(), "", "## Oracle Analysis", ""]
    lines.append("Source : `artefacts/professional_study/oracle_analysis.parquet`.")
    lines.append("Protocole IND-03 : cible `y_up_h20`, dates <= 2022, variables futures volontairement connues.")
    lines.append("")
    ok = result[result["status"].eq("ok")].copy()
    high = ok[ok["priority"].eq("HIGH")]
    if high.empty:
        lines.append("Variables oracle prioritaires (delta DA > 3%) : aucune.")
    else:
        lines.append("Variables oracle prioritaires (delta DA > 3%) :")
        for i, (_, row) in enumerate(high.iterrows(), start=1):
            lines.append(
                f"{i}. `{row['oracle_var']}` : DA {row['da_without']:.3f} -> {row['da_with']:.3f} "
                f"(delta {row['delta_da']:+.3f}), cohérence `{row['economic_coherence']}`."
            )
    lines.append("")
    lines.append("| Variable oracle | DA sans | DA avec | Delta DA | AUC avec | Priorité | Cohérence |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    for _, row in ok.iterrows():
        lines.append(
            f"| `{row['oracle_var']}` | {_fmt(row['da_without'])} | {_fmt(row['da_with'])} | "
            f"{_fmt(row['delta_da'], signed=True)} | {_fmt(row['auc_with'])} | `{row['priority']}` | "
            f"`{row['economic_coherence']}` |"
        )
    lines.append("")
    lines.append("Conclusion : seules les variables `HIGH` justifient un sous-modèle prédictif prioritaire en IND-06.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_experiment_index(result: pd.DataFrame) -> None:
    EXPERIMENT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    text = EXPERIMENT_INDEX.read_text(encoding="utf-8") if EXPERIMENT_INDEX.exists() else ""
    if "IND-03 — Oracle analysis complète" in text:
        return
    exp_id = _next_exp_id(text)
    today = date.today().isoformat()
    high = result[result["priority"].eq("HIGH") & result["status"].eq("ok")]
    high_txt = ", ".join(f"`{v}`" for v in high["oracle_var"].tolist()) if not high.empty else "aucune variable HIGH"
    row = (
        f"| {exp_id} | {today} | `notebooks/corn_study/experiments/oracle_analysis.ipynb` | "
        "Les drivers futurs bornent le signal directionnel maximal. | "
        "Oracle variables futures + benchmark logistique walk-forward sur y_up_h20. | "
        f"Variables HIGH : {high_txt}. | Prioriser ces familles pour IND-06. | neutral |\n"
    )
    detail = f"""
---

## {exp_id} — IND-03 — Oracle analysis complète

**Date :** {today}
**Statut :** `neutral`

**Hypothèse :**
Les variables futures météo, WASDE, COT ou volatilité révèlent quels drivers méritent un sous-modèle prédictif.

**Méthode :**
Création de variables `oracle_*` isolées, WASDE futur via `bfill()` oracle-only, benchmark walk-forward pré-2023 sur `y_up_h20`.

**Résultat :**
Variables HIGH : {high_txt}. Résultats complets dans `artefacts/professional_study/oracle_analysis.parquet`.

**Décision :**
Utiliser les variables HIGH comme priorités de familles pour IND-06.
"""
    if "|---|---|---|---|---|---|---|---|" in text:
        text = text.replace("|---|---|---|---|---|---|---|---|\n", "|---|---|---|---|---|---|---|---|\n" + row, 1)
    else:
        text = text.rstrip() + "\n\n" + row
    EXPERIMENT_INDEX.write_text(text.rstrip() + "\n" + detail, encoding="utf-8")


def _write_notebook(result: pd.DataFrame) -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    table = _markdown_table(result)
    high = result[result["priority"].eq("HIGH") & result["status"].eq("ok")]
    high_lines = "\n".join(
        f"- `{row['oracle_var']}` : delta DA {_fmt(row['delta_da'], signed=True)}, cohérence `{row['economic_coherence']}`"
        for _, row in high.iterrows()
    ) or "- Aucune variable HIGH."

    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# IND-03 — Oracle analysis\n\nVariables futures volontairement connues, usage recherche uniquement."),
        nbf.v4.new_markdown_cell("## Variables prioritaires\n\n" + high_lines),
        nbf.v4.new_markdown_cell("## Résultats\n\n" + table),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "oracle = pd.read_parquet('../../../artefacts/professional_study/oracle_analysis.parquet')\n"
            "oracle"
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)
    try:
        from nbconvert import HTMLExporter

        body, _ = HTMLExporter().from_notebook_node(nb)
        NOTEBOOK_EXPORT.write_text(body, encoding="utf-8")
    except Exception as exc:
        log.warning("oracle_notebook_export_failed", error=str(exc))


def _markdown_table(df: pd.DataFrame) -> str:
    cols = ["oracle_var", "da_without", "da_with", "delta_da", "auc_with", "priority", "economic_coherence"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df[cols].iterrows():
        values = []
        for col in cols:
            val = row[col]
            if col == "delta_da":
                values.append(_fmt(val, signed=True))
            elif isinstance(val, float) or pd.isna(val):
                values.append(_fmt(val))
            else:
                values.append(str(val))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _fmt(value: Any, signed: bool = False) -> str:
    if pd.isna(value):
        return "NA"
    number = float(value)
    return f"{number:+.3f}" if signed else f"{number:.3f}"


def _next_exp_id(text: str) -> str:
    nums = [int(x) for x in re.findall(r"EXP-(\d+)", text)]
    return f"EXP-{(max(nums) + 1) if nums else 1:03d}"


def main() -> None:
    result = run_oracle_analysis()
    print(f"Wrote {ORACLE_ANALYSIS_PARQUET} rows={len(result)}")
    high = result[result["priority"].eq("HIGH") & result["status"].eq("ok")]
    if not high.empty:
        print("HIGH priority:", ", ".join(high["oracle_var"].tolist()))


if __name__ == "__main__":
    main()

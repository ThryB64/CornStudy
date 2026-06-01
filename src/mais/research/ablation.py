"""Family ablation and feature selection for the maize indicator."""

from __future__ import annotations

import re
from contextlib import suppress
from dataclasses import dataclass
from datetime import date
from typing import Any

import nbformat as nbf
import numpy as np
import pandas as pd
import yaml
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score

from mais.paths import ARTEFACTS_DIR, CONFIG_DIR, PROCESSED_DIR, PROJECT_ROOT, TARGETS_PARQUET
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.ablation")

STUDY_DIR = ARTEFACTS_DIR / "professional_study"
ABLATION_RESULTS_PARQUET = STUDY_DIR / "ablation_results.parquet"
FEATURE_SELECTION_PARQUET = STUDY_DIR / "feature_selection.parquet"
SHAP_IMPORTANCE_PARQUET = STUDY_DIR / "shap_importance.parquet"
REPORT_PATH = PROJECT_ROOT / "docs" / "PROFESSIONAL_STUDY_REPORT.md"
EXPERIMENT_INDEX = PROJECT_ROOT / "notebooks" / "corn_study" / "EXPERIMENT_INDEX.md"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "corn_study" / "main" / "07_ablation_feature_selection.ipynb"
NOTEBOOK_EXPORT = PROJECT_ROOT / "notebooks" / "corn_study" / "exports" / "07_ablation_feature_selection.html"

TARGET_COL = "y_down_gt_5pct_h20"
OOT_CUTOFF = pd.Timestamp("2022-12-31")
HORIZON = 20
DELTA_NEUTRAL_BAND = 0.001       # DA delta (kept for reference only)
DELTA_AUC_NEUTRAL_BAND = 0.005  # AUC delta — primary criterion (more robust for imbalanced targets)
PERIODS = [
    ("2010_2013", "2010-01-01", "2013-12-31"),
    ("2014_2017", "2014-01-01", "2017-12-31"),
    ("2018_2021", "2018-01-01", "2021-12-31"),
    ("2022_guarded", "2022-01-01", "2022-12-31"),
]


@dataclass(frozen=True)
class FamilyMeta:
    name: str
    factor_col: str
    shap_importance_avg: float | None


def run_ablation(target_col: str = TARGET_COL, save_output: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    factors = _normalize(pd.read_parquet(PROCESSED_DIR / "factors.parquet"))
    targets = _normalize(pd.read_parquet(TARGETS_PARQUET))
    families = _load_families()
    if target_col not in targets.columns:
        raise KeyError(f"Target not found: {target_col}")

    data = factors.merge(targets[["Date", target_col]], on="Date", how="inner")
    data = data[(data["Date"] <= OOT_CUTOFF) & data[target_col].notna()].reset_index(drop=True)
    factor_cols = [c for c in factors.columns if c != "Date" and pd.api.types.is_numeric_dtype(factors[c])]
    family_cols = {fam.name: [fam.factor_col] if fam.factor_col in factor_cols else [] for fam in families}

    full_metrics = _benchmark(data, factor_cols, target_col)
    vif_by_factor = _compute_vif(data, factor_cols)
    shap_by_family = _shap_by_family(families)

    rows = []
    for fam in families:
        cols = family_cols[fam.name]
        without_cols = [c for c in factor_cols if c not in cols]
        without = _benchmark(data, without_cols, target_col) if without_cols else _empty_metrics()
        only = _benchmark(data, cols, target_col) if cols else _empty_metrics()
        delta = full_metrics["da"] - without["da"] if pd.notna(without["da"]) else np.nan
        delta_auc = (
            full_metrics["auc"] - without["auc"]
            if pd.notna(without["auc"]) and pd.notna(full_metrics["auc"])
            else np.nan
        )
        vif = _family_vif(cols, vif_by_factor)
        rows.append({
            "family": fam.name,
            "factor_col": fam.factor_col,
            "n_factor_cols": len(cols),
            "n_obs": full_metrics["n_obs"],
            "n_test": full_metrics["n_test"],
            "da_full": full_metrics["da"],
            "da_without": without["da"],
            "delta": delta,
            "delta_auc": delta_auc,
            "da_only": only["da"],
            "auc_full": full_metrics["auc"],
            "auc_without": without["auc"],
            "auc_only": only["auc"],
            "brier_full": full_metrics["brier"],
            "brier_without": without["brier"],
            "brier_only": only["brier"],
            "vif_max": vif,
            "shap_avg": shap_by_family.get(fam.name, fam.shap_importance_avg),
            "recommendation": _recommendation(delta_auc, vif, len(cols)),
            "justification": _justification(delta_auc, vif, len(cols)),
            "is_robust": bool(full_metrics["n_test"] >= 100),
        })

    ablation = pd.DataFrame(rows).sort_values("delta_auc", ascending=False, na_position="last").reset_index(drop=True)
    selection = _build_feature_selection(ablation, data, family_cols, target_col)

    if save_output:
        STUDY_DIR.mkdir(parents=True, exist_ok=True)
        write_parquet(ablation, ABLATION_RESULTS_PARQUET)
        write_parquet(selection, FEATURE_SELECTION_PARQUET)
        _update_report(ablation, selection)
        _update_experiment_index(ablation)
        _write_notebook(ablation, selection)

    log.info("ablation_done", rows=len(ablation), target=target_col)
    return ablation, selection


def _load_families() -> list[FamilyMeta]:
    path = CONFIG_DIR / "factor_metadata.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = []
    for item in cfg.get("families", []):
        out.append(FamilyMeta(
            name=str(item["name"]),
            factor_col=str(item.get("factor_col", "")),
            shap_importance_avg=item.get("shap_importance_avg"),
        ))
    if not out:
        raise ValueError("No families found in config/factor_metadata.yaml")
    return out


def _benchmark(data: pd.DataFrame, cols: list[str], target_col: str) -> dict[str, float]:
    if not cols:
        return _empty_metrics()
    splits = _walk_splits(len(data), HORIZON)
    frames = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        train = data.iloc[train_idx]
        test = data.iloc[test_idx]
        pred, score = _fit_predict(train, test, cols, target_col)
        frames.append(pd.DataFrame({
            "fold": fold,
            "y_true": test[target_col].astype(int).values,
            "y_pred": pred,
            "y_score": score,
        }))
    oof = pd.concat(frames, ignore_index=True)
    y = oof["y_true"].astype(int)
    score = np.clip(oof["y_score"].astype(float), 0.0, 1.0)
    metrics = {
        "da": float(accuracy_score(y, oof["y_pred"].astype(int))),
        "auc": np.nan,
        "brier": float(brier_score_loss(y, score)),
        "n_obs": int(len(data)),
        "n_test": int(len(oof)),
        "n_folds": int(oof["fold"].nunique()),
    }
    with suppress(ValueError):
        metrics["auc"] = float(roc_auc_score(y, score))
    return metrics


def _fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    cols: list[str],
    target_col: str,
) -> tuple[np.ndarray, np.ndarray]:
    x_train = train[cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[cols].replace([np.inf, -np.inf], np.nan)
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train_arr = imputer.fit_transform(x_train)
    x_test_arr = imputer.transform(x_test)
    y_train = train[target_col].astype(int).values

    try:
        import lightgbm as lgb

        model = lgb.LGBMClassifier(
            n_estimators=90,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=40,
            lambda_l2=1.0,
            verbose=-1,
            random_state=42,
        )
    except ImportError:
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(
            n_estimators=60,
            max_depth=7,
            min_samples_leaf=30,
            random_state=42,
            n_jobs=-1,
        )

    model.fit(x_train_arr, y_train)
    proba = model.predict_proba(x_test_arr)[:, 1]
    return (proba >= 0.5).astype(int), proba


def _compute_vif(data: pd.DataFrame, factor_cols: list[str]) -> dict[str, float]:
    clean = data[factor_cols].replace([np.inf, -np.inf], np.nan)
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    arr = imputer.fit_transform(clean)
    arr = np.asarray(arr, dtype=float)
    out = {}
    with suppress(Exception):
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        for i, col in enumerate(factor_cols):
            val = float(variance_inflation_factor(arr, i))
            out[col] = val if np.isfinite(val) else np.inf
        return out

    corr = np.corrcoef(arr, rowvar=False)
    for i, col in enumerate(factor_cols):
        others = np.delete(corr[i], i)
        max_r2 = float(np.nanmax(others ** 2)) if len(others) else 0.0
        out[col] = 1.0 / max(1e-6, 1.0 - max_r2)
    return out


def _family_vif(cols: list[str], vif_by_factor: dict[str, float]) -> float:
    vals = [vif_by_factor.get(c, np.nan) for c in cols]
    vals = [v for v in vals if pd.notna(v)]
    return float(max(vals)) if vals else np.nan


def _shap_by_family(families: list[FamilyMeta]) -> dict[str, float]:
    fallback = {fam.name: fam.shap_importance_avg for fam in families if fam.shap_importance_avg is not None}
    if not SHAP_IMPORTANCE_PARQUET.exists():
        return fallback
    shap = pd.read_parquet(SHAP_IMPORTANCE_PARQUET)
    if shap.empty or "family" not in shap.columns:
        return fallback
    measured = shap.groupby("family")["coef_share"].mean().to_dict()
    out = dict(fallback)
    out.update({str(k): float(v) for k, v in measured.items()})
    return out


def _build_feature_selection(
    ablation: pd.DataFrame,
    data: pd.DataFrame,
    family_cols: dict[str, list[str]],
    target_col: str,
) -> pd.DataFrame:
    stability_rows = _stability_rows(ablation, data, family_cols, target_col)
    stability = pd.DataFrame(stability_rows)
    rows = []
    for _, row in ablation.iterrows():
        fam_stab = stability[stability["family"].eq(row["family"])]
        rows.append({
            "family": row["family"],
            "factor_col": row["factor_col"],
            "shap_avg": row["shap_avg"],
            "delta": row["delta"],
            "delta_auc": row["delta_auc"],
            "da_only": row["da_only"],
            "auc_only": row["auc_only"],
            "vif_max": row["vif_max"],
            "recommendation": row["recommendation"],
            "justification": row["justification"],
            "n_obs": row["n_obs"],
            "stability_min_da": float(fam_stab["da_only_period"].min()) if not fam_stab.empty else np.nan,
            "stability_max_da": float(fam_stab["da_only_period"].max()) if not fam_stab.empty else np.nan,
            "stability_periods_tested": int(fam_stab["period"].nunique()) if not fam_stab.empty else 0,
        })
    selection = pd.DataFrame(rows)
    return selection.sort_values(["recommendation", "delta_auc"], ascending=[True, False], na_position="last").reset_index(drop=True)


def _stability_rows(
    ablation: pd.DataFrame,
    data: pd.DataFrame,
    family_cols: dict[str, list[str]],
    target_col: str,
) -> list[dict[str, Any]]:
    top = ablation[ablation["n_factor_cols"] > 0].sort_values("delta_auc", ascending=False).head(3)
    rows = []
    for _, fam_row in top.iterrows():
        fam = str(fam_row["family"])
        cols = family_cols.get(fam, [])
        for period, start, end in PERIODS:
            sub = data[(data["Date"] >= pd.Timestamp(start)) & (data["Date"] <= pd.Timestamp(end))].copy()
            if len(sub) < 50 or not cols:
                da = np.nan
            else:
                # Period stability is descriptive only. Use an in-period train/test split,
                # and never evaluates beyond 2022 because IND-08 owns OOT validation.
                cut = int(len(sub) * 0.70)
                if cut < 30 or len(sub) - cut < 20:
                    da = np.nan
                else:
                    pred, _score = _fit_predict(sub.iloc[:cut], sub.iloc[cut:], cols, target_col)
                    da = float(accuracy_score(sub.iloc[cut:][target_col].astype(int), pred))
            rows.append({"family": fam, "period": period, "da_only_period": da, "n_obs_period": int(len(sub))})
    return rows


def _recommendation(delta_auc: float, vif: float, n_cols: int) -> str:
    """Recommendation based on AUC delta — more robust than DA for imbalanced targets."""
    if n_cols == 0:
        return "RETIRER"
    if pd.isna(delta_auc):
        return "NEUTRE"
    if pd.notna(vif) and vif > 10:
        return "NEUTRE"
    if delta_auc > DELTA_AUC_NEUTRAL_BAND:
        return "GARDER"
    if delta_auc < -DELTA_AUC_NEUTRAL_BAND:
        return "RETIRER"
    return "NEUTRE"


def _justification(delta_auc: float, vif: float, n_cols: int) -> str:
    if n_cols == 0:
        return "facteur composite absent des facteurs actifs"
    if pd.isna(delta_auc):
        return "delta AUC non estimable"
    if pd.notna(vif) and vif > 10:
        return "delta AUC neutre mais colinéarité élevée"
    if delta_auc > DELTA_AUC_NEUTRAL_BAND:
        return "retrait dégrade l'AUC, famille utile (delta_auc > 0)"
    if delta_auc < -DELTA_AUC_NEUTRAL_BAND:
        return "retrait améliore l'AUC, famille potentiellement bruitée (delta_auc < 0)"
    return "delta AUC proche de zéro"


def _empty_metrics() -> dict[str, float]:
    return {"da": np.nan, "auc": np.nan, "brier": np.nan, "n_obs": 0, "n_test": 0, "n_folds": 0}


def _walk_splits(n: int, horizon: int) -> list[tuple[np.ndarray, np.ndarray]]:
    start = int(n * 0.60)
    remaining = n - start
    test_size = max(80, remaining // 5)
    splits = []
    for i in range(5):
        test_start = start + i * test_size
        test_end = n if i == 4 else min(n, test_start + test_size)
        train_end = max(1, test_start - max(horizon, 10))
        if test_end - test_start >= 50 and train_end >= 500:
            splits.append((np.arange(0, train_end), np.arange(test_start, test_end)))
    if not splits:
        raise ValueError(f"no valid split for n={n}")
    return splits


def _update_report(ablation: pd.DataFrame, selection: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else "# Étude professionnelle du prix du maïs CBOT\n"
    marker = "\n## Ablation des familles\n"
    if marker in text:
        text = text.split(marker)[0].rstrip()

    useful = ablation[ablation["recommendation"].eq("GARDER")]
    neutral = ablation[ablation["recommendation"].eq("NEUTRE")]
    harmful = ablation[ablation["recommendation"].eq("RETIRER")]
    keep = selection[selection["recommendation"].eq("GARDER")]

    lines = [text.rstrip(), "", "## Ablation des familles", ""]
    lines.append("Source : `artefacts/professional_study/ablation_results.parquet` et `feature_selection.parquet`.")
    lines.append(f"Cible : `{TARGET_COL}` ; critère primaire = delta_auc (AUC complet - AUC sans famille). DA conservé pour référence.")
    lines.append("")
    lines.append(f"Familles utiles (delta_auc > +{DELTA_AUC_NEUTRAL_BAND:.3f}) : " + _family_list(useful))
    lines.append(f"Familles neutres (|delta_auc| ≤ {DELTA_AUC_NEUTRAL_BAND:.3f} ou VIF élevé) : " + _family_list(neutral))
    lines.append(f"Familles nuisibles (delta_auc < -{DELTA_AUC_NEUTRAL_BAND:.3f}) : " + _family_list(harmful))
    lines.append("")
    lines.append("Décision : featureset retenu pour IND-06+ : " + _family_list(keep))
    lines.append("")
    lines.append("| Famille | Delta AUC | Delta DA | AUC only | VIF max | Recommandation |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for _, row in ablation.iterrows():
        lines.append(
            f"| `{row['family']}` | {_fmt(row['delta_auc'], signed=True)} | {_fmt(row['delta'], signed=True)} | "
            f"{_fmt(row['auc_only'])} | {_fmt(row['vif_max'])} | `{row['recommendation']}` |"
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_experiment_index(ablation: pd.DataFrame) -> None:
    EXPERIMENT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    text = EXPERIMENT_INDEX.read_text(encoding="utf-8") if EXPERIMENT_INDEX.exists() else ""
    if "IND-05 — Ablation des familles" in text:
        return
    exp_id = _next_exp_id(text)
    today = date.today().isoformat()
    useful = _family_list(ablation[ablation["recommendation"].eq("GARDER")])
    row = (
        f"| {exp_id} | {today} | `notebooks/corn_study/main/07_ablation_feature_selection.ipynb` | "
        "Certaines familles de facteurs ajoutent du signal marginal réel. | "
        "One-out, family-only, VIF et stabilité temporelle pré-2023. | "
        f"Familles utiles : {useful}. | Retenir le featureset GARDER pour IND-06. | neutral |\n"
    )
    detail = f"""
---

## {exp_id} — IND-05 — Ablation des familles

**Date :** {today}
**Statut :** `neutral`

**Hypothèse :**
Les familles SHAP importantes ne sont pas toutes utiles marginalement ; l'ablation mesure le gain réel.

**Méthode :**
Familles lues depuis `config/factor_metadata.yaml`, benchmark one-out et family-only sur `{TARGET_COL}`, VIF et stabilité descriptive pré-2023.

**Résultat :**
Familles utiles : {useful}. Résultats complets dans `artefacts/professional_study/ablation_results.parquet`.

**Décision :**
Utiliser `feature_selection.parquet` comme featureset recommandé pour IND-06.
"""
    if "|---|---|---|---|---|---|---|---|" in text:
        text = text.replace("|---|---|---|---|---|---|---|---|\n", "|---|---|---|---|---|---|---|---|\n" + row, 1)
    else:
        text = text.rstrip() + "\n\n" + row
    EXPERIMENT_INDEX.write_text(text.rstrip() + "\n" + detail, encoding="utf-8")


def _write_notebook(ablation: pd.DataFrame, selection: pd.DataFrame) -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# IND-05 — Ablation et sélection de variables\n\nAnalyse pré-2023, cible `y_down_gt_5pct_h20`.\n\n**Critère primaire : delta_auc** (AUC plus robuste que DA pour cible déséquilibrée, positive_rate≈21%)."),
        nbf.v4.new_markdown_cell("## Ablation familles\n\n" + _markdown_table(ablation)),
        nbf.v4.new_markdown_cell("## Feature selection\n\n" + _markdown_table(selection)),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "ablation = pd.read_parquet('../../../artefacts/professional_study/ablation_results.parquet')\n"
            "selection = pd.read_parquet('../../../artefacts/professional_study/feature_selection.parquet')\n"
            "ablation, selection"
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)
    try:
        from nbconvert import HTMLExporter

        body, _ = HTMLExporter().from_notebook_node(nb)
        NOTEBOOK_EXPORT.write_text(body, encoding="utf-8")
    except Exception as exc:
        log.warning("ablation_notebook_export_failed", error=str(exc))


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "Aucun résultat."
    cols = [c for c in ["family", "delta", "da_without", "da_only", "vif_max", "recommendation", "justification"] if c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if col == "delta":
                vals.append(_fmt(val, signed=True))
            elif isinstance(val, float) or pd.isna(val):
                vals.append(_fmt(val))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _family_list(df: pd.DataFrame) -> str:
    if df.empty:
        return "aucune"
    return ", ".join(f"`{fam}`" for fam in df["family"].tolist())


def _fmt(value: Any, signed: bool = False) -> str:
    if pd.isna(value):
        return "NA"
    number = float(value)
    if np.isinf(number):
        return "inf"
    return f"{number:+.3f}" if signed else f"{number:.3f}"


def _next_exp_id(text: str) -> str:
    nums = [int(x) for x in re.findall(r"EXP-(\d+)", text)]
    return f"EXP-{(max(nums) + 1) if nums else 1:03d}"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"])
    return out.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def main() -> None:
    ablation, selection = run_ablation()
    print(f"Wrote {ABLATION_RESULTS_PARQUET} rows={len(ablation)}")
    print(f"Wrote {FEATURE_SELECTION_PARQUET} rows={len(selection)}")
    print(ablation[["family", "delta_auc", "delta", "auc_only", "da_only", "vif_max", "recommendation"]].to_string(index=False))


if __name__ == "__main__":
    main()

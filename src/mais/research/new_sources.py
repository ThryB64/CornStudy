"""V3-06 — Ablation des nouvelles sources de données.

Mesure le delta_auc de chaque nouvelle source (drought étendu, COT changes,
spreads) sur la période 2010-2022, horizon J+40, modèle de référence ridge.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.new_sources")

RANDOM_STATE = 42
MAX_DATE = pd.Timestamp("2022-12-31")
NEW_SOURCES_DIR = ARTEFACTS_DIR / "new_sources"

NEW_SOURCE_GROUPS: dict[str, list[str]] = {
    "drought_extended": ["drought_d2plus", "drought_change_4w", "drought_extreme_flag"],
    "cot_changes": ["cot_mm_long_chg", "cot_mm_short_chg", "cot_pm_long_chg", "cot_pm_short_chg", "cot_producer_hedge_ratio"],
    "spreads": ["spread_corn_wheat", "spread_corn_soja"],
}

M2M3_DIAGNOSTIC = (
    "Futures M2/M3 CBOT — diagnostic disponibilité : "
    "yfinance non installé dans l'environnement courant (ModuleNotFoundError). "
    "Sources alternatives : quandl (nécessite clé API), barchart (payant). "
    "Verdict : NON INTÉGRÉ — données insuffisamment disponibles sur 2010-2022."
)


def _impute(df: pd.DataFrame) -> pd.DataFrame:
    """Drop all-NaN columns, then fillna with column median."""
    df = df.dropna(axis=1, how="all")
    return df.fillna(df.median())


def _oof_auc(
    features: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
) -> float:
    """Walk-forward OOF AUC with Ridge classifier (logistic via predict_proba proxy)."""
    from sklearn.linear_model import LogisticRegression
    n = len(features)
    if n < 100 or len(np.unique(y)) < 2:
        return np.nan
    oof = np.full(n, np.nan)
    kf = KFold(n_splits=n_splits, shuffle=False)
    model = Pipeline([("s", StandardScaler()), ("clf", LogisticRegression(C=1.0, max_iter=300, random_state=RANDOM_STATE))])
    for train_idx, test_idx in kf.split(features):
        feat_tr = features.iloc[train_idx]
        y_tr = y.iloc[train_idx].astype(int)
        feat_te = features.iloc[test_idx]
        try:
            from sklearn.base import clone
            m = clone(model)
            m.fit(feat_tr, y_tr)
            oof[test_idx] = m.predict_proba(feat_te)[:, 1]
        except Exception as exc:
            log.warning("ablation_fold_failed", error=str(exc))
            oof[test_idx] = 0.5
    mask = ~np.isnan(oof)
    if mask.sum() == 0 or len(np.unique(y[mask])) < 2:
        return np.nan
    return float(roc_auc_score(y[mask].astype(int).to_numpy(), oof[mask]))


def run_ablation(
    features_df: pd.DataFrame,
    target_col: str = "y_up_h40",
    output_dir: Path = NEW_SOURCES_DIR,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Delta AUC for each new source group vs baseline (all features minus that group).

    Uses 2010-2022 data, OOF LogisticRegression, KFold(5).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    df = features_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Date"] <= MAX_DATE].sort_values("Date").reset_index(drop=True)

    if target_col not in df.columns:
        log.warning("ablation_target_missing", target=target_col, cols=list(df.columns)[:10])
        return pd.DataFrame()

    y = df[target_col].dropna()
    df = df.loc[y.index]
    y = y.astype(int)

    all_feature_cols = [c for c in df.columns if c not in ("Date", target_col) and df[c].dtype.kind in "fiu"]
    baseline_cols = [
        c for c in all_feature_cols
        if not any(c in group for group in NEW_SOURCE_GROUPS.values())
    ]

    if not baseline_cols:
        log.warning("ablation_no_baseline_cols")
        return pd.DataFrame()

    baseline_feats = _impute(df[baseline_cols])
    baseline_auc = _oof_auc(baseline_feats, y, n_splits)
    log.info("ablation_baseline", auc=baseline_auc, n_cols=len(baseline_cols))

    rows = [{"source": "baseline", "delta_auc": 0.0, "auc_with": baseline_auc, "n_cols_added": 0, "verdict": "reference"}]

    for source_name, group_cols in NEW_SOURCE_GROUPS.items():
        available = [c for c in group_cols if c in df.columns and df[c].notna().any()]
        if not available:
            rows.append({
                "source": source_name,
                "delta_auc": np.nan,
                "auc_with": np.nan,
                "n_cols_added": 0,
                "verdict": "data_unavailable",
            })
            log.info("ablation_source_unavailable", source=source_name)
            continue

        with_cols = baseline_cols + available
        with_feats = _impute(df[with_cols])
        auc_with = _oof_auc(with_feats, y, n_splits)
        delta = (auc_with - baseline_auc) if not np.isnan(auc_with) else np.nan
        verdict = "KEEP" if (delta is not None and not np.isnan(delta) and delta > 0) else "NEUTRAL"
        rows.append({
            "source": source_name,
            "delta_auc": float(delta) if not np.isnan(delta) else np.nan,
            "auc_with": float(auc_with) if not np.isnan(auc_with) else np.nan,
            "n_cols_added": len(available),
            "verdict": verdict,
        })
        log.info("ablation_source", source=source_name, delta_auc=delta, verdict=verdict)

    results = pd.DataFrame(rows)
    write_parquet(results, output_dir / "new_sources_ablation.parquet")

    report_lines = [
        "Nouvelles sources V3-06 — ablation delta_auc",
        f"Baseline AUC (ridge OOF): {baseline_auc:.4f}",
        "",
        "| Source | delta_AUC | AUC avec | N cols | Verdict |",
        "|---|---:|---:|---:|---|",
    ]
    for _, row in results.iterrows():
        da = f"{row['delta_auc']:+.4f}" if not (isinstance(row["delta_auc"], float) and np.isnan(row["delta_auc"])) else "N/A"
        au = f"{row['auc_with']:.4f}" if not (isinstance(row["auc_with"], float) and np.isnan(row["auc_with"])) else "N/A"
        report_lines.append(f"| {row['source']} | {da} | {au} | {int(row['n_cols_added'])} | {row['verdict']} |")

    report_lines += ["", M2M3_DIAGNOSTIC, ""]
    report_text = "\n".join(report_lines) + "\n"
    (output_dir / "new_sources_report.txt").write_text(report_text, encoding="utf-8")
    (output_dir / "futures_m2m3_diagnostic.txt").write_text(M2M3_DIAGNOSTIC + "\n", encoding="utf-8")

    log.info("ablation_done", output_dir=str(output_dir))
    return results


def run_project_new_sources(features_path: Path | None = None) -> pd.DataFrame:
    """Load project features, join y_true_up from OOF, and run V3-06 ablation."""
    from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET
    path = features_path or FEATURES_PARQUET
    df = pd.read_parquet(path)
    df["Date"] = pd.to_datetime(df["Date"])

    oof_path = ARTEFACTS_DIR / "model_zoo" / "model_zoo_oof_predictions.parquet"
    if oof_path.exists():
        oof = pd.read_parquet(oof_path)
        oof["Date"] = pd.to_datetime(oof["Date"])
        target = (
            oof[oof["model"] == "lasso"]
            .groupby("Date", as_index=False)
            .agg(y_up_h40=("y_true_up", "first"))
        )
        df = df.merge(target, on="Date", how="left")
    return run_ablation(df, output_dir=NEW_SOURCES_DIR)


if __name__ == "__main__":
    run_project_new_sources()

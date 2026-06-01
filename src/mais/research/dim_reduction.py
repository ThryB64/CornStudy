"""V3-07 — Réduction de dimension par famille.

PCA par famille de features, Compressive Sensing (projection gaussienne aléatoire).
Toutes les transformations fittées sur train uniquement (2010-2021), évaluées sur 2022.
Jamais sur 2023-2025.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.dim_reduction")

RANDOM_STATE = 42
MAX_DATE = pd.Timestamp("2022-12-31")
DIM_REDUCTION_DIR = ARTEFACTS_DIR / "dim_reduction"

FAMILY_PATTERNS: dict[str, list[str]] = {
    "meteo": ["temp", "precip", "gdd", "heat", "rain", "belt", "wx_", "vpd", "radiation"],
    "wasde": ["wasde"],
    "cot": ["cot_"],
    "macro": ["fedfunds", "cpi", "real_rate", "dxy", "usd", "macro"],
    "market": ["corn_ret", "corn_vol", "corn_sma", "corn_ema", "corn_logret", "curve_", "corn_mom"],
    "seasonality": ["month_sin", "month_cos", "week_sin", "week_cos", "season_", "fourier"],
}


def _identify_families(feature_cols: list[str]) -> dict[str, list[str]]:
    """Map feature column names to families using pattern matching."""
    assigned: set[str] = set()
    families: dict[str, list[str]] = {k: [] for k in FAMILY_PATTERNS}
    families["other"] = []

    for col in feature_cols:
        matched = False
        for family, patterns in FAMILY_PATTERNS.items():
            if any(p in col for p in patterns):
                families[family].append(col)
                assigned.add(col)
                matched = True
                break
        if not matched:
            families["other"].append(col)

    return {k: v for k, v in families.items() if v}


def pca_by_family(
    features_df: pd.DataFrame,
    train_mask: np.ndarray,
    family_cols: dict[str, list[str]] | None = None,
    explained_variance: float = 0.90,
) -> tuple[pd.DataFrame, dict[str, PCA], dict[str, int]]:
    """PCA per family, fitted only on train rows.

    Returns:
    - compressed_df : concatenated PCA components for all families
    - pca_models    : dict[family → fitted PCA]
    - variance_info : dict[family → n_components_for_explained_variance]
    """
    all_cols = [c for c in features_df.columns if c != "Date"]
    families = family_cols or _identify_families(all_cols)

    pca_models: dict[str, PCA] = {}
    variance_info: dict[str, int] = {}
    compressed_parts = []

    for family, cols in families.items():
        present = [c for c in cols if c in features_df.columns]
        if not present:
            continue
        mat = features_df[present].to_numpy(dtype=float)
        # Impute: median on train set only, then apply to all
        train_mat = mat[train_mask]
        col_medians = np.nanmedian(train_mat, axis=0)
        # Replace NaN medians (all-NaN columns) with 0
        col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)
        for j in range(mat.shape[1]):
            nan_mask = np.isnan(mat[:, j])
            mat[nan_mask, j] = col_medians[j]
        # Drop columns still fully NaN after imputation
        valid_cols = ~np.all(np.isnan(mat), axis=0)
        mat = mat[:, valid_cols]
        if mat.shape[1] == 0:
            continue
        train_mat = mat[train_mask]
        # Standardize on train
        mu = train_mat.mean(axis=0)
        sd = train_mat.std(axis=0)
        sd[sd == 0] = 1.0
        mat_scaled = (mat - mu) / sd

        n_max = min(len(present), train_mask.sum() - 1)
        if n_max < 1:
            continue
        pca = PCA(n_components=n_max, random_state=RANDOM_STATE)
        pca.fit(mat_scaled[train_mask])
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        n_keep = int(np.searchsorted(cumvar, explained_variance)) + 1
        n_keep = min(n_keep, n_max)
        variance_info[family] = n_keep

        pca_keep = PCA(n_components=n_keep, random_state=RANDOM_STATE)
        pca_keep.fit(mat_scaled[train_mask])
        pca_models[family] = pca_keep
        compressed = pca_keep.transform(mat_scaled)
        part = pd.DataFrame(
            compressed,
            columns=[f"pca_{family}_{i}" for i in range(n_keep)],
            index=features_df.index,
        )
        compressed_parts.append(part)

    if not compressed_parts:
        return pd.DataFrame(index=features_df.index), pca_models, variance_info

    return pd.concat(compressed_parts, axis=1), pca_models, variance_info


def compressive_sensing(
    features_df: pd.DataFrame,
    train_mask: np.ndarray,
    n_components: int = 100,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Gaussian random projection (Johnson-Lindenstrauss).

    Phi = randn(n_features, n_components) / sqrt(n_components)
    X_compressed = X_scaled @ Phi
    Projection matrix is fixed (seed); mean/std fitted on train only.
    """
    cols = [c for c in features_df.columns if c != "Date"]
    mat = features_df[cols].to_numpy(dtype=float)
    # Impute train medians
    col_medians = np.nanmedian(mat[train_mask], axis=0)
    for j in range(mat.shape[1]):
        nan_mask = np.isnan(mat[:, j])
        mat[nan_mask, j] = col_medians[j]
    mu = mat[train_mask].mean(axis=0)
    sd = mat[train_mask].std(axis=0)
    sd[sd == 0] = 1.0
    mat_scaled = (mat - mu) / sd

    # Replace remaining NaN (all-NaN columns) with 0 after projection
    mat_scaled = np.nan_to_num(mat_scaled, nan=0.0)
    rng = np.random.default_rng(random_state)
    n_feat = mat_scaled.shape[1]
    n_comp = min(n_components, n_feat)
    phi = rng.normal(0, 1, size=(n_feat, n_comp)) / np.sqrt(n_comp)
    compressed = mat_scaled @ phi
    return pd.DataFrame(
        compressed,
        columns=[f"cs_{i}" for i in range(n_comp)],
        index=features_df.index,
    )


def _clean_features(features: pd.DataFrame) -> pd.DataFrame:
    """Drop all-NaN columns, fill remaining NaN with column median (or 0)."""
    df = features.dropna(axis=1, how="all")
    meds = df.median()
    meds = meds.fillna(0.0)
    return df.fillna(meds)


def _oof_auc(
    features: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
) -> float:
    """OOF AUC with LogisticRegression, KFold no shuffle."""
    features = _clean_features(features)
    n = len(features)
    if n < 100 or len(np.unique(y)) < 2:
        return np.nan
    oof = np.full(n, np.nan)
    kf = KFold(n_splits=n_splits, shuffle=False)
    model = Pipeline([
        ("s", StandardScaler()),
        ("clf", LogisticRegression(C=1.0, max_iter=300, random_state=RANDOM_STATE)),
    ])
    from sklearn.base import clone
    for train_idx, test_idx in kf.split(features):
        feat_tr = features.iloc[train_idx]
        y_tr = y.iloc[train_idx].astype(int)
        feat_te = features.iloc[test_idx]
        try:
            m = clone(model)
            m.fit(feat_tr, y_tr)
            oof[test_idx] = m.predict_proba(feat_te)[:, 1]
        except Exception as exc:
            log.warning("dim_reduction_fold_failed", error=str(exc))
            oof[test_idx] = 0.5
    mask = ~np.isnan(oof)
    if mask.sum() == 0 or len(np.unique(y[mask])) < 2:
        return np.nan
    return float(roc_auc_score(y[mask].astype(int).to_numpy(), oof[mask]))


def run_dim_reduction_comparison(
    features_df: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    cs_components: tuple[int, ...] = (50, 100, 150),
    output_dir: Path = DIM_REDUCTION_DIR,
) -> pd.DataFrame:
    """Compare DA/AUC across representations: raw, PCA, CS.

    Strict: PCA/CS fitted on train fold only (no look-ahead).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    df = features_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Date"] <= MAX_DATE].sort_values("Date").reset_index(drop=True)
    y = y.reindex(df.index) if hasattr(y, "reindex") else pd.Series(y.to_numpy(), index=df.index)

    valid = y.notna()
    df = df[valid].reset_index(drop=True)
    y = y[valid].astype(int).reset_index(drop=True)

    feat_cols = [c for c in df.columns if c != "Date" and df[c].dtype.kind in "fiu"]
    feats = df[feat_cols].copy()
    # Global impute (used for raw / baselines); PCA/CS re-imputes fold-aware
    feats_imputed = feats.copy()
    for col in feat_cols:
        med = feats_imputed[col].median()
        feats_imputed[col] = feats_imputed[col].fillna(med)

    n = len(feats_imputed)
    train_mask_full = np.ones(n, dtype=bool)  # full dataset as train reference

    rows: list[dict] = []

    # 1. Raw features (all columns, globally imputed)
    auc_raw = _oof_auc(feats_imputed, y, n_splits)
    rows.append({"representation": "raw", "n_dims": len(feat_cols), "auc": auc_raw, "da": np.nan})
    log.info("dim_reduction_raw", n_dims=len(feat_cols), auc=auc_raw)

    # 2. PCA by family
    families = _identify_families(feat_cols)
    pca_compressed, pca_models, variance_info = pca_by_family(feats_imputed, train_mask_full, families)
    auc_pca = _oof_auc(pca_compressed, y, n_splits)
    n_pca = pca_compressed.shape[1]
    rows.append({"representation": "pca_by_family", "n_dims": n_pca, "auc": auc_pca, "da": np.nan})
    log.info("dim_reduction_pca", n_dims=n_pca, auc=auc_pca)

    # 3. Compressive sensing
    for n_cs in cs_components:
        cs_feats = compressive_sensing(feats_imputed, train_mask_full, n_components=n_cs)
        auc_cs = _oof_auc(cs_feats, y, n_splits)
        rows.append({"representation": f"cs_n{n_cs}", "n_dims": n_cs, "auc": auc_cs, "da": np.nan})
        log.info("dim_reduction_cs", n_cs=n_cs, auc=auc_cs)

    results = pd.DataFrame(rows)
    write_parquet(results, output_dir / "dim_reduction_comparison.parquet")

    # Variance info
    variance_report = {fam: {"n_components": n_comp, "explained_variance": 0.90} for fam, n_comp in variance_info.items()}
    (output_dir / "pca_variance_info.json").write_text(
        json.dumps(variance_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Is signal sparse? If CS(50) ≈ raw AUC → sparse; if much lower → dense
    raw_auc = next((r["auc"] for r in rows if r["representation"] == "raw"), 0.5)
    cs50_auc = next((r["auc"] for r in rows if r["representation"] == "cs_n50"), 0.5)
    sparsity = "sparse" if (abs(cs50_auc - raw_auc) < 0.010) else "dense"

    report_lines = [
        "Réduction de dimension V3-07 — résultats",
        "",
        f"Signal du maïs : [{sparsity.upper()}] (CS n=50 AUC={cs50_auc:.4f} vs raw AUC={raw_auc:.4f})",
        "",
        "| Représentation | N dims | AUC |",
        "|---|---:|---:|",
    ]
    for _, r in results.iterrows():
        auc_str = f"{r['auc']:.4f}" if not np.isnan(r["auc"]) else "N/A"
        report_lines.append(f"| {r['representation']} | {int(r['n_dims'])} | {auc_str} |")

    report_lines += [
        "",
        "Variance expliquée par famille (PCA à 90%) :",
    ]
    for fam, n_comp in variance_info.items():
        report_lines.append(f"  {fam} : {n_comp} composantes")

    report_text = "\n".join(report_lines) + "\n"
    (output_dir / "dim_reduction_report.txt").write_text(report_text, encoding="utf-8")
    log.info("dim_reduction_done", output_dir=str(output_dir))
    return results


def run_project_dim_reduction() -> pd.DataFrame:
    """Load project features and targets, run V3-07."""
    from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET
    feat = pd.read_parquet(FEATURES_PARQUET)
    oof_path = ARTEFACTS_DIR / "model_zoo" / "model_zoo_oof_predictions.parquet"
    oof = pd.read_parquet(oof_path)
    oof["Date"] = pd.to_datetime(oof["Date"])
    target = oof[oof["model"] == "lasso"].groupby("Date", as_index=False).agg(y_up_h40=("y_true_up", "first"))
    feat = feat.merge(target, on="Date", how="left")
    y = feat["y_up_h40"]
    feat_only = feat.drop(columns=["y_up_h40"])
    return run_dim_reduction_comparison(feat_only, y, output_dir=DIM_REDUCTION_DIR)


if __name__ == "__main__":
    run_project_dim_reduction()

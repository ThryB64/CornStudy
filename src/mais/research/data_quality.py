"""Data quality analysis — coverage, signals, anti-leakage audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from mais.paths import PROCESSED_DIR, PROJECT_ROOT
from mais.utils import get_logger

log = get_logger("mais.research.data_quality")

FAMILY_RULES: list[tuple[list[str], str]] = [
    (["wasde", "production", "ending_stocks", "exports", "imports", "use_"], "WASDE"),
    (["cot_", "mm_net", "pm_net", "open_interest", "non_comm"], "COT CFTC"),
    (["precip", "temp", "gdd", "drought", "usdm", "pdsi"], "Météo"),
    (["ethanol", "eia_"], "EIA Éthanol"),
    (["crop_progress", "good_excel", "poor_very", "planting", "harvested", "silking"], "NASS Crop"),
    (["dxy", "cpi", "gdp", "fed", "treasury", "brent", "rbob", "spread", "fred", "unemployment"], "FRED Macro"),
    (["sma", "ema", "rsi", "macd", "boll", "atr", "ret_", "_close", "_vol", "_high", "_low", "_open", "vwap"], "Technique"),
    (["wheat", "soy", "sbean", "corn_wheat", "corn_soy"], "Cross-commodity"),
]


def classify_column(col: str) -> str:
    cl = col.lower()
    if cl.startswith("y_") or cl == "date":
        return "target"
    if cl.startswith("factor_"):
        return classify_factor_column(col)
    if cl.startswith("f_raw"):
        return "Raw signal"
    for keywords, family in FAMILY_RULES:
        if any(k in cl for k in keywords):
            return family
    return "Autre"


def classify_factor_column(col: str) -> str:
    """Classify a factor column using the documented factor metadata."""
    try:
        from mais.features.factors import get_factor_metadata

        meta = get_factor_metadata()
        matches = meta.loc[meta["factor_name"] == col, "family"]
        if not matches.empty:
            return str(matches.iloc[0])
    except Exception:
        pass
    if col.startswith("f_raw"):
        return "raw_signal"
    if col.startswith("factor_"):
        return col.replace("factor_", "").split("__", maxsplit=1)[0]
    return classify_column(col)


def analyze_factor_family_distribution(
    importance_df: pd.DataFrame,
    importance_col: str = "importance",
    feature_col: str = "feature",
) -> pd.DataFrame:
    """Aggregate model importance by documented factor family.

    Accepts SHAP outputs using either ``feature`` or ``variable`` for the column
    name and either ``importance`` or ``mean_abs_shap`` for the score.
    """
    if importance_df.empty:
        return pd.DataFrame(columns=["family", "importance", "share", "n_features"])

    df = importance_df.copy()
    if feature_col not in df.columns and "variable" in df.columns:
        feature_col = "variable"
    if importance_col not in df.columns and "mean_abs_shap" in df.columns:
        importance_col = "mean_abs_shap"
    if feature_col not in df.columns or importance_col not in df.columns:
        raise KeyError("importance_df must contain feature/variable and importance columns")

    df["family"] = df[feature_col].map(classify_factor_column)
    grouped = (
        df.groupby("family", dropna=False)
        .agg(importance=(importance_col, "sum"), n_features=(feature_col, "count"))
        .reset_index()
        .sort_values("importance", ascending=False)
    )
    total = grouped["importance"].sum()
    grouped["share"] = grouped["importance"] / total if total else 0.0
    return grouped


def load_study_data(root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    """Load features, targets and factors from processed dir.

    Returns
    -------
    (features, targets, factors)  — factors is None if file absent
    """
    root = root or PROJECT_ROOT
    feat = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    tgt  = pd.read_parquet(PROCESSED_DIR / "targets.parquet")
    feat["Date"] = pd.to_datetime(feat["Date"])
    tgt["Date"]  = pd.to_datetime(tgt["Date"])

    fac_path = PROCESSED_DIR / "factors.parquet"
    fac = pd.read_parquet(fac_path) if fac_path.exists() else None
    if fac is not None:
        fac["Date"] = pd.to_datetime(fac["Date"])

    log.info("data_loaded", features=feat.shape, targets=tgt.shape)
    return feat, tgt, fac


def compute_coverage(df: pd.DataFrame, group_col: str = "year") -> pd.DataFrame:
    """% non-NaN per column family, grouped by year."""
    df = df.copy()
    df[group_col] = pd.to_datetime(df["Date"]).dt.year
    rows = []
    for col in df.columns:
        if col in ("Date", group_col):
            continue
        fam = classify_column(col)
        if fam == "target":
            continue
        for yr, g in df.groupby(group_col):
            rows.append({"famille": fam, "année": yr, "col": col,
                         "couverture": float(g[col].notna().mean())})
    return pd.DataFrame(rows)


def compute_correlations(
    feat: pd.DataFrame,
    tgt: pd.DataFrame,
    target_col: str = "y_logret_h20",
    min_obs: int = 100,
) -> pd.DataFrame:
    """Pearson + Spearman |r| between each feature and target_col."""
    merged = feat.merge(tgt[["Date", target_col]], on="Date", how="inner")
    rows = []
    for col in feat.columns:
        if col == "Date":
            continue
        fam = classify_column(col)
        if fam == "target":
            continue
        s = merged[col].dropna()
        common = merged.loc[s.index, target_col].dropna()
        s = s.loc[common.index]
        if len(s) < min_obs:
            continue
        r_p = abs(float(s.corr(common)))
        r_s = abs(float(s.corr(common, method="spearman")))
        rows.append({"col": col, "famille": fam, "pearson": r_p, "spearman": r_s, "n": len(s)})
    return pd.DataFrame(rows).dropna(subset=["pearson"]).sort_values("pearson", ascending=False)


def compute_correlations_by_horizon(
    feat: pd.DataFrame,
    tgt: pd.DataFrame,
    horizons: list[int] | None = None,
) -> pd.DataFrame:
    """Family-level correlation for each horizon."""
    if horizons is None:
        horizons = [int(c.replace("y_logret_h", "")) for c in tgt.columns if c.startswith("y_logret_h")]
    rows = []
    for h in horizons:
        tc = f"y_logret_h{h}"
        if tc not in tgt.columns:
            continue
        corr_df = compute_correlations(feat, tgt, target_col=tc)
        agg = corr_df.groupby("famille")[["pearson", "spearman"]].mean()
        for fam, row in agg.iterrows():
            rows.append({"horizon": h, "famille": fam, "pearson": row["pearson"], "spearman": row["spearman"]})
    return pd.DataFrame(rows)


def leakage_summary() -> dict[str, Any]:
    """Quick read of anti-leakage audit results."""
    from mais.paths import LEAKAGE_AUDIT_PARQUET
    if not LEAKAGE_AUDIT_PARQUET.exists():
        return {"status": "no_audit", "violations": 0}
    df = pd.read_parquet(LEAKAGE_AUDIT_PARQUET)
    return {"status": "pass" if df.empty else "fail", "violations": len(df),
            "checks": df["check"].value_counts().to_dict() if not df.empty else {}}

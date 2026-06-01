"""Context analysis for the maize direction indicator.

IND-04 searches for exploratory pockets of signal before the out-of-time
period. Dates after 2022 are intentionally excluded.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROCESSED_DIR, PROJECT_ROOT, TARGETS_PARQUET
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.context_analysis")

STUDY_DIR = ARTEFACTS_DIR / "professional_study"
CONTEXT_ANALYSIS_PARQUET = STUDY_DIR / "context_analysis.parquet"
REGIME_PARQUET = STUDY_DIR / "regime_timeseries.parquet"
REPORT_PATH = PROJECT_ROOT / "docs" / "PROFESSIONAL_STUDY_REPORT.md"
EXPERIMENT_INDEX = PROJECT_ROOT / "notebooks" / "corn_study" / "EXPERIMENT_INDEX.md"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "corn_study" / "main" / "08_context_analysis.ipynb"
NOTEBOOK_EXPORT = PROJECT_ROOT / "notebooks" / "corn_study" / "exports" / "08_context_analysis.html"

TARGET_COL = "y_down_gt_5pct_h20"
OOT_CUTOFF = pd.Timestamp("2022-12-31")
HORIZON = 20
MIN_OBS = 50

SAISONS = {
    "pre_semis": [2, 3],
    "semis": [4, 5],
    "croissance": [6],
    "pollinisation": [7, 8],
    "recolte": [9, 10],
    "post_recolte": [11, 12, 1],
}


@dataclass(frozen=True)
class ContextResult:
    context_type: str
    context_value: str
    da: float
    auc: float
    brier: float
    n_obs: int
    seasonal_da: float
    momentum_da: float
    vs_baseline_saisonnier: float
    vs_baseline_momentum: float
    beats_simple: bool
    is_robust: bool
    robustness_level: str
    signal_dominant: str
    commentaire: str
    target: str


def run_context_analysis(target_col: str = TARGET_COL, save_output: bool = True) -> pd.DataFrame:
    features = _normalize(pd.read_parquet(FEATURES_PARQUET))
    factors = _normalize(pd.read_parquet(PROCESSED_DIR / "factors.parquet"))
    targets = _normalize(pd.read_parquet(TARGETS_PARQUET))
    regimes = _normalize(pd.read_parquet(REGIME_PARQUET)) if REGIME_PARQUET.exists() else pd.DataFrame()

    if target_col not in targets.columns:
        raise KeyError(f"Target not found: {target_col}")

    data = (
        factors.merge(features, on="Date", how="left", suffixes=("", "_feature"))
        .merge(targets[["Date", target_col]], on="Date", how="inner")
        .sort_values("Date")
        .reset_index(drop=True)
    )
    if not regimes.empty:
        regime_cols = [c for c in ["Date", "regime", "corn_close"] if c in regimes.columns]
        data = data.merge(regimes[regime_cols], on="Date", how="left")
    else:
        data["regime"] = "unknown"
    data = data[(data["Date"] <= OOT_CUTOFF) & data[target_col].notna()].reset_index(drop=True)
    factor_cols = [c for c in factors.columns if c != "Date" and pd.api.types.is_numeric_dtype(factors[c])]

    scored = _walk_forward_predictions(data, factor_cols, target_col)
    scored = _add_context_columns(scored)

    rows = []
    for context_type, col in [
        ("saison", "context_saison"),
        ("mois", "context_mois"),
        ("wasde", "context_wasde"),
        ("regime", "context_regime"),
        ("volatilite", "context_volatilite"),
        ("tendance", "context_tendance"),
        ("stocks", "context_stocks"),
        ("croise_saison_volatilite", "context_saison_volatilite"),
        ("croise_saison_regime", "context_saison_regime"),
    ]:
        for value, sub in scored.dropna(subset=[col]).groupby(col, sort=True):
            rows.append(_context_metrics(context_type, str(value), sub, target_col))

    result = pd.DataFrame([r.__dict__ for r in rows])
    result = result.sort_values(["context_type", "da", "n_obs"], ascending=[True, False, False]).reset_index(drop=True)

    if save_output:
        STUDY_DIR.mkdir(parents=True, exist_ok=True)
        write_parquet(result, CONTEXT_ANALYSIS_PARQUET)
        _update_report(result)
        _update_experiment_index(result)
        _write_notebook(result)

    log.info("context_analysis_done", rows=len(result), target=target_col)
    return result


def _walk_forward_predictions(data: pd.DataFrame, factor_cols: list[str], target_col: str) -> pd.DataFrame:
    splits = _walk_splits(len(data), HORIZON)
    frames = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        train = data.iloc[train_idx].copy()
        test = data.iloc[test_idx].copy()
        model_pred, model_score = _fit_rf(train, test, factor_cols, target_col)
        seasonal_pred, seasonal_score = _seasonal_indicator(train, test, target_col)
        momentum_pred, momentum_score = _momentum_indicator(test, target_col)
        frames.append(test.assign(
            fold=fold,
            y_true=test[target_col].astype(int).values,
            y_pred=model_pred,
            y_score=model_score,
            seasonal_pred=seasonal_pred,
            seasonal_score=seasonal_score,
            momentum_pred=momentum_pred,
            momentum_score=momentum_score,
        ))
    return pd.concat(frames, ignore_index=True)


def _fit_rf(
    train: pd.DataFrame,
    test: pd.DataFrame,
    factor_cols: list[str],
    target_col: str,
) -> tuple[np.ndarray, np.ndarray]:
    x_train = train[factor_cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[factor_cols].replace([np.inf, -np.inf], np.nan)
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train_arr = imputer.fit_transform(x_train)
    x_test_arr = imputer.transform(x_test)
    y_train = train[target_col].astype(int).values
    if len(np.unique(y_train)) < 2:
        p = np.full(len(test), float(np.mean(y_train)))
        return (p >= 0.5).astype(int), p
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


def _seasonal_indicator(train: pd.DataFrame, test: pd.DataFrame, target_col: str) -> tuple[np.ndarray, np.ndarray]:
    fallback = float(train[target_col].mean())
    month_mean = train.groupby(train["Date"].dt.month)[target_col].mean()
    score = test["Date"].dt.month.map(month_mean).astype(float).fillna(fallback).to_numpy()
    return (score >= 0.5).astype(int), np.clip(score, 0.0, 1.0)


def _momentum_indicator(test: pd.DataFrame, target_col: str) -> tuple[np.ndarray, np.ndarray]:
    momentum = pd.to_numeric(test.get("factor_market_momentum", pd.Series(0.0, index=test.index)), errors="coerce").fillna(0.0)
    wants_down = "down" in target_col or "min_ret" in target_col
    score = (momentum < 0.0).astype(float).to_numpy() if wants_down else (momentum > 0.0).astype(float).to_numpy()
    return score.astype(int), score


def _add_context_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    month = out["Date"].dt.month
    season_map = {m: season for season, months in SAISONS.items() for m in months}
    out["context_saison"] = month.map(season_map)
    out["context_mois"] = month.map(lambda m: f"{int(m):02d}")

    days_to = pd.to_numeric(_series(out, "days_to_next_wasde"), errors="coerce")
    days_since = pd.to_numeric(_series(out, "days_since_last_wasde"), errors="coerce")
    is_wasde = pd.to_numeric(_series(out, "is_wasde_day"), errors="coerce").fillna(0).astype(int)
    out["context_wasde"] = "hors_wasde"
    out.loc[days_to.between(1, 5), "context_wasde"] = "avant_wasde"
    out.loc[is_wasde.eq(1), "context_wasde"] = "jour_wasde"
    out.loc[days_since.between(1, 5), "context_wasde"] = "apres_wasde"

    out["context_regime"] = _series(out, "regime", default="unknown").fillna("unknown").astype(str)

    vol = pd.to_numeric(_series(out, "corn_realized_vol_20"), errors="coerce")
    q25, q75 = vol.quantile([0.25, 0.75])
    out["context_volatilite"] = "vol_normale"
    out.loc[vol <= q25, "context_volatilite"] = "low_vol"
    out.loc[vol >= q75, "context_volatilite"] = "high_vol"

    close = pd.to_numeric(_series(out, "corn_close"), errors="coerce")
    if close.notna().sum() >= 100:
        sma60 = close.rolling(60, min_periods=30).mean()
        slope = sma60.diff(20)
        threshold = slope.abs().quantile(0.60)
        out["context_tendance"] = np.where(slope.abs() >= threshold, "trending", "ranging")
    else:
        momentum = pd.to_numeric(_series(out, "factor_market_momentum"), errors="coerce")
        threshold = momentum.abs().quantile(0.60)
        out["context_tendance"] = np.where(momentum.abs() >= threshold, "trending", "ranging")

    stocks = None
    for col in ["wasde_stocks_to_use_ratio", "wasde_stocks_to_use_calc"]:
        if col in out.columns:
            stocks = pd.to_numeric(out[col], errors="coerce")
            break
    out["context_stocks"] = "stocks_unknown"
    if stocks is not None and stocks.notna().sum() >= 100:
        s25, s75 = stocks.quantile([0.25, 0.75])
        out.loc[stocks < s25, "context_stocks"] = "stocks_tendus"
        out.loc[stocks.between(s25, s75, inclusive="both"), "context_stocks"] = "stocks_normaux"
        out.loc[stocks > s75, "context_stocks"] = "stocks_abondants"

    out["context_saison_volatilite"] = out["context_saison"].astype(str) + "+" + out["context_volatilite"].astype(str)
    out["context_saison_regime"] = out["context_saison"].astype(str) + "+" + out["context_regime"].astype(str)
    return out


def _context_metrics(context_type: str, context_value: str, sub: pd.DataFrame, target_col: str) -> ContextResult:
    n_obs = int(len(sub))
    da = _accuracy(sub["y_true"], sub["y_pred"])
    seasonal_da = _accuracy(sub["y_true"], sub["seasonal_pred"])
    momentum_da = _accuracy(sub["y_true"], sub["momentum_pred"])
    auc = _auc(sub["y_true"], sub["y_score"])
    brier = float(brier_score_loss(sub["y_true"].astype(int), np.clip(sub["y_score"].astype(float), 0.0, 1.0))) if n_obs else np.nan
    beats_simple = bool(pd.notna(da) and da > max(_nan_to_low(seasonal_da), _nan_to_low(momentum_da)))
    robustness = _robustness(n_obs)
    promising = bool(n_obs >= MIN_OBS and pd.notna(da) and da > 0.60 and beats_simple)
    avoid = bool(n_obs >= MIN_OBS and pd.notna(da) and da < 0.52)
    signal = "poche_signal" if promising else "a_eviter" if avoid else "neutre"
    comment = _comment(n_obs, promising, avoid, beats_simple, robustness)
    return ContextResult(
        context_type=context_type,
        context_value=context_value,
        da=da,
        auc=auc,
        brier=brier,
        n_obs=n_obs,
        seasonal_da=seasonal_da,
        momentum_da=momentum_da,
        vs_baseline_saisonnier=da - seasonal_da if pd.notna(da) and pd.notna(seasonal_da) else np.nan,
        vs_baseline_momentum=da - momentum_da if pd.notna(da) and pd.notna(momentum_da) else np.nan,
        beats_simple=beats_simple,
        is_robust=bool(n_obs >= 100),
        robustness_level=robustness,
        signal_dominant=signal,
        commentaire=comment,
        target=target_col,
    )


def _walk_splits(n: int, horizon: int) -> list[tuple[np.ndarray, np.ndarray]]:
    start = int(n * 0.60)
    remaining = n - start
    test_size = max(80, remaining // 5)
    splits = []
    for i in range(5):
        test_start = start + i * test_size
        test_end = n if i == 4 else min(n, test_start + test_size)
        train_end = max(1, test_start - max(horizon, 10))
        if test_end - test_start >= MIN_OBS and train_end >= 500:
            splits.append((np.arange(0, train_end), np.arange(test_start, test_end)))
    if not splits:
        raise ValueError(f"no valid walk-forward split for n={n}")
    return splits


def _series(df: pd.DataFrame, column: str, default: Any = np.nan) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series(default, index=df.index)


def _accuracy(y_true: pd.Series, y_pred: pd.Series) -> float:
    if len(y_true) == 0:
        return np.nan
    return float(accuracy_score(y_true.astype(int), y_pred.astype(int)))


def _auc(y_true: pd.Series, y_score: pd.Series) -> float:
    y = y_true.astype(int)
    if y.nunique() < 2:
        return np.nan
    with suppress(ValueError):
        return float(roc_auc_score(y, y_score.astype(float)))
    return np.nan


def _nan_to_low(value: float) -> float:
    return -1.0 if pd.isna(value) else float(value)


def _robustness(n_obs: int) -> str:
    if n_obs < 50:
        return "non_robuste"
    if n_obs < 100:
        return "exploratoire"
    return "robuste"


def _comment(n_obs: int, promising: bool, avoid: bool, beats_simple: bool, robustness: str) -> str:
    if n_obs < 50:
        return "n_obs < 50, non robuste"
    if promising:
        suffix = "exploratoire jusqu'à IND-08" if robustness != "robuste" else "à valider hors échantillon IND-08"
        return f"poche de signal, {suffix}"
    if avoid:
        return "contexte à éviter, signal inférieur à 52%"
    if not beats_simple:
        return "ne bat pas les indicateurs simples"
    return "signal intermédiaire"


def _update_report(result: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else "# Étude professionnelle du prix du maïs CBOT\n"
    marker = "\n## Analyse par contexte\n"
    if marker in text:
        text = text.split(marker)[0].rstrip()

    pockets = result[
        (result["signal_dominant"].eq("poche_signal"))
        & (result["n_obs"] >= MIN_OBS)
        & (result["beats_simple"])
    ].sort_values(["da", "n_obs"], ascending=False)
    avoid = result[(result["signal_dominant"].eq("a_eviter")) & (result["n_obs"] >= MIN_OBS)].sort_values("da")

    lines = [text.rstrip(), "", "## Analyse par contexte", ""]
    lines.append("Source : `artefacts/professional_study/context_analysis.parquet`.")
    lines.append(f"Cible de travail : `{TARGET_COL}`. Protocole pré-2023, walk-forward avec embargo.")
    lines.append("")
    lines.append("Poches de signal identifiées (DA > 60%, n_obs >= 50, bat les indicateurs simples) :")
    if pockets.empty:
        lines.append("- Aucune poche de signal exploitable selon ces critères.")
    else:
        for _, row in pockets.head(10).iterrows():
            lines.append(
                f"- `{row['context_type']}={row['context_value']}` : DA={row['da']:.3f}, "
                f"AUC={_fmt(row['auc'])}, n_obs={int(row['n_obs'])}, {row['robustness_level']}."
            )
    lines.append("")
    lines.append("Contextes à éviter (DA < 52%, n_obs >= 50) :")
    if avoid.empty:
        lines.append("- Aucun contexte à éviter selon ce seuil.")
    else:
        for _, row in avoid.head(10).iterrows():
            lines.append(
                f"- `{row['context_type']}={row['context_value']}` : DA={row['da']:.3f}, n_obs={int(row['n_obs'])}."
            )
    lines.append("")
    lines.append("Garde-fou : les contextes croisés et les résultats avec 50 <= n_obs < 100 restent exploratoires jusqu'à validation IND-08.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_experiment_index(result: pd.DataFrame) -> None:
    EXPERIMENT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    text = EXPERIMENT_INDEX.read_text(encoding="utf-8") if EXPERIMENT_INDEX.exists() else ""
    if "IND-04 — Analyse par contexte" in text:
        return
    exp_id = _next_exp_id(text)
    today = date.today().isoformat()
    pockets = result[result["signal_dominant"].eq("poche_signal")].sort_values(["da", "n_obs"], ascending=False)
    top = ", ".join(f"`{r.context_type}={r.context_value}`" for r in pockets.head(3).itertuples()) if not pockets.empty else "aucune poche"
    row = (
        f"| {exp_id} | {today} | `notebooks/corn_study/main/08_context_analysis.ipynb` | "
        "Le signal varie fortement selon saison, WASDE, régime et volatilité. | "
        "Walk-forward pré-2023 puis métriques DA/AUC/Brier par contexte. | "
        f"Poches principales : {top}. | Contextes exploratoires à valider IND-08. | neutral |\n"
    )
    detail = f"""
---

## {exp_id} — IND-04 — Analyse par contexte

**Date :** {today}
**Statut :** `neutral`

**Hypothèse :**
La performance globale masque des poches de signal par saison, publication WASDE, régime, volatilité ou niveau de stocks.

**Méthode :**
Prédictions walk-forward pré-2023 sur `{TARGET_COL}`, puis métriques par contexte avec comparaison aux indicateurs saisonnier et momentum.

**Résultat :**
Poches principales : {top}. Résultats complets dans `artefacts/professional_study/context_analysis.parquet`.

**Décision :**
Conserver ces contextes comme hypothèses exploratoires, à valider hors échantillon en IND-08.
"""
    if "|---|---|---|---|---|---|---|---|" in text:
        text = text.replace("|---|---|---|---|---|---|---|---|\n", "|---|---|---|---|---|---|---|---|\n" + row, 1)
    else:
        text = text.rstrip() + "\n\n" + row
    EXPERIMENT_INDEX.write_text(text.rstrip() + "\n" + detail, encoding="utf-8")


def _write_notebook(result: pd.DataFrame) -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    pockets = result[result["signal_dominant"].eq("poche_signal")].sort_values(["da", "n_obs"], ascending=False).head(15)
    avoid = result[result["signal_dominant"].eq("a_eviter")].sort_values("da").head(10)
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# IND-04 — Analyse par contexte\n\nAnalyse pré-2023, contextes exploratoires avant validation IND-08."),
        nbf.v4.new_markdown_cell("## Poches de signal\n\n" + _markdown_table(pockets)),
        nbf.v4.new_markdown_cell("## Contextes à éviter\n\n" + _markdown_table(avoid)),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "context = pd.read_parquet('../../../artefacts/professional_study/context_analysis.parquet')\n"
            "context.sort_values(['signal_dominant', 'da'], ascending=[True, False]).head(30)"
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)
    try:
        from nbconvert import HTMLExporter

        body, _ = HTMLExporter().from_notebook_node(nb)
        NOTEBOOK_EXPORT.write_text(body, encoding="utf-8")
    except Exception as exc:
        log.warning("context_notebook_export_failed", error=str(exc))


def _markdown_table(df: pd.DataFrame) -> str:
    cols = ["context_type", "context_value", "da", "auc", "brier", "n_obs", "seasonal_da", "momentum_da", "robustness_level", "commentaire"]
    if df.empty:
        return "Aucun résultat."
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df[cols].iterrows():
        values = []
        for col in cols:
            val = row[col]
            if isinstance(val, float) or pd.isna(val):
                values.append(_fmt(val))
            else:
                values.append(str(val))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if pd.isna(value):
        return "NA"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.3f}"


def _next_exp_id(text: str) -> str:
    nums = [int(x) for x in re.findall(r"EXP-(\d+)", text)]
    return f"EXP-{(max(nums) + 1) if nums else 1:03d}"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"])
    return out.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def main() -> None:
    result = run_context_analysis()
    pockets = result[result["signal_dominant"].eq("poche_signal")]
    print(f"Wrote {CONTEXT_ANALYSIS_PARQUET} rows={len(result)}")
    print(f"Pockets: {len(pockets)}")
    if not pockets.empty:
        print(pockets.sort_values(["da", "n_obs"], ascending=False).head(5)[["context_type", "context_value", "da", "n_obs"]].to_string(index=False))


if __name__ == "__main__":
    main()

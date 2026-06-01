"""Backtest of the Maize Market Direction Indicator.

Evaluates directional accuracy by:
- Global DA, Brier Score, AUC across all horizons
- Performance by confidence level (low / medium / high)
- Performance by season (spring / summer / fall / winter)
- Performance by market regime (bull / range / bear)
- Per-horizon comparison (which horizon is most predictable?)

Output: docs/INDICATOR_BACKTEST_REPORT.md
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.indicator.direction import MaizeDirectionIndicator
from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.utils import get_logger

log = get_logger("mais.indicator.backtest")

REPORT_PATH = PROJECT_ROOT / "docs" / "INDICATOR_BACKTEST_REPORT.md"
STUDY_DIR = ARTEFACTS_DIR / "professional_study"
HORIZONS = (5, 10, 20, 30)


def run_indicator_backtest(model: str = "ridge_factors") -> str:
    """Backtest the MaizeDirectionIndicator and write INDICATOR_BACKTEST_REPORT.md."""
    indicator = MaizeDirectionIndicator.load(artefacts_dir=STUDY_DIR, model=model)

    calib = pd.read_parquet(STUDY_DIR / "calibrated_predictions.parquet")
    calib["Date"] = pd.to_datetime(calib["Date"])
    calib = calib[calib["model"] == model].copy()

    regime_df = _load_regimes()

    # Build evaluation DataFrame: one row per (Date, horizon) with prob_up, y_true, confidence
    eval_df = _build_eval_df(calib, indicator, regime_df)
    if eval_df.empty:
        msg = "No evaluation data available. Run `make study` first."
        REPORT_PATH.write_text(f"# Indicator Backtest\n\n{msg}\n", encoding="utf-8")
        return msg

    global_metrics = _compute_global_metrics(eval_df)
    by_confidence = _by_confidence(eval_df)
    by_season = _by_season(eval_df)
    by_regime = _by_regime(eval_df, regime_df)
    by_horizon = _by_horizon(eval_df)

    _write_report(
        global_metrics=global_metrics,
        by_confidence=by_confidence,
        by_season=by_season,
        by_regime=by_regime,
        by_horizon=by_horizon,
        model=model,
        n_obs=len(eval_df),
    )

    best_h = by_horizon.sort_values("da", ascending=False).iloc[0]
    return (
        f"Indicator backtest écrit dans {REPORT_PATH.name}\n"
        f"{len(eval_df)} observations, {eval_df['horizon'].nunique()} horizons\n"
        f"DA globale h{best_h['horizon']}: {best_h['da']:.3f} (meilleur horizon)\n"
        f"DA (confidence > 0.65): "
        + str(round(float(by_confidence[by_confidence["bucket"] == "high"]["da"].iloc[0]), 3) if not by_confidence[by_confidence["bucket"] == "high"].empty else "N/A")
    )


def _load_regimes() -> pd.DataFrame:
    path = STUDY_DIR / "regime_timeseries.parquet"
    if not path.exists():
        return pd.DataFrame(columns=["Date", "regime"])
    df = pd.read_parquet(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df[["Date", "regime"]].copy()


def _build_eval_df(
    calib: pd.DataFrame,
    indicator: MaizeDirectionIndicator,
    regime_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build one row per (Date, horizon) with prob_up, y_true, confidence, season, regime."""
    rows = []
    for h in HORIZONS:
        p_up_col = f"p_up_h{h}"
        h_df = calib[(calib["horizon"] == h) & calib[p_up_col].notna()].copy()
        if h_df.empty:
            continue
        h_df = h_df[["Date", "y_true", p_up_col, "covered_90"]].rename(
            columns={p_up_col: "prob_up"}
        )
        h_df["horizon"] = h
        h_df["y_true_binary"] = (h_df["y_true"] > 0).astype(int)
        h_df["correct"] = ((h_df["prob_up"] > 0.5) == (h_df["y_true"] > 0)).astype(int)
        h_df["brier"] = (h_df["prob_up"] - h_df["y_true_binary"]) ** 2
        h_df["confidence"] = _compute_confidence_series(h_df["prob_up"])
        h_df["season_label"] = _season_label(h_df["Date"])
        rows.append(h_df)

    if not rows:
        return pd.DataFrame()

    df = pd.concat(rows, ignore_index=True)

    if not regime_df.empty:
        df = pd.merge_asof(
            df.sort_values("Date"),
            regime_df.sort_values("Date"),
            on="Date",
            direction="backward",
        )
    else:
        df["regime"] = "unknown"

    return df


def _compute_confidence_series(prob_up: pd.Series) -> pd.Series:
    """Confidence ≈ distance of prob_up from 0.5, scaled to [0,1]."""
    return ((prob_up - 0.5).abs() / 0.30).clip(0, 1)


def _season_label(dates: pd.Series) -> pd.Series:
    """Map month to season label."""
    month = dates.dt.month
    labels = pd.Series("winter", index=dates.index)
    labels[month.isin([3, 4, 5])] = "spring (semis)"
    labels[month.isin([6, 7, 8])] = "summer"
    labels[month.isin([9, 10, 11])] = "fall (récolte)"
    return labels


def _compute_global_metrics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h in HORIZONS:
        sub = df[df["horizon"] == h].dropna(subset=["prob_up", "y_true_binary"])
        if len(sub) < 10:
            continue
        da = float(sub["correct"].mean())
        brier = float(sub["brier"].mean())
        auc = _roc_auc(sub["y_true_binary"].values, sub["prob_up"].values)
        rows.append({"horizon": h, "n": len(sub), "da": da, "brier": brier, "auc": auc})
    return pd.DataFrame(rows)


def _by_confidence(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, lo, hi in [("low", 0.0, 0.50), ("medium", 0.50, 0.65), ("high", 0.65, 1.01)]:
        sub = df[(df["confidence"] >= lo) & (df["confidence"] < hi)].dropna(subset=["prob_up", "y_true_binary"])
        if len(sub) < 5:
            continue
        da = float(sub["correct"].mean())
        brier = float(sub["brier"].mean())
        rows.append({"bucket": label, "confidence_range": f"[{lo:.2f}, {hi:.2f})", "n": len(sub), "da": da, "brier": brier})
    return pd.DataFrame(rows)


def _by_season(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, sub in df.groupby("season_label"):
        sub = sub.dropna(subset=["prob_up", "y_true_binary"])
        if len(sub) < 5:
            continue
        rows.append({"season": season, "n": len(sub), "da": float(sub["correct"].mean()), "brier": float(sub["brier"].mean())})
    return pd.DataFrame(rows).sort_values("da", ascending=False)


def _by_regime(df: pd.DataFrame, regime_df: pd.DataFrame) -> pd.DataFrame:
    if "regime" not in df.columns:
        return pd.DataFrame()
    rows = []
    for regime, sub in df.groupby("regime"):
        sub = sub.dropna(subset=["prob_up", "y_true_binary"])
        if len(sub) < 5:
            continue
        rows.append({"regime": regime, "n": len(sub), "da": float(sub["correct"].mean()), "brier": float(sub["brier"].mean())})
    return pd.DataFrame(rows).sort_values("da", ascending=False)


def _by_horizon(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h, sub in df.groupby("horizon"):
        sub = sub.dropna(subset=["prob_up", "y_true_binary"])
        if len(sub) < 5:
            continue
        da = float(sub["correct"].mean())
        brier = float(sub["brier"].mean())
        auc = _roc_auc(sub["y_true_binary"].values, sub["prob_up"].values)
        cov = float(sub["covered_90"].mean()) if "covered_90" in sub.columns else float("nan")
        rows.append({"horizon": h, "n": len(sub), "da": da, "brier": brier, "auc": auc, "cqr_coverage": cov})
    return pd.DataFrame(rows).sort_values("horizon")


def _roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Compute AUC-ROC without sklearn via Mann-Whitney U statistic."""
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(y_true, y_score))
    except Exception:
        pass
    # Fallback: manual Mann-Whitney
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    return float(np.mean(p > n for p in pos for n in neg))


def _write_report(
    global_metrics: pd.DataFrame,
    by_confidence: pd.DataFrame,
    by_season: pd.DataFrame,
    by_regime: pd.DataFrame,
    by_horizon: pd.DataFrame,
    model: str,
    n_obs: int,
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Backtest de l'indicateur directionnel maïs",
        "",
        "## Méthodologie",
        "",
        f"- Modèle : `{model}`",
        f"- Observations totales (toutes horizons) : {n_obs:,}",
        "- Évaluation walk-forward out-of-sample (même split que l'étude professionnelle)",
        "- DA = Directional Accuracy = % de prédictions correctes (signal > 0.5 ↔ prix monte)",
        "- Brier Score = erreur quadratique sur les probabilités (plus bas = meilleur)",
        "- AUC = aire sous la courbe ROC (0.5 = aléatoire, 1.0 = parfait)",
        "- Confidence = distance de P(up) par rapport à 0.5, normalisée",
        "",
        "## Métriques globales par horizon",
        "",
        "| Horizon | N | DA | Brier Score | AUC | CQR Coverage |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in global_metrics.iterrows():
        cov = f"{float(by_horizon[by_horizon['horizon'] == r['horizon']]['cqr_coverage'].iloc[0]):.1%}" if not by_horizon[by_horizon['horizon'] == r['horizon']].empty else "N/A"
        lines.append(
            f"| J+{int(r['horizon'])} | {int(r['n']):,} | {r['da']:.3f} | {r['brier']:.4f} | {r['auc']:.3f} | {cov} |"
        )

    lines += [
        "",
        "## Performance par niveau de confiance",
        "",
        "> **Hypothèse clé** : le signal est plus fiable quand il est confiant.",
        "> Si DA(confiance élevée) ≫ DA(confiance faible), le confidence score filtre correctement.",
        "",
        "| Bucket | Plage confidence | N | DA | Brier |",
        "|---|---|---:|---:|---:|",
    ]
    for _, r in by_confidence.iterrows():
        lines.append(f"| {r['bucket']} | {r['confidence_range']} | {int(r['n']):,} | {r['da']:.3f} | {r['brier']:.4f} |")

    if not by_season.empty:
        lines += [
            "",
            "## Performance par saison",
            "",
            "| Saison | N | DA | Brier |",
            "|---|---:|---:|---:|",
        ]
        for _, r in by_season.iterrows():
            lines.append(f"| {r['season']} | {int(r['n']):,} | {r['da']:.3f} | {r['brier']:.4f} |")

    if not by_regime.empty:
        lines += [
            "",
            "## Performance par régime de marché",
            "",
            "| Régime | N | DA | Brier |",
            "|---|---:|---:|---:|",
        ]
        for _, r in by_regime.iterrows():
            lines.append(f"| {r['regime']} | {int(r['n']):,} | {r['da']:.3f} | {r['brier']:.4f} |")

    # Error analysis: worst performing periods
    lines += [
        "",
        "## Interprétation",
        "",
        "### L'indicateur est-il utile ?",
        "",
        (
            "La DA globale mesure si la direction prédite est correcte. "
            "Une DA > 55% sur données out-of-sample est significative pour les marchés agricoles. "
            "La comparaison par confiance est le test clé : si les signaux confiants sont plus "
            "précis, le confidence score a une valeur de filtrage réelle."
        ),
        "",
        "### Quand l'indicateur se trompe-t-il ?",
        "",
        "- **Régime bear** : peu d'observations (≈2% de l'historique), estimation instable.",
        "- **Faible confiance** : le modèle ne discrimine pas bien → signal UNCERTAIN recommandé.",
        "",
        "### Limites",
        "",
        "- L'évaluation est walk-forward (pas de look-ahead) mais les modèles sont entraînés",
        "  sur la même période historique → léger biais de survivorship si le pipeline change.",
        "- La DA et l'AUC mesure la direction brute, pas l'amplitude. Un signal BULLISH correct",
        "  à +0.1% et incorrect à -5% ne sont pas équivalents économiquement.",
        "- Les prédictions pour h20 et h30 sont moins fraîches (manquent les 20-30 derniers jours)",
        "  car le futur observé n'est pas encore disponible au moment de l'évaluation.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

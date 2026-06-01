"""Reporting utilities — standardised charts and tables for notebooks."""

from __future__ import annotations

import pandas as pd

MONTH_FR = {1:"Jan",2:"Fév",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
             7:"Jul",8:"Aoû",9:"Sep",10:"Oct",11:"Nov",12:"Déc"}


def style_benchmark_table(df: pd.DataFrame, metric: str = "rmse") -> pd.io.formats.style.Styler:
    """Return a styled DataFrame highlighting best/worst values."""
    ascending = metric in ("rmse", "mae")
    disp = df.copy()
    for c in ["rmse", "mae", "r2", "da", "da_nn", "accuracy", "auc"]:
        if c in disp.columns:
            disp[c] = disp[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")

    def highlight(s):
        if s.name != metric:
            return [""] * len(s)
        raw = df[metric].dropna()
        best = raw.min() if ascending else raw.max()
        return ["background-color: #c6efce; font-weight: bold"
                if pd.notna(df[metric].iloc[i]) and df[metric].iloc[i] == best else ""
                for i in range(len(s))]

    return disp.style.apply(highlight, axis=0)


def plot_benchmark_comparison(
    summary_df: pd.DataFrame,
    metric: str = "rmse",
    title: str = "Model benchmark",
    baseline_prefix: str = "baseline",
    ax=None,
):
    """Horizontal bar chart: baselines in red, ML in blue."""
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(12, max(4, len(summary_df) * 0.4)))

    ascending = metric in ("rmse", "mae")
    df = summary_df.sort_values(metric, ascending=ascending).copy()
    colors = ["#d9534f" if baseline_prefix in str(m) else "#5bc0de"
              for m in df["model"]]
    ax.barh(df["model"], df[metric], color=colors, alpha=0.85)

    best_base = df[df["model"].str.contains(baseline_prefix)][metric]
    if not best_base.empty:
        ref = best_base.min() if ascending else best_base.max()
        ax.axvline(ref, color="red", lw=1.5, ls="--", label=f"Best baseline ({ref:.4f})")

    ax.set_title(title)
    ax.set_xlabel(metric)
    legend = [mpatches.Patch(facecolor="#d9534f", alpha=0.85, label="Baseline"),
              mpatches.Patch(facecolor="#5bc0de", alpha=0.85, label="ML model")]
    ax.legend(handles=legend)
    return ax


def plot_strategy_comparison(summary_df: pd.DataFrame, ax=None):
    """Bar chart comparing farmer strategies."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 5))

    df = summary_df.sort_values("avg_revenue_usd_bu", ascending=False)
    colors = ["#5cb85c" if "dca" in s or "model" in s else
              "#d9534f" if "harvest" in s else "#5bc0de"
              for s in df["strategy"]]
    ax.bar(df["strategy"], df["avg_revenue_usd_bu"], color=colors, alpha=0.85)

    if "avg_revenue_usd_bu" in df.columns:
        for i, (_, row) in enumerate(df.iterrows()):
            ax.annotate(f"{row['avg_revenue_usd_bu']:.3f}",
                        xy=(i, row["avg_revenue_usd_bu"] + 0.005),
                        ha="center", fontsize=9, fontweight="bold")

    ax.set_title("Revenu moyen USD/bu par stratégie agriculteur")
    ax.set_ylabel("USD/bu")
    plt.xticks(rotation=20, ha="right")
    return ax


def notebook_header(
    question: str,
    hypothesis: str,
    data_used: str,
    interest: str,
) -> str:
    """Return a markdown string for the standard notebook header block."""
    return f"""
| | |
|---|---|
| **Question** | {question} |
| **Hypothèse** | {hypothesis} |
| **Données** | {data_used} |
| **Intérêt agricole** | {interest} |
"""

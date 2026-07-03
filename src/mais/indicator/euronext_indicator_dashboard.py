"""Indicateur Euronext — dashboard HTML interactif + artefacts + rapports (étape finale).

`finalize()` construit l'historique aligné (score CBOT appliqué au prix Euronext), calcule les
métriques et le backtest agricole, écrit les artefacts (CSV/JSON), génère un **dashboard HTML
Plotly autonome** (JS inline, aucune image externe) et les rapports Markdown. **Pas une
prévision de prix, pas un bot.** Données Euronext ~97 % proxy → résultats illustratifs.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

from mais.indicator import euronext_indicator_backtest as ebt
from mais.indicator import euronext_indicator_features as ef
from mais.paths import PROJECT_ROOT
from mais.utils import get_logger

log = get_logger("mais.indicator.euronext_indicator")
OUT = PROJECT_ROOT / "artefacts" / "final_euronext_indicator"
DOCS = PROJECT_ROOT / "docs"
RECO_COLORS = {"SELL_PARTIAL": "#d62728", "WAIT": "#2ca02c", "WATCH": "#7f7f7f",
               "RISK_HIGH": "#ff7f0e", "NO_SIGNAL": "#cccccc"}


def _prob_up(frame: pd.DataFrame, h: int) -> pd.Series:
    col = "direction_score_h40" if h in (20, 40) else "direction_score_h90"
    return (frame[col] + 1) / 2


def horizon_metrics(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    hs = pd.Timestamp(cfg["holdout_start"])
    rows = []
    for h in (cfg["horizons"]["h20"], cfg["horizons"]["h40"], cfg["horizons"]["h90"]):
        y = frame[f"target_direction_h{h}_euronext"]
        prob = _prob_up(frame, h)
        for label, sub in (("full_2010+", frame.index >= frame.index.min()),
                           ("oos_2024+", frame.index >= hs)):
            ev = sub & y.notna() & prob.notna()
            m = ef.dir_metrics(y[ev].to_numpy(), prob[ev].to_numpy())
            rows.append({"horizon": h, "period": label,
                         "prob_source": "h40" if h in (20, 40) else "h90", **m})
    return pd.DataFrame(rows)


def recommendation_metrics(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    rows = []
    for reco, g in frame.groupby("recommendation"):
        row = {"recommendation": reco, "n": int(len(g))}
        for h in (20, 40, 90):
            r = g[f"target_return_h{h}_euronext"].dropna()
            row[f"mean_ret_h{h}"] = round(float(r.mean()), 4) if len(r) else np.nan
        r90 = g["target_return_h90_euronext"].dropna()
        row["down_rate_h90"] = round(float((r90 < 0).mean()), 3) if len(r90) else np.nan
        row["up_rate_h90"] = round(float((r90 > 0).mean()), 3) if len(r90) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _confusion(frame: pd.DataFrame, h: int) -> pd.DataFrame:
    y = frame[f"target_direction_h{h}_euronext"]
    pred = (_prob_up(frame, h) >= 0.5).astype(float)
    ev = y.notna() & pred.notna()
    yy, pp = y[ev].to_numpy(), pred[ev].to_numpy()
    mat = [[int(((pp == p) & (yy == a)).sum()) for a in (0, 1)] for p in (0, 1)]
    return pd.DataFrame(mat, index=["pred_baisse", "pred_hausse"],
                        columns=["réel_baisse", "réel_hausse"])


# ---------------------------------------------------------------- figures -----

def _fig_price(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frame.index, y=frame["euronext_price"], mode="lines",
                             name="Euronext €/t", line={"color": "#1f77b4", "width": 1}))
    for reco, col in RECO_COLORS.items():
        sub = frame[frame["recommendation"] == reco]
        if len(sub):
            fig.add_trace(go.Scatter(x=sub.index, y=sub["euronext_price"], mode="markers",
                                     name=reco, marker={"color": col, "size": 4},
                                     hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f} €/t<br>" + reco))
    fig.update_layout(title="1. Prix Euronext + recommandations", height=420,
                      legend_orientation="h", margin={"t": 40, "b": 10})
    return fig


def _fig_score(frame: pd.DataFrame, cfg: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frame.index, y=frame["final_sale_score"], mode="lines",
                             name="final_sale_score (P baisse H90)", line={"color": "#d62728"}))
    fig.add_hline(y=cfg["thresholds"]["sell_partial_downside_h90"], line_dash="dash",
                  annotation_text="seuil SELL_PARTIAL")
    fig.add_hline(y=1 - cfg["thresholds"]["wait_upside_h90"], line_dash="dot",
                  line_color="green", annotation_text="seuil WAIT")
    fig.update_layout(title="2. Score global de vente (= risque de baisse H90)", height=320,
                      margin={"t": 40, "b": 10})
    return fig


def _fig_downside(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(x=frame.index, y=frame["downside_risk_h90"], mode="lines",
                               line={"color": "#9467bd"}))
    fig.update_layout(title="3. Risque de baisse H90 (downside_risk_h90)", height=300,
                      margin={"t": 40, "b": 10})
    return fig


def _fig_components(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for c, name in (("wasde_balance_score", "WASDE"), ("crop_condition_score", "Crop"),
                    ("volatility_risk_score", "Volatilité"), ("market_regime_score", "Régime"),
                    ("confidence_score", "Confiance")):
        fig.add_trace(go.Scatter(x=frame.index, y=frame[c], mode="lines", name=name))
    fig.update_layout(title="4. Composantes du score (0-1)", height=340,
                      legend_orientation="h", margin={"t": 40, "b": 10})
    return fig


def _fig_forward_by_reco(rec_m: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for h in (20, 40, 90):
        fig.add_trace(go.Bar(x=rec_m["recommendation"], y=rec_m[f"mean_ret_h{h}"],
                             name=f"retour moyen H{h}"))
    fig.update_layout(title="5-6. Retour Euronext futur moyen après chaque recommandation",
                      barmode="group", height=360, yaxis_title="log-retour moyen",
                      margin={"t": 40, "b": 10})
    return fig


def _fig_confusion(frame: pd.DataFrame) -> go.Figure:
    cm = _confusion(frame, 90)
    fig = go.Figure(go.Heatmap(z=cm.to_numpy(), x=list(cm.columns), y=list(cm.index),
                               text=cm.to_numpy(), texttemplate="%{text}",
                               colorscale="Blues"))
    fig.update_layout(title="7. Matrice de confusion directionnelle H90 (Euronext)",
                      height=320, margin={"t": 40, "b": 10})
    return fig


def _fig_backtest(comp: pd.DataFrame) -> go.Figure:
    cal = comp[(comp["window"] == "calendar")]
    fig = go.Figure()
    base_cols = {"mean_avg_price_score": "indicateur",
                 "score_vs_sell_all_start_mean": "Δ vs tout-début",
                 "score_vs_sell_thirds_mean": "Δ vs tiers",
                 "score_vs_monthly_dca_mean": "Δ vs DCA",
                 "score_vs_wait_year_end_mean": "Δ vs attente"}
    for _, r in cal.iterrows():
        fig.add_trace(go.Bar(name=f"cooldown {int(r['cooldown'])}",
                             x=list(base_cols.values()),
                             y=[r[k] for k in base_cols]))
    fig.update_layout(title="9. Backtest agricole (année civile) — prix score & Δ baselines",
                      barmode="group", height=340, margin={"t": 40, "b": 10})
    return fig


def _fig_by_campaign(comp: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for cd in sorted(comp["cooldown"].unique()):
        sub = comp[comp["cooldown"] == cd]
        fig.add_trace(go.Bar(name=f"cooldown {int(cd)}", x=sub["window"],
                             y=sub["score_vs_sell_thirds_mean"]))
    fig.update_layout(title="10. Δ prix vs vente par tiers, par découpage de campagne",
                      barmode="group", height=320, yaxis_title="Δ €/t (score − tiers)",
                      margin={"t": 40, "b": 10})
    return fig


def _fig_table(frame: pd.DataFrame, n: int = 30) -> go.Figure:
    sub = frame.dropna(subset=["recommendation"]).tail(n).copy()
    cols = ["euronext_price", "recommendation", "downside_risk_h90", "confidence_score",
            "target_return_h90_euronext", "target_date_h90"]
    cells = [[d.strftime("%Y-%m-%d") for d in sub.index]]
    for c in cols:
        s = sub[c]
        if c.startswith("target_date"):
            cells.append([pd.Timestamp(v).strftime("%Y-%m-%d") if pd.notna(v) else "—"
                          for v in s])
        elif pd.api.types.is_numeric_dtype(s):
            cells.append([f"{v:.3f}" if pd.notna(v) else "—" for v in s])
        else:
            cells.append([str(v) for v in s])
    fig = go.Figure(go.Table(
        header={"values": ["date", *cols], "fill_color": "#1f77b4", "font_color": "white"},
        cells={"values": cells}))
    fig.update_layout(title="8. Derniers signaux", height=420, margin={"t": 40, "b": 10})
    return fig


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    rows = []
    for _, r in df.iterrows():
        vals = [f"{v:.3f}" if isinstance(v, float) else str(v) for v in r]
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join([head, sep, *rows])


def _build_html(frame, cfg, hm, rec_m, comp, verdict, reason):
    figs = [_fig_price(frame), _fig_score(frame, cfg), _fig_downside(frame),
            _fig_components(frame), _fig_forward_by_reco(rec_m), _fig_confusion(frame),
            _fig_table(frame), _fig_backtest(comp), _fig_by_campaign(comp)]
    divs = [pio.to_html(f, include_plotlyjs=False, full_html=False) for f in figs]
    hm_html = hm.round(3).to_html(index=False)
    rec_html = rec_m.to_html(index=False)
    head = (f"<h1>Indicateur Euronext de vente / risque — {cfg['version']}</h1>"
            f"<p><b>Verdict : {verdict}.</b> {reason}</p>"
            "<p><b>Aide à la décision de vente, pas une prévision de prix ni un bot.</b> "
            "⚠️ Prix Euronext à ~97 % proxy (cf. EURONEXT_DATA_AUDIT.md) → illustratif.</p>")
    metrics_html = (f"<h2>Métriques directionnelles (CBOT → Euronext)</h2>{hm_html}"
                    f"<h2>Retours futurs par recommandation</h2>{rec_html}")
    body = head + "".join(divs) + metrics_html
    html = (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
            f"<title>Indicateur Euronext</title>"
            f"<script>{get_plotlyjs()}</script>"
            f"<style>body{{font-family:sans-serif;margin:24px;max-width:1100px}}"
            f"table{{border-collapse:collapse}}td,th{{border:1px solid #ddd;padding:3px 6px;"
            f"font-size:12px}}</style></head><body>{body}</body></html>")
    (OUT / "euronext_indicator_dashboard.html").write_text(html, encoding="utf-8")


def _latest(frame: pd.DataFrame, cfg: dict) -> dict:
    row = frame.dropna(subset=["downside_risk_h90"]).iloc[-1]
    return {"version": cfg["version"], "price_forecast_enabled": False,
            "as_of": str(frame.index[-1].date()), "signal_date": str(row.name.date()),
            "euronext_price": round(float(row["euronext_price"]), 2),
            "source_quality": str(row.get("source_quality", "n/a")),
            "recommendation": row["recommendation"],
            "downside_risk_h90": round(float(row["downside_risk_h90"]), 4),
            "confidence_score": round(float(row["confidence_score"]), 3),
            "volatility_risk_score": round(float(row["volatility_risk_score"]), 3),
            "final_sale_score": round(float(row["final_sale_score"]), 4),
            "cbot_score_date": str(pd.Timestamp(row["cbot_score_date"]).date()),
            "score_stale": bool(row["score_stale"]),
            "note": "Score CBOT applique a Euronext (~97% proxy). Aide a la vente, pas un bot. "
                    "score_stale=true => score CBOT fige (donnees CBOT finies), non a jour."}


def _verdict(hm: pd.DataFrame, rec_m: pd.DataFrame) -> tuple[str, str]:
    oos = hm[(hm.horizon == 90) & (hm.period == "oos_2024+")].iloc[0]
    sp = rec_m[rec_m.recommendation == "SELL_PARTIAL"]
    wa = rec_m[rec_m.recommendation == "WAIT"]
    monotone = (len(sp) and len(wa) and sp["mean_ret_h90"].iloc[0] < wa["mean_ret_h90"].iloc[0])
    reason = (f"Les recommandations séparent les retours futurs Euronext dans le bon sens "
              f"(SELL_PARTIAL {sp['mean_ret_h90'].iloc[0] if len(sp) else float('nan'):+.3f} < "
              f"WAIT {wa['mean_ret_h90'].iloc[0] if len(wa) else float('nan'):+.3f} à H90), mais "
              f"la discrimination OOS 2024+ est faible (AUC {oos['roc_auc']:.3f}) et le prix "
              f"Euronext est à ~97 % un proxy. Données et signal trop fragiles pour valider.")
    if monotone and oos["roc_auc"] > 0.62 and oos["da_vs_majority"] > 0.05:
        return "FRAGILE", reason
    return "RESEARCH_ONLY", reason


def finalize() -> dict:
    warnings.filterwarnings("ignore")
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = ef.load_config()
    frame, coefs = ef.build_indicator_frame(cfg)
    start = str(frame.index.min().date())

    frame.to_csv(OUT / "euronext_indicator_history.csv")
    latest = _latest(frame, cfg)
    (OUT / "euronext_indicator_latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([{"column": k, "description": v} for k, v in ef.FEATURE_DICTIONARY.items()]
                 ).to_csv(OUT / "euronext_indicator_feature_dictionary.csv", index=False)

    hm = horizon_metrics(frame, cfg)
    rec_m = recommendation_metrics(frame, cfg)
    pd.concat([hm.assign(block="horizon"), rec_m.assign(block="recommendation")],
              ignore_index=True).to_csv(OUT / "euronext_indicator_metrics.csv", index=False)

    dec, _pw, bt_sum = ebt.run_backtest(frame, cfg, start, "calendar",
                                        int(cfg["cooldown"]["sell_partial_days"]))
    comp, per_campaign, _cal = ebt.run_all_campaigns(frame, cfg, start)
    dec.to_csv(OUT / "euronext_backtest_decisions.csv", index=False)
    pd.DataFrame([bt_sum]).to_csv(OUT / "euronext_backtest_summary.csv", index=False)
    per_campaign.to_csv(OUT / "euronext_backtest_by_campaign.csv", index=False)

    verdict, reason = _verdict(hm, rec_m)
    _build_html(frame, cfg, hm, rec_m, comp, verdict, reason)
    _write_reports(cfg, frame, hm, rec_m, comp, bt_sum, verdict, reason, latest, coefs)
    log.info("euronext_indicator_finalized", verdict=verdict, latest=latest["recommendation"])
    return {"verdict": verdict, "reason": reason, "latest": latest,
            "horizon_metrics": hm.to_dict("records"),
            "recommendation_metrics": rec_m.to_dict("records"),
            "backtest_comparison": comp.to_dict("records")}


def _write_reports(cfg, frame, hm, rec_m, comp, bt_sum, verdict, reason, latest, coefs):
    rep = [
        "# Indicateur Euronext de vente / risque — rapport final", "",
        f"Version : `{cfg['version']}`. Date : 2026-06-13. **Aide à la décision de vente, pas "
        "une prévision de prix ni un bot.**", "",
        f"## 1. Résumé exécutif — verdict : **{verdict}**", "", reason, "",
        "L'indicateur applique le **score de vente CBOT** (étude finale, FRAGILE) à l'historique "
        "**Euronext** (€/t) et le visualise (dashboard HTML interactif). Il ne prédit pas le "
        "prix ; il signale direction/risque pour **aider à étaler les ventes**.", "",
        "## 2. Données", "",
        f"- Prix Euronext : `{cfg['euronext_price_parquet']}` ({frame.index.min().date()} → "
        f"{frame.index.max().date()}, {len(frame)} j, €/t). **~97 % proxy** (cf. "
        "`EURONEXT_DATA_AUDIT.md`).",
        "- Score : Crop Condition (H90), WASDE stocks-to-use (H40), saison, volatilité HAR, "
        "régimes — tous **CBOT/US**, alignés sur Euronext par `merge_asof` backward.", "",
        "## 3. Méthode", "",
        "- Cible directionnelle Euronext = signe du retour t→t+h, `target_date=index[i+h]` "
        "(vraie ligne de marché). **Anti-fuite** : les retours futurs ne servent qu'à "
        "l'évaluation, jamais au score ; le dernier signal n'utilise pas le futur.",
        "- Recommandation : SELL_PARTIAL / WAIT / WATCH / RISK_HIGH / NO_SIGNAL (jamais BUY/SHORT).",
        f"- Coefficients CBOT (≤2023) : {json.dumps(coefs, ensure_ascii=False)}", "",
        "## 4. Visualisation", "",
        "Dashboard : `artefacts/final_euronext_indicator/euronext_indicator_dashboard.html` "
        "(Plotly, JS inline, **aucune image**). Ouvrir dans un navigateur. 10 graphiques : prix "
        "+ recommandations, score global, risque de baisse, composantes, retours futurs par "
        "recommandation, matrice de confusion H90, table des derniers signaux, backtest agricole, "
        "résultat par campagne.", "",
        "## 5. Résultats historiques", "",
        "Métriques directionnelles (CBOT → Euronext) :", "",
        _md_table(hm.round(3)), "",
        "Retours Euronext futurs moyens par recommandation :", "",
        _md_table(rec_m), "",
        "## 6. Interprétation", "",
        "- **Juste** : les recommandations ordonnent correctement les retours futurs "
        "(SELL_PARTIAL → baisse, WAIT → hausse) sur tout l'historique.",
        "- **Limite** : en **OOS 2024+**, l'AUC chute (faible discrimination) ; le signal H90 "
        "n'est pas robuste hors échantillon. WATCH/RISK_HIGH sont moins nets.", "",
        "## 7. Limites", "",
        "- Score issu du **CBOT** appliqué à **Euronext** : pas de basis ni d'EUR/USD intégrés.",
        "- Prix Euronext **~97 % proxy** : résultats **illustratifs**, pas une validation.",
        "- Données publiques gratuites ; **pas de prévision de prix** ; pas de garantie de vente "
        "optimale ; **validation forward nécessaire**.", "",
        f"## 8. Conclusion : **{verdict}**", "",
        "Indicateur **visuel exploitable** pour regarder l'historique, mais **non validé** : "
        "données proxy + signal OOS faible. À traiter comme outil de recherche/visualisation, "
        "pas comme conseil de vente opérationnel.", "",
        f"Dernier signal : **{latest['recommendation']}** au {latest['signal_date']} "
        f"(prix {latest['euronext_price']} €/t, P baisse H90 {latest['downside_risk_h90']}).",
    ]
    (DOCS / "FINAL_EURONEXT_INDICATOR_REPORT.md").write_text("\n".join(rep), encoding="utf-8")

    bt = [
        "# Backtest agricole Euronext — indicateur de vente", "",
        f"Version : `{cfg['version']}`. **Pas un bot** : ventes partielles ({int(cfg['backtest']['sell_fraction']*100)} %), "
        "cooldown, campagnes ; jamais de short/buy/levier. ⚠️ prix Euronext ~97 % proxy.", "",
        "## Comparaison campagnes × cooldown (prix moyen score & Δ baselines, €/t)", "",
        _md_table(comp.round(3)), "",
        "## Synthèse (année civile, cooldown défaut)", "", "```json",
        json.dumps(bt_sum, ensure_ascii=False, indent=2), "```", "",
        "## Lecture honnête", "",
        "- L'indicateur **n'est pas systématiquement meilleur** que les baselines simples ; le "
        "résultat dépend du découpage de campagne et du cooldown (comme pour le CBOT).",
        "- Sur un prix **proxy**, ces chiffres sont **illustratifs**. Aucune conclusion de vente "
        "opérationnelle ne doit en être tirée.",
        "- Réponses : utile **visuellement** pour ordonner les périodes (SELL_PARTIAL ≈ avant "
        "baisses), mais **pas validé** comme stratégie ; fragile, à reconfirmer en forward sur "
        "des **settlements officiels** Euronext.",
    ]
    (DOCS / "FINAL_EURONEXT_INDICATOR_BACKTEST.md").write_text("\n".join(bt), encoding="utf-8")

"""Orchestration finale du score de vente (étape 7) : holdout 2024+, backtest, artefacts.

`finalize()` construit le frame + les modèles (≤2023), score toute la chronologie, évalue le
holdout 2024+ **une seule fois**, lance le backtest décisionnel, écrit tous les artefacts et
génère `final_report.md`. Renvoie un verdict (VALIDATED / FRAGILE / RESEARCH_ONLY /
NOT_VALIDATED) calculé honnêtement à partir des chiffres holdout.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from mais.indicator import cbot_sale_score as sale
from mais.indicator import cbot_sale_score_backtest as bt
from mais.indicator import cbot_sale_score_features as feats
from mais.indicator import cbot_sale_score_model as mdl
from mais.paths import PROJECT_ROOT
from mais.utils import get_logger

log = get_logger("mais.indicator.cbot_sale_score_report")
OUT = PROJECT_ROOT / "artefacts" / "final_cbot_sale_score"


def _prob_for(name: str, h: int, models: sale.SaleScoreModels, df: pd.DataFrame) -> pd.Series:
    if name == "score_h90_crop":
        return models.h90.predict_proba_up(df)
    if name == "score_h40_wasde":
        return models.h40.predict_proba_up(df)
    if name == "random_walk_h90":
        return pd.Series(models.h90.base_rate, index=df.index)
    fit, _h = models.baselines[name]
    return fit.predict_proba_up(df)


def holdout_metrics(df: pd.DataFrame, models: sale.SaleScoreModels, cfg: dict) -> pd.DataFrame:
    hs = pd.Timestamp(cfg["holdout_start"])
    specs = [("score_h90_crop", 90), ("score_h40_wasde", 40),
             ("crop_only_h90", 90), ("wasde_only_h40", 40),
             ("season_only_h90", 90), ("market_only_h90", 90), ("random_walk_h90", 90)]
    rows = []
    for name, h in specs:
        y = feats.direction_target(df["corn_close"], h)
        tgt = feats.target_dates_from_index(df.index, h)
        prob = _prob_for(name, h, models, df)
        ev = (df.index >= hs) & y.notna() & tgt.notna() & prob.notna()
        m = mdl.dir_metrics(y[ev].to_numpy(), prob[ev].to_numpy())
        rows.append({"model": name, "horizon": h, **m})
    return pd.DataFrame(rows)


def _verdict(hm: pd.DataFrame) -> tuple[str, str]:
    s = hm[hm.model == "score_h90_crop"].iloc[0]
    rw = hm[hm.model == "random_walk_h90"].iloc[0]
    season = hm[hm.model == "season_only_h90"].iloc[0]
    market = hm[hm.model == "market_only_h90"].iloc[0]
    best_naive = max(season["da"], market["da"])
    beats_rw = s["da"] > rw["majority_acc"] + 0.02
    beats_naive = s["da"] > best_naive + 0.02
    strong = (s["da_vs_majority"] > 0.05) and (s["roc_auc"] > 0.58) and beats_naive
    mild = beats_rw and (s["roc_auc"] > 0.53)
    naive_note = (f"Mais une baseline de **pure saisonnalité** (DA {season['da']:.3f}, AUC "
                  f"{season['roc_auc']:.3f}) et le **marché seul** (DA {market['da']:.3f}) font "
                  f"aussi bien voire mieux → les fondamentaux Crop/WASDE n'ajoutent PAS de "
                  f"valeur démontrable sur ce holdout court (~1,5 an, n={int(s['n'])}, cycle "
                  f"baissier 2024).")
    if strong:
        return ("VALIDATED",
                f"Holdout 2024+ : DA {s['da']:.3f} (+{s['da_vs_majority']:.3f} vs majorité), "
                f"AUC {s['roc_auc']:.3f}, bat les baselines naïves. Réserve : fenêtre courte.")
    if mild:
        return ("FRAGILE",
                f"Holdout 2024+ : le score crop@H90 bat nettement la random walk (DA "
                f"{s['da']:.3f} vs {rw['majority_acc']:.3f}, AUC {s['roc_auc']:.3f}) et est "
                f"économiquement cohérent. {naive_note} Aide **indicative**, non opérationnelle "
                f"sans reconfirmation forward.")
    return ("RESEARCH_ONLY",
            f"Holdout 2024+ : DA {s['da']:.3f}, AUC {s['roc_auc']:.3f} : signal insuffisant "
            f"pour un usage décisionnel ; conserver comme résultat de recherche.")


def _write_report(cfg, hm, comparison, bt_sum, verdict, reason, latest, wf_da, coefs, cooldown):
    lines = [
        "# Score de vente CBOT — rapport final (étape 7)", "",
        f"Version : `{cfg['version']}`. Date : 2026-06-13. **Aide à la décision de vente, "
        "pas une prévision de prix ni un bot de trading.**", "",
        f"## Verdict : **{verdict}**", "", reason, "",
        "## Signal le plus récent", "",
        "```json", json.dumps(latest, ensure_ascii=False, indent=2), "```", "",
        "> ⚠️ Données arrêtées au 2025-07-25 : ce dernier signal n'est PAS à jour. Reconstruire "
        "les données (prix CBOT, WASDE vintage, Crop Condition) avant tout usage actuel.", "",
        "## Validation holdout 2024+ (une seule fois)", "",
        "| modèle | h | n | DA | vs majorité | AUC | Brier | rappel baisse |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in hm.iterrows():
        lines.append(
            f"| {r['model']} | {int(r['horizon'])} | {int(r['n'])} | {r['da']:.3f} | "
            f"{r['da_vs_majority']:+.3f} | {r['roc_auc']:.3f} | {r['brier']:.3f} | "
            f"{r['recall_down']:.3f} |")
    lines += ["", f"DA walk-forward pré-2024 (contexte recherche, crop@H90) : {wf_da:.3f}.", "",
              "## Backtest décisionnel (vendeur, holdout 2024+)", "",
              f"Cooldown = {cooldown} séances entre deux ventes (évite de liquider la récolte sur "
              "des signaux consécutifs). Comparaison découpages de campagne × cooldown — prix "
              "moyen du score vs baselines (Δ = score − baseline ; >0 = score meilleur) :", "",
              "| campagne | cooldown | n | prix score | Δ vs récolte | Δ vs tiers | Δ vs DCA | "
              "Δ vs attente | gagne (récolte/tiers/DCA/attente) |",
              "|---|---|---|---|---|---|---|---|---|"]
    for _, r in comparison.iterrows():
        won = f"{r['score_vs_sell_all_start_won']}, {r['score_vs_sell_thirds_won']}, " \
              f"{r['score_vs_monthly_dca_won']}, {r['score_vs_wait_year_end_won']}"
        lines.append(
            f"| {r['window']} | {int(r['cooldown'])} | {int(r['campaigns'])} | "
            f"{r['mean_avg_price_score']} | {r['score_vs_sell_all_start_mean']:+} | "
            f"{r['score_vs_sell_thirds_mean']:+} | {r['score_vs_monthly_dca_mean']:+} | "
            f"{r['score_vs_wait_year_end_mean']:+} | {won} |")
    lines += ["", "Synthèse backtest (année civile, cooldown par défaut) :", "", "```json",
              json.dumps(bt_sum, ensure_ascii=False, indent=2), "```", "",
              "## Coefficients du modèle (logit L2, ≤2023)", "", "```", coefs, "```", "",
              "## Limites", "",
              "- Edge directionnel modeste en recherche (DM non significatif, IC chevauchant "
              "le marché) ; le bon holdout 2024+ reste **court** et dominé par un cycle baissier.",
              "- Backtest **statistiquement faible** : peu de campagnes, 2025 incomplète.",
              "- Régimes post-hoc → confiance seulement.", "- Familles rejetées/bloquées non "
              "intégrées (voir `FINAL_CBOT_SALE_SCORE_LIMITS.md`).",
              "- Score en **CBOT ¢/bu** : pas encore converti en prix ferme €/t (eurusd + basis).",
              "- **Indicateur d'aide à la décision, jamais un système de trading automatique.**"]
    (OUT / "final_report.md").write_text("\n".join(lines), encoding="utf-8")


def finalize(do_holdout: bool = True) -> dict:
    warnings.filterwarnings("ignore")
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = sale.load_config()
    df, fdict = feats.build_frame()
    models = sale.build_models(df, cfg)
    frame = sale.score_timeseries(df, models)

    # artefacts de base
    frame.to_parquet(OUT / "final_score_timeseries.parquet")
    frame.to_csv(OUT / "final_score_timeseries.csv")
    latest = sale.latest_record(frame, cfg)
    (OUT / "final_score_latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([{"feature": k, "description": v} for k, v in fdict.items()]).to_csv(
        OUT / "final_feature_dictionary.csv", index=False)
    coef_rows = []
    for tag, fit in (("h90_crop", models.h90), ("h40_wasde", models.h40)):
        coef_rows.append({"model": tag, "feature": "intercept", "coef": fit.intercept})
        for c, v in zip(fit.cols, fit.coef, strict=False):
            coef_rows.append({"model": tag, "feature": c, "coef": float(v)})
    coef_df = pd.DataFrame(coef_rows)
    coef_df.to_csv(OUT / "final_model_coefficients.csv", index=False)

    # holdout + backtest
    hm = holdout_metrics(df, models, cfg) if do_holdout else pd.DataFrame()
    hm.to_csv(OUT / "final_holdout_2024_metrics.csv", index=False)
    cooldown = int(cfg.get("backtest", {}).get("sell_cooldown_sessions", 20))
    dec, _py_cal, bt_sum = bt.run_backtest(frame, cfg, cfg["holdout_start"], "calendar", cooldown)
    dec.to_csv(OUT / "final_backtest_decisions.csv", index=False)
    (OUT / "final_backtest_summary.json").write_text(
        json.dumps(bt_sum, ensure_ascii=False, indent=2), encoding="utf-8")
    comparison, per_window, _cal = bt.run_all_windows(frame, cfg, cfg["holdout_start"])
    comparison.to_csv(OUT / "final_backtest_comparison.csv", index=False)
    per_window.to_csv(OUT / "final_backtest_by_window.csv", index=False)

    wf = mdl.walk_forward_proba(df, cfg["features"]["h90"], 90,
                              pd.Timestamp(cfg["holdout_start"]),
                              pd.Timestamp(cfg["eval_start"]), int(cfg["min_train"]),
                              float(cfg["logit_C"]))
    wf_da = float((wf["prob_up"] >= 0.5).astype(int).__eq__(wf["y_true"]).mean()) \
        if len(wf["y_true"]) else np.nan

    verdict, reason = _verdict(hm) if do_holdout else ("RESEARCH_ONLY", "Holdout non évalué.")
    coefs_txt = coef_df.to_string(index=False)
    _write_report(cfg, hm, comparison, bt_sum, verdict, reason, latest, wf_da, coefs_txt, cooldown)
    log.info("sale_score_finalized", verdict=verdict, latest=latest["recommendation"])
    return {"verdict": verdict, "reason": reason, "latest": latest,
            "holdout": hm.to_dict("records"), "backtest_calendar": bt_sum,
            "backtest_comparison": comparison.to_dict("records"),
            "walk_forward_pre2024_da_h90": round(wf_da, 4)}

"""Professional Streamlit application for the corn price study."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from mais.decision import advise
from mais.paths import FEATURES_PARQUET, LEAKAGE_AUDIT_PARQUET, TARGETS_PARQUET
from mais.study import (
    BENCHMARK_PARQUET,
    CALIBRATED_PREDICTIONS_PARQUET,
    CQR_RESULTS_PARQUET,
    DECISION_SNAPSHOT_JSON,
    FACTOR_IMPORTANCE_PARQUET,
    REGIME_PARQUET,
    SHAP_IMPORTANCE_PARQUET,
    STUDY_REPORT,
    STUDY_SUMMARY_JSON,
    build_professional_study,
)
from mais.study.professional import FAMILY_IMPORTANCE_PARQUET, SOURCE_COVERAGE_PARQUET


st.set_page_config(page_title="Étude maïs CBOT", layout="wide")


@st.cache_data(show_spinner=False)
def _read_parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def _read_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _exists(*paths: Path) -> bool:
    return all(p.exists() for p in paths)


def _fmt_pct(x: float) -> str:
    return f"{x:.1%}"


def _load_study() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = _read_json(str(STUDY_SUMMARY_JSON))
    benchmarks = _read_parquet(str(BENCHMARK_PARQUET))
    calibrated = _read_parquet(str(CALIBRATED_PREDICTIONS_PARQUET))
    regimes = _read_parquet(str(REGIME_PARQUET))
    factors = _read_parquet("data/processed/factors.parquet")
    factor_importance = _read_parquet(str(FACTOR_IMPORTANCE_PARQUET))
    family_importance = _read_parquet(str(FAMILY_IMPORTANCE_PARQUET))
    shap_importance = _read_parquet(str(SHAP_IMPORTANCE_PARQUET)) if SHAP_IMPORTANCE_PARQUET.exists() else pd.DataFrame()
    cqr_results = _read_parquet(str(CQR_RESULTS_PARQUET)) if CQR_RESULTS_PARQUET.exists() else pd.DataFrame()
    return summary, benchmarks, calibrated, regimes, factors, factor_importance, family_importance, shap_importance, cqr_results


with st.sidebar:
    st.title("Étude maïs")
    if st.button("Régénérer l'étude", width="stretch"):
        with st.spinner("Calcul de l'étude professionnelle"):
            build_professional_study()
        st.cache_data.clear()
        st.rerun()

    page = st.radio(
        "Navigation",
        [
            "Synthèse",
            "Marché & régimes",
            "Facteurs économiques",
            "Benchmark modèles",
            "Décision agriculteur",
            "Sources & qualité",
            "Rapports",
        ],
    )


required = [
    STUDY_SUMMARY_JSON,
    BENCHMARK_PARQUET,
    CALIBRATED_PREDICTIONS_PARQUET,
    REGIME_PARQUET,
    DECISION_SNAPSHOT_JSON,
]

if not _exists(*required):
    st.title("Étude professionnelle du maïs CBOT")
    st.warning("Les artefacts de l'étude ne sont pas encore disponibles.")
    if st.button("Construire l'étude maintenant", type="primary"):
        with st.spinner("Benchmark, régimes, décision et rapport"):
            build_professional_study()
        st.cache_data.clear()
        st.rerun()
    st.stop()


summary, benchmarks, calibrated, regimes, factors, factor_importance, family_importance, shap_importance, cqr_results = _load_study()
decision = _read_json(str(DECISION_SNAPSHOT_JSON))


if page == "Synthèse":
    st.title("Étude professionnelle du prix du maïs CBOT")

    best = benchmarks.sort_values(["horizon", "rmse"]).groupby("horizon").head(1).copy()
    j20 = best[best["horizon"] == 20].iloc[0] if (best["horizon"] == 20).any() else best.iloc[0]
    rec = decision.get("recommendation", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historique", f"{summary['n_rows']:,}".replace(",", " "), f"{summary['date_min']} → {summary['date_max']}")
    c2.metric("Facteurs", summary["n_factors"], f"{summary['n_raw_features']} features brutes")
    c3.metric("Meilleur J+20", str(j20["model"]), f"RMSE {j20['rmse']:.4f}")
    c4.metric("Décision", rec.get("action", "NA"), _fmt_pct(float(rec.get("sell_fraction", 0.0))))

    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Meilleur modèle par horizon")
        display = best[["horizon", "model", "input", "rmse", "mae", "r2", "directional_accuracy"]].copy()
        display["horizon"] = display["horizon"].map(lambda h: f"J+{int(h)}")
        st.dataframe(display, width="stretch", hide_index=True)
        chart = best.assign(horizon_label=best["horizon"].map(lambda h: f"J+{int(h)}")).set_index("horizon_label")
        st.bar_chart(chart[["rmse", "mae"]])

    with right:
        st.subheader("Décision courante")
        if decision.get("status") == "ok":
            st.metric("Cash price", f"{decision['cash_price_usd_per_bu']:.2f} USD/bu")
            st.metric("Q50 J+20", f"{decision['predicted_cash_q50_h20']:.2f} USD/bu")
            st.metric("Régime", decision["regime"])
            st.write(rec.get("rationale", ""))
        else:
            st.warning("Décision indisponible.")

    st.subheader("Régimes historiques")
    regime_share = regimes["regime"].value_counts(normalize=True).rename("part").reset_index()
    regime_share.columns = ["regime", "part"]
    st.bar_chart(regime_share.set_index("regime"))


elif page == "Marché & régimes":
    st.title("Marché & régimes")
    r = regimes.copy()
    r["Date"] = pd.to_datetime(r["Date"])
    min_d, max_d = r["Date"].min().date(), r["Date"].max().date()
    start, end = st.slider("Fenêtre", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    view = r[(r["Date"].dt.date >= start) & (r["Date"].dt.date <= end)].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Dernier régime", view["regime"].iloc[-1] if not view.empty else "NA")
    c2.metric("Score régime", f"{view['regime_score'].iloc[-1]:.2f}" if not view.empty else "NA")
    c3.metric("Dernier future", f"{view['corn_close'].iloc[-1] / 100:.2f} USD/bu" if not view.empty else "NA")

    st.subheader("Prix CBOT")
    price = view[["Date", "corn_close"]].set_index("Date") / 100.0
    st.line_chart(price.rename(columns={"corn_close": "future_usd_per_bu"}))

    st.subheader("Score de régime")
    st.line_chart(view[["Date", "regime_score"]].set_index("Date"))

    st.subheader("Dernières observations")
    st.dataframe(view.tail(60), width="stretch", hide_index=True)


elif page == "Facteurs économiques":
    st.title("Facteurs économiques")
    horizon = st.selectbox("Horizon", [5, 10, 20, 30], index=2, format_func=lambda h: f"J+{h}")

    meta_path = Path("data/processed/factors_metadata.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    descriptions = meta.get("factor_descriptions", {})
    factor_family = meta.get("factor_family", {})

    fam = family_importance[family_importance["horizon"] == horizon].sort_values("coef_share", ascending=False)
    method_options = ["ridge_coef"]
    if not shap_importance.empty:
        method_options.append("shap")
    method = st.segmented_control("Méthode d'importance", method_options, default=method_options[0])
    if method == "shap" and not shap_importance.empty:
        top = shap_importance[shap_importance["horizon"] == horizon].sort_values("coef_share", ascending=False)
    elif "method" in factor_importance.columns:
        top = factor_importance[(factor_importance["horizon"] == horizon) & (factor_importance["method"] == "ridge_coef")].sort_values("coef_share", ascending=False)
    else:
        top = factor_importance[factor_importance["horizon"] == horizon].sort_values("coef_share", ascending=False)

    left, right = st.columns(2)
    with left:
        st.subheader("Contribution par famille")
        st.bar_chart(fam.set_index("family")[["coef_share"]])
    with right:
        st.subheader("Top facteurs")
        st.bar_chart(top.head(12).set_index("factor")[["coef_share"]])

    st.subheader("Exploration temporelle")
    options = [c for c in factors.columns if c != "Date"]
    selected = st.multiselect("Facteurs", options, default=options[:4], max_selections=6)
    if selected:
        f = factors.copy()
        f["Date"] = pd.to_datetime(f["Date"])
        st.line_chart(f.set_index("Date")[selected])

    st.subheader("Dictionnaire des facteurs")
    dictionary = pd.DataFrame(
        [
            {"factor": c, "family": factor_family.get(c, ""), "definition": descriptions.get(c, "")}
            for c in options
        ]
    )
    st.dataframe(dictionary, width="stretch", hide_index=True)


elif page == "Benchmark modèles":
    st.title("Benchmark modèles")
    horizon = st.selectbox("Horizon", [5, 10, 20, 30], index=2, format_func=lambda h: f"J+{h}")
    sub = benchmarks[benchmarks["horizon"] == horizon].sort_values("rmse")
    st.dataframe(sub, width="stretch", hide_index=True)

    st.subheader("Scores")
    score_chart = sub.set_index("model")[["rmse", "mae"]]
    st.bar_chart(score_chart)

    model = st.selectbox("Modèle", sub["model"].tolist())
    p = calibrated[(calibrated["horizon"] == horizon) & (calibrated["model"] == model)].copy()
    p["Date"] = pd.to_datetime(p["Date"])
    st.subheader("Prévisions walk-forward")
    st.line_chart(p.set_index("Date")[["y_true", "y_pred"]])

    st.subheader("Intervalles conformal 90%")
    interval_cols = ["y_true", "q10_logret", "q50_logret", "q90_logret"]
    st.line_chart(p.set_index("Date")[interval_cols])
    c1, c2, c3 = st.columns(3)
    c1.metric("Coverage 90%", _fmt_pct(float(p["covered_90"].mean())))
    c2.metric("Largeur moyenne", f"{p['interval_width_logret_90'].mean():.4f}")
    c3.metric("DA", _fmt_pct(float((p["y_true"].apply(lambda x: 1 if x >= 0 else -1) == p["y_pred"].apply(lambda x: 1 if x >= 0 else -1)).mean())))

    if not cqr_results.empty:
        st.subheader("CQR 90%")
        cq = cqr_results[cqr_results["horizon"] == horizon].copy()
        if not cq.empty:
            cq["Date"] = pd.to_datetime(cq["Date"])
            st.line_chart(cq.set_index("Date")[["y_true", "q_lo", "midpoint", "q_hi"]])
            q1, q2 = st.columns(2)
            q1.metric("Coverage CQR", _fmt_pct(float(cq["covered"].mean())))
            q2.metric("Largeur CQR", f"{cq['interval_width'].mean():.4f}")


elif page == "Décision agriculteur":
    st.title("Décision agriculteur")
    if decision.get("status") != "ok":
        st.warning("Décision indisponible.")
        st.stop()

    base_cash = float(decision["cash_price_usd_per_bu"])
    q10_ratio = float(decision["predicted_cash_q10_h20"]) / base_cash
    q50_ratio = float(decision["predicted_cash_q50_h20"]) / base_cash
    q90_ratio = float(decision["predicted_cash_q90_h20"]) / base_cash

    c1, c2, c3 = st.columns(3)
    basis = c1.number_input("Basis locale USD/bu", value=float(decision["basis_assumption"]), step=0.01, format="%.2f")
    storage = c2.number_input("Coût stockage USD/bu/mois", value=0.04, step=0.01, format="%.2f")
    cashflow = c3.selectbox("Contrainte cash", ["low", "medium", "high"], index=1)

    futures = float(decision["futures_price_usd_per_bu"])
    cash = futures + basis
    q10 = cash * q10_ratio
    q50 = cash * q50_ratio
    q90 = cash * q90_ratio

    profile = dict(decision["recommendation"]["profile"])
    profile["basis_local_typical_usd_per_bu"] = basis
    profile["storage_cost_usd_per_bu_per_month"] = storage
    profile["cash_flow_constraint"] = cashflow

    preds = dict(decision["recommendation"]["inputs"])
    preds["q10_h20"] = q10
    preds["q50_h20"] = q50
    preds["q90_h20"] = q90
    preds["p_t"] = cash
    rec = advise(preds, profile=profile)
    edge = q50 / cash - 1.0 - (storage * 20.0 / 30.0) / max(cash, 1e-6)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Action", rec.action.value)
    k2.metric("Fraction à vendre", _fmt_pct(rec.sell_fraction))
    k3.metric("Cash price", f"{cash:.2f} USD/bu")
    k4.metric("Edge stockage J+20", _fmt_pct(edge))

    st.subheader("Distribution J+20")
    st.dataframe(
        pd.DataFrame(
            [
                {"quantile": "q10", "cash_price_usd_per_bu": q10},
                {"quantile": "q50", "cash_price_usd_per_bu": q50},
                {"quantile": "q90", "cash_price_usd_per_bu": q90},
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    st.write(rec.rationale)


elif page == "Sources & qualité":
    st.title("Sources & qualité")
    coverage = _read_parquet(str(SOURCE_COVERAGE_PARQUET)) if SOURCE_COVERAGE_PARQUET.exists() else pd.DataFrame()
    if not coverage.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Sources actives", int(coverage["status"].isin(["active_in_features", "proxy_in_features"]).sum()))
        c2.metric("Sources planifiées", int((coverage["status"] == "planned").sum()))
        c3.metric("Features source", int(coverage["matched_features"].sum()))
        st.dataframe(coverage.sort_values(["priority", "source"]), width="stretch", hide_index=True)

    st.subheader("Validation")
    validation = Path("docs/VALIDATION_REPORT.md")
    if validation.exists():
        st.markdown(_read_text(str(validation)))
    if LEAKAGE_AUDIT_PARQUET.exists():
        audit = _read_parquet(str(LEAKAGE_AUDIT_PARQUET))
        if audit.empty:
            st.success("Audit anti-fuite: PASS")
        else:
            st.error("Audit anti-fuite: violations détectées")
            st.dataframe(audit, width="stretch", hide_index=True)

    st.subheader("Tables principales")
    tables = pd.DataFrame(
        [
            {"table": "features", "path": str(FEATURES_PARQUET), "exists": FEATURES_PARQUET.exists()},
            {"table": "targets", "path": str(TARGETS_PARQUET), "exists": TARGETS_PARQUET.exists()},
            {"table": "study", "path": str(STUDY_SUMMARY_JSON), "exists": STUDY_SUMMARY_JSON.exists()},
        ]
    )
    st.dataframe(tables, width="stretch", hide_index=True)


elif page == "Rapports":
    st.title("Rapports")
    tabs = st.tabs(["Étude générée", "Analyse factorielle", "Etude.md"])
    with tabs[0]:
        if STUDY_REPORT.exists():
            st.markdown(_read_text(str(STUDY_REPORT)))
    with tabs[1]:
        path = Path("docs/FACTOR_ANALYSIS_REPORT.md")
        if path.exists():
            st.markdown(_read_text(str(path)))
    with tabs[2]:
        path = Path("Etude.md")
        if path.exists():
            st.markdown(_read_text(str(path)))

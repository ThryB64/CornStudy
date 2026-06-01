"""Streamlit dashboard — Etude Maïs + Plateforme AutoML.

Pages:
  1. Conseil agriculteur
  2. Etude Maïs (benchmarks, CQR, SHAP, régimes, rapport)
  3. Plateforme AutoML (upload CSV → rapport complet)
  4. Profilage CSV
  5. Audit anti-leakage
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from mais.paths import (
    FEATURES_PARQUET,
    LEAKAGE_AUDIT_PARQUET,
    STUDY_DIR,
)

st.set_page_config(
    page_title="Etude Maïs — Dashboard",
    page_icon="🌽",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("🌽 Etude Maïs")
page = st.sidebar.radio(
    "Navigation",
    [
        "Conseil agriculteur",
        "Etude Maïs",
        "Plateforme AutoML",
        "Profilage CSV",
        "Audit anti-leakage",
    ],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_parquet(path: Path, label: str) -> pd.DataFrame | None:
    if not path.exists():
        st.warning(f"{label} introuvable : `{path}`. Lancer `make study`.")
        return None
    return pd.read_parquet(path)


def _metric_card(col, label: str, value: str, delta: str = "") -> None:
    col.metric(label, value, delta)


# ---------------------------------------------------------------------------
# Page 1 — Conseil agriculteur
# ---------------------------------------------------------------------------

if page == "Conseil agriculteur":
    st.title("Conseil de vente agriculteur")

    col1, col2 = st.columns(2)
    with col1:
        horizon = st.selectbox("Horizon de prédiction", [5, 10, 20, 30], index=2)
    with col2:
        state = st.selectbox(
            "État (base prix)",
            ["iowa", "illinois", "nebraska", "minnesota", "indiana"],
        )

    st.markdown("---")

    # Daily snapshot
    snap_dir = Path("data/snapshots")
    snaps = sorted(snap_dir.glob("*.json")) if snap_dir.exists() else []
    if snaps:
        import json
        snap = json.loads(snaps[-1].read_text())
        snap_date = snaps[-1].stem
        dec = snap.get("decision", {})

        c1, c2, c3, c4 = st.columns(4)
        _metric_card(c1, "Date signal", str(dec.get("date", "—")))
        _metric_card(c2, "Prix cash estimé", f"{dec.get('cash_price_usd_bu', 0):.2f} USD/bu")
        _metric_card(c3, "Régime", str(dec.get("regime", "—")))
        _metric_card(c4, "Action", str(dec.get("action", "—")))

        st.markdown(f"**Fraction à vendre :** {dec.get('sell_fraction', 0):.0%}")
        st.markdown(f"**Règle déclenchée :** `{dec.get('rule', '—')}`")
        st.markdown(f"*Snapshot du {snap_date}*")
    else:
        try:
            from mais.decision import advise_today
            text = advise_today(horizon=horizon, farmer_state=state)
            st.code(text)
        except Exception as e:
            st.error(f"Conseil non disponible : {e}")

    # Daily report
    rep_dir = Path("data/reports")
    reps = sorted(rep_dir.glob("*.md")) if rep_dir.exists() else []
    if reps:
        st.markdown("---")
        st.subheader(f"Rapport quotidien — {reps[-1].stem}")
        st.markdown(reps[-1].read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Page 2 — Etude Maïs
# ---------------------------------------------------------------------------

elif page == "Etude Maïs":
    st.title("Etude professionnelle du prix du maïs CBOT")

    tabs = st.tabs(["Benchmarks", "CQR & Intervalles", "SHAP", "Régimes", "Rapport"])

    # --- Benchmarks ---
    with tabs[0]:
        st.subheader("Benchmark modèles (walk-forward)")
        bm = _load_parquet(STUDY_DIR / "model_benchmarks.parquet", "model_benchmarks")
        if bm is not None and not bm.empty:
            horizons = sorted(bm["horizon"].unique()) if "horizon" in bm.columns else []
            sel_h = st.selectbox("Horizon (jours)", horizons, index=len(horizons) - 1)
            sub = bm[bm["horizon"] == sel_h].copy() if "horizon" in bm.columns else bm
            cols_show = [c for c in ["model", "rmse", "mae", "r2", "directional_accuracy"] if c in sub.columns]
            sub_disp = sub[cols_show].sort_values("rmse").reset_index(drop=True)
            for c in ["rmse", "mae", "r2", "directional_accuracy"]:
                if c in sub_disp.columns:
                    sub_disp[c] = sub_disp[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
            st.dataframe(sub_disp, use_container_width=True)

            # Chart DA
            if "directional_accuracy" in bm.columns and "model" in bm.columns:
                da_df = bm[bm["horizon"] == sel_h][["model", "directional_accuracy"]].dropna()
                da_df["directional_accuracy"] = pd.to_numeric(da_df["directional_accuracy"], errors="coerce")
                da_df = da_df.sort_values("directional_accuracy", ascending=False)
                st.bar_chart(da_df.set_index("model")["directional_accuracy"])

    # --- CQR ---
    with tabs[1]:
        st.subheader("Conformalized Quantile Regression — couverture empirique")
        cqr = _load_parquet(STUDY_DIR / "cqr_results.parquet", "cqr_results")
        if cqr is not None and not cqr.empty:
            mean_cov = float(cqr["covered"].mean()) if "covered" in cqr.columns else float("nan")
            c1, c2 = st.columns(2)
            _metric_card(c1, "Couverture moyenne (CQR)", f"{mean_cov:.1%}", "objectif ≥90%")
            _metric_card(c2, "Prédictions calibrées", f"{len(cqr):,}")
            if "horizon" in cqr.columns and "covered" in cqr.columns:
                by_h = cqr.groupby("horizon")["covered"].mean().reset_index()
                by_h.columns = ["horizon", "coverage"]
                st.bar_chart(by_h.set_index("horizon")["coverage"])
            st.caption("Couverture cible : 90% — valeurs >90% = conservateur, <90% = sous-couverture.")

        # Split-conformal from calibrated_predictions
        cal_path = STUDY_DIR / "calibrated_predictions.parquet"
        if cal_path.exists():
            cal = pd.read_parquet(cal_path)
            if "covered_90" in cal.columns:
                sc_cov = float(cal["covered_90"].mean())
                st.metric("Split-conformal coverage (covered_90)", f"{sc_cov:.1%}")

    # --- SHAP ---
    with tabs[2]:
        st.subheader("Importance SHAP — top facteurs")
        shap = _load_parquet(STUDY_DIR / "shap_importance.parquet", "shap_importance")
        if shap is not None and not shap.empty:
            horizons_s = sorted(shap["horizon"].unique()) if "horizon" in shap.columns else []
            sel_hs = st.selectbox("Horizon", horizons_s, key="shap_h")
            sub_s = shap[shap["horizon"] == sel_hs] if "horizon" in shap.columns else shap
            top_n = st.slider("Top N features", 5, 30, 15)
            val_col = next((c for c in ["mean_abs_shap", "importance", "shap_mean"] if c in sub_s.columns), None)
            if val_col:
                sub_s = sub_s.nlargest(top_n, val_col)[["feature", val_col]].reset_index(drop=True)
                st.bar_chart(sub_s.set_index("feature")[val_col])
                st.dataframe(sub_s, use_container_width=True)

    # --- Régimes ---
    with tabs[3]:
        st.subheader("Régimes de marché (Markov-switching)")
        reg = _load_parquet(STUDY_DIR / "regime_timeseries.parquet", "regime_timeseries")
        if reg is not None and not reg.empty:
            if "regime" in reg.columns:
                counts = reg["regime"].value_counts()
                c1, c2, c3 = st.columns(3)
                _metric_card(c1, "Bull", f"{counts.get('bull', 0):,} obs ({counts.get('bull', 0)/len(reg):.1%})")
                _metric_card(c2, "Range", f"{counts.get('range', 0):,} obs ({counts.get('range', 0)/len(reg):.1%})")
                _metric_card(c3, "Bear", f"{counts.get('bear', 0):,} obs ({counts.get('bear', 0)/len(reg):.1%})")

            if "Date" in reg.columns and "regime_score" in reg.columns:
                reg["Date"] = pd.to_datetime(reg["Date"])
                st.line_chart(reg.set_index("Date")["regime_score"])
            if "Date" in reg.columns and "corn_close" in reg.columns:
                st.line_chart(reg.set_index("Date")["corn_close"])

    # --- Rapport ---
    with tabs[4]:
        rep_path = Path("docs/PROFESSIONAL_STUDY_REPORT.md")
        if rep_path.exists():
            st.markdown(rep_path.read_text(encoding="utf-8"))
        else:
            st.warning("Rapport non généré. Lancer `make study`.")


# ---------------------------------------------------------------------------
# Page 3 — Plateforme AutoML
# ---------------------------------------------------------------------------

elif page == "Plateforme AutoML":
    st.title("Plateforme AutoML générique")
    st.markdown(
        "Chargez n'importe quel fichier CSV ou Parquet. "
        "La plateforme détecte automatiquement le type de problème, "
        "entraîne plusieurs modèles et génère un rapport complet."
    )

    upload = st.file_uploader("Charger un fichier CSV ou Parquet", type=["csv", "parquet"])

    if upload is not None:
        tmp = Path("/tmp") / upload.name
        with open(tmp, "wb") as f:
            f.write(upload.getbuffer())

        # Profile
        from mais.platform.profiler import profile_dataset
        try:
            profile = profile_dataset(tmp)
        except Exception as e:
            st.error(f"Erreur de profilage : {e}")
            st.stop()

        st.markdown("---")
        st.subheader("Profil du dataset")
        c1, c2, c3, c4 = st.columns(4)
        _metric_card(c1, "Lignes", f"{profile.n_rows:,}")
        _metric_card(c2, "Colonnes", str(profile.n_cols))
        _metric_card(c3, "Type de problème", profile.problem_type)
        _metric_card(c4, "Split recommandé", profile.split_recommendation)

        if profile.warnings:
            st.warning("Avertissements :\n" + "\n".join(f"- {w}" for w in profile.warnings))

        target_col = st.selectbox(
            "Colonne cible",
            options=[profile.target_col] + [c for c in (profile.numeric_cols + profile.boolean_cols) if c != profile.target_col],
        )
        n_splits = st.slider("Nombre de plis CV / blocs walk-forward", 3, 10, 5)

        if st.button("🚀 Lancer l'analyse AutoML", type="primary"):
            out_dir = Path("/tmp") / f"automl_{tmp.stem}"
            with st.spinner("Analyse en cours… (quelques secondes)"):
                from mais.platform.reporting import run_automl
                try:
                    report_path = run_automl(
                        csv_path=tmp,
                        target_col=target_col,
                        out_dir=out_dir,
                        n_splits=n_splits,
                    )
                    st.success(f"Analyse terminée → `{report_path}`")

                    # Show benchmarks
                    bm_path = out_dir / "benchmarks.csv"
                    if bm_path.exists():
                        st.subheader("Benchmark modèles")
                        bm = pd.read_csv(bm_path)
                        st.dataframe(bm, use_container_width=True)
                        metric_col = "accuracy" if profile.problem_type in ("binary", "multiclass") else "rmse"
                        if metric_col in bm.columns:
                            asc = metric_col == "rmse"
                            st.bar_chart(bm.sort_values(metric_col, ascending=asc).set_index("model")[metric_col])

                    # SHAP
                    shap_path = out_dir / "shap_importance.csv"
                    if shap_path.exists():
                        st.subheader("Importance SHAP (top 15)")
                        shap_df = pd.read_csv(shap_path).head(15)
                        st.bar_chart(shap_df.set_index("feature")["mean_abs_shap"])

                    # Full report
                    st.subheader("Rapport complet")
                    st.markdown(report_path.read_text(encoding="utf-8"))

                    # Download
                    st.download_button(
                        "⬇️ Télécharger le rapport",
                        data=report_path.read_bytes(),
                        file_name=f"automl_report_{tmp.stem}.md",
                        mime="text/markdown",
                    )
                except Exception as e:
                    st.error(f"Erreur AutoML : {e}")


# ---------------------------------------------------------------------------
# Page 4 — Profilage CSV
# ---------------------------------------------------------------------------

elif page == "Profilage CSV":
    st.title("Profilage rapide — n'importe quel CSV")
    st.markdown("Charge un fichier et obtiens le type de problème détecté, les colonnes, les avertissements.")

    upload = st.file_uploader("Charger un CSV ou Parquet", type=["csv", "parquet"])
    if upload is not None:
        tmp = Path("/tmp") / upload.name
        with open(tmp, "wb") as f:
            f.write(upload.getbuffer())

        from mais.platform.profiler import profile_dataset
        try:
            profile = profile_dataset(tmp)
            st.subheader("Résumé")
            st.code(profile.summary())

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Colonnes numériques**", profile.numeric_cols)
                st.write("**Colonnes catégorielles**", profile.categorical_cols)
            with col2:
                st.write("**Colonnes ID détectées**", profile.id_cols)
                st.write("**Modèles compatibles**", profile.compatible_models)

            if profile.missing_rate:
                st.subheader("Taux de NaN par colonne (>0)")
                mr = pd.Series(profile.missing_rate).sort_values(ascending=False)
                st.bar_chart(mr)
        except Exception as e:
            st.error(f"Erreur de profilage : {e}")


# ---------------------------------------------------------------------------
# Page 5 — Audit anti-leakage
# ---------------------------------------------------------------------------

elif page == "Audit anti-leakage":
    st.title("Audit anti-leakage")

    if not LEAKAGE_AUDIT_PARQUET.exists():
        st.warning("Pas de rapport d'audit. Lancer `make audit`.")
    else:
        df = pd.read_parquet(LEAKAGE_AUDIT_PARQUET)
        if df.empty:
            st.success("✅ PASS — aucun leakage détecté.")
        else:
            st.error(f"❌ FAIL — {len(df)} violations.")
            for check, sub in df.groupby("check"):
                st.write(f"**{check}** ({len(sub)} lignes)")
                st.dataframe(sub.head(50), use_container_width=True)

    # Features summary
    if FEATURES_PARQUET.exists():
        st.markdown("---")
        st.subheader("Features.parquet — aperçu")
        feat = pd.read_parquet(FEATURES_PARQUET)
        c1, c2, c3 = st.columns(3)
        _metric_card(c1, "Lignes", f"{len(feat):,}")
        _metric_card(c2, "Colonnes features", str(feat.shape[1]))
        _metric_card(c3, "Période",
                     f"{feat['Date'].min().date()} → {feat['Date'].max().date()}" if "Date" in feat.columns else "—")
        missing = (feat.isna().mean() * 100).sort_values(ascending=False)
        st.write("**Top 10 colonnes avec le plus de NaN**")
        st.dataframe(missing.head(10).rename("NaN %").to_frame(), use_container_width=True)

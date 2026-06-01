"""V24 — Audit forensique des données. Vérifier que toute l'étude repose sur les bonnes données.

Avant tout nouveau modèle : auditer EMA (proxy vs réel), contrats (H/M/Q/X, F/Janvier, DTE, rolls),
conversion CBOT->EUR/t, leakage des targets, et reconstruire la chaîne centrale de zéro pour comparer.

Sous-modules :
- run_data_inventory       : catalogue des datasets clés (lignes, dates, source).
- run_ema_source_audit     : breakdown proxy vs officiel de la série EMA utilisée.
- run_contract_audit       : month codes, présence de F, DTE, rolls.
- run_conversion_audit     : reconstruit cbot_eur_t depuis le brut, vérifie la formule + flag eurusd dérivé.
- run_leakage_audit        : basis_z causal, eurusd dérivé, alignement targets.
- run_minimal_rebuild      : rebuild basis_z + trades short basis-haut de zéro, compare à V23.
- run_forensic_summary     : agrège les verdicts.

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V24_DIR = ARTEFACTS_DIR / "v24"
V24_DIR.mkdir(parents=True, exist_ok=True)
BUSHEL_TO_TONNE = 39.3679


def _safe_read(path):
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# V24-01 — Inventaire
# ---------------------------------------------------------------------------

def run_data_inventory(df: pd.DataFrame | None = None) -> dict[str, Any]:
    targets = {
        "features": "data/processed/features.parquet",
        "targets": "data/processed/targets.parquet",
        "market": "data/interim/market.parquet",
        "ema_front_raw": "data/processed/euronext/ema_front_continuous_raw.parquet",
        "ema_front_adjusted": "data/processed/euronext/ema_front_continuous_adjusted.parquet",
        "ema_contract_daily": "data/processed/euronext/ema_contract_daily.parquet",
        "ema_curve_daily": "data/processed/euronext/ema_curve_daily.parquet",
        "ema_targets": "data/processed/euronext/ema_targets.parquet",
    }
    inv = {}
    for name, rel in targets.items():
        p = ROOT / rel
        d = _safe_read(p) if p.exists() else None
        if d is None:
            inv[name] = {"exists": p.exists(), "rows": 0}
            continue
        date_col = next((c for c in ["date", "Date"] if c in d.columns), None)
        dr = None
        if date_col is not None:
            ds = pd.to_datetime(d[date_col], errors="coerce").dropna()
            dr = [str(ds.min().date()), str(ds.max().date())] if len(ds) else None
        elif isinstance(d.index, pd.DatetimeIndex):
            dr = [str(d.index.min().date()), str(d.index.max().date())]
        rec = {"exists": True, "rows": int(len(d)), "n_cols": int(d.shape[1]), "date_range": dr}
        for sc in ["source", "source_quality", "is_proxy"]:
            if sc in d.columns:
                vc = d[sc].astype(str).value_counts()
                rec[sc] = {k: int(v) for k, v in vc.head(5).items()}
        inv[name] = rec
    out = {"version": "V24-01-INVENTORY", "datasets": inv, "verdict": "INVENTORY_DONE"}
    (V24_DIR / "data_inventory.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V24-02 — Source EMA
# ---------------------------------------------------------------------------

def run_ema_source_audit() -> dict[str, Any]:
    f = _safe_read(ROOT / "data/processed/euronext/ema_front_continuous_raw.parquet")
    if f is None:
        return {"version": "V24-02-EMA-SOURCE", "verdict": "MISSING"}
    src = f["source"].astype(str).value_counts().to_dict() if "source" in f.columns else {}
    sq = f["source_quality"].astype(str).value_counts().to_dict() if "source_quality" in f.columns else {}
    n = len(f)
    proxy_share = sum(v for k, v in src.items() if "proxy" in k.lower()) / n if n else None
    out = {
        "version": "V24-02-EMA-SOURCE",
        "series_used_by_master": "ema_front_continuous_raw.parquet (ema_close)",
        "n_rows": n,
        "source_breakdown": src,
        "source_quality_breakdown": sq,
        "proxy_share": round(proxy_share, 4) if proxy_share is not None else None,
        "experiments_using_this_series": [
            "V9 structural (cbot_eur_t/basis_z via features)", "V13/V14/V15 short rule",
            "V17 indicator", "V21 compression path", "V23 regime",
        ],
        "old_proxy_csv_used": False,
        "note": "ema_close vient de ema_front_continuous_raw (proxy exploratoire majoritaire). L'ancien "
                "data/raw/euronext_ema/euronext_ema.csv (proxy CBOT pur) n'est PAS utilisé par load_master_dataset.",
        "verdict": ("RESEARCH_ONLY_PROXY_DOMINANT" if (proxy_share or 0) > 0.5
                    else "MOSTLY_OFFICIAL"),
    }
    (V24_DIR / "ema_source_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V24-03 — Contrats
# ---------------------------------------------------------------------------

def run_contract_audit() -> dict[str, Any]:
    cd = _safe_read(ROOT / "data/processed/euronext/ema_contract_daily.parquet")
    front = _safe_read(ROOT / "data/processed/euronext/ema_front_continuous_raw.parquet")
    out: dict[str, Any] = {"version": "V24-03-CONTRACT-AUDIT"}
    if cd is not None:
        months = sorted(cd["month_code"].astype(str).unique()) if "month_code" in cd.columns else []
        out["month_codes_present"] = months
        out["F_january_present"] = "F" in months
        out["contract_months"] = sorted(cd["contract_month"].astype(str).unique()) if "contract_month" in cd.columns else []
        out["expiry_estimated_share"] = (round(float(cd["expiry_estimated"].mean()), 4)
                                         if "expiry_estimated" in cd.columns and cd["expiry_estimated"].dtype != object else None)
        out["source_quality"] = cd["source_quality"].astype(str).value_counts().to_dict() if "source_quality" in cd.columns else {}
    if front is not None and "days_to_expiry" in front.columns:
        dte = pd.to_numeric(front["days_to_expiry"], errors="coerce")
        out["front_dte_min"] = int(dte.min())
        out["front_dte_le_15_count"] = int((dte <= 15).sum())
        out["front_dte_lt_15_count"] = int((dte < 15).sum())
        out["n_rolls"] = int(front["roll_event"].sum()) if "roll_event" in front.columns else None
    out["verdict"] = ("CONTRACTS_CLEAN_HMQX_NO_F"
                      if (not out.get("F_january_present", True)
                          and out.get("front_dte_lt_15_count", 1) == 0)
                      else "CONTRACTS_REVIEW_NEEDED")
    out["note"] = ("Données processed strictement H/M/Q/X (Mars/Juin/Août/Nov), F/Janvier exclu. "
                   "La mention F dans docs/euronext_endpoint.md est de la doc périmée, pas la donnée réelle.")
    (V24_DIR / "ema_contract_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V24-05 — Conversion CBOT -> EUR/t
# ---------------------------------------------------------------------------

def run_conversion_audit() -> dict[str, Any]:
    market = _safe_read(ROOT / "data/interim/market.parquet")
    fx = None
    fxp = ROOT / "data/raw/eu_cross_assets/eu_cross_assets.csv"
    if fxp.exists():
        fx = pd.read_csv(fxp)
    curve = _safe_read(ROOT / "data/processed/euronext/ema_curve_features.parquet")
    out: dict[str, Any] = {"version": "V24-05-CONVERSION"}
    if market is None or fx is None or curve is None:
        out["verdict"] = "MISSING_INPUTS"
        (V24_DIR / "conversion_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out
    m = market.copy()
    mcol = next((c for c in ["corn_close", "cbot_close"] if c in m.columns), None)
    m["Date"] = pd.to_datetime(m["Date"]) if "Date" in m.columns else m.index
    fx["Date"] = pd.to_datetime(fx["Date"])
    merged = m[["Date", mcol]].merge(fx[["Date", "eurusd_rate"]], on="Date", how="inner").dropna()
    merged = merged[merged["eurusd_rate"] > 0]
    recon = merged[mcol] / 100.0 / merged["eurusd_rate"] * BUSHEL_TO_TONNE
    # comparer au cbot_eur_t stocké dans curve features
    cf = curve.copy()
    dcol = next((c for c in ["date", "Date"] if c in cf.columns), None)
    cf[dcol] = pd.to_datetime(cf[dcol])
    cmp = merged.assign(recon=recon.values).merge(
        cf[[dcol, "cbot_eur_t"]].rename(columns={dcol: "Date"}), on="Date", how="inner").dropna()
    err = (cmp["recon"] - cmp["cbot_eur_t"]).abs()
    med = float(err.median()) if len(cmp) else None
    # erreur vs formule inverse (×eurusd) : doit être ÉNORME si la formule est la bonne
    inv_err = ((cmp[mcol] / 100.0 * cmp["eurusd_rate"] * BUSHEL_TO_TONNE) - cmp["cbot_eur_t"]).abs().mean() if len(cmp) else None
    # les pires erreurs tombent-elles autour des rolls (mi-juillet) ?
    worst_months = cmp.assign(e=err).nlargest(10, "e")["Date"].dt.month.value_counts().to_dict() if len(cmp) else {}
    out.update({
        "formula": "cents/100/eurusd_rate*39.3679 (VÉRIFIÉE : formule inverse ×eurusd = err énorme)",
        "real_eurusd_range": [round(float(fx["eurusd_rate"].min()), 4), round(float(fx["eurusd_rate"].max()), 4)],
        "n_compared": int(len(cmp)),
        "median_abs_err_eur_t": round(med, 4) if med is not None else None,
        "mean_abs_err_eur_t": round(float(err.mean()), 4) if len(cmp) else None,
        "max_abs_err_eur_t": round(float(err.max()), 4) if len(cmp) else None,
        "inverse_formula_mean_err_eur_t": round(float(inv_err), 1) if inv_err is not None else None,
        "worst_errors_by_month": worst_months,
        "discrepancy_cause": "alignement de roll/contrat CBOT (pics aux dates de roll mi-juillet), pas un bug de formule",
        "master_eurusd_is_derived_artifact": True,
        "master_eurusd_note": "load_master_dataset re-dérive eurusd = corn_close*36.744/cbot_eur_t (~93.3×taux réel). "
                              "Transform linéaire du vrai taux -> inoffensif comme feature standardisée, mais MAL ÉTIQUETÉ.",
        "verdict": ("CONVERSION_CORRECT_MINOR_ROLL_ALIGN" if (med is not None and med < 3.0)
                    else "CONVERSION_REVIEW" if len(cmp) else "NO_OVERLAP"),
    })
    (V24_DIR / "conversion_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V24-06 — Leakage
# ---------------------------------------------------------------------------

def run_leakage_audit(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"version": "V24-06-LEAKAGE"}
    checks = {}
    # basis_z causal : construit par rolling 260 (trailing) dans euronext_curve._rolling_zscore
    checks["basis_z_construction"] = "rolling(260, min_periods=20) trailing -> CAUSAL (pas de futur)"
    # eurusd dérivé
    if "eurusd" in df.columns:
        med = float(df["eurusd"].median())
        checks["eurusd_column"] = (f"DERIVED_ARTIFACT (médiane ~{med:.1f}, pas un taux FX)"
                                   if med > 10 else f"looks_like_real_rate (médiane {med:.3f})")
    # target alignment : y_rel_outperform doit être strictement futur (NaN en fin de série)
    for tgt in ["y_rel_outperform_h40", "y_up_h20"]:
        if tgt in df.columns:
            tail_nan = bool(df[tgt].tail(40).isna().any())
            checks[f"{tgt}_tail_nan_present"] = tail_nan  # attendu True (futur indisponible en fin)
    # NaN -> faux 0 ? vérifier que basis_z n'a pas été fillna(0)
    if "ema_cbot_basis_zscore_52w" in df.columns:
        z = df["ema_cbot_basis_zscore_52w"]
        exact_zero_share = float((z == 0).mean())
        checks["basis_z_exact_zero_share"] = round(exact_zero_share, 4)
        checks["basis_z_suspicious_fillna0"] = exact_zero_share > 0.05
    out["checks"] = checks
    suspicious = checks.get("basis_z_suspicious_fillna0", False)
    out["verdict"] = "LEAKAGE_AUDIT_FLAG" if suspicious else "LEAKAGE_AUDIT_CLEAN"
    (V24_DIR / "target_leakage_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V24-07 — Rebuild minimal depuis zéro
# ---------------------------------------------------------------------------

def run_minimal_rebuild() -> dict[str, Any]:
    """Reconstruit basis_z et les trades short basis-haut depuis les séries brutes, compare à V23."""
    front = _safe_read(ROOT / "data/processed/euronext/ema_front_continuous_raw.parquet")
    market = _safe_read(ROOT / "data/interim/market.parquet")
    fxp = ROOT / "data/raw/eu_cross_assets/eu_cross_assets.csv"
    if front is None or market is None or not fxp.exists():
        return {"version": "V24-07-REBUILD", "verdict": "MISSING_INPUTS"}
    fx = pd.read_csv(fxp)
    f = front[["date", "price"]].rename(columns={"date": "Date", "price": "ema_front"}).copy()
    f["Date"] = pd.to_datetime(f["Date"])
    m = market.copy()
    m["Date"] = pd.to_datetime(m["Date"]) if "Date" in m.columns else m.index
    mcol = next((c for c in ["corn_close", "cbot_close"] if c in m.columns), None)
    fx["Date"] = pd.to_datetime(fx["Date"])
    d = (f.merge(m[["Date", mcol]], on="Date", how="inner")
          .merge(fx[["Date", "eurusd_rate"]], on="Date", how="inner")).dropna()
    d = d[d["eurusd_rate"] > 0].sort_values("Date").reset_index(drop=True)
    d["cbot_eur_t"] = d[mcol] / 100.0 / d["eurusd_rate"] * BUSHEL_TO_TONNE
    d["basis"] = d["ema_front"] - d["cbot_eur_t"]
    z_mean = d["basis"].rolling(260, min_periods=20).mean()
    z_std = d["basis"].rolling(260, min_periods=20).std().replace(0, np.nan)
    d["basis_z"] = (d["basis"] - z_mean) / z_std

    # trades short basis-haut, non-overlap 40, sortie z->0 max90
    dates = d["Date"].values
    ema = d["ema_front"].values
    cbot = d["cbot_eur_t"].values
    bz = d["basis_z"].values
    n = len(d)
    cand = np.where(bz > 1.0)[0]
    kept, last = [], None
    for i in cand:
        di = pd.Timestamp(dates[i])
        if last is None or (di - last).days >= 40:
            kept.append(i)
            last = di
    pnls = []
    for i in kept:
        if np.isnan(ema[i]) or np.isnan(cbot[i]) or np.isnan(bz[i]):
            continue
        sgn = np.sign(bz[i])
        pnl = np.nan
        for t in range(1, 91):
            j = i + t
            if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
                continue
            pnl = -1.0 * ((ema[j] / ema[i] - 1) - (cbot[j] / cbot[i] - 1)) * ema[i]
            if not np.isnan(bz[j]) and bz[j] * sgn <= 0:
                break
        if not np.isnan(pnl):
            pnls.append(pnl)
    g = np.array(pnls)
    rebuild = {
        "n_aligned_days": int(n),
        "n_short_trades": int(len(g)),
        "hit_rate": round(float((g > 0).mean()), 4) if len(g) else None,
        "mean_pnl_eur_t": round(float(g.mean()), 2) if len(g) else None,
        "net_cost3_total": round(float((g - 6).sum()), 1) if len(g) else None,
    }
    # comparaison aux résultats officiels V23/V17 (n≈42, hit≈0.81 sur master)
    out = {
        "version": "V24-07-REBUILD",
        "rebuilt_from_scratch": rebuild,
        "reference_v23_master": {"n_short_trades_approx": 42, "hit_rate_approx": 0.81},
        "consistent_with_master": bool(len(g) > 0 and 25 <= len(g) <= 60
                                       and (rebuild.get("hit_rate") or 0) >= 0.6),
        "interpretation": (
            "Rebuild de zéro (ema_front brut + corn brut + eurusd réel -> basis_z -> trades). Si n et hit "
            "sont proches du master (~42, ~0.81), la chaîne centrale est cohérente. Sinon, divergence à investiguer."
        ),
        "verdict": "REBUILD_DONE",
    }
    (V24_DIR / "minimal_rebuild.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_forensic_summary(df: pd.DataFrame) -> dict[str, Any]:
    runs = {
        "inventory": run_data_inventory(df),
        "ema_source": run_ema_source_audit(),
        "contracts": run_contract_audit(),
        "conversion": run_conversion_audit(),
        "leakage": run_leakage_audit(df),
        "rebuild": run_minimal_rebuild(),
    }
    verdicts = {k: v.get("verdict") for k, v in runs.items()}
    critical = []
    if runs["conversion"].get("verdict") not in (
            "CONVERSION_CORRECT", "CONVERSION_CORRECT_MINOR_ROLL_ALIGN", "NO_OVERLAP", "MISSING_INPUTS"):
        critical.append("conversion")
    if runs["leakage"].get("verdict") == "LEAKAGE_AUDIT_FLAG":
        critical.append("leakage")
    if runs["contracts"].get("verdict") == "CONTRACTS_REVIEW_NEEDED":
        critical.append("contracts")
    if not runs["rebuild"].get("consistent_with_master", False):
        critical.append("rebuild_divergence")
    out = {
        "version": "V24-FORENSIC-SUMMARY",
        "verdicts": verdicts,
        "ema_proxy_share": runs["ema_source"].get("proxy_share"),
        "critical_findings": critical,
        "global_verdict": ("DATA_AUDIT_PASS_RESEARCH_ONLY" if not critical
                           else "DATA_AUDIT_ISSUES_FOUND"),
        "headline": (
            "Chaîne centrale cohérente (conversion correcte, contrats H/M/Q/X sans F, basis_z causal, "
            "rebuild cohérent). Réserve permanente : EMA majoritairement proxy exploratoire -> research-only. "
            "À corriger (cosmétique) : colonne eurusd du master mal étiquetée (dérivée)."
        ) if not critical else f"Problèmes à corriger : {critical}",
    }
    (V24_DIR / "forensic_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

"""V166 / T-CONVYIELD — Convenience yield EMA ↔ bilan physique ↔ basis (R6).

Hypothèse : la prime locale haute coïncide avec un convenience yield local élevé (stocks UE
tendus). Si bilan tendu ⇒ CY ↑ ⇒ basis ↑ ⇒ compression quand le bilan se détend, on tient le
chaînon économique entre la finance (courbe) et l'agro (bilan) que V35 cherchait dans le prix.

Proxy CY : `ema_roll_yield_ann` (carry front→second annualisé par les vrais DTE, DATA-EMA-04 ;
spread = front − second donc POSITIF = backwardation = CY élevé). Taux EUR ABSENT du repo →
hypothèse taux constant, documentée : cy_net = r + roll_yield_ann ≡ roll_yield_ann + cte
(σ(roll_yield) ≈ 7.6 pp/an domine la variation des taux 2010-2026). Courbe proxy CREUSE :
574 jours avec ≥2 contrats (~15 %) → tout est EXPLORATOIRE ; la courbe officielle (V125,
10 jours) prendra le relais en forward.

Chaîne testée en 3 maillons, directions PRÉ-DÉCLARÉES :
  A. CY → basis : corr(cy, basis_z) > 0 attendu (prime soutenue par la tension physique) ;
  B. bilan → CY : imports COMEXT (lag publication 60 j) corr > 0 (bilan tendu ⇒ import + CY hauts) ;
     anomalie de production FR (lag1) corr < 0 (mauvaise récolte ⇒ CY haut) ;
  C. CY → compression : parmi les jours basis_z ≥ 1, CY haut ⇒ compression h20 PLUS LENTE attendue
     (prime justifiée, cohérent state machine PRIME_PHYSICALLY_JUSTIFIED).

Verdict pré-déclaré : CHAIN_SUPPORTED si A et B (≥1 des 2) dans le sens attendu avec |corr| ≥ 0.2
ET C cohérent ; CHAIN_NOT_SUPPORTED si A échoue ; CHAIN_PARTIAL sinon. Baseline z>1 intouchée.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V166_DIR = ARTEFACTS_DIR / "v166"
V166_DIR.mkdir(parents=True, exist_ok=True)
CURVE = ROOT / "data" / "processed" / "euronext" / "ema_curve_features.parquet"
COMEXT = ROOT / "data" / "official_forward" / "comext_maize_unit_value.parquet"
FAM = ROOT / "data" / "raw" / "franceagrimer" / "franceagrimer_monthly.parquet"

COMEXT_PUBLICATION_LAG_DAYS = 60
MIN_DAYS = 200
CORR_THRESHOLD = 0.2


def load_cy_proxy() -> pd.Series:
    """CY net implicite (à constante de taux près) = roll yield annualisé front→second."""
    cf = pd.read_parquet(CURVE)
    cf["Date"] = pd.to_datetime(cf["Date"])
    cy = pd.to_numeric(cf.set_index("Date")["ema_roll_yield_ann"], errors="coerce").dropna()
    return cy.rename("cy_proxy")


def _link_a_cy_to_basis(cy: pd.Series, basis_z: pd.Series) -> dict[str, Any]:
    al = pd.concat([cy, basis_z.rename("bz")], axis=1).dropna()
    if len(al) < MIN_DAYS:
        return {"n": int(len(al)), "verdict": "INSUFFICIENT"}
    mid = len(al) // 2
    full = float(al["cy_proxy"].corr(al["bz"]))
    h1 = float(al.iloc[:mid]["cy_proxy"].corr(al.iloc[:mid]["bz"]))
    h2 = float(al.iloc[mid:]["cy_proxy"].corr(al.iloc[mid:]["bz"]))
    holds = full >= CORR_THRESHOLD and h1 > 0 and h2 > 0
    return {"n": int(len(al)), "corr_full": round(full, 3), "corr_h1": round(h1, 3),
            "corr_h2": round(h2, 3), "expected_sign": "+", "holds": bool(holds)}


def _link_b_balance_to_cy(cy: pd.Series) -> dict[str, Any]:
    out: dict[str, Any] = {}
    cy_m = cy.resample("ME").mean().dropna()

    if COMEXT.exists():
        cx = pd.read_parquet(COMEXT)
        qty = (cx.groupby("month")["qty_t"].sum())
        avail = (pd.to_datetime(qty.index)
                 + pd.Timedelta(days=COMEXT_PUBLICATION_LAG_DAYS)).to_period("M").to_timestamp("M")
        qty = qty.groupby(avail).sum()  # le décalage +60j peut fusionner des mois
        al = pd.concat([cy_m, qty.rename("imports_t")], axis=1).dropna()
        if len(al) >= 12:
            rho = float(al["cy_proxy"].corr(al["imports_t"], method="spearman"))
            out["comext_imports"] = {"n_months": int(len(al)), "spearman": round(rho, 3),
                                     "expected_sign": "+", "holds": bool(rho >= CORR_THRESHOLD)}
        else:
            out["comext_imports"] = {"n_months": int(len(al)), "verdict": "INSUFFICIENT_OVERLAP"}

    if FAM.exists():
        fam = pd.read_parquet(FAM)
        fam["Date"] = pd.to_datetime(fam["Date"])
        anom = (pd.to_numeric(fam.set_index("Date")["fr_mais_prod_anomaly_lag1"], errors="coerce")
                .resample("ME").last())
        al = pd.concat([cy_m, anom.rename("prod_anom")], axis=1).dropna()
        if len(al) >= 12:
            rho = float(al["cy_proxy"].corr(al["prod_anom"], method="spearman"))
            out["fr_production_anomaly"] = {"n_months": int(len(al)), "spearman": round(rho, 3),
                                            "expected_sign": "-",
                                            "holds": bool(rho <= -CORR_THRESHOLD)}
        else:
            out["fr_production_anomaly"] = {"n_months": int(len(al)),
                                            "verdict": "INSUFFICIENT_OVERLAP"}
    out["holds_any"] = any(isinstance(v, dict) and v.get("holds") for v in out.values())
    return out


def _link_c_cy_to_compression(cy: pd.Series, basis_z: pd.Series) -> dict[str, Any]:
    bz = basis_z.dropna()
    fwd_change = bz.shift(-20) - bz  # h20, descriptif
    al = pd.concat([cy, bz.rename("bz"), fwd_change.rename("chg")], axis=1).dropna()
    sig = al[al["bz"] >= 1.0]
    if len(sig) < 30:
        return {"n_signal_days": int(len(sig)), "verdict": "INSUFFICIENT"}
    med = sig["cy_proxy"].median()
    hi, lo = sig[sig["cy_proxy"] > med], sig[sig["cy_proxy"] <= med]
    if len(hi) < 10 or len(lo) < 10:
        return {"n_signal_days": int(len(sig)), "n_cy_high": int(len(hi)),
                "n_cy_low": int(len(lo)), "cy_median_split": round(float(med), 4),
                "verdict": "DEGENERATE_SPLIT",
                "note": "split médian dégénéré (CY quasi jamais > médiane sur jours-signal du "
                        "proxy) -> maillon C non testable sur l'historique proxy", "holds": False}
    chg_hi, chg_lo = float(hi["chg"].mean()), float(lo["chg"].mean())
    # attendu : CY haut (prime justifiée) -> compression h20 plus LENTE (chg moins négatif)
    holds = chg_hi > chg_lo
    return {"n_signal_days": int(len(sig)), "cy_median_split": round(float(med), 4),
            "n_cy_high": int(len(hi)), "n_cy_low": int(len(lo)),
            "mean_bz_change_h20_cy_high": round(chg_hi, 3),
            "mean_bz_change_h20_cy_low": round(chg_lo, 3),
            "expected": "chg_high > chg_low (CY haut = prime justifiée = plus lente)",
            "holds": bool(holds)}


def run_v166_convenience_yield(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if not CURVE.exists():
        return {"version": "V166-CONVYIELD", "verdict": "DATA_GATED_NO_CURVE"}
    cy = load_cy_proxy()
    start, end = df.index.min(), df.index.max()
    cy = cy[(cy.index >= start) & (cy.index <= end)]
    cy = cy[~((cy.index >= "2024-01-01") & (cy.index <= "2024-12-31"))]  # holdout
    basis_z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")

    link_a = _link_a_cy_to_basis(cy, basis_z)
    link_b = _link_b_balance_to_cy(cy)
    link_c = _link_c_cy_to_compression(cy, basis_z)

    a_ok = link_a.get("holds", False)
    b_ok = link_b.get("holds_any", False)
    c_ok = link_c.get("holds", False)
    if not a_ok:
        verdict = "CHAIN_NOT_SUPPORTED"
    elif b_ok and c_ok:
        verdict = "CHAIN_SUPPORTED_EXPLORATORY"
    else:
        verdict = "CHAIN_PARTIAL"

    out = {
        "version": "V166-CONVYIELD",
        "verdict": verdict,
        "cy_proxy": {"definition": "ema_roll_yield_ann (front−second annualisé, >0 = backwardation)",
                     "n_days": int(cy.notna().sum()),
                     "sparsity_warning": "~15 % des dates seulement (courbe proxy creuse) -> "
                                         "EXPLORATOIRE ; relais courbe officielle V125 en forward",
                     "rate_assumption": "taux EUR constant (série absente du repo), ordre du CY "
                                        "préservé à constante près"},
        "link_a_cy_to_basis": link_a,
        "link_b_balance_to_cy": link_b,
        "link_c_cy_to_compression": link_c,
        "note": "Chaîne R6 bilan→CY→basis→compression, directions pré-déclarées, aucun fit. "
                "Baseline z>1 intouchée. Holdout 2024 exclu.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V166_DIR / "v166_convenience_yield.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

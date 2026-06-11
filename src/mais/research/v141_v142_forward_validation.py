"""V141/V142 — Validation forward de la courbe EMA et de la substitution MATIF (auto-mûrissante).

Les deux hypothèses à valider EN FORWARD (jamais sur le proxy seul) :
  V141 : le narrowing du front-next officiel précède/accompagne la compression du basis officiel.
  V142 : la baisse du ratio blé/maïs MATIF accompagne la compression (substitution).

Le journal officiel n'a que quelques jours : tout verdict est GATÉ par MIN_DAYS. En dessous, le module
rend ACCUMULATING_n et se contente d'aligner les séries — il mûrit automatiquement avec le daily CI,
sans retouche de code. Corrélations de Spearman sur variations, aucun modèle. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT

V_DIR = ARTEFACTS_DIR / "v141_v142"
V_DIR.mkdir(parents=True, exist_ok=True)

CURVE_PATH = PROJECT_ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
MATIF_PATH = PROJECT_ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
MIN_DAYS = 40   # gate : aucun claim avant 40 jours officiels alignés


def _spearman(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    m = x.notna() & y.notna()
    n = int(m.sum())
    if n < 10:
        return {"n": n, "rho": None, "p": None}
    try:
        from scipy.stats import spearmanr
        rho, p = spearmanr(x[m], y[m])
        return {"n": n, "rho": round(float(rho), 4), "p": round(float(p), 4)}
    except ImportError:
        return {"n": n, "rho": round(float(x[m].corr(y[m], method="spearman")), 4), "p": None}


def build_aligned_panel() -> pd.DataFrame:
    """Aligne basis officiel (vue FINAL-only), front-next spread et ratio MATIF par price_date."""
    from mais.research import v27_official_forward as v27
    j = v27.load_forward_journal(final_only=True)
    if j is None or j.empty:
        return pd.DataFrame()
    j = j[["price_date", "basis_official_eur_t", "basis_z_used"]].copy()
    j["price_date"] = pd.to_datetime(j["price_date"].astype(str))
    panel = j.sort_values("price_date").drop_duplicates("price_date", keep="last")
    if CURVE_PATH.exists():
        c = pd.read_parquet(CURVE_PATH)
        c["price_date"] = pd.to_datetime(c["price_date"].astype(str))
        panel = panel.merge(c[["price_date", "front_next_spread", "backwardation"]],
                            on="price_date", how="left")
    if MATIF_PATH.exists():
        m = pd.read_parquet(MATIF_PATH)
        m["price_date"] = pd.to_datetime(m["price_date"].astype(str))
        panel = panel.merge(m[["price_date", "ratio"]], on="price_date", how="left")
    return panel.reset_index(drop=True)


def run_v141_v142_forward() -> dict[str, Any]:
    panel = build_aligned_panel()
    n = int(len(panel))
    out: dict[str, Any] = {
        "version": "V141-V142-FORWARD",
        "n_official_days_aligned": n,
        "min_days_for_claim": MIN_DAYS,
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    if n == 0:
        out["verdict"] = "WAITING_DATA"
        return out
    d_basis = pd.to_numeric(panel["basis_official_eur_t"], errors="coerce").diff()
    tests = {}
    if "front_next_spread" in panel.columns:
        tests["v141_d_spread_vs_d_basis"] = _spearman(
            pd.to_numeric(panel["front_next_spread"], errors="coerce").diff(), d_basis)
    if "ratio" in panel.columns:
        tests["v142_d_ratio_vs_d_basis"] = _spearman(
            pd.to_numeric(panel["ratio"], errors="coerce").diff(), d_basis)
    out["tests_spearman_on_changes"] = tests
    out["verdict"] = (f"ACCUMULATING_{n}_DAYS" if n < MIN_DAYS else "SAMPLE_OK_SEE_TESTS")
    out["note"] = ("Gate honnête : aucun claim avant 40 jours officiels ; le module mûrit "
                   "automatiquement avec le daily CI (V125 courbe + V126 MATIF + journal V27).")
    (V_DIR / "v141_v142_forward.json").write_text(json.dumps(out, indent=2, default=str),
                                                  encoding="utf-8")
    return out

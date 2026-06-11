"""V161 — Parité d'import physique UE et résidu du basis.

Hypothèse économique : la prime EMA/CBOT devrait être ancrée par le COÛT D'IMPORT physique réel
(prix unitaire CIF des imports extra-UE, COMEXT). Si le basis s'écarte de cette parité, l'écart
(résidu) devrait revenir plus vite/proprement que le basis_z brut — c'est le test GO du ticket.

Anti-leakage : la parité du mois M n'est connue qu'à fin M + PUBLICATION_LAG_DAYS (merge_asof backward) ;
le z du résidu est expandant avec shift(1). AR(1) descriptif, aucun trading. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.collect.comext_unit_value import PUBLICATION_LAG_DAYS, load_comext_unit_values
from mais.paths import ARTEFACTS_DIR, PROCESSED_DIR

V161_DIR = ARTEFACTS_DIR / "v161"
V161_DIR.mkdir(parents=True, exist_ok=True)

PARITY_PARTNER = "EXT_EU27_2020"   # coût d'import marginal toutes origines extra-UE
MIN_Z_PERIODS = 252


def _half_life(s: pd.Series) -> tuple[float | None, float | None]:
    """AR(1) sur série stationnarisée : phi et demi-vie en jours de bourse."""
    s = s.dropna()
    if len(s) < 120:
        return None, None
    x, y = s.shift(1).dropna(), s.iloc[1:]
    x, y = x.align(y, join="inner")
    phi = float(np.polyfit(x, y, 1)[0])
    if not (0 < phi < 1):
        return phi, None
    return phi, float(np.log(0.5) / np.log(phi))


def _expanding_z(s: pd.Series, min_periods: int = MIN_Z_PERIODS) -> pd.Series:
    m = s.expanding(min_periods).mean().shift(1)
    sd = s.expanding(min_periods).std().shift(1)
    return (s - m) / sd


def build_parity_series(df_daily: pd.DataFrame, comext: pd.DataFrame) -> pd.DataFrame:
    """Série quotidienne : parité connue à t (laggée publication) + résidu basis - parité."""
    cb = comext[comext["partner"] == PARITY_PARTNER].copy()
    if cb.empty:
        return pd.DataFrame()
    cb["month_end"] = pd.to_datetime(cb["month"] + "-01") + pd.offsets.MonthEnd(0)
    cb["available_at"] = cb["month_end"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)

    d = df_daily.copy()
    d["Date"] = pd.to_datetime(d["Date"])
    d["month"] = d["Date"].dt.strftime("%Y-%m")
    cbot_m = d.groupby("month")["cbot_eur_t"].mean().rename("cbot_month_mean")
    cb = cb.merge(cbot_m, on="month", how="inner")
    # parité = prime physique implicite : coût d'import CIF - CBOT converti du même mois
    cb["parity_premium"] = cb["unit_value_eur_t"] - cb["cbot_month_mean"]

    out = pd.merge_asof(
        d.sort_values("Date"),
        cb.sort_values("available_at")[["available_at", "parity_premium", "unit_value_eur_t"]],
        left_on="Date", right_on="available_at", direction="backward")
    out["parity_residual"] = out["ema_cbot_basis"] - out["parity_premium"]
    return out


def run_v161_import_parity(df_daily: pd.DataFrame | None = None) -> dict[str, Any]:
    if df_daily is None:
        df_daily = pd.read_parquet(
            PROCESSED_DIR / "features.parquet",
            columns=["Date", "ema_cbot_basis", "ema_cbot_basis_zscore_52w", "cbot_eur_t"])
    comext = load_comext_unit_values()
    if comext.empty:
        return {"version": "V161-IMPORT-PARITY", "verdict": "WAITING_DATA",
                "reason": "archive COMEXT absente (fetch_comext_unit_values)"}
    df_daily = df_daily[df_daily["ema_cbot_basis"].notna()]
    panel = build_parity_series(df_daily, comext)
    panel = panel[panel["parity_premium"].notna()]
    if len(panel) < 500:
        return {"version": "V161-IMPORT-PARITY", "verdict": "WAITING_DATA",
                "reason": f"overlap insuffisant ({len(panel)} jours)"}

    basis_z = pd.to_numeric(panel["ema_cbot_basis_zscore_52w"], errors="coerce")
    residual_z = _expanding_z(pd.to_numeric(panel["parity_residual"], errors="coerce"))
    common = basis_z.notna() & residual_z.notna()
    phi_b, hl_b = _half_life(basis_z[common])
    phi_r, hl_r = _half_life(residual_z[common])
    corr_level = float(pd.to_numeric(panel["ema_cbot_basis"], errors="coerce")
                       .corr(pd.to_numeric(panel["parity_premium"], errors="coerce")))

    go = hl_r is not None and hl_b is not None and hl_r < hl_b
    out = {
        "version": "V161-IMPORT-PARITY",
        "verdict": "PARITY_RESIDUAL_BETTER" if go else "PARITY_EXPLANATORY_ONLY",
        "n_days_overlap": int(common.sum()),
        "publication_lag_days": PUBLICATION_LAG_DAYS,
        "partner": PARITY_PARTNER,
        "corr_basis_vs_parity_premium_level": round(corr_level, 3),
        "ar1": {"basis_z": {"phi": round(phi_b, 4) if phi_b else None,
                            "half_life_days": round(hl_b, 1) if hl_b else None},
                "parity_residual_z": {"phi": round(phi_r, 4) if phi_r else None,
                                      "half_life_days": round(hl_r, 1) if hl_r else None}},
        "go_criterion": "residual half-life < basis_z half-life (réversion plus rapide vers l'ancre physique)",
        "guardrails": [
            "parité laggée publication (fin de mois + 60 j) : connue à t, pas de fuite",
            "z expandant shift(1) ; AR(1) descriptif, aucun signal ajouté à la baseline",
            "unit value CIF = FOB + fret implicite ; pas de décomposition fret (Baltic non branché)",
        ],
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V161_DIR / "v161_import_parity.json").write_text(json.dumps(out, indent=2, default=str),
                                                      encoding="utf-8")
    return out

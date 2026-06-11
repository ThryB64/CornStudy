"""V155 — Validation exploratoire du Weather Forecast Revision Engine (données réelles previous-runs).

Première exploitation de l'archive V140-DATA (`data/weather/forecast_revisions.parquet`) : est-ce que les
RÉVISIONS de prévision (lead-fixe, anti-leakage par issue_date) sont associées aux mouvements CBOT qui
suivent ? Canal économique : révision vers PLUS CHAUD / PLUS SEC sur le corn belt US = soutien haussier
CBOT (V140), donc compression de la prime plus probable par rattrapage CBOT.

HONNÊTETÉ STATISTIQUE : la fenêtre API ne donne que ~92 jours (~60 séances). Tout résultat ici est
PRELIMINARY_N_SMALL — aucune décision d'indicateur ne s'appuie dessus tant que l'archive accumulée
(append quotidien CI) n'atteint pas une saison complète. Résultats négatifs conservés.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.collect.openmeteo_forecast_collector import US_CORN_BELT_CENTROIDS
from mais.collect.openmeteo_previous_runs import load_revisions, revision_tape
from mais.paths import ARTEFACTS_DIR

V155_DIR = ARTEFACTS_DIR / "v155"
V155_DIR.mkdir(parents=True, exist_ok=True)

NEAR_LEADS = (1, 2, 3)   # révisions proches de l'échéance (to_lead <= 2 : from_lead 1..3)
MIN_N_FOR_ANY_CLAIM = 150  # en dessous, verdict bloqué à PRELIMINARY_N_SMALL


def build_revision_features(df_long: pd.DataFrame) -> pd.DataFrame:
    """Features par issue_date × région : révision moyenne vers chaud (tmax) et vers sec (-precip).

    Une révision `from_lead k -> to_lead k-1` est indexée par la date d'émission du run le plus récent
    (connue ce jour-là) : aucune valeur future n'entre dans la ligne du jour.
    """
    if df_long.empty:
        return pd.DataFrame()
    tape = revision_tape(df_long)
    if tape.empty:
        return pd.DataFrame()
    tape = tape[tape["from_lead"].isin(NEAR_LEADS)].copy()
    tape["region"] = np.where(tape["zone"].isin(US_CORN_BELT_CENTROIDS), "us", "eu")
    rows = []
    for (issue, region), g in tape.groupby(["issue_date", "region"]):
        tmax = g[g["variable"] == "tmax"]["revision"]
        prec = g[g["variable"] == "precip"]["revision"]
        rows.append({
            "issue_date": issue, "region": region,
            "rev_hot": float(tmax.mean()) if len(tmax) else np.nan,
            "rev_dry": float(-prec.mean()) if len(prec) else np.nan,
            "n_zone_revisions": int(len(g)),
        })
    feats = pd.DataFrame(rows)
    feats["bullish_revision"] = feats["rev_hot"].fillna(0) + feats["rev_dry"].fillna(0)
    return feats.sort_values(["issue_date", "region"]).reset_index(drop=True)


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


def _cbot_closes(cbot_close: pd.Series | None) -> pd.Series | None:
    if cbot_close is not None:
        return cbot_close
    try:
        import yfinance as yf
        df = yf.download("ZC=F", start="2026-03-01", progress=False, auto_adjust=True)
        s = df["Close"]
        if isinstance(s, pd.DataFrame):  # colonne MultiIndex (Ticker)
            s = s.iloc[:, 0]
        s.index = pd.to_datetime(s.index).strftime("%Y-%m-%d")
        return s.astype(float)
    except Exception:  # noqa: BLE001
        return None


def run_v155_validation(cbot_close: pd.Series | None = None) -> dict[str, Any]:
    """Test exploratoire : révisions US (chaud/sec) vs rendements CBOT forward h5/h10."""
    rev = load_revisions()
    if rev.empty:
        return {"version": "V155-WEATHER-REVISION", "verdict": "WAITING_DATA",
                "reason": "archive forecast_revisions absente (lancer fetch_previous_runs)"}
    feats = build_revision_features(rev)
    us = feats[feats["region"] == "us"].set_index("issue_date")
    closes = _cbot_closes(cbot_close)
    if closes is None or us.empty:
        return {"version": "V155-WEATHER-REVISION", "verdict": "WAITING_DATA",
                "reason": "série CBOT indisponible (réseau) ou pas de features US"}

    logp = np.log(closes)
    fwd = {h: (logp.shift(-h) - logp) for h in (5, 10)}
    us = us.join(pd.DataFrame({f"cbot_fwd_h{h}": f for h, f in fwd.items()}), how="inner")

    tests = {}
    for feat in ("rev_hot", "rev_dry", "bullish_revision"):
        for h in (5, 10):
            tests[f"{feat}__cbot_fwd_h{h}"] = _spearman(us[feat], us[f"cbot_fwd_h{h}"])

    n_days = int(us.shape[0])
    sample_too_small = n_days < MIN_N_FOR_ANY_CLAIM
    # lecture directionnelle honnête (pas un GO) : combien de tests vont dans le sens économique attendu
    expected_positive = [k for k in tests if tests[k]["rho"] is not None]
    n_pos = sum(1 for k in expected_positive if tests[k]["rho"] > 0)
    out = {
        "version": "V155-WEATHER-REVISION",
        "verdict": "PRELIMINARY_N_SMALL" if sample_too_small else "SAMPLE_OK_SEE_TESTS",
        "n_issue_days_matched": n_days,
        "min_n_for_any_claim": MIN_N_FOR_ANY_CLAIM,
        "window": {"first_issue": str(us.index.min()), "last_issue": str(us.index.max())},
        "tests_spearman": tests,
        "directional_reading": {
            "expected_sign": "positif (révision chaud/sec US -> CBOT up)",
            "n_tests": len(expected_positive), "n_positive_rho": n_pos,
        },
        "guardrails": [
            "AUCUNE décision d'indicateur sur ce n ; l'archive CI append chaque jour (fenêtre API 92 j)",
            "features indexées issue_date (anti-leakage lead-fixe), cibles forward only",
            "résultat négatif conservé tel quel (V45 : le réalisé ne prédit pas ; ceci teste la RÉVISION)",
        ],
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V155_DIR / "v155_weather_revision_results.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

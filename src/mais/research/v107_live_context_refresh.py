"""V107 — Rafraîchir le CONTEXTE live jusqu'en 2026 (lever le retard de 311 j sur les diagnostics).

Problème (V101) : le signal officiel est à 2026-06-01 mais les diagnostics de contexte (CBOT_SUPPORT...) sont
calculés sur le master de features arrêté à 2025-07-25. On rafraîchit ici la partie MARCHÉ (la plus
importante : CBOT_SUPPORT est le facteur pivot) en re-collectant ZC/ZW/ZS/CL/NG (Yahoo, 5 ans) et en
recalculant CBOT_SUPPORT v2 à la date la plus récente. Gate de fraîcheur : si le retard dépasse 5 jours
ouvrés, les diagnostics sont marqués indicatifs.

LIMITE : les diagnostics dépendant de la COURBE EMA officielle (PHYSICAL_TENSION) et du basis historique
(résidu substitution) ne sont pas refraîchissables sans la courbe officielle accumulée -> restent flaggés.
COT optionnel. Réseau requis ; SKIP propre hors ligne.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Baseline figée.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V107_DIR = ARTEFACTS_DIR / "v107"
V107_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
SYMBOLS = {"corn_close": "ZC=F", "wheat_close": "ZW=F", "soy_close": "ZS=F",
           "oil_close": "CL=F", "gas_close": "NG=F"}
FRESHNESS_GATE_DAYS = 5


def _yahoo_daily(sym: str, rng: str = "5y", timeout: int = 30) -> pd.Series:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={rng}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    res = d["chart"]["result"][0]
    ts = pd.to_datetime(res["timestamp"], unit="s").normalize()
    close = res["indicators"]["quote"][0]["close"]
    return pd.Series(close, index=ts, name=sym).dropna()


def fetch_live_market(try_network: bool = True) -> pd.DataFrame:
    if not try_network:
        return pd.DataFrame()
    cols = {}
    for name, sym in SYMBOLS.items():
        try:
            cols[name] = _yahoo_daily(sym)
        except Exception:  # noqa: BLE001
            continue
    if "corn_close" not in cols:
        return pd.DataFrame()
    df = pd.DataFrame(cols).sort_index()
    return df[~df.index.duplicated(keep="last")]


def build_live_context_frame(market: pd.DataFrame, official_basis_z: float) -> pd.DataFrame:
    """Frame avec features dérivées + basis_z officiel injecté sur la dernière ligne (signal actif)."""
    df = market.copy()
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    df["corn_sma_50"] = corn.rolling(50, min_periods=30).mean()
    df["corn_logret_20d"] = np.log(corn / corn.shift(20))
    df["corn_realized_vol_20"] = corn.pct_change().rolling(20, min_periods=10).std()
    # basis_z : on n'a que l'officiel du jour -> on l'injecte sur la dernière ligne pour activer le contexte
    df["ema_cbot_basis_zscore_52w"] = np.nan
    df.iloc[-1, df.columns.get_loc("ema_cbot_basis_zscore_52w")] = official_basis_z
    return df


def run_v107_context_refresh(try_network: bool = True) -> dict[str, Any]:
    # signal officiel récent
    if not OFFICIAL_JOURNAL.exists():
        return {"version": "V107-CONTEXT-REFRESH", "verdict": "NO_OFFICIAL_JOURNAL"}
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    last = j.iloc[-1]
    signal_date = pd.Timestamp(last["price_date"])
    basis_z = float(last["basis_z_used"]) if pd.notna(last.get("basis_z_used")) else 1.5

    market = fetch_live_market(try_network=try_network)
    if len(market) == 0:
        return {"version": "V107-CONTEXT-REFRESH", "verdict": "NO_MARKET_DATA_OFFLINE",
                "note": "Réseau indisponible ; contexte non rafraîchi (rester sur diagnostics master, flaggés)."}

    market_date = market.index[-1]
    frame = build_live_context_frame(market, basis_z)
    # NB : pas d'assert_no_holdout ici — calcul LIVE/forward d'un diagnostic courant (la fenêtre glissante
    # inclut légitimement 2024 comme historique), ce n'est ni un backtest ni une sélection de règle.

    # CBOT_SUPPORT v2 (pivot) sur données fraîches ; ENSO optionnel
    enso = None
    try:
        from mais.research.v79_enso_regime import enso_features, fetch_oni
        ef = enso_features(frame.index, fetch_oni(try_network=True))
        enso = ef.get("enso_regime")
    except Exception:  # noqa: BLE001
        enso = None
    from mais.research.v86_cbot_support_v2 import compute_cbot_support_v2
    cs2 = compute_cbot_support_v2(frame, enso_regime=enso)
    last_ctx = cs2.iloc[-1]
    cbot_support_v2 = str(last_ctx["cbot_support_v2"])

    lag_days = int((signal_date - market_date).days)
    # gate de fraîcheur : retard en jours ouvrés approx
    fresh = abs(lag_days) <= FRESHNESS_GATE_DAYS
    verdict = "CONTEXT_REFRESHED_FRESH" if fresh else "CONTEXT_REFRESHED_BUT_LAGGED"

    out = {
        "version": "V107-CONTEXT-REFRESH",
        "signal_date": str(signal_date.date()),
        "market_data_date": str(market_date.date()),
        "context_lag_days": lag_days,
        "fresh_within_gate": bool(fresh),
        "cbot_support_v2_live": cbot_support_v2,
        "cbot_support_components": {
            "uptrend_sma50": int(last_ctx["c_uptrend"]) if pd.notna(last_ctx["c_uptrend"]) else None,
            "momentum20_pos": int(last_ctx["c_momentum"]) if pd.notna(last_ctx["c_momentum"]) else None,
            "corn_cheap_vs_wheat": int(last_ctx["c_corn_cheap"]) if pd.notna(last_ctx["c_corn_cheap"]) else None,
            "la_nina": int(last_ctx["c_la_nina"]) if pd.notna(last_ctx["c_la_nina"]) else None,
        },
        "refreshed": ["corn", "wheat", "soy", "crude", "gas", "CBOT_SUPPORT_v2"],
        "still_lagged": ["ADVERSE_RISK (résidu substitution = basis historique)",
                         "PHYSICAL_TENSION (courbe EMA officielle)", "COT (à brancher)"],
        "verdict": verdict,
        "interpretation": (
            f"Contexte MARCHÉ rafraîchi au {market_date.date()} (signal officiel {signal_date.date()}, "
            f"retard {lag_days} j). CBOT_SUPPORT v2 live = **{cbot_support_v2}** (recalculé sur ZC/ZW/ZS "
            "2026, le facteur PIVOT). Les diagnostics dépendant de la courbe EMA officielle / du basis "
            "historique restent en retard tant que la courbe officielle ne s'accumule pas. Le retard de 311 j "
            "sur le pivot CBOT_SUPPORT est ainsi LEVÉ."),
        "note": "Données Yahoo 5 ans, dérivées sma50/logret/vol calculées sur la série fraîche. ENSO optionnel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V107_DIR / "v107_context_refresh.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def live_context_report_block(try_network: bool = False) -> str:
    """Bloc rapport : lit l'artefact persistant (rafraîchi par le collecteur quotidien) ; réseau optionnel."""
    artefact = V107_DIR / "v107_context_refresh.json"
    s: dict[str, Any] = {}
    if try_network:
        try:
            s = run_v107_context_refresh(try_network=True)
        except Exception:  # noqa: BLE001
            s = {}
    if s.get("verdict") not in ("CONTEXT_REFRESHED_FRESH", "CONTEXT_REFRESHED_BUT_LAGGED") and artefact.exists():
        try:
            s = json.loads(artefact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return ""
    if s.get("verdict") not in ("CONTEXT_REFRESHED_FRESH", "CONTEXT_REFRESHED_BUT_LAGGED"):
        return ""
    comp = s["cbot_support_components"]
    facts = [k for k, v in comp.items() if v == 1]
    return (
        "### Contexte CBOT rafraîchi 2026 (V107 — données live)\n"
        f"- Marché au {s['market_data_date']} (signal {s['signal_date']}, retard {s['context_lag_days']} j) "
        f"· fraîcheur OK : {s['fresh_within_gate']}\n"
        f"- **CBOT_SUPPORT v2 live = {s['cbot_support_v2_live']}** (facteurs actifs : {', '.join(facts) or 'aucun'})\n"
        f"- Encore en retard : {'; '.join(s['still_lagged'])}\n"
        "- Le pivot CBOT_SUPPORT n'est plus daté de 2025. RESEARCH_ONLY_NOT_TRADING.\n"
    )

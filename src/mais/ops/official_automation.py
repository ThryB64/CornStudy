"""V42 — Official Data Automation & Backfill.

Industrialise la collecte officielle Euronext EMA : calendrier de marché, table de sessions append-only,
comparaison proxy vs officiel jour après jour. AUCUNE modification de la baseline short basis-haut.

NB nommage : la phase recherche `V41` du dépôt = CBOT_SUPPORT. Cette phase d'INFRASTRUCTURE est nommée
`V42` pour ne pas écraser ce module ; elle correspond aux tickets « V41 Official Data Automation » demandés.

- V42-01 calendrier : `mais.calendar.market_calendar` (week-end / férié / session).
- V42-04 table sessions append-only (option B : tous les jours calendaires, statut NO_SESSION explicite).
- V42-05 comparaison proxy vs officiel glissante (spread, accord de signal) sur le journal V27.
- V42-06 monitoring calendar-aware : un jour NO_SESSION n'est jamais une panne.

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.calendar import classify_session, is_trading_day
from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V42_DIR = ARTEFACTS_DIR / "v42"
V42_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_DIR = ROOT / "data" / "official_forward"
OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
MARKET_SESSIONS_PARQUET = OFFICIAL_DIR / "market_sessions.parquet"
MARKET_SESSIONS_CSV = OFFICIAL_DIR / "market_sessions.csv"


def update_market_sessions(as_of: pd.Timestamp | None = None, lookback_days: int = 30) -> dict[str, Any]:
    """V42-04 : table calendrier append-only (option B). Une ligne par jour, statut de session explicite."""
    as_of = pd.Timestamp(as_of).normalize() if as_of is not None else pd.Timestamp.today().normalize()
    start = as_of - pd.Timedelta(days=lookback_days)
    rng = pd.date_range(start, as_of, freq="D")
    rows = [{"date": ts.date().isoformat(), "weekday": ts.day_name(),
             "session": classify_session(ts), "trading_session": bool(is_trading_day(ts))} for ts in rng]
    fresh = pd.DataFrame(rows)
    if MARKET_SESSIONS_PARQUET.exists():
        prev = pd.read_parquet(MARKET_SESSIONS_PARQUET)
        combined = pd.concat([prev, fresh], ignore_index=True).drop_duplicates("date", keep="last")
    else:
        combined = fresh
    combined = combined.sort_values("date").reset_index(drop=True)
    combined.to_parquet(MARKET_SESSIONS_PARQUET, index=False)
    combined.to_csv(MARKET_SESSIONS_CSV, index=False)
    return {"n_days": int(len(combined)), "trading_days": int(combined["trading_session"].sum()),
            "no_session_days": int((~combined["trading_session"]).sum()),
            "last_date": str(combined["date"].iloc[-1])}


OFFICIAL_STORE = ROOT / "data" / "raw" / "euronext_ema_official" / "official_daily.parquet"


def assess_public_backfill_coverage() -> dict[str, Any]:
    """V42-02 : que couvre réellement la source publique Euronext ? (snapshot accumulé, pas d'historique long)."""
    if not OFFICIAL_STORE.exists():
        out = {"version": "V42-PUBLIC-BACKFILL", "verdict": "NO_STORE", "n_days": 0}
        (V42_DIR / "public_backfill_coverage.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        return out
    df = pd.read_parquet(OFFICIAL_STORE)
    days = sorted(df["price_date"].astype(str).unique())
    n = len(days)
    contracts = sorted(df["contract_code"].dropna().astype(str).unique()) if "contract_code" in df else []
    verdict = ("PUBLIC_BACKFILL_TOO_LIMITED_SNAPSHOT_ONLY" if n < 10
               else "PUBLIC_BACKFILL_OK_SHORT_HISTORY")
    out = {
        "version": "V42-PUBLIC-BACKFILL",
        "n_days": n,
        "date_range": [days[0], days[-1]] if n else None,
        "n_contracts_seen": len(contracts),
        "contracts_seen": contracts,
        "verdict": verdict,
        "data_strategy": {
            "niveau_1_public": "Endpoint live.euronext.com EMA/DPAR = SNAPSHOT du jour (contrats actifs + "
                               "settlement/OI/volume). PAS d'historique profond ni contrats expirés. "
                               "-> on accumule jour après jour (append-only).",
            "niveau_2_web_services": "Euronext Web Services (REST/JSON, historical) : demande officielle pour "
                                     "EMA-DPAR daily settlement OHLC/volume/OI + contrats expirés depuis 2014.",
            "niveau_3_vendors": "Bloomberg (EPA<COMDTY>CT), LSEG/Refinitiv (0#EMA:), CQG (PZ), "
                                "Trading Technologies (yEMA), Barchart API.",
        },
        "note": "L'historique long fiable nécessite Web Services/vendor. La source publique sert au forward.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V42_DIR / "public_backfill_coverage.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def proxy_vs_official_tracking(master_df: pd.DataFrame | None = None) -> dict[str, Any]:
    """V42-05 : compare jour après jour le proxy historique vs l'officiel (journal V27)."""
    from mais.research.v27_official_forward import load_forward_journal
    j = load_forward_journal()
    if j is None or len(j) == 0:
        out = {"version": "V42-PROXY-VS-OFFICIAL", "verdict": "NO_OFFICIAL_DATA", "n_official_days": 0}
        (V42_DIR / "proxy_vs_official_tracking.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        return out

    j = j.sort_values("price_date").copy()
    rows = []
    bz_proxy = None
    basis_proxy = None
    if master_df is not None and "ema_cbot_basis_zscore_52w" in master_df.columns:
        bz_proxy = master_df["ema_cbot_basis_zscore_52w"]
        basis_proxy = master_df.get("ema_cbot_basis")
    for _, r in j.iterrows():
        d = pd.Timestamp(r["price_date"])
        rec = {
            "price_date": str(d.date()),
            "basis_official": _num(r.get("basis_official_eur_t")),
            "basis_z_official_used": _num(r.get("basis_z_used")),
            "z_source": r.get("z_source"),
            "signal_official": r.get("signal_tier"),
        }
        if bz_proxy is not None and d in bz_proxy.index:
            zp = _num(bz_proxy.loc[d])
            rec["basis_z_proxy"] = round(zp, 3) if zp is not None else None
            if basis_proxy is not None and d in basis_proxy.index:
                bp = _num(basis_proxy.loc[d])
                rec["basis_proxy"] = round(bp, 2) if bp is not None else None
                if rec["basis_official"] is not None and bp is not None:
                    rec["spread_official_minus_proxy"] = round(rec["basis_official"] - bp, 2)
            zo = rec["basis_z_official_used"]
            if zo is not None and zp is not None:
                rec["signal_agreement"] = bool((zo >= 1.0) == (zp >= 1.0))
        rows.append(rec)

    comp = pd.DataFrame(rows)
    n = len(comp)
    agree = comp["signal_agreement"].mean() if "signal_agreement" in comp.columns else None
    if n < 10:
        verdict = "TOO_SHORT_KEEP_ACCUMULATING"
    elif n < 40:
        verdict = "FIRST_COMPARISON_10D"
    else:
        verdict = "SERIOUS_COMPARISON_40D_PLUS"
    out = {
        "version": "V42-PROXY-VS-OFFICIAL",
        "n_official_days": int(n),
        "signal_agreement_rate": round(float(agree), 3) if agree is not None and not pd.isna(agree) else None,
        "milestones": {"first": 10, "serious": 40, "conclusion": 90},
        "verdict": verdict,
        "note": "Comparaison proxy vs officiel : crédibilise (ou non) le backtest proxy en conditions réelles.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    comp.to_parquet(V42_DIR / "proxy_vs_official_tracking.parquet", index=False)
    (V42_DIR / "proxy_vs_official_tracking.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def _num(v):
    try:
        if v is None or pd.isna(v):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def run_v42_automation(master_df: pd.DataFrame | None = None,
                       as_of: pd.Timestamp | None = None) -> dict[str, Any]:
    """V42-06 : orchestration calendar-aware. Un jour NO_SESSION n'est jamais une panne."""
    as_of = pd.Timestamp(as_of).normalize() if as_of is not None else pd.Timestamp.today().normalize()
    session = classify_session(as_of)
    sessions = update_market_sessions(as_of=as_of)
    tracking = proxy_vs_official_tracking(master_df)
    coverage = assess_public_backfill_coverage()
    collect_expected = is_trading_day(as_of)
    out = {
        "version": "V42-OFFICIAL-AUTOMATION",
        "as_of": str(as_of.date()),
        "session_today": session,
        "collect_expected_today": collect_expected,
        "monitoring_status": ("OK_NO_SESSION" if not collect_expected else "TRADING_DAY_COLLECT_EXPECTED"),
        "market_sessions": sessions,
        "public_backfill_coverage": coverage,
        "proxy_vs_official": tracking,
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V42_DIR / "v42_automation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

"""V128 — Basis CBOT aligné intraday : probe + accumulation forward.

Le basis quotidien compare le settlement EMA (~14h30 Paris) au CBOT close US (~20h Paris) : ~5h30 de
désynchro. V60-intraday a borné ce bruit sur la fenêtre intraday gratuite (Yahoo ZC=F, ~1-2 mois). L'historique
intraday complet est PAYANT (Barchart/CQG/TT) -> un backtest aligné sur les 42 trades est DATA_BLOCKED.

Ici on (a) ré-estime la borne de bruit sur la fenêtre dispo (réutilise V60-intraday), et (b) journalise en
forward, jour après jour, le move settlement-EU→close-US, pour accumuler la série alignée et trancher plus
tard. Verdict réaliste : WATCHLIST (accumulable forward), pas ADD_TO_PIPELINE tant que l'historique manque.
Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V128_DIR = ARTEFACTS_DIR / "v128"
V128_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL = ROOT / "data" / "official_forward" / "intraday_align_journal.jsonl"
SETTLE_HOUR_UTC = 13  # ~14h30 Paris été ≈ 12-13h UTC ; on prend l'heure pleine la plus proche


def _daily_settle_close_moves(intraday: pd.DataFrame) -> pd.DataFrame:
    """Par jour : CBOT à l'heure de settlement EU vs CBOT close US, et leur écart (move de désynchro)."""
    if intraday is None or len(intraday) == 0 or "close" not in intraday.columns:
        return pd.DataFrame()
    s = intraday["close"].dropna()
    if not isinstance(s.index, pd.DatetimeIndex):
        return pd.DataFrame()
    df = pd.DataFrame({"close": s})
    df["date"] = df.index.normalize()
    df["hour"] = df.index.hour
    recs = []
    for d, g in df.groupby("date"):
        at_settle = g[g["hour"] <= SETTLE_HOUR_UTC]
        if len(at_settle) == 0 or len(g) == 0:
            continue
        cbot_settle = float(at_settle["close"].iloc[-1])
        cbot_close = float(g["close"].iloc[-1])
        recs.append({"date": pd.Timestamp(d).normalize(), "cbot_at_eu_settle": round(cbot_settle, 2),
                     "cbot_us_close": round(cbot_close, 2), "move": round(cbot_close - cbot_settle, 2)})
    return pd.DataFrame(recs)


def _append_journal(rows: pd.DataFrame) -> int:
    if len(rows) == 0:
        return 0
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if JOURNAL.exists():
        for ln in JOURNAL.read_text(encoding="utf-8").splitlines():
            try:
                seen.add(json.loads(ln).get("date"))
            except ValueError:
                continue
    n = 0
    with JOURNAL.open("a", encoding="utf-8") as fh:
        for _, r in rows.iterrows():
            key = str(pd.Timestamp(r["date"]).date())
            if key in seen:
                continue
            fh.write(json.dumps({"date": key, "cbot_at_eu_settle": r["cbot_at_eu_settle"],
                                 "cbot_us_close": r["cbot_us_close"], "move": r["move"],
                                 "logged_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")},
                                default=str) + "\n")
            n += 1
    return n


def run_v128_intraday(try_network: bool = True) -> dict[str, Any]:
    from mais.research.intraday_aligned_basis import align_gap_stats, fetch_cbot_intraday
    intraday = fetch_cbot_intraday(try_network=try_network)
    if len(intraday) == 0:
        return {"version": "V128-INTRADAY-PROBE", "verdict": "DATA_BLOCKED",
                "reason": "intraday CBOT indisponible (réseau/offline ou historique payant)",
                "historical_status": "DATA_BLOCKED_PAID", "status": "RESEARCH_ONLY_NOT_TRADING"}
    gap = align_gap_stats(intraday)
    moves = _daily_settle_close_moves(intraday)
    n_appended = _append_journal(moves)
    n_journal = 0
    if JOURNAL.exists():
        n_journal = sum(1 for ln in JOURNAL.read_text(encoding="utf-8").splitlines() if ln.strip())

    mean_abs_move = round(float(moves["move"].abs().mean()), 2) if len(moves) else None
    out = {
        "version": "V128-INTRADAY-PROBE",
        "verdict": "WATCHLIST",
        "intraday_window_bars": int(len(intraday)),
        "align_gap_stats": gap,
        "n_days_with_move": int(len(moves)),
        "mean_abs_settle_close_move_cents": mean_abs_move,
        "journal_days_total": n_journal,
        "journal_appended_today": n_appended,
        "historical_status": "DATA_BLOCKED_PAID",
        "interpretation": (
            f"Fenêtre intraday gratuite : {len(intraday)} barres, {len(moves)} jours. Move moyen "
            f"settlement-EU→close-US ≈ {mean_abs_move} cents/boisseau (borne du bruit de désynchro intégré au "
            "basis quotidien). L'historique intraday complet étant payant, le backtest aligné sur les 42 trades "
            "reste DATA_BLOCKED -> WATCHLIST : on accumule le move en forward (journal append-only) pour "
            "trancher plus tard si l'alignement réduit assez le bruit pour valoir l'effort."),
        "note": "Réutilise V60-intraday. Probe + accumulation forward. Voir le plan de sourcing V134.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V128_DIR / "v128_intraday_probe.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def intraday_probe_report_block() -> str:
    artefact = V128_DIR / "v128_intraday_probe.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") not in ("WATCHLIST", "DATA_BLOCKED"):
        return ""
    if s["verdict"] == "DATA_BLOCKED":
        return ("### Basis aligné intraday (V128 — probe)\n"
                "- Intraday CBOT indisponible (historique payant) → **DATA_BLOCKED**. Voir sourcing V134. "
                "RESEARCH_ONLY_NOT_TRADING.\n")
    return (
        "### Basis aligné intraday (V128 — probe + accumulation)\n"
        f"- Fenêtre {s['intraday_window_bars']} barres · {s['n_days_with_move']} jours · move désynchro moyen "
        f"≈ {s['mean_abs_settle_close_move_cents']} cents · journal {s['journal_days_total']} j\n"
        "- Historique complet payant → **WATCHLIST** (accumulation forward). RESEARCH_ONLY_NOT_TRADING.\n"
    )

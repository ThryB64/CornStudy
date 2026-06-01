"""V27 — Suivi forward officiel + journal append-only.

Maintenant que la source EMA officielle Euronext est débloquée (V26), on l'utilise EN LIVE chaque jour :
on calcule le basis officiel du jour, le tier de l'indicateur figé (`MaizePremiumIndicator_RESEARCH_V1`),
les warnings, et on écrit le tout dans un journal forward APPEND-ONLY. Le passé n'est jamais réécrit.

Tant que l'historique officiel est court, le z-score reste implicite (distribution proxy trailing) :
`basis_z_official_implied`. Quand l'historique officiel atteint assez de jours, on calcule en plus
`basis_z_official_rolling` sur le basis officiel lui-même.

Statut : RESEARCH_ONLY_NOT_TRADING. Aucune exécution réelle.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V27_DIR = ARTEFACTS_DIR / "v27"
V27_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL_DIR = ROOT / "data" / "forward_journal"
JOURNAL_PARQUET = JOURNAL_DIR / "official_forward_journal.parquet"
JOURNAL_JSONL = JOURNAL_DIR / "official_forward_journal.jsonl"

ROLL_MONTHS = (2, 5, 7, 10)
MIN_OFFICIAL_ROLLING = 40
SEASON_MEDIAN_DAYS = {1: 53, 2: 53, 3: 53, 4: 23, 5: 23, 6: 23,
                      7: 47, 8: 47, 9: 51, 10: 51, 11: 51, 12: 47}


def _tier(z: float) -> str:
    if pd.isna(z) or z < 1.0:
        return "NO_SIGNAL"
    if z < 1.5:
        return "SHORT_PREMIUM_MODERATE"
    if z < 2.0:
        return "SHORT_PREMIUM_STRONG"
    return "SHORT_PREMIUM_EXTREME"


def _non_reversion_risk(z: float) -> str:
    if pd.isna(z):
        return ""
    if z >= 2.0:
        return "high"
    if z >= 1.5:
        return "medium"
    return "low"


PROXY_STATS_SNAPSHOT = JOURNAL_DIR / "proxy_trailing_stats.json"


def proxy_trailing_stats(window: int = 260) -> dict[str, float] | None:
    """Moyenne/écart-type des derniers `window` basis proxy (même construction causale que basis_z).

    Le parquet proxy est lourd (gitignoré, absent en CI). Quand il est présent on calcule ET on rafraîchit
    un petit snapshot committé ; sinon (CI/serveur) on lit ce snapshot pour rester reproductible.
    """
    import json as _json
    curve = ROOT / "data/processed/euronext/ema_curve_features.parquet"
    if curve.exists():
        cf = pd.read_parquet(curve)
        if "ema_cbot_basis" in cf.columns:
            b = pd.to_numeric(cf["ema_cbot_basis"], errors="coerce").dropna()
            if len(b) >= 20:
                tail = b.tail(window)
                stats = {"mean": float(tail.mean()), "std": float(tail.std()), "n": int(len(tail)),
                         "full_mean": float(b.mean()), "full_std": float(b.std()),
                         "refreshed_from": "ema_curve_features.parquet"}
                try:
                    PROXY_STATS_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
                    PROXY_STATS_SNAPSHOT.write_text(_json.dumps(stats, indent=2), encoding="utf-8")
                except OSError:
                    pass
                return stats
    if PROXY_STATS_SNAPSHOT.exists():
        try:
            return _json.loads(PROXY_STATS_SNAPSHOT.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    return None


def _official_rolling_z(official_basis: float) -> float | None:
    """z du basis officiel sur l'historique officiel accumulé (None tant que trop court)."""
    if not JOURNAL_PARQUET.exists():
        return None
    j = pd.read_parquet(JOURNAL_PARQUET)
    b = pd.to_numeric(j.get("basis_official_eur_t"), errors="coerce").dropna()
    if len(b) < MIN_OFFICIAL_ROLLING or b.std() == 0:
        return None
    return float((official_basis - b.mean()) / b.std())


def compute_official_signal() -> dict[str, Any]:
    """Signal du jour à partir de la donnée OFFICIELLE live (EMA settlement + CBOT/FX)."""
    from mais.research.v26_official_ema_validation import run_official_basis
    basis = run_official_basis()
    if basis.get("verdict") != "OFFICIAL_BASIS_COMPUTED":
        return {"version": "V27-OFFICIAL-SIGNAL", "verdict": basis.get("verdict", "SKIP"),
                "reason": basis.get("reason", "official basis indisponible")}

    official_basis = float(basis["basis_official_eur_t"])
    price_date = str(basis["price_date"])
    stats = proxy_trailing_stats()
    z_implied = None
    if stats and stats["std"]:
        z_implied = (official_basis - stats["mean"]) / stats["std"]
    z_official = _official_rolling_z(official_basis)
    z_used = z_official if z_official is not None else z_implied

    month = pd.Timestamp(price_date).month
    tier = _tier(z_used) if z_used is not None else "NO_SIGNAL"
    warnings_list: list[str] = []
    if month in ROLL_MONTHS:
        warnings_list.append("ROLL_RISK")
    if z_used is not None and z_used >= 2.0:
        warnings_list.append("NON_REVERSION_RISK_HIGH")

    # Contexte de courbe officielle (V30) : backwardation nearby + basis haut => compression plus lente.
    from mais.research.v30_official_curve_structure import curve_context_for_journal
    curve = curve_context_for_journal(price_date)
    if curve.get("curve_shape") == "BACKWARDATION" and tier != "NO_SIGNAL":
        warnings_list.append("BACKWARDATION_SLOWER_COMPRESSION")

    return {
        "version": "V27-OFFICIAL-SIGNAL",
        "verdict": "OFFICIAL_SIGNAL_COMPUTED",
        "price_date": price_date,
        "official_front_contract": basis["official_front_contract"],
        "official_front_settlement": basis["official_front_settlement"],
        "official_front_oi": basis["official_front_oi"],
        "cbot_cents_bu": basis["cbot_cents_bu"],
        "eurusd": basis["eurusd"],
        "cbot_eur_t": basis["cbot_eur_t"],
        "basis_official_eur_t": round(official_basis, 2),
        "basis_z_official_implied": round(float(z_implied), 3) if z_implied is not None else None,
        "basis_z_official_rolling": round(float(z_official), 3) if z_official is not None else None,
        "basis_z_used": round(float(z_used), 3) if z_used is not None else None,
        "z_source": "official_rolling" if z_official is not None else "proxy_implied",
        "signal_tier": tier,
        "objective_prudent": "z->0.5",
        "objective_full": "z->0",
        "stop_eur_t": -20.0,
        "median_horizon_days": SEASON_MEDIAN_DAYS.get(month, 47),
        "non_reversion_risk": _non_reversion_risk(z_used) if tier != "NO_SIGNAL" else "",
        "curve_shape": curve.get("curve_shape"),
        "curve_overall": curve.get("curve_overall"),
        "most_liquid_contract": curve.get("most_liquid_contract"),
        "warnings": warnings_list,
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }


def append_forward_journal(record: dict[str, Any]) -> dict[str, Any]:
    """Append-only : ajoute le signal du jour au journal. Ne réécrit JAMAIS une date déjà présente."""
    if record.get("verdict") != "OFFICIAL_SIGNAL_COMPUTED":
        return {"status": "SKIP", "reason": record.get("reason", record.get("verdict"))}
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    record = dict(record)
    record["logged_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    row = pd.DataFrame([{k: v for k, v in record.items() if not isinstance(v, list)}])
    row["warnings"] = ";".join(record.get("warnings", []))

    if JOURNAL_PARQUET.exists():
        prev = pd.read_parquet(JOURNAL_PARQUET)
        if str(record["price_date"]) in set(prev["price_date"].astype(str)):
            return {"status": "ALREADY_LOGGED", "price_date": record["price_date"],
                    "n_total": int(len(prev))}
        combined = pd.concat([prev, row], ignore_index=True)
    else:
        combined = row
    combined.to_parquet(JOURNAL_PARQUET, index=False)
    with JOURNAL_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
    return {"status": "APPENDED", "price_date": record["price_date"],
            "n_total": int(len(combined)), "signal_tier": record["signal_tier"]}


def load_forward_journal() -> pd.DataFrame:
    if not JOURNAL_PARQUET.exists():
        return pd.DataFrame()
    return pd.read_parquet(JOURNAL_PARQUET)


def summarize_forward_journal() -> dict[str, Any]:
    j = load_forward_journal()
    if j.empty:
        return {"version": "V27-JOURNAL-SUMMARY", "n_days": 0, "verdict": "EMPTY",
                "note": "Aucun jour officiel encore journalisé. Lancer le collecteur en cron quotidien."}
    j = j.sort_values("price_date")
    days = int(j["price_date"].nunique())
    tiers = j["signal_tier"].value_counts().to_dict()
    basis = pd.to_numeric(j["basis_official_eur_t"], errors="coerce").dropna()
    months_needed = max(0, 6 - days / 21)
    return {
        "version": "V27-JOURNAL-SUMMARY",
        "n_days": days,
        "first_date": str(j["price_date"].iloc[0]),
        "last_date": str(j["price_date"].iloc[-1]),
        "tier_counts": {str(k): int(v) for k, v in tiers.items()},
        "basis_official_mean": round(float(basis.mean()), 2) if len(basis) else None,
        "basis_official_last": round(float(basis.iloc[-1]), 2) if len(basis) else None,
        "official_rolling_z_available": days >= MIN_OFFICIAL_ROLLING,
        "approx_months_to_first_review": round(months_needed, 1),
        "verdict": "FORWARD_ACCUMULATING",
        "note": "Bilan forward sérieux à >=6 mois. Journal append-only, passé jamais réécrit.",
    }


def run_v27_forward() -> dict[str, Any]:
    signal = compute_official_signal()
    appended = append_forward_journal(signal)
    summary = summarize_forward_journal()
    out = {
        "version": "V27-FORWARD",
        "signal": signal,
        "journal_append": appended,
        "journal_summary": summary,
        "unblock": "OFFICIAL_FORWARD_TRACKING_OPERATIONAL",
    }
    (V27_DIR / "v27_forward.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

"""VN-A2 — Vérité des dates de session : PROVISIONAL / FINAL / REVISED + champs de temps.

Le Daily Settlement Price des commodités Euronext est fixé à **18:30 CET (heure de Paris)**, inchangé malgré
l'extension du trading à 20:15 CET (2026-04-13). Donc un snapshot collecté AVANT 18:30 reprend potentiellement
le settlement de la veille tout en étant daté du jour courant par l'en-tête → faux changement de signal.

Règle stricte (heure de Paris) :
  - collecte < 18:30      -> PROVISIONAL (settlement non final)
  - collecte >= 18:35     -> FINAL
  - 18:30-18:35           -> SETTLING (zone tampon, traité comme PROVISIONAL)

On estampille chaque ligne avec collected_at_utc/paris, record_status, effective_session_date, et on expose
des invariants vérifiables. Aucune réécriture d'un FINAL passé (anti look-ahead, cohérent V122).
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any

try:
    from zoneinfo import ZoneInfo
    _PARIS = ZoneInfo("Europe/Paris")
except Exception:  # noqa: BLE001
    _PARIS = None

DSP_CUTOFF = time(18, 30)
FINAL_AFTER = time(18, 35)


def _to_paris(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(_PARIS) if _PARIS is not None else dt_utc


def classify_record_status(collected_at_utc: datetime) -> str:
    """PROVISIONAL avant 18:30 Paris, FINAL après 18:35, SETTLING entre les deux."""
    paris = _to_paris(collected_at_utc)
    t = paris.time()
    if t >= FINAL_AFTER:
        return "FINAL"
    if t < DSP_CUTOFF:
        return "PROVISIONAL"
    return "SETTLING"


def stamp_timing(record: dict[str, Any], collected_at_utc: datetime | None = None) -> dict[str, Any]:
    """Ajoute les champs de temps + record_status. effective_session_date = price_date de l'en-tête."""
    collected_at_utc = collected_at_utc or datetime.now(timezone.utc)
    paris = _to_paris(collected_at_utc)
    status = classify_record_status(collected_at_utc)
    out = dict(record)
    out["collected_at_utc"] = collected_at_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    out["collected_at_paris"] = paris.strftime("%Y-%m-%d %H:%M:%S %Z")
    out["record_status"] = status
    out["effective_session_date"] = str(record.get("price_date")) if record.get("price_date") else None
    # avertissement explicite : signal calculé sur un settlement non final
    out["provisional_warning"] = (status != "FINAL")
    return out


def session_invariants(record: dict[str, Any]) -> list[str]:
    """Retourne la liste des violations d'invariants de session (vide = OK)."""
    violations = []
    st = record.get("record_status")
    if st not in ("PROVISIONAL", "FINAL", "SETTLING", "REVISED"):
        violations.append(f"record_status invalide: {st}")
    # un FINAL doit avoir été collecté >= 18:35 Paris
    cap = record.get("collected_at_paris")
    if st == "FINAL" and cap:
        try:
            hhmm = cap.split(" ")[1]
            t = time(int(hhmm[:2]), int(hhmm[3:5]))
            if t < FINAL_AFTER:
                violations.append(f"FINAL mais collecté {hhmm} < 18:35 Paris")
        except (IndexError, ValueError):
            pass
    if record.get("effective_session_date") is None and record.get("price_date"):
        violations.append("effective_session_date manquante")
    return violations

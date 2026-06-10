"""V150 — Backfill append-only de la vérité de session sur le journal officiel existant.

Les lignes historiques du journal n'ont pas été estampillées (le code stamp_timing n'était pas poussé
quand le bot GitHub a collecté). Mais chaque ligne porte `logged_at` (UTC). On en dérive
`record_status` / `collected_at_*` / `effective_session_date` SANS toucher au signal lui-même.

Idempotent : une ligne déjà estampillée n'est pas modifiée. On n'altère aucune valeur économique.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.premium.session_timing import classify_record_status, stamp_timing
from mais.research.v27_official_forward import JOURNAL_JSONL, JOURNAL_PARQUET

SESSION_FIELDS = ("record_status", "collected_at_utc", "collected_at_paris",
                  "effective_session_date", "provisional_warning")


def _parse_logged_at(s: str | None) -> datetime | None:
    if not s:
        return None
    txt = str(s).replace(" UTC", "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(txt, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def infer_status_from_logged_at(logged_at: str | None) -> str | None:
    dt = _parse_logged_at(logged_at)
    return classify_record_status(dt) if dt is not None else None


def _stamp_existing(record: dict[str, Any]) -> dict[str, Any]:
    """Estampille une ligne historique à partir de son logged_at (sans changer le signal)."""
    if record.get("record_status") in ("PROVISIONAL", "FINAL", "SETTLING", "REVISED"):
        return record
    dt = _parse_logged_at(record.get("logged_at"))
    if dt is None:
        out = dict(record)
        out["record_status"] = "UNKNOWN_TIMING"
        out["collected_at_utc"] = record.get("logged_at")
        out["collected_at_paris"] = None
        out["effective_session_date"] = str(record.get("price_date")) if record.get("price_date") else None
        out["provisional_warning"] = True
        return out
    return stamp_timing(record, collected_at_utc=dt)


def backfill_session_truth(write: bool = True) -> dict[str, Any]:
    """Ajoute la vérité de session aux lignes du journal qui ne l'ont pas. Réécrit jsonl + parquet.

    Append-only en esprit : on n'ajoute que des colonnes de métadonnées de session, jamais on ne
    modifie une valeur économique ni l'ordre des lignes.
    """
    if not JOURNAL_JSONL.exists():
        return {"verdict": "NO_JOURNAL", "n_lines": 0}

    lines = [ln for ln in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    records = [json.loads(ln) for ln in lines]
    n_before = sum(1 for r in records if r.get("record_status"))
    stamped = [_stamp_existing(r) for r in records]
    n_after = sum(1 for r in stamped if r.get("record_status"))
    changed = n_after - n_before

    status_counts: dict[str, int] = {}
    for r in stamped:
        status_counts[str(r.get("record_status"))] = status_counts.get(str(r.get("record_status")), 0) + 1

    # parquet désynchronisé si absent de colonne record_status (cas d'un jsonl déjà ré-estampillé)
    parquet_stale = False
    if JOURNAL_PARQUET.exists():
        try:
            parquet_stale = "record_status" not in pd.read_parquet(JOURNAL_PARQUET).columns
        except Exception:  # noqa: BLE001
            parquet_stale = True

    if write and (changed or parquet_stale):
        # jsonl : réécriture ligne à ligne (ordre préservé)
        with JOURNAL_JSONL.open("w", encoding="utf-8") as fh:
            for r in stamped:
                fh.write(json.dumps(r, default=str) + "\n")
        # parquet : reconstruit depuis les enregistrements estampillés (listes -> string warnings)
        rows = []
        for r in stamped:
            row = {k: v for k, v in r.items() if not isinstance(v, list)}
            row["warnings"] = ";".join(r.get("warnings", [])) if isinstance(r.get("warnings"), list) \
                else r.get("warnings", "")
            rows.append(row)
        pd.DataFrame(rows).to_parquet(JOURNAL_PARQUET, index=False)

    return {
        "parquet_resynced": bool(write and (changed or parquet_stale)),
        "verdict": "BACKFILLED" if changed else "ALREADY_STAMPED",
        "n_lines": len(records),
        "n_stamped_before": n_before,
        "n_stamped_after": n_after,
        "n_changed": changed,
        "session_status_counts": status_counts,
        "written": bool(write and changed),
    }


if __name__ == "__main__":
    print(json.dumps(backfill_session_truth(), indent=2))

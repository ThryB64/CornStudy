"""V150 — vérité de session : backfill, champs obligatoires, précédence FINAL."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from mais.audit import session_backfill as sb
from mais.research import v27_official_forward as v27

SESSION_FIELDS = ("record_status", "collected_at_utc", "collected_at_paris", "effective_session_date")


def test_infer_status_from_logged_at_morning_evening():
    # 09:04 UTC en juin = 11:04 Paris -> avant 18:30 -> PROVISIONAL
    assert sb.infer_status_from_logged_at("2026-06-10 09:04:54 UTC") == "PROVISIONAL"
    # 19:04 UTC = 21:04 Paris -> FINAL
    assert sb.infer_status_from_logged_at("2026-05-29 19:04:52 UTC") == "FINAL"
    assert sb.infer_status_from_logged_at(None) is None


def _seed_journal(tmp: Path) -> tuple[Path, Path]:
    jsonl = tmp / "j.jsonl"
    parquet = tmp / "j.parquet"
    recs = [
        {"price_date": "2026-06-09", "signal_tier": "SHORT_PREMIUM_STRONG",
         "basis_official_eur_t": 73.0, "warnings": [], "logged_at": "2026-06-09 08:46:34 UTC"},
        {"price_date": "2026-05-29", "signal_tier": "SHORT_PREMIUM_STRONG",
         "basis_official_eur_t": 76.0, "warnings": [], "logged_at": "2026-05-29 19:04:52 UTC"},
    ]
    jsonl.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, list)} for r in recs]).to_parquet(parquet)
    return jsonl, parquet


def test_backfill_adds_fields_and_is_idempotent(tmp_path, monkeypatch):
    jsonl, parquet = _seed_journal(tmp_path)
    monkeypatch.setattr(sb, "JOURNAL_JSONL", jsonl)
    monkeypatch.setattr(sb, "JOURNAL_PARQUET", parquet)

    out1 = sb.backfill_session_truth(write=True)
    assert out1["verdict"] == "BACKFILLED"
    assert out1["n_changed"] == 2
    assert out1["session_status_counts"]["PROVISIONAL"] == 1
    assert out1["session_status_counts"]["FINAL"] == 1

    # toutes les lignes ont désormais la vérité de session
    for ln in jsonl.read_text(encoding="utf-8").splitlines():
        rec = json.loads(ln)
        for f in SESSION_FIELDS:
            assert rec.get(f) is not None, f
    # parquet aussi
    pj = pd.read_parquet(parquet)
    for f in SESSION_FIELDS:
        assert f in pj.columns

    # idempotent : un 2e passage ne change rien
    out2 = sb.backfill_session_truth(write=True)
    assert out2["n_changed"] == 0


def test_official_journal_has_session_fields_real():
    """Le journal réel doit porter la vérité de session sur 100 % de ses lignes."""
    if not v27.JOURNAL_JSONL.exists():
        pytest.skip("journal officiel absent")
    lines = [ln for ln in v27.JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for ln in lines:
        rec = json.loads(ln)
        assert rec.get("record_status") in ("PROVISIONAL", "FINAL", "SETTLING", "REVISED",
                                             "UNKNOWN_TIMING"), rec.get("price_date")
        assert rec.get("effective_session_date") is not None


def test_final_over_provisional_precedence():
    """load_forward_journal(final_only=True) ne garde que FINAL/REVISED."""
    if not v27.JOURNAL_PARQUET.exists():
        pytest.skip("journal officiel absent")
    f = v27.load_forward_journal(final_only=True)
    if not f.empty:
        assert set(f["record_status"].astype(str)).issubset({"FINAL", "REVISED"})
        # pas de doublon de date dans la vue FINAL
        assert f["price_date"].is_unique

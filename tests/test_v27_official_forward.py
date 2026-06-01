"""Tests V27 — forward tracking officiel + journal append-only (offline-safe)."""
from __future__ import annotations

import mais.research.v27_official_forward as v27


def _fake_signal(price_date="2026-05-29", basis=76.0, z=2.5):
    return {
        "version": "V27-OFFICIAL-SIGNAL", "verdict": "OFFICIAL_SIGNAL_COMPUTED",
        "price_date": price_date, "official_front_contract": "EMA_Q2026",
        "official_front_settlement": 227.0, "official_front_oi": 14447,
        "cbot_cents_bu": 446.75, "eurusd": 1.166, "cbot_eur_t": 150.85,
        "basis_official_eur_t": basis, "basis_z_official_implied": z,
        "basis_z_official_rolling": None, "basis_z_used": z, "z_source": "proxy_implied",
        "signal_tier": v27._tier(z), "objective_prudent": "z->0.5", "objective_full": "z->0",
        "stop_eur_t": -20.0, "median_horizon_days": 23, "non_reversion_risk": "high",
        "warnings": ["ROLL_RISK", "NON_REVERSION_RISK_HIGH"], "status": "RESEARCH_ONLY_NOT_TRADING",
    }


def test_tier_thresholds():
    assert v27._tier(0.5) == "NO_SIGNAL"
    assert v27._tier(1.2) == "SHORT_PREMIUM_MODERATE"
    assert v27._tier(1.7) == "SHORT_PREMIUM_STRONG"
    assert v27._tier(2.6) == "SHORT_PREMIUM_EXTREME"


def test_append_is_append_only_and_dedup(tmp_path, monkeypatch):
    monkeypatch.setattr(v27, "JOURNAL_DIR", tmp_path)
    monkeypatch.setattr(v27, "JOURNAL_PARQUET", tmp_path / "j.parquet")
    monkeypatch.setattr(v27, "JOURNAL_JSONL", tmp_path / "j.jsonl")

    a = v27.append_forward_journal(_fake_signal("2026-05-29"))
    assert a["status"] == "APPENDED" and a["n_total"] == 1
    # même date -> jamais réécrite
    again = v27.append_forward_journal(_fake_signal("2026-05-29", basis=999.0))
    assert again["status"] == "ALREADY_LOGGED"
    j = v27.load_forward_journal()
    assert float(j["basis_official_eur_t"].iloc[0]) == 76.0  # passé intact
    # nouveau jour -> ajouté
    b = v27.append_forward_journal(_fake_signal("2026-05-30", z=1.2))
    assert b["status"] == "APPENDED" and b["n_total"] == 2


def test_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(v27, "JOURNAL_DIR", tmp_path)
    monkeypatch.setattr(v27, "JOURNAL_PARQUET", tmp_path / "j.parquet")
    monkeypatch.setattr(v27, "JOURNAL_JSONL", tmp_path / "j.jsonl")
    assert v27.summarize_forward_journal()["verdict"] == "EMPTY"
    v27.append_forward_journal(_fake_signal("2026-05-29"))
    s = v27.summarize_forward_journal()
    assert s["n_days"] == 1 and s["verdict"] == "FORWARD_ACCUMULATING"
    assert s["official_rolling_z_available"] is False


def test_compute_signal_skips_offline(monkeypatch):
    import mais.research.v26_official_ema_validation as v26
    monkeypatch.setattr(v26, "run_official_basis", lambda: {"verdict": "SKIP_OFFLINE", "reason": "no net"})
    out = v27.compute_official_signal()
    assert out["verdict"] == "SKIP_OFFLINE"
    assert v27.append_forward_journal(out)["status"] == "SKIP"

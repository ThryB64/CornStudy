"""V178 — validation 40 j proxy↔officiel : gate, paires, seuils figés."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.premium import v178_official_validation as v178


def _official(n=45, settle=216.5):
    dates = pd.date_range("2026-05-29", periods=n, freq="B").strftime("%Y-%m-%d")
    return pd.DataFrame({
        "price_date": dates, "official_front_contract": "EMA_Q2026",
        "official_front_settlement": settle, "cbot_eur_t": settle - 74.0,
        "basis_official_eur_t": 74.0, "basis_z_used": 1.85,
    })


def _quotes(official, err=0.5):
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "price_date": official["price_date"],
        "contract": official["official_front_contract"],
        "proxy_last_price": pd.to_numeric(official["official_front_settlement"])
        + rng.normal(0, err, len(official)),
    })


def test_tier_mapping():
    assert v178.tier_from_z(2.3) == "EXTREME"
    assert v178.tier_from_z(1.6) == "STRONG"
    assert v178.tier_from_z(1.1) == "MODERATE"
    assert v178.tier_from_z(0.4) == "NO_SIGNAL"
    assert v178.tier_from_z(None) is None


def test_accumulating_below_gate(monkeypatch, tmp_path):
    off = _official(n=12)
    monkeypatch.setattr(v178, "_load_official", lambda: off)
    qp = tmp_path / "quotes.parquet"
    _quotes(off).to_parquet(qp, index=False)
    monkeypatch.setattr(v178, "PROXY_QUOTES", qp)
    monkeypatch.setattr(v178, "V178_DIR", tmp_path)
    out = v178.run_v178_validation()
    assert out["verdict"] == "ACCUMULATING_12_OF_40"
    assert "preliminary_metrics_not_a_verdict" in out  # 12 paires >= 5


def test_validated_when_proxy_tracks(monkeypatch, tmp_path):
    off = _official(n=45)
    monkeypatch.setattr(v178, "_load_official", lambda: off)
    monkeypatch.setattr(v178, "PROXY_QUOTES", tmp_path / "q.parquet")
    _quotes(off, err=0.3).to_parquet(tmp_path / "q.parquet", index=False)
    monkeypatch.setattr(v178, "V178_DIR", tmp_path)
    import mais.research.v27_official_forward as v27
    monkeypatch.setattr(v27, "proxy_trailing_stats", lambda: {"mean": 37.0, "std": 20.0})
    out = v178.run_v178_validation()
    assert out["verdict"] == "PROXY_VALIDATED"
    assert out["metrics"]["price"]["mae"] < 2.0
    assert out["metrics"]["tier_agreement"] >= 0.9


def test_invalid_when_proxy_drifts(monkeypatch, tmp_path):
    off = _official(n=45)
    q = _quotes(off, err=0.1)
    q["proxy_last_price"] = q["proxy_last_price"] + 8.0  # biais énorme
    monkeypatch.setattr(v178, "_load_official", lambda: off)
    monkeypatch.setattr(v178, "PROXY_QUOTES", tmp_path / "q.parquet")
    q.to_parquet(tmp_path / "q.parquet", index=False)
    monkeypatch.setattr(v178, "V178_DIR", tmp_path)
    import mais.research.v27_official_forward as v27
    monkeypatch.setattr(v27, "proxy_trailing_stats", lambda: {"mean": 37.0, "std": 20.0})
    out = v178.run_v178_validation()
    assert out["verdict"] == "PROXY_INVALID"


def test_no_pairs_is_research_only(monkeypatch, tmp_path):
    off = _official(n=45)
    monkeypatch.setattr(v178, "_load_official", lambda: off)
    monkeypatch.setattr(v178, "PROXY_QUOTES", tmp_path / "missing.parquet")
    monkeypatch.setattr(v178, "V178_DIR", tmp_path)
    out = v178.run_v178_validation()
    assert out["verdict"] == "PROXY_RESEARCH_ONLY"

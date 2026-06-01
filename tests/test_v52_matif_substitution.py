"""Tests V52 — substitution MATIF blé/maïs (offline, fetchers mockés)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.collect.euronext_milling_wheat as ebm
import mais.collect.euronext_official_live as ema
import mais.research.v52_matif_substitution as v52


def _snap(prod, settle, oi):
    return pd.DataFrame({
        "price_date": [pd.Timestamp("2026-06-01")] * 2,
        "contract_code": [f"{prod}_U2026", f"{prod}_Z2026"],
        "settlement": settle, "open_interest": oi,
    })


def _master(n=300):
    idx = pd.bdate_range("2015-01-01", periods=n)
    rng = np.random.default_rng(0)
    corn = 150 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame({"corn_close": corn * 9.5, "wheat_close": corn * 9.5 * 1.28}, index=idx)


def test_most_liquid_picks_max_oi():
    df = _snap("EBM", [207.5, 216.0], [230480.0, 145754.0])
    assert v52._most_liquid(df)["contract_code"] == "EBM_U2026"


def test_run_v52_live_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(v52, "V52_DIR", tmp_path)
    monkeypatch.setattr(v52, "JOURNAL", tmp_path / "matif_ratio_journal.jsonl")
    monkeypatch.setattr(ebm, "fetch_milling_wheat", lambda *a, **k: _snap("EBM", [207.5, 216.0], [230480.0, 145754.0]))
    monkeypatch.setattr(ema, "fetch_official_ema", lambda *a, **k: _snap("EMA", [227.0, 222.0], [636.0, 500.0]))
    out = v52.run_v52_matif(_master())
    assert out["version"] == "V52-MATIF-SUBSTITUTION"
    assert out["live_matif"]["status"] == "OK"
    assert abs(out["live_matif"]["matif_wheat_corn_ratio"] - 207.5 / 227.0) < 1e-3
    assert out["n_matif_journal_points"] == 1
    assert out["verdict"] == "MATIF_RATIO_LIVE_OK_HISTORICAL_WAITING_DATA"


def test_run_v52_network_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(v52, "V52_DIR", tmp_path)
    monkeypatch.setattr(v52, "JOURNAL", tmp_path / "j.jsonl")

    def _boom(*a, **k):
        raise NotImplementedError("réseau indisponible")
    monkeypatch.setattr(ebm, "fetch_milling_wheat", _boom)
    monkeypatch.setattr(ema, "fetch_official_ema", _boom)
    out = v52.run_v52_matif(_master())
    assert out["verdict"] == "MATIF_RATIO_NETWORK_UNAVAILABLE"
    assert out["live_matif"]["status"] == "SKIP"

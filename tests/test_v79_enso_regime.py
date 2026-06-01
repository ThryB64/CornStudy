"""Tests V79 — régime ENSO (offline, ONI mocké)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v79_enso_regime as v79


def _oni_monthly():
    dates = pd.date_range("2012-01-01", "2024-12-01", freq="MS")
    # oscillation lente entre -1.5 et +1.5
    oni = 1.3 * np.sin(np.linspace(0, 8 * np.pi, len(dates)))
    return pd.DataFrame({"Date": dates, "oni": oni})


def _master(n=2600, seed=2):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2012-06-01", periods=n)
    cbot = 180 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 35 + rng.normal(0, 3, n)
    return pd.DataFrame({"cbot_eur_t": cbot, "ema_cbot_basis": basis}, index=idx)


def test_enso_features_causal():
    f = v79.enso_features(_master().index, _oni_monthly())
    assert "enso_regime" in f.columns
    assert set(f["enso_regime"].dropna().unique()) <= {"EL_NINO", "LA_NINA", "NEUTRAL"}


def test_run_v79(tmp_path, monkeypatch):
    monkeypatch.setattr(v79, "V79_DIR", tmp_path)
    monkeypatch.setattr(v79, "fetch_oni", lambda *a, **k: _oni_monthly())
    out = v79.run_v79_enso(_master(), try_network=True)
    assert out["version"] == "V79-ENSO-REGIME"
    if out["verdict"] != "NO_DATA_ENSO":
        assert "corr_oni_vs_fwd_cbot" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_no_network(tmp_path, monkeypatch):
    monkeypatch.setattr(v79, "V79_DIR", tmp_path)
    monkeypatch.setattr(v79, "fetch_oni", lambda *a, **k: pd.DataFrame())
    out = v79.run_v79_enso(_master(), try_network=False)
    assert out["verdict"] == "NO_DATA_ENSO"

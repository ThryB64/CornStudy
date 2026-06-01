"""Tests V24 — audit forensique (logique sur données synthétiques + invariants)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research.v24_data_forensic import run_leakage_audit


def _df():
    rng = np.random.default_rng(24)
    n = 800
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    y = (rng.normal(0, 1, n) > 0).astype(float)
    y[-40:] = np.nan  # futur indisponible en fin
    return pd.DataFrame({
        "ema_cbot_basis_zscore_52w": bz,
        "eurusd": 114.0 + rng.normal(0, 1, n),  # dérivé (mal étiqueté)
        "y_rel_outperform_h40": y,
    }, index=idx)


def test_leakage_audit_detects_derived_eurusd():
    out = run_leakage_audit(_df())
    assert "DERIVED_ARTIFACT" in out["checks"]["eurusd_column"]


def test_leakage_audit_clean_when_basis_z_not_zero_filled():
    out = run_leakage_audit(_df())
    # basis_z synthétique non rempli de 0 -> pas de flag suspect
    assert out["verdict"] in {"LEAKAGE_AUDIT_CLEAN", "LEAKAGE_AUDIT_FLAG"}
    assert out["checks"]["basis_z_suspicious_fillna0"] is False


def test_leakage_audit_flags_zero_filled_basis():
    df = _df()
    df["ema_cbot_basis_zscore_52w"] = 0.0  # simulate fillna(0) leak/bug
    out = run_leakage_audit(df)
    assert out["verdict"] == "LEAKAGE_AUDIT_FLAG"


def test_target_tail_nan_expected():
    out = run_leakage_audit(_df())
    assert out["checks"]["y_rel_outperform_h40_tail_nan_present"] is True

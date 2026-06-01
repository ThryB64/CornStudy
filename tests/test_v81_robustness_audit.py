"""Tests V81 — audit de robustesse (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v81_robustness_audit as v81


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 14 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_stats_helper():
    df = pd.DataFrame({"pnl": [10.0, -5.0, 20.0], "adverse": [0, 1, 0]})
    s = v81._stats(df, cost=2.0)
    assert s["n"] == 3
    assert 0 <= s["win_rate"] <= 1


def test_run_v81(tmp_path, monkeypatch):
    monkeypatch.setattr(v81, "V81_DIR", tmp_path)
    out = v81.run_v81_robustness(_synthetic_master())
    assert out["version"] == "V81-ROBUSTNESS"
    if out["verdict"] != "TOO_FEW":
        assert "by_year" in out and "cost_sensitivity" in out
        assert out["verdict"] in (
            "EDGE_STABLE_NOT_DRIVEN_BY_ONE_YEAR",
            "EDGE_SURVIVES_EX_CRISIS_SOME_YEAR_SENSITIVITY",
            "EDGE_FRAGILE_CONCENTRATED")
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"

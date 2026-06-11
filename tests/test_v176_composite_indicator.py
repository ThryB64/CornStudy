"""V176 — indicateur composite : causalité, variantes, éligibilité, live (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v176_composite_indicator as v176


def _synth(n_years: int = 9):
    idx = pd.date_range("2008-01-01", periods=252 * n_years, freq="B")
    t = np.arange(len(idx))
    rng = np.random.default_rng(1)
    bz = 2.2 * np.sin(2 * np.pi * t / 252.0) + rng.normal(0, 0.05, len(idx))
    cbot = 150 + np.cumsum(rng.normal(0.005, 0.1, len(idx)))
    ema = cbot + 60 + 18 * bz
    return pd.DataFrame({
        "ema_close": ema, "cbot_eur_t": cbot, "ema_cbot_basis_zscore_52w": bz,
        "corn_wheat_ratio": 0.8 + 0.05 * np.sin(2 * np.pi * t / 600.0),
    }, index=idx)


def test_components_causal_no_future_dependency():
    df = _synth()
    full = v176.composite_components(df)
    cut = v176.composite_components(df.iloc[:-200])
    common = cut.index
    pd.testing.assert_frame_equal(full.loc[common], cut, check_freq=False)


def test_score_range_and_tiers():
    df = _synth()
    comp = v176.composite_components(df)
    assert comp["composite_score"].between(-1, 5).all()
    assert set(comp["intensity"].unique()) <= {0, 1, 2}
    # paliers baseline respectés
    assert (comp.loc[comp["basis_z"] >= 2.0, "intensity"] == 2).all()


def test_run_composite_outputs_and_baseline_untouched(monkeypatch, tmp_path):
    monkeypatch.setattr(v176, "V176_DIR", tmp_path)
    out = v176.run_v176_composite(_synth())
    assert out["baseline_untouched"] is True
    assert set(out["variants"]) == set(v176.VARIANTS)
    base = out["variants"]["baseline_all_z1"]
    assert base["n_trades"] > 0
    # un filtre ne peut que retirer des trades par rapport à la baseline
    for name, m in out["variants"].items():
        if m.get("n_trades"):
            assert m["n_trades"] <= base["n_trades"]


def test_eligibility_requires_offseason_positive():
    bad = {"n_trades": 30, "mean_net": 5.0, "hit_rate_net": 0.7, "trades_per_year": 2.0,
           "month_coverage": 8, "offseason": {"n": 10, "mean_net": -1.0, "hit": 0.4}}
    good = {**bad, "offseason": {"n": 10, "mean_net": 2.0, "hit": 0.6}}
    assert v176._eligible(bad) is False
    assert v176._eligible(good) is True


def test_live_no_state_fallback(monkeypatch, tmp_path):
    import mais.paths as paths
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path)
    out = v176.run_v176_live()
    assert out["verdict"] == "NO_LIVE_STATE"
    assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"

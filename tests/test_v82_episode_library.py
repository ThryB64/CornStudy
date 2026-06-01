"""Tests V82 — bibliothèque d'épisodes (offline, with_network=False)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v82_episode_library as v82


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


def test_build_episodes_offline():
    ep = v82.build_episodes(_synthetic_master(), with_network=False)
    for c in ("entry_date", "path", "cbot_support", "mfe", "exit_z05_date", "probable_reason"):
        assert c in ep.columns


def test_run_v82(tmp_path, monkeypatch):
    monkeypatch.setattr(v82, "V82_DIR", tmp_path)
    monkeypatch.setattr(v82, "EPISODES_PARQUET", tmp_path / "episodes.parquet")
    monkeypatch.setattr(v82, "LIBRARY_MD", tmp_path / "lib.md")
    out = v82.run_v82_episodes(_synthetic_master(), with_network=False)
    assert out["version"] == "V82-EPISODE-LIBRARY"
    if out["verdict"] == "EPISODE_LIBRARY_BUILT":
        assert (tmp_path / "episodes.parquet").exists()
        assert (tmp_path / "lib.md").exists()
        assert out["n_episodes"] >= 15

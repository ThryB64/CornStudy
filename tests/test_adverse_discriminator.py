"""Tests VN-D3 — discriminant ADVERSE (entry-time only)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v_adverse_discriminator as ad


def _episodes(tmp_path):
    rng = np.random.default_rng(0)
    n = 42
    adverse = (rng.random(n) < 0.2).astype(int)
    ep = pd.DataFrame({
        "entry_z": rng.uniform(1.0, 2.5, n),
        "wheat_corn_z": rng.normal(0, 1, n),
        "roll_month": rng.integers(0, 2, n),
        "crisis": rng.integers(0, 2, n),
        "cbot_support": rng.choice(["LOW", "MEDIUM", "HIGH"], n),
        "adverse_risk": rng.choice(["LOW", "MEDIUM", "HIGH"], n),
        "mfe": rng.uniform(0, 40, n),  # outcome -> doit être ignoré
        "adverse": adverse,
    })
    p = tmp_path / "episodes.parquet"
    ep.to_parquet(p, index=False)
    return p


def test_run(tmp_path, monkeypatch):
    monkeypatch.setattr(ad, "EPISODES", _episodes(tmp_path))
    monkeypatch.setattr(ad, "V_DIR", tmp_path)
    out = ad.run_v_adverse_discriminator()
    assert out["verdict"] == "WATCHLIST_SMALL_N"
    assert out["n_episodes"] == 42
    # mfe (outcome) ne doit pas figurer parmi les séparateurs (entry-time only)
    assert "mfe" not in out["univariate_separation_auc"]
    assert "entry_z" in out["univariate_separation_auc"]


def test_no_episodes(tmp_path, monkeypatch):
    monkeypatch.setattr(ad, "EPISODES", tmp_path / "absent.parquet")
    assert ad.run_v_adverse_discriminator()["verdict"] == "NO_EPISODES"

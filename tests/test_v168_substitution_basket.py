"""V168 — panier de substitution élargi vs blé seul."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v168_substitution_basket as v168


def _df(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2010-01-04", periods=n, freq="B")
    corn = pd.Series(400 + np.cumsum(rng.normal(0, 2, n)), index=idx).clip(lower=100)
    return pd.DataFrame({
        "corn_close": corn,
        "wheat_close": corn * (1.4 + 0.1 * np.sin(np.arange(n) / 200)),
        "oats_close": corn * (0.8 + 0.1 * np.sin(np.arange(n) / 150)),
        "soy_close": corn * (2.5 + 0.2 * np.sin(np.arange(n) / 180)),
        "ema_cbot_basis": 30 + 10 * np.sin(np.arange(n) / 100) + rng.normal(0, 1, n),
    }, index=idx)


def test_expanding_z_is_causal_and_finite():
    df = _df()
    z = v168.expanding_ratio_z(df["wheat_close"], df["corn_close"])
    assert z.iloc[:119].isna().all()
    assert np.isfinite(z.iloc[300:]).all()


def test_basket_requires_two_components():
    df = _df().drop(columns=["oats_close", "soy_close"])
    basket = v168.build_basket(df)
    assert basket["basket_z"].isna().all()


def test_basket_is_mean_of_components():
    basket = v168.build_basket(_df())
    comp = basket[["wheat_corn_z", "oats_corn_z", "soy_corn_z"]]
    expected = comp.mean(axis=1)
    valid = basket["basket_z"].notna()
    assert np.allclose(basket.loc[valid, "basket_z"], expected[valid])


def test_run_writes_artefact_and_verdict(monkeypatch, tmp_path):
    monkeypatch.setattr(v168, "V168_DIR", tmp_path)
    monkeypatch.setattr(v168, "EPISODES", tmp_path / "missing.parquet")
    out = v168.run_v168_basket(_df())
    assert out["verdict"] in ("GO_BASKET_BEATS_WHEAT", "NO_GO_WHEAT_SUFFICIENT", "WATCHLIST_MIXED")
    assert (tmp_path / "v168_substitution_basket.json").exists()
    assert out["basket"]["weights"] == "equal_fixed_ex_ante"


def test_holdout_guard(monkeypatch, tmp_path):
    import pytest

    from mais.registry.holdout_lock import HoldoutLeakageError
    monkeypatch.setattr(v168, "V168_DIR", tmp_path)
    df = _df()
    df.index = pd.date_range("2023-06-01", periods=len(df), freq="B")
    with pytest.raises(HoldoutLeakageError):
        v168.run_v168_basket(df)

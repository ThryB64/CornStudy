"""V166 — convenience yield : chaîne bilan → CY → basis → compression."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v166_convenience_yield as v166


def _master(n=1200, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2015-01-05", periods=n, freq="B")
    bz = pd.Series(1.2 * np.sin(np.arange(n) / 60) + rng.normal(0, 0.3, n), index=idx)
    return pd.DataFrame({"ema_cbot_basis_zscore_52w": bz}, index=idx)


def _cy_correlated(df, noise=0.02, seed=1):
    rng = np.random.default_rng(seed)
    bz = df["ema_cbot_basis_zscore_52w"]
    return (0.05 * bz + rng.normal(0, noise, len(bz))).rename("cy_proxy")


def test_link_a_detects_positive_relation():
    df = _master()
    cy = _cy_correlated(df, noise=0.01)
    out = v166._link_a_cy_to_basis(cy, df["ema_cbot_basis_zscore_52w"])
    assert out["holds"] is True
    assert out["corr_full"] > 0.5


def test_link_a_rejects_noise():
    df = _master()
    rng = np.random.default_rng(7)
    cy = pd.Series(rng.normal(0, 0.05, len(df)), index=df.index, name="cy_proxy")
    out = v166._link_a_cy_to_basis(cy, df["ema_cbot_basis_zscore_52w"])
    assert out["holds"] is False


def test_link_c_split_direction():
    df = _master()
    bz = df["ema_cbot_basis_zscore_52w"]
    # CY haut exactement quand la compression future est lente -> holds True
    fwd = bz.shift(-20) - bz
    cy = fwd.fillna(0).rename("cy_proxy")
    out = v166._link_c_cy_to_compression(cy, bz)
    if out.get("verdict") != "INSUFFICIENT":
        assert out["holds"] is True


def test_run_handles_missing_curve(monkeypatch, tmp_path):
    monkeypatch.setattr(v166, "CURVE", tmp_path / "absent.parquet")
    out = v166.run_v166_convenience_yield(_master())
    assert out["verdict"] == "DATA_GATED_NO_CURVE"


def test_run_writes_artefact(monkeypatch, tmp_path):
    df = _master()
    cy = _cy_correlated(df)
    curve = pd.DataFrame({"Date": df.index, "ema_roll_yield_ann": cy.to_numpy()})
    cp = tmp_path / "curve.parquet"
    curve.to_parquet(cp, index=False)
    monkeypatch.setattr(v166, "CURVE", cp)
    monkeypatch.setattr(v166, "COMEXT", tmp_path / "absent1.parquet")
    monkeypatch.setattr(v166, "FAM", tmp_path / "absent2.parquet")
    monkeypatch.setattr(v166, "V166_DIR", tmp_path)
    out = v166.run_v166_convenience_yield(df)
    assert out["verdict"] in ("CHAIN_SUPPORTED_EXPLORATORY", "CHAIN_PARTIAL", "CHAIN_NOT_SUPPORTED")
    assert (tmp_path / "v166_convenience_yield.json").exists()

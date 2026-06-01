"""Tests V15 — réalisme indicateur short basis-haut."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v15_short_realism import (
    _sim,
    _sim_partial,
    run_censored_archaeology,
    run_drawdown_study,
    run_dynamic_cost,
    run_partial_exits,
    run_position_sizing,
    run_season_aware_exits,
    run_strict_portfolio,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(15)
    n = 2800
    idx = pd.date_range("2008-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot + 30 - 5 * bz + rng.normal(0, 2, n)
    return pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot,
        "ema_cbot_basis_zscore_52w": bz,
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
        "corn_macd_hist": rng.normal(0, 1, n),
    }, index=idx)


def test_sim_returns_tuple(synthetic_df):
    ema = synthetic_df["ema_close"].values
    cbot = synthetic_df["cbot_eur_t"].values
    bz = synthetic_df["ema_cbot_basis_zscore_52w"].values
    i = int(np.argmax(bz > 1.5))
    p, t, m = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
    assert m <= 0  # MAE négatif ou nul
    pp, tt, mm = _sim_partial(ema, cbot, bz, i, -1.0, 0.5, 0.0, 90)
    assert not np.isnan(pp)


def test_season_aware(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v15_short_realism as mod
    monkeypatch.setattr(mod, "V15_DIR", tmp_path)
    out = run_season_aware_exits(synthetic_df)
    assert out["verdict"] == "SEASON_AWARE_DONE"
    assert "season_aware" in out["results"]


def test_censored(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v15_short_realism as mod
    monkeypatch.setattr(mod, "V15_DIR", tmp_path)
    out = run_censored_archaeology(synthetic_df)
    assert out["verdict"] in {"CENSORED_ARCHAEOLOGY_DONE", "TOO_FEW"}


def test_drawdown(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v15_short_realism as mod
    monkeypatch.setattr(mod, "V15_DIR", tmp_path)
    out = run_drawdown_study(synthetic_df)
    assert out["verdict"] in {"DRAWDOWN_STUDY_DONE", "TOO_FEW"}
    if out["verdict"] == "DRAWDOWN_STUDY_DONE":
        assert out["mae_percentiles_eur_t"]["worst"] <= out["mae_percentiles_eur_t"]["p50"]


def test_partial_and_sizing_and_cost_and_portfolio(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v15_short_realism as mod
    monkeypatch.setattr(mod, "V15_DIR", tmp_path)
    assert run_partial_exits(synthetic_df)["verdict"] == "PARTIAL_EXITS_DONE"
    assert run_position_sizing(synthetic_df)["verdict"] == "POSITION_SIZING_DONE"
    assert run_dynamic_cost(synthetic_df)["verdict"] in {"DYNAMIC_COST_DONE", "TOO_FEW"}
    assert run_strict_portfolio(synthetic_df)["verdict"] == "STRICT_PORTFOLIO_DONE"

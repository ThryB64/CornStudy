"""Tests V17 — indicateur research de prime."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v17_research_indicator import (
    _tier,
    build_trades_detailed,
    compute_indicator_v17,
    generate_daily_report,
    run_failure_analysis,
    run_trade_fiches,
    run_walk_forward_final,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(17)
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
        "ema_data_availability_score": np.clip(rng.normal(0.8, 0.1, n), 0, 1),
        "curve_backwardation_proxy": rng.normal(0, 0.2, n),
    }, index=idx)


def test_tiers():
    assert _tier(0.5) == "NO_SIGNAL"
    assert _tier(1.2) == "SHORT_PREMIUM_MODERATE"
    assert _tier(1.7) == "SHORT_PREMIUM_STRONG"
    assert _tier(2.5) == "SHORT_PREMIUM_EXTREME"


def test_indicator_labels(synthetic_df):
    ind = compute_indicator_v17(synthetic_df)
    valid = {"NO_SIGNAL", "SHORT_PREMIUM_MODERATE", "SHORT_PREMIUM_STRONG",
             "SHORT_PREMIUM_EXTREME", "UNCERTAIN_DATA", "UNCERTAIN_ROLL", "UNCERTAIN_VOL"}
    assert set(ind["signal"].unique()) <= valid
    assert (ind["statut"] == "RESEARCH_ONLY_NOT_TRADING").all()


def test_data_warning_downgrades(synthetic_df):
    df = synthetic_df.copy()
    df["ema_data_availability_score"] = 0.1
    ind = compute_indicator_v17(df)
    actives = ind[ind["basis_z"] >= 1.0]
    # tout signal actif doit être rétrogradé en UNCERTAIN (data)
    assert (actives["signal"].isin(["UNCERTAIN_DATA", "UNCERTAIN_ROLL", "UNCERTAIN_VOL"])).all()


def test_trades_detailed_and_fiches(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v17_research_indicator as mod
    monkeypatch.setattr(mod, "V17_DIR", tmp_path)
    tdf = build_trades_detailed(synthetic_df)
    assert len(tdf) > 0
    assert {"entry_date", "exit_date", "pnl_z0_max90_sl20", "mae", "tier", "win"} <= set(tdf.columns)
    out = run_trade_fiches(synthetic_df)
    assert out["verdict"] == "TRADE_FICHES_DONE"
    assert (tmp_path / "trade_fiches.parquet").exists()


def test_walk_forward_and_failure(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v17_research_indicator as mod
    monkeypatch.setattr(mod, "V17_DIR", tmp_path)
    wf = run_walk_forward_final(synthetic_df)
    assert wf["verdict"] in {"WALKFORWARD_ROBUST", "WALKFORWARD_PARTIAL", "TOO_FEW"}
    fa = run_failure_analysis(synthetic_df)
    assert fa["verdict"] in {"FAILURE_ANALYSIS_DONE", "NO_TRADES"}


def test_daily_report(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v17_research_indicator as mod
    monkeypatch.setattr(mod, "V17_DIR", tmp_path)
    rep = generate_daily_report(synthetic_df)
    assert "Rapport maïs EMA/CBOT" in rep
    assert "RESEARCH_ONLY_NOT_TRADING" in rep

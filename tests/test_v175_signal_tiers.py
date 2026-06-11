"""V175 — paliers de signal (offline, série synthétique). Baseline intouchée."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v175_signal_tiers as v175


def _df(zs):
    n = len(zs)
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=n, freq="B"),
        v175.Z_COL: zs,
        "cbot_eur_t": np.linspace(150, 155, n),
        "ema_cbot_rel_strength_20d": np.zeros(n),
    })


def test_assign_tier_respects_baseline_thresholds():
    assert v175.assign_tier(0.2) == "NORMAL"
    assert v175.assign_tier(0.6) == "WATCHLIST"
    assert v175.assign_tier(0.8) == "PRE_SIGNAL"
    assert v175.assign_tier(1.2) == "BASELINE_SIGNAL"
    assert v175.assign_tier(1.7) == "STRONG"
    assert v175.assign_tier(2.5) == "EXTREME"
    assert v175.assign_tier(-1.0) == "BELOW_NORMAL"
    assert v175.assign_tier(float("nan")) == "NO_DATA"


def test_escalation_detects_escalated_and_fizzled():
    # upcross 0.75 au jour 2 (0.8), atteint 1.1 au jour 4 -> ESCALATED
    # puis retombe ; nouvel upcross au jour 30 (0.85) qui retombe sous 0.5 -> FIZZLED
    zs = [0.3, 0.6, 0.8, 0.9, 1.1, 1.2, 0.9] + [0.3] * 22 + [0.85, 0.7, 0.4, 0.3] + [0.2] * 10
    ep = v175.escalation_episodes(_df(zs), 0.75, 1.0)
    assert len(ep) == 2
    assert ep.iloc[0]["outcome"] == "ESCALATED"
    assert ep.iloc[0]["days_to_target"] == 2
    assert ep.iloc[1]["outcome"] == "FIZZLED"


def test_gap_jump_entries_excluded():
    # saute de 0.4 directement à 1.3 : pas un pré-signal (déjà au-dessus de la cible)
    zs = [0.4, 1.3, 1.4, 1.5] + [0.2] * 20
    ep = v175.escalation_episodes(_df(zs), 0.75, 1.0)
    assert len(ep) == 0


def test_run_writes_artifacts_and_keeps_baseline(tmp_path, monkeypatch):
    monkeypatch.setattr(v175, "V175_DIR", tmp_path)
    monkeypatch.setattr(v175, "TIERS_PARQUET", tmp_path / "signal_tiers.parquet")
    zs = [0.3, 0.6, 0.8, 1.1, 0.9, 0.4] * 10
    out = v175.run_v175_signal_tiers(_df(zs))
    assert out["verdict"] == "TIERS_BUILT_DESCRIPTIVE_ONLY"
    assert out["baseline_untouched"] is True
    assert (tmp_path / "signal_tiers.parquet").exists()
    assert (tmp_path / "v175_signal_tiers_results.json").exists()

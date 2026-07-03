"""Tests du backtest agricole Euronext : pas de short/buy, total vendu <= 100 %, cooldown."""
from __future__ import annotations

import pytest

from mais.indicator import euronext_indicator_backtest as ebt
from mais.indicator import euronext_indicator_features as ef


@pytest.fixture(scope="module")
def frame_cfg():
    cfg = ef.load_config()
    frame, _ = ef.build_indicator_frame(cfg)
    return frame, cfg


def test_total_sold_not_above_100pct(frame_cfg):
    frame, cfg = frame_cfg
    start = str(frame.index.min().date())
    dec, _pw, _s = ebt.run_backtest(frame, cfg, start, "calendar", 20)
    score = dec[dec["strategy"] == "score"]
    for _campaign, g in score.groupby("campaign"):
        assert g["fraction"].sum() <= 1.0 + 1e-6


def test_no_buy_no_short_in_decisions(frame_cfg):
    frame, cfg = frame_cfg
    start = str(frame.index.min().date())
    dec, _pw, _s = ebt.run_backtest(frame, cfg, start, "calendar", 20)
    assert (dec["fraction"] >= 0).all()                 # jamais de fraction négative (short)
    assert (dec["fraction"] <= 1.0 + 1e-6).all()


def test_cooldown_respected(frame_cfg):
    frame, cfg = frame_cfg
    start = str(frame.index.min().date())
    cooldown = 20
    dec, _pw, _s = ebt.run_backtest(frame, cfg, start, "calendar", cooldown)
    score = dec[(dec["strategy"] == "score")]
    # ventes "score" (hors solde final) espacées d'au moins `cooldown` séances de marché
    px = frame.index
    pos = {d.date(): i for i, d in enumerate(px)}
    for _campaign, g in score.groupby("campaign"):
        idxs = sorted(pos[d] for d in g["date"] if d in pos)
        partial = idxs[:-1] if len(idxs) > 1 else idxs   # le dernier peut être le solde
        for a, b in zip(partial, partial[1:], strict=False):
            assert (b - a) >= cooldown


def test_all_campaign_windows_run(frame_cfg):
    frame, cfg = frame_cfg
    start = str(frame.index.min().date())
    comp, _pc, _cal = ebt.run_all_campaigns(frame, cfg, start)
    assert set(comp["window"].unique()) == {"calendar", "sep_aug", "oct_sep"}

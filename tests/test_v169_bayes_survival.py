"""V169 — survie bayésienne hiérarchique (sampler + pooling + censure)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v169_bayes_survival as v169


def test_metropolis_recovers_gaussian_mean():
    def logpost(x):
        return float(-0.5 * ((x - 3.0) ** 2).sum())
    draws = np.concatenate([v169._metropolis(logpost, 1, seed=s, n_draws=6000, n_burn=2000)
                            for s in range(2)])
    assert abs(draws.mean() - 3.0) < 0.15
    assert abs(draws.std() - 1.0) < 0.15


def test_survival_recovers_known_weibull():
    rng = np.random.default_rng(0)
    # deux groupes : médianes vraies ~20 j et ~60 j, k=1.5, n=60 chacun -> bien identifiable
    t1 = 20 / np.log(2) ** (1 / 1.5) * rng.weibull(1.5, 60)
    t2 = 60 / np.log(2) ** (1 / 1.5) * rng.weibull(1.5, 60)
    t = np.clip(np.concatenate([t1, t2]), 1, None)
    censored = np.zeros(120, dtype=bool)
    groups = pd.Series(["fast"] * 60 + ["slow"] * 60)
    out = v169.fit_survival(t, censored, groups)
    med = out.pop("_median_draws")
    assert out["fast"]["median_days_posterior"]["median"] < out["slow"]["median_days_posterior"]["median"]
    assert (med["fast"] < med["slow"]).mean() > 0.9
    assert out["rhat_max"] < 1.3  # RWM en ~7 dims : mixing lent toléré, diagnostic rapporté


def test_censoring_pushes_median_up():
    rng = np.random.default_rng(1)
    t = np.clip(30 * rng.weibull(1.5, 40), 1, None)
    groups = pd.Series(["g"] * 40)
    no_cens = v169.fit_survival(t, np.zeros(40, dtype=bool), groups)
    # mêmes temps mais la moitié censurée -> la vraie durée est au moins t -> médiane postérieure plus haute
    half = np.zeros(40, dtype=bool)
    half[:20] = True
    with_cens = v169.fit_survival(t, half, groups)
    assert (with_cens["g"]["median_days_posterior"]["median"]
            > no_cens["g"]["median_days_posterior"]["median"])


def test_partial_pooling_shrinks_small_groups():
    rng = np.random.default_rng(2)
    win = np.concatenate([rng.binomial(1, 0.8, 30), np.ones(4)])  # petit groupe 4/4 wins
    groups = pd.Series(["big"] * 30 + ["tiny"] * 4)
    out = v169.fit_winrate(win, groups)
    # le postérieur du petit groupe est tiré sous 1.0 (shrinkage), avec CrI large
    assert out["tiny"]["posterior"]["median"] < 0.99
    assert out["tiny"]["ci_width"] > out["big"]["ci_width"] * 0.8


def test_run_writes_artefact(monkeypatch, tmp_path):
    monkeypatch.setattr(v169, "V169_DIR", tmp_path)
    monkeypatch.setattr(v169, "N_DRAWS", 3000)
    monkeypatch.setattr(v169, "N_BURN", 1000)
    out = v169.run_v169_bayes()
    if out["verdict"] == "NO_EPISODES":
        return
    assert out["verdict"] == "POSTERIORS_DELIVERED_DESCRIPTIVE"
    assert (tmp_path / "v169_bayes_survival.json").exists()
    assert "q1_p_extreme_faster_than_moderate" in out["predeclared_questions"]

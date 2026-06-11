"""V170 — d-séparation, back-door et classification d'effets sur DAGs connus."""
from __future__ import annotations

from mais.research import v170_causal_dag as v170

CHAIN = {"A": ["B"], "B": ["C"], "C": []}
FORK = {"U": ["X", "Y"], "X": [], "Y": []}
COLLIDER = {"X": ["C"], "Y": ["C"], "C": []}
CONFOUNDED = {"U": ["X", "Y"], "X": ["Y"], "Y": []}  # X->Y confondu par U


def test_chain_blocked_by_middle():
    assert not v170.d_separated(CHAIN, "A", "C", set())
    assert v170.d_separated(CHAIN, "A", "C", {"B"})


def test_fork_blocked_by_root():
    assert not v170.d_separated(FORK, "X", "Y", set())
    assert v170.d_separated(FORK, "X", "Y", {"U"})


def test_collider_opens_when_conditioned():
    assert v170.d_separated(COLLIDER, "X", "Y", set())
    assert not v170.d_separated(COLLIDER, "X", "Y", {"C"})


def test_backdoor_requires_confounder_observed():
    assert v170.is_valid_backdoor(CONFOUNDED, "X", "Y", {"U"})
    assert not v170.is_valid_backdoor(CONFOUNDED, "X", "Y", set())
    assert v170.find_minimal_backdoor(CONFOUNDED, "X", "Y", {"U"}) == {"U"}
    assert v170.find_minimal_backdoor(CONFOUNDED, "X", "Y", set()) is None


def test_descendants_not_allowed_in_adjustment():
    g = {"X": ["M", "Y"], "M": ["Y"], "Y": []}
    assert not v170.is_valid_backdoor(g, "X", "Y", {"M"})


def test_market_dag_key_classifications(monkeypatch, tmp_path):
    monkeypatch.setattr(v170, "V170_DIR", tmp_path)
    out = v170.run_v170_dag()
    eff = {e["effect"]: e for e in out["effects"]}
    # météo US exogène -> effet sur le basis identifiable sans ajustement
    assert eff["WEATHER_US -> BASIS"]["status"] == "IDENTIFIABLE"
    # courbe : pur enfant du bilan latent, aucun chemin causal vers le basis
    assert eff["CURVE -> BASIS"]["status"] == "NO_CAUSAL_PATH"
    # EMA -> CBOT : aucun chemin causal (covariation = fourche latente)
    assert eff["EMA -> CBOT"]["status"] == "NO_CAUSAL_PATH"
    # bilan EU latent : non identifiable directement
    assert eff["U_EU_BALANCE -> BASIS"]["status"] == "NOT_IDENTIFIABLE_LATENT_CAUSE"
    # Granger : EMA et CBOT marginalement dépendants malgré l'absence de lien causal
    assert out["why_granger_fails"]["ema_cbot_marginally_dependent"] is True
    assert (tmp_path / "v170_causal_dag.json").exists()

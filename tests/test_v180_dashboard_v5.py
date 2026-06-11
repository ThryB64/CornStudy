"""V180 — dashboard v5 : baseline vs confirmé, assemblage lecture seule."""
from __future__ import annotations

from mais.premium import dashboard_v5 as v180


def test_baseline_vs_confirmed_labels():
    assert "BASELINE z>1 ACTIVE" in v180.baseline_vs_confirmed(1.87)
    assert "CONFIRMÉ z≥1.2" in v180.baseline_vs_confirmed(1.87)
    assert "non confirmé" in v180.baseline_vs_confirmed(1.1)
    assert "sous baseline" in v180.baseline_vs_confirmed(0.4)
    assert v180.baseline_vs_confirmed(None) == "z indisponible"


def test_confirmed_threshold_is_not_baseline():
    # garde-fou : le seuil de confirmation V131 ne doit jamais devenir la baseline
    assert v180.CONFIRMED_Z == 1.2
    out = v180.baseline_vs_confirmed(1.05)
    assert "BASELINE z>1 ACTIVE" in out and "non confirmé" in out


def test_run_builds_markdown_on_real_layers(monkeypatch, tmp_path):
    monkeypatch.setattr(v180, "REPORTS_DIR", tmp_path)
    out = v180.run_v180_dashboard()
    if out["verdict"] == "NO_PREMIUM_STATE":
        return  # environnement sans head : court-circuit honnête
    assert out["verdict"] == "DASHBOARD_V5_BUILT"
    md = (tmp_path / "dashboard_v5.md").read_text(encoding="utf-8")
    for needle in ("Baseline vs confirmé", "Compression réalisée", "MATIF blé/maïs",
                   "Validation V178", "Re-runs data-gated", "RESEARCH_ONLY_NOT_TRADING"):
        assert needle in md

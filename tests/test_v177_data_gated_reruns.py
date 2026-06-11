"""V177 — gates de re-run data-gated : ACCUMULATING sous le seuil, TRIGGERED au-dessus."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v177_data_gated_reruns as v177


def test_accumulating_below_gate(monkeypatch, tmp_path):
    curve = pd.DataFrame({"price_date": pd.date_range("2026-06-01", periods=10),
                          "front_next_spread": 1.0})
    cp = tmp_path / "curve.parquet"
    curve.to_parquet(cp, index=False)
    monkeypatch.setattr(v177, "CURVE_OFFICIAL", cp)
    out = v177.check_v166_official()
    assert out["status"] == "ACCUMULATING"
    assert out["n"] == 10


def test_triggered_at_gate_runs_frozen_protocol(monkeypatch, tmp_path):
    n = 200
    dates = pd.date_range("2026-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    bz = pd.Series(np.sin(np.arange(n) / 30) + rng.normal(0, 0.1, n), index=dates)
    curve = pd.DataFrame({"price_date": dates,
                          "front_next_spread": (2 * bz + rng.normal(0, 0.1, n)).to_numpy()})
    cp = tmp_path / "curve.parquet"
    curve.to_parquet(cp, index=False)
    monkeypatch.setattr(v177, "CURVE_OFFICIAL", cp)
    monkeypatch.setattr(v177, "V177_DIR", tmp_path)
    journal = pd.DataFrame({"price_date": dates, "basis_z_used": bz.to_numpy()})
    monkeypatch.setattr(v177, "_official_frame",
                        lambda: journal.set_index(pd.to_datetime(journal["price_date"])))
    out = v177.check_v166_official()
    assert out["status"] == "TRIGGERED"
    assert out["verdict"] == "CY_OFFICIAL_SUPPORTS_PREMIUM"
    assert (tmp_path / "v166_official_rerun.json").exists()


def test_missing_files_do_not_crash(monkeypatch, tmp_path):
    for attr in ("CURVE_OFFICIAL", "MATIF_HISTORY", "WEATHER_REVISIONS"):
        monkeypatch.setattr(v177, attr, tmp_path / "absent.parquet")
    monkeypatch.setattr(v177, "V177_DIR", tmp_path)
    monkeypatch.setattr(v177, "STATUS_PATH", tmp_path / "status.json")
    out = v177.run_v177_data_gated()
    assert all(g["status"] == "ACCUMULATING" for g in out["gates"])
    assert (tmp_path / "status.json").exists()


def test_status_artifact_lists_three_gates(monkeypatch, tmp_path):
    monkeypatch.setattr(v177, "V177_DIR", tmp_path)
    monkeypatch.setattr(v177, "STATUS_PATH", tmp_path / "status.json")
    out = v177.run_v177_data_gated()
    assert {g["rerun"] for g in out["gates"]} == {"V166_OFFICIAL", "V168_MATIF", "V155_SUMMER"}

"""V181 — maintenance hebdo : checks individuels et verdict global."""
from __future__ import annotations

import json

import pandas as pd

from mais.ops import weekly_maintenance as v181


def test_ci_check_fail_when_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(v181, "DAILY_LATEST", tmp_path / "absent.json")
    assert v181.check_ci()["status"] == "FAIL"


def test_ci_check_fail_when_old(monkeypatch, tmp_path):
    p = tmp_path / "latest.json"
    p.write_text(json.dumps({"as_of": "2026-01-05", "result": "OK"}), encoding="utf-8")
    monkeypatch.setattr(v181, "DAILY_LATEST", p)
    assert v181.check_ci()["status"] == "FAIL"


def test_head_check_ok_when_fresh(monkeypatch, tmp_path):
    p = tmp_path / "head.json"
    p.write_text(json.dumps({"as_of": pd.Timestamp.now().strftime("%Y-%m-%d"),
                             "consistency": {"verdict": "LIVE_SIGNAL_CONSISTENT"}}),
                 encoding="utf-8")
    monkeypatch.setattr(v181, "HEAD", p)
    assert v181.check_head()["status"] == "OK"


def test_accumulation_warn_when_stale(monkeypatch, tmp_path):
    old = pd.DataFrame({"price_date": pd.date_range("2026-01-01", periods=5)})
    for name in ("j", "c", "m"):
        old.to_parquet(tmp_path / f"{name}.parquet", index=False)
    pd.DataFrame({"valid_date": pd.date_range("2026-01-01", periods=5)}).to_parquet(
        tmp_path / "w.parquet", index=False)
    monkeypatch.setattr(v181, "JOURNAL", tmp_path / "j.parquet")
    monkeypatch.setattr(v181, "CURVE", tmp_path / "c.parquet")
    monkeypatch.setattr(v181, "MATIF", tmp_path / "m.parquet")
    monkeypatch.setattr(v181, "WEATHER", tmp_path / "w.parquet")
    checks = v181.check_accumulations()
    assert all(c["status"] == "WARN" for c in checks)


def test_global_verdict_broken_on_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(v181, "V181_DIR", tmp_path)
    monkeypatch.setattr(v181, "WEEKLY_DIR", tmp_path / "weekly")
    monkeypatch.setattr(v181, "DAILY_LATEST", tmp_path / "absent.json")
    out = v181.run_v181_weekly(run_tests=False)
    assert out["verdict"] in ("BROKEN", "DEGRADED")
    assert (tmp_path / "weekly_maintenance.json").exists()
    assert (tmp_path / "weekly" / "maintenance_latest.md").exists()

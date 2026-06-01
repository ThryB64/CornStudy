from __future__ import annotations

import json

import pandas as pd
import pytest

from mais.research.proxy_audit import (
    assert_no_proxy_in_benchmark,
    compare_proxy_vs_real,
    run_proxy_audit,
)


def test_compare_proxy_vs_real_metrics() -> None:
    dates = pd.bdate_range("2026-01-01", periods=5)
    proxy = pd.DataFrame({"Date": dates, "ema_close": [190, 191, 192, 193, 194]})
    real = pd.DataFrame({"date": dates, "price": [200, 201, 202, 203, 204]})

    report = compare_proxy_vs_real(proxy, real)

    assert report["n_overlap"] == 5
    assert report["correlation"] == pytest.approx(1.0)
    assert report["mae_eur_t"] == 10.0
    assert report["spread_proxy_minus_real_mean_eur_t"] == -10.0
    assert report["proxy_allowed_in_benchmark"] is False


def test_compare_proxy_vs_real_no_overlap() -> None:
    proxy = pd.DataFrame({"Date": ["2026-01-01"], "ema_close": [190.0]})
    real = pd.DataFrame({"date": ["2026-02-01"], "price": [200.0]})

    report = compare_proxy_vs_real(proxy, real)

    assert report["n_overlap"] == 0
    assert report["verdict"] == "INCONCLU"


def test_assert_no_proxy_in_benchmark_rejects_proxy_rows() -> None:
    features = pd.DataFrame({"Date": pd.bdate_range("2026-01-01", periods=2), "ema_is_proxy": [False, True]})

    with pytest.raises(ValueError):
        assert_no_proxy_in_benchmark(features)


def test_assert_no_proxy_in_benchmark_allows_real_rows() -> None:
    features = pd.DataFrame({"Date": pd.bdate_range("2026-01-01", periods=2), "ema_is_proxy": [False, False]})

    assert_no_proxy_in_benchmark(features)


def test_run_proxy_audit_writes_report(tmp_path) -> None:
    dates = pd.bdate_range("2026-01-01", periods=3)
    proxy_path = tmp_path / "proxy.csv"
    real_path = tmp_path / "real.parquet"
    output_path = tmp_path / "proxy_vs_real_ema_report.json"
    pd.DataFrame({"Date": dates, "ema_close": [190, 191, 192]}).to_csv(proxy_path, index=False)
    pd.DataFrame({"date": dates, "price": [200, 201, 202]}).to_parquet(real_path, index=False)

    report = run_proxy_audit(proxy_path=proxy_path, real_path=real_path, output_path=output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["n_overlap"] == 3
    assert payload["verdict"] == "PROXY_FORBIDDEN"

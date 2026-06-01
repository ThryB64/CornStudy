from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research.ema_cbot_relationship import (
    BUSHEL_TO_TONNE,
    build_relationship_frame,
    lead_lag_correlations,
    render_markdown,
    run_ema_cbot_relationship_study,
)


def _fixture(n: int = 180) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2020-01-01", periods=n)
    cbot_cents = 500 + np.linspace(0, 50, n) + np.sin(np.arange(n) / 5) * 8
    eurusd = np.full(n, 1.10)
    cbot_eur_t = (cbot_cents / 100.0) / eurusd * BUSHEL_TO_TONNE
    ema_raw = cbot_eur_t + 12 + np.sin(np.arange(n) / 9)
    ema_adjusted = ema_raw.copy()
    front_raw = pd.DataFrame({"date": dates, "price": ema_raw})
    front_adjusted = pd.DataFrame({"date": dates, "adjusted_price": ema_adjusted})
    cbot = pd.DataFrame({"Date": dates, "corn_close": cbot_cents})
    fx = pd.DataFrame({"Date": dates, "eurusd_rate": eurusd})
    return front_raw, front_adjusted, cbot, fx


def test_build_relationship_frame_converts_cbot_to_eur_t(tmp_path) -> None:
    front_raw, front_adjusted, cbot, fx = _fixture()
    paths = {}
    for name, frame in {
        "front_raw": front_raw,
        "front_adjusted": front_adjusted,
        "cbot": cbot,
        "fx": fx,
    }.items():
        path = tmp_path / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path

    frame = build_relationship_frame(
        ema_front_raw_path=paths["front_raw"],
        ema_front_adjusted_path=paths["front_adjusted"],
        cbot_path=paths["cbot"],
        eurusd_path=paths["fx"],
    )

    expected = (cbot["corn_close"].iloc[0] / 100.0) / fx["eurusd_rate"].iloc[0] * BUSHEL_TO_TONNE
    assert frame["cbot_eur_t"].iloc[0] == expected
    assert frame["ema_cbot_basis"].notna().all()
    assert {"ema_logret_1d", "cbot_eur_logret_1d"}.issubset(frame.columns)


def test_lead_lag_identifies_ema_lead_candidate() -> None:
    dates = pd.bdate_range("2024-01-01", periods=120)
    signal = np.sin(np.arange(120) / 4)
    frame = pd.DataFrame(
        {
            "Date": dates,
            "ema_logret_1d": signal,
            "cbot_eur_logret_1d": pd.Series(signal).shift(2).to_numpy(),
        }
    )

    report = lead_lag_correlations(frame, max_lag=5)

    assert report["best_ema_leads"]["lag"] == 2
    assert report["best_ema_leads"]["corr_ema_t_cbot_t_plus_lag"] > 0.99


def test_run_relationship_study_writes_outputs(tmp_path) -> None:
    front_raw, front_adjusted, cbot, fx = _fixture()
    front_raw_path = tmp_path / "front_raw.parquet"
    front_adjusted_path = tmp_path / "front_adjusted.parquet"
    cbot_path = tmp_path / "cbot.parquet"
    fx_path = tmp_path / "fx.csv"
    output_json = tmp_path / "relationship.json"
    output_md = tmp_path / "relationship.md"
    front_raw.to_parquet(front_raw_path, index=False)
    front_adjusted.to_parquet(front_adjusted_path, index=False)
    cbot.to_parquet(cbot_path, index=False)
    fx.to_csv(fx_path, index=False)

    payload = run_ema_cbot_relationship_study(
        ema_front_raw_path=front_raw_path,
        ema_front_adjusted_path=front_adjusted_path,
        cbot_path=cbot_path,
        eurusd_path=fx_path,
        output_json_path=output_json,
        output_markdown_path=output_md,
        max_lag=4,
        granger_maxlag=2,
    )

    assert output_json.exists()
    assert output_md.exists()
    assert payload["price_relationship"]["n_price_overlap"] == len(front_raw)
    assert payload["lead_lag"]["max_lag"] == 4
    assert payload["interpretation"]["lead_lag_verdict"] in {
        "mostly_contemporaneous",
        "ema_leads_cbot_candidate",
        "cbot_leads_ema_candidate",
    }


def test_render_markdown_contains_core_sections() -> None:
    payload = {
        "source_quality_note": "note",
        "n_rows": 2,
        "date_start": "2024-01-01",
        "date_end": "2024-01-02",
        "price_relationship": {
            "n_price_overlap": 2,
            "price_corr": 0.9,
            "return_corr_1d": 0.8,
            "basis_mean_eur_t": 10,
            "basis_std_eur_t": 2,
            "basis_min_eur_t": 5,
            "basis_max_eur_t": 15,
        },
        "lead_lag": {
            "definition": "definition",
            "contemporaneous": {"lag": 0, "meaning": "same day", "corr_ema_t_cbot_t_plus_lag": 0.8, "n": 2},
            "best_ema_leads": None,
            "best_cbot_leads": None,
        },
        "rolling_relationship": {
            "window": 60,
            "mean_corr": 0.5,
            "median_corr": 0.5,
            "min_corr": 0.1,
            "max_corr": 0.9,
            "share_positive": 1.0,
        },
        "granger": {"status": "SKIPPED", "reason": "optional"},
        "interpretation": {
            "lead_lag_verdict": "mostly_contemporaneous",
            "caution": "careful",
            "next_step": "basis",
        },
    }

    markdown = render_markdown(payload)

    assert "EMA / CBOT Relationship" in markdown
    assert "Lead-Lag" in markdown
    assert "Granger" in markdown

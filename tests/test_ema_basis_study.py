from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research.ema_basis_study import (
    analyze_basis_regimes,
    classify_basis_regime,
    decide_basis_signal,
    render_markdown,
    run_ema_basis_study,
)


def _relationship_frame(n: int = 180) -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=n)
    cbot = pd.Series(200.0 + np.linspace(0, 10, n))
    basis = pd.Series(np.zeros(n), dtype=float)
    basis.iloc[20:60] = 30.0
    basis.iloc[60:100] = -30.0
    for idx in range(20, 59):
        basis.iloc[idx + 20 if idx + 20 < n else idx] = max(basis.iloc[idx] - 12, basis.iloc[idx + 20 if idx + 20 < n else idx])
    ema = cbot + basis
    frame = pd.DataFrame(
        {
            "Date": dates,
            "ema_price_adjusted": ema,
            "cbot_eur_t": cbot,
            "ema_cbot_basis": basis,
            "basis_z": 0.0,
        }
    )
    frame.loc[20:40, "basis_z"] = 2.5
    frame.loc[60:80, "basis_z"] = -2.5
    return frame


def test_classify_basis_regime() -> None:
    z = pd.Series([2.1, -2.2, 0.5, 1.5, np.nan])
    regimes = classify_basis_regime(z, high_threshold=2.0, low_threshold=-2.0)

    assert regimes.tolist() == ["high", "low", "neutral", "other", "missing"]


def test_analyze_basis_regimes_reports_reversion_rates() -> None:
    frame = _relationship_frame()

    table = analyze_basis_regimes(frame, horizons=(20,))

    high = table[table["regime"].eq("high")].iloc[0]
    low = table[table["regime"].eq("low")].iloc[0]
    assert high["n"] > 0
    assert low["n"] > 0
    assert "basis_reversion_rate" in table.columns


def test_decide_basis_signal_partial_or_confirmed() -> None:
    table = pd.DataFrame(
        {
            "regime": ["high", "low"],
            "horizon": [20, 20],
            "n": [25, 25],
            "basis_change_mean": [-5.0, 4.0],
            "basis_reversion_rate": [0.7, 0.65],
        }
    )

    decision = decide_basis_signal(table)

    assert decision["verdict"] == "BASIS_MEAN_REVERSION_CONFIRMED"


def test_run_ema_basis_study_writes_outputs(tmp_path) -> None:
    dates = pd.bdate_range("2020-01-01", periods=320)
    cbot_cents = 500 + np.linspace(0, 10, len(dates))
    eurusd = np.full(len(dates), 1.10)
    cbot_eur = (cbot_cents / 100.0) / eurusd * 39.3679
    basis = np.sin(np.arange(len(dates)) / 15) * 20
    front_raw = pd.DataFrame({"date": dates, "price": cbot_eur + basis})
    front_adjusted = pd.DataFrame({"date": dates, "adjusted_price": cbot_eur + basis})
    cbot = pd.DataFrame({"Date": dates, "corn_close": cbot_cents})
    fx = pd.DataFrame({"Date": dates, "eurusd_rate": eurusd})
    paths = {}
    for name, frame in {
        "front_raw": front_raw,
        "front_adjusted": front_adjusted,
        "cbot": cbot,
    }.items():
        path = tmp_path / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path
    fx_path = tmp_path / "fx.csv"
    fx.to_csv(fx_path, index=False)

    payload = run_ema_basis_study(
        ema_front_raw_path=paths["front_raw"],
        ema_front_adjusted_path=paths["front_adjusted"],
        cbot_path=paths["cbot"],
        eurusd_path=fx_path,
        output_json_path=tmp_path / "basis.json",
        output_markdown_path=tmp_path / "basis.md",
        horizons=(20,),
        z_window=60,
    )

    assert (tmp_path / "basis.json").exists()
    assert (tmp_path / "basis.md").exists()
    assert payload["basis_distribution"]["basis_n"] == len(dates)
    assert payload["decision"]["verdict"] in {
        "BASIS_MEAN_REVERSION_CONFIRMED",
        "BASIS_MEAN_REVERSION_PARTIAL",
        "BASIS_INCONCLUSIVE",
    }


def test_render_markdown_contains_decision() -> None:
    payload = {
        "source_quality_note": "note",
        "n_rows": 1,
        "date_start": "2024-01-01",
        "date_end": "2024-01-02",
        "z_window": 260,
        "basis_distribution": {
            "basis_mean": 1,
            "basis_std": 2,
            "basis_p05": -1,
            "basis_p50": 0,
            "basis_p95": 3,
            "basis_z_high_share": 0.1,
            "basis_z_low_share": 0.2,
        },
        "regime_results": [
            {
                "regime": "high",
                "horizon": 20,
                "n": 10,
                "basis_change_mean": -2,
                "basis_reversion_rate": 0.6,
                "relative_ema_minus_cbot_mean": -0.01,
            }
        ],
        "decision": {"verdict": "BASIS_INCONCLUSIVE", "interpretation": "text"},
    }

    markdown = render_markdown(payload)

    assert "EMA Basis Study" in markdown
    assert "BASIS_INCONCLUSIVE" in markdown

import pandas as pd
import pytest

from mais.clean.market_refresh import refresh_database


def _write_raw(raw_dir, source, prefix, dates, base=100.0):
    d = raw_dir / source
    d.mkdir(parents=True)
    df = pd.DataFrame({
        "Date": dates,
        f"{prefix}_open": [base + i for i in range(len(dates))],
        f"{prefix}_high": [base + 1 + i for i in range(len(dates))],
        f"{prefix}_low": [base - 1 + i for i in range(len(dates))],
        f"{prefix}_close": [base + 0.5 + i for i in range(len(dates))],
        f"{prefix}_volume": [1000 + i for i in range(len(dates))],
    })
    df.to_csv(d / f"{source}.csv", index=False)


def test_refresh_appends_only_new_dates(tmp_path):
    interim = tmp_path / "interim"
    raw = tmp_path / "raw"
    interim.mkdir()
    old_dates = pd.bdate_range("2025-01-01", periods=5)
    db = pd.DataFrame({"Date": old_dates, "corn_close": [400.0] * 5,
                       "legacy_only_col": [1.0] * 5})
    db.to_parquet(interim / "database.parquet")

    all_dates = pd.bdate_range("2025-01-01", periods=8)
    _write_raw(raw, "cbot_corn", "corn", all_dates, base=410)
    _write_raw(raw, "cbot_wheat", "wheat", all_dates, base=500)

    res = refresh_database(interim_dir=interim, raw_dir=raw)
    assert res["appended"] == 3

    out = pd.read_parquet(interim / "database.parquet")
    assert len(out) == 8
    assert out["Date"].is_monotonic_increasing
    # anciennes lignes intactes (pas de réécriture du legacy)
    assert (out["corn_close"].iloc[:5] == 400.0).all()
    # nouvelles lignes remplies depuis le raw, colonnes legacy en NaN
    assert out["corn_close"].iloc[5:].notna().all()
    assert out["wheat_close"].iloc[5:].notna().all()
    assert out["legacy_only_col"].iloc[5:].isna().all()

    res2 = refresh_database(interim_dir=interim, raw_dir=raw)
    assert res2["appended"] == 0


def test_refresh_requires_corn(tmp_path):
    interim = tmp_path / "interim"
    raw = tmp_path / "raw"
    interim.mkdir()
    raw.mkdir()
    db = pd.DataFrame({"Date": pd.bdate_range("2025-01-01", periods=3),
                       "corn_close": [400.0] * 3})
    db.to_parquet(interim / "database.parquet")
    with pytest.raises(RuntimeError):
        refresh_database(interim_dir=interim, raw_dir=raw)

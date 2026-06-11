"""V174 — règle FX BCE horodatée : parsing offline + math de reconstruction + audit réel."""
from __future__ import annotations

import pytest

from mais.audit.data_truth import BU_PER_TONNE
from mais.audit.fx_bce import reconstruct_cbot_eur_t, run_fx_bce_audit
from mais.collect.ecb_fx_collector import ARCHIVE_PATH, parse_ecb_csv
from mais.research import v27_official_forward as v27

_CSV = (
    "KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE\n"
    "EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-06-09,1.1550\n"
    "EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-06-10,1.1539\n"
)


def test_parse_ecb_csv():
    df = parse_ecb_csv(_CSV)
    assert list(df.columns) == ["Date", "eurusd_ecb"]
    assert len(df) == 2
    assert df.iloc[1]["eurusd_ecb"] == 1.1539


def test_reconstruct_cbot_eur_t_roundtrip():
    # 419 cents/bu à 1.15 USD/EUR : (4.19 USD/bu * 39.3679 bu/t) / 1.15
    expected = 4.19 * BU_PER_TONNE / 1.15
    assert abs(reconstruct_cbot_eur_t(419.0, 1.15) - expected) < 1e-9


@pytest.mark.skipif(not v27.JOURNAL_JSONL.exists() or not ARCHIVE_PATH.exists(),
                    reason="journal ou archive BCE absents")
def test_fx_bce_audit_bounded():
    r = run_fx_bce_audit()
    assert r["verdict"] in ("PASS", "WARN", "SKIP")
    if r["verdict"] == "PASS":
        assert r["max_abs_dev_ecb_vs_journal_eur_t"] <= 1.0

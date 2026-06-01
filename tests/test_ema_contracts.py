from __future__ import annotations

import pytest

from mais.collect.euronext_endpoint_probe import parse_contract_label


def test_contract_month_code_mapping() -> None:
    assert parse_contract_label("Jun 2026") == "EMA_M2026"
    assert parse_contract_label("Aug 2026") == "EMA_Q2026"
    assert parse_contract_label("Nov 2026") == "EMA_X2026"
    assert parse_contract_label("Mar 2027") == "EMA_H2027"
    with pytest.raises(ValueError):
        parse_contract_label("Jan 2027")

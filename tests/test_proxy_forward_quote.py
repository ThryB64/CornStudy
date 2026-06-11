"""V144-DATA — quote proxy forward du front officiel (offline, fetch injecté)."""
from __future__ import annotations

from mais.collect import proxy_forward_quote as pfq


def test_official_contract_to_symbol():
    assert pfq.official_contract_to_symbol("EMA_Q2026") == "XBQ26"
    assert pfq.official_contract_to_symbol("EMA_X2026") == "XBX26"
    assert pfq.official_contract_to_symbol("nimporte") is None


def test_parse_quote():
    html = '... "lastPrice":"216.50" ... "previousSettlement":"217.00" ...'
    q = pfq.parse_quote(html)
    assert q["last_price"] == 216.5
    assert q["previous_settlement"] == 217.0
    assert pfq.parse_quote("rien")["last_price"] is None


def test_append_dedup(tmp_path, monkeypatch):
    monkeypatch.setattr(pfq, "JOURNAL_JSONL", tmp_path / "j.jsonl")
    monkeypatch.setattr(pfq, "JOURNAL_PARQUET", tmp_path / "j.parquet")
    fetch = lambda sym: (200, '"lastPrice":"216.50"')  # noqa: E731
    r1 = pfq.append_proxy_quote("EMA_Q2026", "2026-06-10", fetch=fetch)
    assert r1["verdict"] == "PROXY_QUOTE_LOGGED"
    r2 = pfq.append_proxy_quote("EMA_Q2026", "2026-06-10", fetch=fetch)
    assert r2["verdict"] == "ALREADY_LOGGED"
    assert len(pfq.load_proxy_quotes()) == 1

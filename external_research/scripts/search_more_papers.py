from __future__ import annotations

import argparse
import time
from typing import Any

import requests

from _common import SOURCES_DIR, write_yaml

QUERIES = [
    "corn futures price forecasting machine learning",
    "CBOT corn futures WASDE announcement impact",
    "USDA WASDE corn futures volatility",
    "corn futures weather premium",
    "corn futures GARCH volatility",
    "agricultural futures price forecasting deep learning",
    "grain futures price forecasting LSTM",
    "agricultural commodity price forecasting explainable machine learning",
    "CFTC COT agricultural futures forecasting",
    "corn ethanol DDG price relationship",
    "futures curve corn nearby deferred price discovery",
    "corn basis futures spot price transmission",
    "weather shocks corn futures prices",
    "crop condition reports corn futures",
    "agricultural commodity price foundation models",
]

KEEP_TERMS = [
    "corn",
    "maize",
    "futures",
    "wasde",
    "usda",
    "weather",
    "volatility",
    "basis",
    "commodity",
    "forecast",
    "forecasting",
    "machine learning",
    "deep learning",
]


def relevance_score(title: str, abstract: str, query: str) -> float:
    text = f"{title} {abstract} {query}".lower()
    hits = sum(1 for term in KEEP_TERMS if term in text)
    return round(hits / max(len(KEEP_TERMS), 1), 3)


def semantic_scholar(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    response = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,venue,abstract,url,externalIds",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    rows = []
    for item in response.json().get("data", []):
        title = item.get("title") or ""
        abstract = item.get("abstract") or ""
        authors = ", ".join(author.get("name", "") for author in item.get("authors", []))
        external = item.get("externalIds") or {}
        rows.append(
            {
                "title": title,
                "authors": authors,
                "year": item.get("year", ""),
                "venue": item.get("venue", ""),
                "doi": external.get("DOI", ""),
                "url": item.get("url", ""),
                "abstract_if_available": abstract,
                "query": query,
                "relevance_score": relevance_score(title, abstract, query),
                "reason_to_keep": "Semantic Scholar search result",
                "status": "discovered",
            }
        )
    return rows


def crossref(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    response = requests.get(
        "https://api.crossref.org/works",
        params={"query.bibliographic": query, "rows": limit},
        timeout=timeout,
    )
    response.raise_for_status()
    rows = []
    for item in response.json().get("message", {}).get("items", []):
        title = " ".join(item.get("title") or [])[:500]
        authors = ", ".join(
            " ".join(filter(None, [author.get("given", ""), author.get("family", "")]))
            for author in item.get("author", [])
        )
        year_parts = item.get("published-print") or item.get("published-online") or {}
        year = ""
        if year_parts.get("date-parts"):
            year = year_parts["date-parts"][0][0]
        abstract = item.get("abstract", "") or ""
        rows.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "venue": " ".join(item.get("container-title") or []),
                "doi": item.get("DOI", ""),
                "url": item.get("URL", ""),
                "abstract_if_available": abstract,
                "query": query,
                "relevance_score": relevance_score(title, abstract, query),
                "reason_to_keep": "Crossref search result",
                "status": "discovered",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Search papers for external research.")
    parser.add_argument("--limit-per-query", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=1.5)
    parser.add_argument(
        "--provider",
        choices=["semantic_scholar", "crossref"],
        default="semantic_scholar",
    )
    args = parser.parse_args()

    rows_by_key: dict[str, dict[str, Any]] = {}
    provider = semantic_scholar if args.provider == "semantic_scholar" else crossref
    for query in QUERIES:
        try:
            rows = provider(query, args.limit_per_query, args.timeout)
        except requests.RequestException as exc:
            if args.provider == "semantic_scholar":
                try:
                    rows = crossref(query, args.limit_per_query, args.timeout)
                    for row in rows:
                        row["reason_to_keep"] = "Crossref fallback after Semantic Scholar failure"
                except requests.RequestException:
                    rows = []
            else:
                rows = []
            if not rows:
                rows = [
                    {
                        "title": "",
                        "authors": "",
                        "year": "",
                        "venue": "",
                        "doi": "",
                        "url": "",
                        "abstract_if_available": "",
                        "query": query,
                        "relevance_score": 0,
                        "reason_to_keep": f"Search failed: {exc}",
                        "status": "search_failed",
                    }
                ]
        for row in rows:
            key = str(row.get("doi") or row.get("url") or row.get("title") or row.get("query"))
            previous = rows_by_key.get(key)
            if previous is None or float(row["relevance_score"]) > float(previous["relevance_score"]):
                rows_by_key[key] = row
        time.sleep(args.sleep)

    output = sorted(
        rows_by_key.values(),
        key=lambda row: float(row.get("relevance_score") or 0),
        reverse=True,
    )
    write_yaml(SOURCES_DIR / "discovered_papers.yml", output)
    print(f"Wrote {len(output)} paper records")


if __name__ == "__main__":
    main()

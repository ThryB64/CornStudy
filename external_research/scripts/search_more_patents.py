from __future__ import annotations

import argparse
import json
import re
import time
from typing import Any
from urllib.parse import quote

import requests

from _common import SOURCES_DIR, write_yaml

QUERIES = [
    "agricultural commodity price prediction machine learning patent",
    "crop price forecasting satellite patent",
    "futures price prediction commodity machine learning patent",
    "agricultural futures risk management patent",
    "basis futures agricultural patent",
    "grain storage drying weather price patent",
    "crop yield price prediction patent",
]

KEEP_TERMS = {
    "agric",
    "basis",
    "commodity",
    "commodities",
    "corn",
    "crop",
    "farm",
    "field",
    "futures",
    "grain",
    "maize",
    "price",
    "satellite",
    "storage",
    "weather",
    "yield",
}


def google_patents_search_url(query: str) -> str:
    return f"https://patents.google.com/?q=({quote(query)})"


def patent_relevance(title: str, assignee: str) -> tuple[float, str]:
    text = f"{title} {assignee}".lower()
    hits = sorted(term for term in KEEP_TERMS if term in text)
    score = round(len(hits) / 6.0, 3)
    reason = "Keyword match: " + ", ".join(hits[:8]) if hits else "No strong keyword match"
    return score, reason


def parse_patent_results(payload: dict[str, Any], query: str) -> list[dict[str, Any]]:
    results = []
    clusters = payload.get("results", {}).get("cluster", [])
    for cluster in clusters:
        for result in cluster.get("result", []):
            patent = result.get("patent", {})
            publication = patent.get("publication_number", "")
            title = re.sub(r"\s+", " ", patent.get("title", "")).strip()
            assignee = patent.get("assignee", "")
            score, reason = patent_relevance(title, assignee)
            if score <= 0:
                continue
            result_query = query
            results.append(
                {
                    "patent_id": publication,
                    "title": title,
                    "authors_or_owner": assignee,
                    "year": str(patent.get("publication_date", ""))[:4],
                    "url": f"https://patents.google.com/patent/{publication}" if publication else "",
                    "query": result_query,
                    "relevance_score": score,
                    "reason_to_keep": reason,
                    "status": "discovered",
                }
            )
    return results


def search_query(query: str, timeout: int) -> list[dict[str, Any]]:
    xhr_url = "https://patents.google.com/xhr/query"
    response = requests.get(
        xhr_url,
        params={"url": f"q=({query})"},
        timeout=timeout,
        headers={"User-Agent": "external-research-catalog/1.0"},
    )
    response.raise_for_status()
    text = response.text
    if text.startswith(")]}'"):
        text = text.split("\n", 1)[1]
    payload = json.loads(text)
    return parse_patent_results(payload, query)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search patent candidates.")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=1.5)
    parser.add_argument("--max-results-per-query", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.167)
    args = parser.parse_args()

    rows_by_id: dict[str, dict[str, Any]] = {}
    for query in QUERIES:
        try:
            rows = [
                row
                for row in search_query(query, args.timeout)
                if float(row.get("relevance_score") or 0) >= args.min_score
            ][: args.max_results_per_query]
        except (requests.RequestException, json.JSONDecodeError, KeyError) as exc:
            rows = [
                {
                    "patent_id": "",
                    "title": f"Manual Google Patents search - {query}",
                    "authors_or_owner": "",
                    "year": "",
                    "url": google_patents_search_url(query),
                    "query": query,
                    "relevance_score": 0,
                    "reason_to_keep": f"Automated search failed: {exc}",
                    "status": "manual_search_required",
                }
            ]
        if not rows:
            rows = [
                {
                    "patent_id": "",
                    "title": f"Manual Google Patents search - {query}",
                    "authors_or_owner": "",
                    "year": "",
                    "url": google_patents_search_url(query),
                    "query": query,
                    "relevance_score": 0,
                    "reason_to_keep": "No relevant automated Google Patents result; manual review URL kept",
                    "status": "manual_search_required",
                }
            ]
        for row in rows:
            key = str(row.get("patent_id") or row.get("url") or row.get("query"))
            rows_by_id[key] = row
        time.sleep(args.sleep)

    rows = sorted(
        rows_by_id.values(),
        key=lambda row: float(row.get("relevance_score") or 0),
        reverse=True,
    )
    write_yaml(SOURCES_DIR / "discovered_patents.yml", rows)
    print(f"Wrote {len(rows)} patent records")


if __name__ == "__main__":
    main()

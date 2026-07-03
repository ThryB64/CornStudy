from __future__ import annotations

import argparse
import time
from typing import Any

import requests

from _common import SOURCES_DIR, load_yaml, write_yaml

QUERIES = [
    "corn futures prediction machine learning",
    "CBOT corn futures machine learning",
    "agricultural commodity price prediction futures",
    "grain futures forecasting",
    "WASDE corn futures",
    "CFTC COT futures python",
    "commodity futures backtesting python",
    "futures trend following python",
    "roll futures contracts python",
    "crop price prediction weather machine learning",
    "grain market forecasting",
    "corn soybean wheat futures forecasting",
]

KEEP_KEYWORDS = {
    "corn",
    "maize",
    "grain",
    "commodity",
    "commodities",
    "futures",
    "forecast",
    "forecasting",
    "prediction",
    "weather",
    "wasde",
    "cot",
    "cftc",
    "roll",
    "backtest",
}


def relevance_score(repo: dict[str, Any]) -> float:
    text = " ".join(
        [
            str(repo.get("full_name", "")),
            str(repo.get("description", "")),
        ]
    ).lower()
    keyword_hits = sum(1 for keyword in KEEP_KEYWORDS if keyword in text)
    stars = min(float(repo.get("stargazers_count") or 0), 500.0) / 500.0
    recent_bonus = 0.2 if str(repo.get("updated_at", "")) >= "2022" else 0.0
    return round(keyword_hits / 8.0 + stars + recent_bonus, 3)


def reason_to_keep(repo: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(repo.get("full_name", "")),
            str(repo.get("description", "")),
        ]
    ).lower()
    hits = [keyword for keyword in sorted(KEEP_KEYWORDS) if keyword in text]
    if hits:
        return "Keyword match: " + ", ".join(hits[:6])
    return "Potential adjacent futures or agriculture repository"


def search_query(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    response = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
        headers={"Accept": "application/vnd.github+json"},
        timeout=timeout,
    )
    response.raise_for_status()
    return list(response.json().get("items", []))


def main() -> None:
    parser = argparse.ArgumentParser(description="Search public GitHub repositories.")
    parser.add_argument("--limit-per-query", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=2.0)
    parser.add_argument("--min-score", type=float, default=0.45)
    args = parser.parse_args()

    seed_repos = {
        str(row.get("repo") or row.get("title") or "").lower()
        for row in load_yaml(SOURCES_DIR / "seed_repositories.yml")
    }
    rows_by_repo: dict[str, dict[str, Any]] = {}
    for query in QUERIES:
        try:
            items = search_query(query, args.limit_per_query, args.timeout)
        except requests.RequestException as exc:
            rows_by_repo[f"SEARCH_FAILED::{query}"] = {
                "repo": "",
                "url": "",
                "description": "",
                "stars": "",
                "forks": "",
                "language": "",
                "last_update": "",
                "query": query,
                "relevance_score": 0,
                "reason_to_keep": f"Search failed: {exc}",
                "status": "search_failed",
            }
            continue

        for repo in items:
            name = str(repo.get("full_name", ""))
            if not name:
                continue
            if name.lower() in seed_repos:
                continue
            score = relevance_score(repo)
            if score < args.min_score:
                continue
            row = {
                "repo": name,
                "url": repo.get("html_url", ""),
                "description": repo.get("description", "") or "",
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", "") or "",
                "last_update": repo.get("updated_at", ""),
                "query": query,
                "relevance_score": score,
                "reason_to_keep": reason_to_keep(repo),
                "status": "discovered",
            }
            previous = rows_by_repo.get(name)
            if previous is None or score > float(previous["relevance_score"]):
                rows_by_repo[name] = row
        time.sleep(args.sleep)

    rows = sorted(
        rows_by_repo.values(),
        key=lambda row: (float(row["relevance_score"]), int(row.get("stars") or 0)),
        reverse=True,
    )
    write_yaml(SOURCES_DIR / "discovered_repositories.yml", rows)
    print(f"Wrote {len(rows)} repository records")


if __name__ == "__main__":
    main()

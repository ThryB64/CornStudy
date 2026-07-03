from __future__ import annotations

from pathlib import Path
from typing import Any

from _common import MATRICES_DIR, ROOT, SOURCES_DIR, load_yaml, source_id, write_csv


def card_path(source_type: str, sid: str) -> str:
    folder = {
        "repository": "repositories",
        "paper": "papers",
        "patent": "patents",
    }[source_type]
    path = ROOT / "source_cards" / folder / f"{sid}.md"
    return str(path.relative_to(ROOT)) if path.exists() else ""


def row_for_source(row: dict[str, Any], source_type: str, origin: str, index: int) -> dict[str, Any]:
    sid = source_id(row, f"{source_type}-{index}")
    name = row.get("title") or row.get("repo") or row.get("patent_id") or ""
    return {
        "id": row.get("id") or sid,
        "source_type": source_type,
        "source_name": name,
        "priority": row.get("priority", ""),
        "status": row.get("status", ""),
        "origin": origin,
        "url": row.get("url_if_known") or row.get("url") or "",
        "topic": row.get("topic", ""),
        "source_query": row.get("source_query") or row.get("query") or "",
        "card_path": card_path(source_type, sid),
        "summary_path": "",
        "notes": "",
    }


def load_group(seed_file: str, discovered_file: str) -> list[tuple[dict[str, Any], str]]:
    rows = [(row, "seed") for row in load_yaml(SOURCES_DIR / seed_file)]
    rows += [(row, "discovered") for row in load_yaml(SOURCES_DIR / discovered_file)]
    return rows


def main() -> None:
    rows: list[dict[str, Any]] = []
    groups = [
        ("repository", "seed_repositories.yml", "discovered_repositories.yml"),
        ("paper", "seed_papers.yml", "discovered_papers.yml"),
        ("patent", "seed_patents.yml", "discovered_patents.yml"),
    ]
    for source_type, seed_file, discovered_file in groups:
        for index, (row, origin) in enumerate(load_group(seed_file, discovered_file), start=1):
            rows.append(row_for_source(row, source_type, origin, index))

    write_csv(
        MATRICES_DIR / "source_inventory_catalog.csv",
        rows,
        [
            "id",
            "source_type",
            "source_name",
            "priority",
            "status",
            "origin",
            "url",
            "topic",
            "source_query",
            "card_path",
            "summary_path",
            "notes",
        ],
    )
    print(f"Wrote {len(rows)} source records")


if __name__ == "__main__":
    main()

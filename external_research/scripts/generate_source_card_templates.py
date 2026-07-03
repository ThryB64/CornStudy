from __future__ import annotations

from pathlib import Path
from typing import Any

from _common import ROOT, SOURCES_DIR, load_yaml, source_id


def frontmatter(row: dict[str, Any], source_type: str) -> str:
    return "\n".join(
        [
            "---",
            f"id: {row.get('id', '')}",
            f"source_type: {source_type}",
            f"title: {str(row.get('title') or row.get('repo') or '').replace(':', ' -')}",
            f"priority: {row.get('priority', '')}",
            f"status: {row.get('status', '')}",
            "---",
            "",
        ]
    )


def repo_template(row: dict[str, Any]) -> str:
    name = row.get("repo") or row.get("title") or ""
    url = row.get("url_if_known") or row.get("url") or ""
    return frontmatter(row, "repository") + f"""# {name}

## Nom

{name}

## URL

{url}

## Licence

TODO

## Dernier commit si disponible

TODO

## Objectif

TODO

## Donnees utilisees

TODO

## Features

TODO

## Cible predite

TODO

## Horizon

TODO

## Modeles

TODO

## Methode d'evaluation

TODO

## Metriques

TODO

## Points forts

TODO

## Faiblesses

TODO

## Risques de fuite de donnees

TODO

## Code reutilisable

TODO

## Idees testables pour notre etude

TODO

## Priorite

{row.get("priority", "TODO")}

## Conclusion

TODO
"""


def paper_template(row: dict[str, Any], source_type: str) -> str:
    title = row.get("title") or row.get("patent_id") or ""
    reference = row.get("authors_or_owner") or row.get("authors") or ""
    year = row.get("year") or ""
    url = row.get("url_if_known") or row.get("url") or ""
    return frontmatter(row, source_type) + f"""# {title}

## Reference

{reference} ({year}). {title}

URL: {url}

## Type

{source_type}

## Resume

TODO

## Donnees

TODO

## Methode

TODO

## Resultats importants

TODO

## Idee economique

TODO

## Idee de feature

TODO

## Idee de modele

TODO

## Idee d'evaluation

TODO

## Limites

TODO

## Risque de fuite

TODO

## Experience EXT possible

TODO

## Priorite

{row.get("priority", "TODO")}
"""


def write_if_missing(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    created = 0

    repo_rows = load_yaml(SOURCES_DIR / "seed_repositories.yml")
    repo_rows += load_yaml(SOURCES_DIR / "discovered_repositories.yml")
    for index, row in enumerate(repo_rows, start=1):
        sid = source_id(row, f"repo-{index}")
        created += write_if_missing(
            ROOT / "source_cards" / "repositories" / f"{sid}.md",
            repo_template(row),
        )

    paper_rows = load_yaml(SOURCES_DIR / "seed_papers.yml")
    paper_rows += load_yaml(SOURCES_DIR / "discovered_papers.yml")
    for index, row in enumerate(paper_rows, start=1):
        sid = source_id(row, f"paper-{index}")
        created += write_if_missing(
            ROOT / "source_cards" / "papers" / f"{sid}.md",
            paper_template(row, "paper"),
        )

    patent_rows = load_yaml(SOURCES_DIR / "seed_patents.yml")
    patent_rows += load_yaml(SOURCES_DIR / "discovered_patents.yml")
    for index, row in enumerate(patent_rows, start=1):
        sid = source_id(row, f"patent-{index}")
        created += write_if_missing(
            ROOT / "source_cards" / "patents" / f"{sid}.md",
            paper_template(row, "patent"),
        )

    print(f"Created {created} source-card templates")


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
from pathlib import Path

from _common import MATRICES_DIR, ROOT, utc_now, write_csv

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "data",
    "artefacts",
    "artifacts",
    "logs",
    "csv",
    "notebooks",
}

LANG_EXTENSIONS = {
    ".py": "python",
    ".r": "r",
    ".R": "r",
    ".ipynb": "notebook",
    ".jl": "julia",
    ".js": "javascript",
    ".ts": "typescript",
    ".cpp": "cpp",
    ".c": "c",
    ".java": "java",
}

DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".parquet",
    ".pkl",
    ".pickle",
    ".xlsx",
    ".xls",
    ".feather",
}


def root_file_names(path: Path) -> set[str]:
    return {child.name.lower() for child in path.iterdir() if child.is_file()}


def scan_repo(path: Path) -> dict[str, object]:
    names = root_file_names(path)
    languages: set[str] = set()
    notebooks_count = 0
    python_files_count = 0
    r_files_count = 0
    data_files_count = 0
    skipped_dirs: set[str] = set()

    for current, dirs, files in os.walk(path):
        kept_dirs = []
        for dirname in dirs:
            if dirname in SKIP_DIRS:
                skipped_dirs.add(dirname)
            else:
                kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in files:
            suffix = Path(filename).suffix
            language = LANG_EXTENSIONS.get(suffix)
            if language:
                languages.add(language)
            if suffix == ".ipynb":
                notebooks_count += 1
            elif suffix == ".py":
                python_files_count += 1
            elif suffix.lower() == ".r":
                r_files_count += 1
            elif suffix.lower() in DATA_EXTENSIONS:
                data_files_count += 1

    repo = path.name.replace("__", "/")
    notes = ""
    if skipped_dirs:
        notes = "Skipped dirs: " + ", ".join(sorted(skipped_dirs))

    return {
        "id": repo.lower().replace("/", "-"),
        "repo": repo,
        "local_path": path.relative_to(ROOT),
        "has_readme": any(name.startswith("readme") for name in names),
        "has_license": any(name.startswith("license") for name in names),
        "languages_detected": ";".join(sorted(languages)),
        "notebooks_count": notebooks_count,
        "python_files_count": python_files_count,
        "r_files_count": r_files_count,
        "data_files_count": data_files_count,
        "last_scan_date": utc_now(),
        "notes": notes,
    }


def main() -> None:
    repos_dir = ROOT / "github_repos"
    rows = []
    if repos_dir.exists():
        for child in sorted(repos_dir.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                rows.append(scan_repo(child))

    write_csv(
        MATRICES_DIR / "source_inventory.csv",
        rows,
        [
            "id",
            "repo",
            "local_path",
            "has_readme",
            "has_license",
            "languages_detected",
            "notebooks_count",
            "python_files_count",
            "r_files_count",
            "data_files_count",
            "last_scan_date",
            "notes",
        ],
    )
    print(f"Scanned {len(rows)} repositories")


if __name__ == "__main__":
    main()

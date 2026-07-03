from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from _common import ROOT, SOURCES_DIR, load_yaml, utc_now, write_csv


def repo_url(row: dict[str, object]) -> str:
    known = str(row.get("url_if_known") or "").strip()
    if known:
        return known
    repo = str(row.get("repo") or row.get("title") or "").strip()
    return f"https://github.com/{repo}"


def repo_folder_name(row: dict[str, object]) -> str:
    repo = str(row.get("repo") or row.get("title") or row.get("id")).strip()
    return repo.replace("/", "__").replace(" ", "_")


def clone_repo(row: dict[str, object], target: Path, timeout: int) -> tuple[str, str]:
    if target.exists():
        return "skipped_existing", "local folder already exists"
    git = shutil.which("git")
    if git is None:
        return "failed", "git executable not found"

    url = repo_url(row)
    command = [git, "clone", "--depth", "1", url, str(target)]
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "failed", f"clone timed out after {timeout}s"

    if proc.returncode == 0:
        return "cloned", "ok"
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    message = (proc.stderr or proc.stdout or "unknown clone error").strip()
    return "failed", message[:500]


def main() -> None:
    parser = argparse.ArgumentParser(description="Clone seed GitHub repositories.")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    repos = load_yaml(SOURCES_DIR / "seed_repositories.yml")
    output_dir = ROOT / "github_repos"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for row in repos:
        target = output_dir / repo_folder_name(row)
        status, message = clone_repo(row, target, args.timeout)
        rows.append(
            {
                "id": row.get("id", ""),
                "repo": row.get("repo") or row.get("title", ""),
                "url": repo_url(row),
                "local_path": target.relative_to(ROOT),
                "status": status,
                "message": message,
                "timestamp_utc": utc_now(),
            }
        )

    write_csv(
        SOURCES_DIR / "repo_clone_log.csv",
        rows,
        [
            "id",
            "repo",
            "url",
            "local_path",
            "status",
            "message",
            "timestamp_utc",
        ],
    )
    print(f"Wrote {SOURCES_DIR / 'repo_clone_log.csv'}")


if __name__ == "__main__":
    main()

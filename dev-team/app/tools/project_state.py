"""High-level project status reader for dev-team agents."""
from __future__ import annotations

import json
import subprocess

from config import Config

_config = Config.from_env()


def get_project_status() -> str:
    """Get a comprehensive summary of the current project state.

    Reads open issues, recent PRs, recent commits, directory structure,
    and checks for Next.js project indicators.

    Returns:
        JSON string with project status snapshot.
    """
    status: dict = {
        "open_issues": [],
        "open_prs": [],
        "recent_commits": [],
        "repo_structure": [],
        "has_package_json": False,
        "has_nextjs": False,
    }

    result = subprocess.run(
        ["gh", "issue", "list", "--state", "open",
         "--json", "number,title,labels", "--limit", "30",
         "-R", _config.product_repo],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        try:
            status["open_issues"] = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    result = subprocess.run(
        ["gh", "pr", "list", "--state", "open",
         "--json", "number,title,headRefName,author", "--limit", "10",
         "-R", _config.product_repo],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        try:
            status["open_prs"] = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    result = subprocess.run(
        ["git", "log", "--oneline", "-15"],
        cwd=str(_config.product_repo_dir),
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        status["recent_commits"] = result.stdout.strip().split("\n")

    result = subprocess.run(
        ["find", ".", "-maxdepth", "2",
         "-not", "-path", "./.git/*", "-not", "-path", "./node_modules/*",
         "-not", "-name", ".*"],
        cwd=str(_config.product_repo_dir),
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        status["repo_structure"] = [
            f for f in result.stdout.strip().split("\n") if f and f != "."
        ]

    pkg_path = _config.product_repo_dir / "package.json"
    status["has_package_json"] = pkg_path.exists()

    for name in ("next.config.js", "next.config.mjs", "next.config.ts"):
        if (_config.product_repo_dir / name).exists():
            status["has_nextjs"] = True
            break

    return json.dumps(status)

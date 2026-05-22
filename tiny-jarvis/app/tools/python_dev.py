"""Python development helper tools for tiny-jarvis agents."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from config import Config

_config = Config.from_env()
_CWD = str(_config.product_repo_dir)
_TIMEOUT = 120

_KEEP_ON_CLEAN = {".git", ".gitignore", ".env", ".env.local", "docs", "work_plan.json"}


def clean_for_init() -> str:
    """Remove all files and directories in the product repo EXCEPT .git, .gitignore, docs/, and .env files.

    Call this BEFORE initializing a new Python project to ensure a clean directory.
    The docs/ folder is preserved so product specs and progress logs survive.

    Returns:
        JSON string with list of removed items.
    """
    repo = Path(_CWD)
    removed = []
    errors = []

    for item in repo.iterdir():
        if item.name in _KEEP_ON_CLEAN:
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            removed.append(item.name)
        except Exception as e:
            errors.append({"name": item.name, "error": str(e)})

    return json.dumps({
        "success": True,
        "removed": removed,
        "removed_count": len(removed),
        "preserved": list(_KEEP_ON_CLEAN),
        "errors": errors,
    })


def uv_init() -> str:
    """Initialize a new Python project with uv in the product repository.

    Creates pyproject.toml and basic project structure using `uv init`.

    Returns:
        JSON string with init output.
    """
    try:
        result = subprocess.run(
            ["uv", "init", "--no-readme"],
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": output,
            "stderr": result.stderr.strip()[:1000],
        })
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "uv not found. Ensure uv is installed."})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "uv init timed out after 30s"})


def uv_add(packages: str) -> str:
    """Add Python package dependencies using uv.

    Args:
        packages: Space-separated package names (e.g., 'telethon apscheduler pydantic').

    Returns:
        JSON string with install output.
    """
    if not packages.strip():
        return json.dumps({"success": False, "error": "No packages specified"})
    try:
        result = subprocess.run(
            ["uv", "add"] + packages.split(),
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip()
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": output,
            "stderr": result.stderr.strip()[:1000],
        })
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "uv not found."})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "uv add timed out after 120s"})


def uv_add_dev(packages: str) -> str:
    """Add Python dev dependencies using uv.

    Args:
        packages: Space-separated package names (e.g., 'pytest pytest-asyncio').

    Returns:
        JSON string with install output.
    """
    if not packages.strip():
        return json.dumps({"success": False, "error": "No packages specified"})
    try:
        result = subprocess.run(
            ["uv", "add", "--group", "dev"] + packages.split(),
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip()
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": output,
            "stderr": result.stderr.strip()[:1000],
        })
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "uv not found."})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "uv add --dev timed out after 120s"})


def uv_run(command: str) -> str:
    """Run a command through uv (e.g., 'python main.py', 'pytest tests/ -v').

    Args:
        command: The command to run via `uv run` (e.g., 'pytest tests/ -v').

    Returns:
        JSON string with command output and exit code.
    """
    _blocked = {"rm -rf", "sudo", "shutdown", "reboot", "mkfs", "dd if="}
    for b in _blocked:
        if b in command:
            return json.dumps({"success": False, "error": f"Blocked: contains '{b}'"})
    try:
        result = subprocess.run(
            ["uv", "run"] + command.split(),
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        output = result.stdout.strip()
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": output,
            "stderr": result.stderr.strip()[:2000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": f"uv run timed out after {_TIMEOUT}s"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "uv not found."})


def run_pytest(args: str = "tests/ -v") -> str:
    """Run pytest in the product repository via uv.

    Args:
        args: Arguments to pass to pytest (default: 'tests/ -v').

    Returns:
        JSON string with test results.
    """
    try:
        result = subprocess.run(
            ["uv", "run", "pytest"] + args.split(),
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        output = result.stdout.strip()
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": output,
            "stderr": result.stderr.strip()[:2000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": f"pytest timed out after {_TIMEOUT}s"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "uv not found."})


def run_ruff(fix: bool = False) -> str:
    """Run ruff linter/formatter on the product repository.

    Args:
        fix: If True, auto-fix fixable issues. Default False (check only).

    Returns:
        JSON string with lint results.
    """
    args = ["uv", "run", "ruff", "check", "."]
    if fix:
        args.append("--fix")
    try:
        result = subprocess.run(
            args,
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": output,
            "stderr": result.stderr.strip()[:1000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "ruff timed out after 60s"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "uv not found."})

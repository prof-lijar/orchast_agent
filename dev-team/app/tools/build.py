"""Generic build/test/lint tools that auto-detect the project stack."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.tools.skills import run_skill
from config import Config

_config = Config.get()
_REPO_DIR = _config.product_repo_dir


def _detect_stack() -> str | None:
    if (_REPO_DIR / "package.json").exists():
        return "node"
    if (_REPO_DIR / "pyproject.toml").exists() or (_REPO_DIR / "requirements.txt").exists():
        return "python"
    if (_REPO_DIR / "go.mod").exists():
        return "go"
    if (_REPO_DIR / "Cargo.toml").exists():
        return "rust"
    return None


def run_build() -> str:
    """Auto-detect the project stack and run the build command.

    Detects the project type (Node.js, Python, Go, Rust) from project files
    and runs the appropriate build command via the skill system.

    Returns:
        JSON string with build output.
    """
    stack = _detect_stack()
    if not stack:
        return json.dumps({"success": False, "error": "Cannot detect project stack. No package.json, pyproject.toml, go.mod, or Cargo.toml found."})
    return run_skill(stack, "build")


def run_tests(args: str = "") -> str:
    """Auto-detect the project stack and run tests.

    Args:
        args: Optional arguments to pass to the test runner (e.g., test file path, test name pattern).

    Returns:
        JSON string with test output.
    """
    stack = _detect_stack()
    if not stack:
        return json.dumps({"success": False, "error": "Cannot detect project stack."})
    return run_skill(stack, "test", args)


def run_lint(args: str = "") -> str:
    """Auto-detect the project stack and run the linter.

    Args:
        args: Optional arguments to pass to the linter (e.g., specific file path).

    Returns:
        JSON string with lint output.
    """
    stack = _detect_stack()
    if not stack:
        return json.dumps({"success": False, "error": "Cannot detect project stack."})
    return run_skill(stack, "lint", args)

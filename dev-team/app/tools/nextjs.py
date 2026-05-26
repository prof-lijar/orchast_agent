"""Next.js development helper tools for dev-team agents."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from config import Config

_config = Config.from_env()
_CWD = str(_config.product_repo_dir)
_TIMEOUT = 120

_BLOCKED_SCRIPTS = {"eject"}

_KEEP_ON_CLEAN = {".git", ".gitignore", ".env", ".env.local", "docs", "work_plan.json"}


def clean_for_init() -> str:
    """Remove all files and directories in the product repo EXCEPT .git, .gitignore, docs/, and .env files.

    Call this BEFORE running create-next-app to ensure a clean directory.
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


def npm_install(packages: str = "") -> str:
    """Install npm dependencies in the product repository.

    Args:
        packages: Space-separated package names to install (e.g., 'axios zustand').
                  If empty, runs 'npm install' to install all from package.json.

    Returns:
        JSON string with install output.
    """
    if packages:
        args = ["npm", "install"] + packages.split()
    else:
        args = ["npm", "install"]
    try:
        result = subprocess.run(
            args,
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout.strip()
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": output,
            "stderr": result.stderr.strip()[:1000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "npm install timed out after 300s"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "npm not found. Ensure Node.js is installed."})


def npm_run(script: str) -> str:
    """Run an npm script defined in package.json.

    Args:
        script: The npm script to run (e.g., 'build', 'lint', 'test', 'dev').

    Returns:
        JSON string with script output and exit code.
    """
    if script in _BLOCKED_SCRIPTS:
        return json.dumps({"success": False, "error": f"Script '{script}' is blocked for safety."})
    try:
        result = subprocess.run(
            ["npm", "run", script],
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
        return json.dumps({"success": False, "error": f"npm run {script} timed out after {_TIMEOUT}s"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "npm not found."})


def npx_command(command: str) -> str:
    """Run an npx command in the product repository.

    Args:
        command: The npx command to run (e.g., 'create-next-app@latest . --ts --tailwind --app --eslint --src-dir').

    Returns:
        JSON string with command output.
    """
    _blocked = {"rm", "sudo", "shutdown", "reboot", "mkfs", "dd ", ":(){ "}
    for b in _blocked:
        if b in command:
            return json.dumps({"success": False, "error": f"Blocked: contains '{b}'"})
    try:
        result = subprocess.run(
            ["npx", "--yes"] + command.split(),
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout.strip()
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": output,
            "stderr": result.stderr.strip()[:2000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "npx command timed out after 300s"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "npx not found."})

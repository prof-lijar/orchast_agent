"""Vercel CLI wrapper tools for dev-team agents."""
from __future__ import annotations

import json
import subprocess

from config import Config

_config = Config.from_env()
_CWD = str(_config.product_repo_dir)
_TIMEOUT = 120


def _run_vercel(args: list[str], timeout: int = _TIMEOUT) -> dict:
    try:
        result = subprocess.run(
            ["vercel"] + args + ["--yes"],
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip()}
        return {"success": True, "output": result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Vercel command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": "vercel CLI not found. Install with: npm i -g vercel"}


def vercel_deploy(production: bool = False) -> str:
    """Deploy the project to Vercel.

    Args:
        production: If True, deploy to production. If False, creates a preview deployment.

    Returns:
        JSON string with deployment URL and status.
    """
    args = ["deploy"]
    if production:
        args.append("--prod")
    result = _run_vercel(args, timeout=300)
    return json.dumps(result)


def vercel_list_deployments(limit: int = 5) -> str:
    """List recent Vercel deployments.

    Args:
        limit: Maximum number of deployments to show. Default 5.

    Returns:
        JSON string with deployment list.
    """
    result = _run_vercel(["ls", "--limit", str(limit)])
    return json.dumps(result)


def vercel_logs(deployment_url: str) -> str:
    """Get logs for a specific Vercel deployment.

    Args:
        deployment_url: The deployment URL to get logs for.

    Returns:
        JSON string with deployment logs.
    """
    result = _run_vercel(["logs", deployment_url, "--limit", "100"], timeout=30)
    return json.dumps(result)


def vercel_env_set(key: str, value: str, environment: str = "production") -> str:
    """Set an environment variable in Vercel.

    Args:
        key: Environment variable name.
        value: Environment variable value.
        environment: Target environment: 'production', 'preview', or 'development'.

    Returns:
        JSON string indicating success or failure.
    """
    valid_envs = ("production", "preview", "development")
    if environment not in valid_envs:
        return json.dumps({"success": False, "error": f"Invalid environment. Use one of: {valid_envs}"})
    try:
        result = subprocess.run(
            ["vercel", "env", "add", key, environment],
            input=value,
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return json.dumps({"success": False, "error": result.stderr.strip()})
        return json.dumps({"success": True, "key": key, "environment": environment})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def vercel_env_list() -> str:
    """List all environment variables configured in Vercel.

    Returns:
        JSON string with environment variable names and their target environments.
    """
    result = _run_vercel(["env", "ls"], timeout=30)
    return json.dumps(result)

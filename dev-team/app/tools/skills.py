"""Dynamic skill system for dev-team agents."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from config import Config

_config = Config.get()
_SKILLS_DIR = _config.skills_dir
_REPO_DIR = str(_config.product_repo_dir)
_TIMEOUT = 120

_BLOCKED_PATTERNS = {
    "rm -rf /", "rm -rf ~", "sudo ", "shutdown", "reboot",
    "mkfs", "dd if=", ":(){ ", "fork", "> /dev/sd",
}


def _load_registry() -> dict:
    registry_path = _SKILLS_DIR / "registry.json"
    if not registry_path.exists():
        return {"skills": []}
    with open(registry_path) as f:
        return json.load(f)


def _save_registry(registry: dict) -> None:
    registry_path = _SKILLS_DIR / "registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)


def _check_binary(name: str) -> bool:
    return shutil.which(name) is not None


def _parse_skill_header(script_path: Path) -> dict:
    meta = {}
    with open(script_path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("#"):
                break
            for key in ("SKILL_NAME", "SKILL_DESC", "SKILL_VERSION", "SKILL_REQUIRES", "SKILL_COMMANDS"):
                if key + "=" in line:
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    meta[key] = val
    return meta


def list_skills() -> str:
    """List all available skills with their status.

    Shows each skill's name, description, available commands, and whether
    its required binaries are installed on this system.

    Returns:
        JSON string with list of skills and their availability.
    """
    registry = _load_registry()
    skills = []
    for skill in registry.get("skills", []):
        requires = skill.get("requires", [])
        installed = all(_check_binary(b) for b in requires) if requires else True
        missing = [b for b in requires if not _check_binary(b)]
        skills.append({
            "name": skill["name"],
            "description": skill.get("description", ""),
            "installed": installed,
            "missing_binaries": missing,
            "commands": [c["name"] for c in skill.get("commands", [])],
        })
    return json.dumps({"success": True, "skills": skills, "count": len(skills)})


def skill_info(skill_name: str) -> str:
    """Get detailed information about a specific skill.

    Args:
        skill_name: The name of the skill (e.g., 'node', 'python', 'docker').

    Returns:
        JSON string with skill details including all commands and their arguments.
    """
    registry = _load_registry()
    for skill in registry.get("skills", []):
        if skill["name"] == skill_name:
            requires = skill.get("requires", [])
            installed = all(_check_binary(b) for b in requires) if requires else True
            missing = [b for b in requires if not _check_binary(b)]
            return json.dumps({
                "success": True,
                "skill": {
                    **skill,
                    "installed": installed,
                    "missing_binaries": missing,
                },
            })
    return json.dumps({"success": False, "error": f"Skill '{skill_name}' not found. Use list_skills() to see available skills."})


def run_skill(skill: str, command: str, args: str = "") -> str:
    """Execute a command from a skill script.

    This runs a specific command provided by a skill. For example:
    - run_skill("node", "build") runs npm build
    - run_skill("python", "test", "tests/") runs pytest on tests/
    - run_skill("docker", "build", "myapp:latest .") builds a Docker image

    Args:
        skill: The skill name (e.g., 'node', 'python', 'go', 'rust', 'docker', 'deploy').
        command: The command to run within the skill (e.g., 'build', 'test', 'lint', 'install').
        args: Space-separated arguments to pass to the command.

    Returns:
        JSON string with stdout, stderr, and return code.
    """
    registry = _load_registry()
    skill_entry = None
    for s in registry.get("skills", []):
        if s["name"] == skill:
            skill_entry = s
            break
    if not skill_entry:
        return json.dumps({"success": False, "error": f"Skill '{skill}' not found. Use list_skills() to see available skills."})

    valid_commands = [c["name"] for c in skill_entry.get("commands", [])]
    if command not in valid_commands:
        return json.dumps({"success": False, "error": f"Command '{command}' not found in skill '{skill}'. Available: {valid_commands}"})

    script_path = _SKILLS_DIR / skill_entry["file"]
    if not script_path.exists():
        return json.dumps({"success": False, "error": f"Skill script not found: {script_path}"})

    full_command = f"{command} {args}".strip()
    for blocked in _BLOCKED_PATTERNS:
        if blocked in full_command or blocked in args:
            return json.dumps({"success": False, "error": f"Blocked: command contains '{blocked}'"})

    env = os.environ.copy()
    env["SKILL_REPO_DIR"] = _REPO_DIR

    cmd = ["bash", str(script_path), command]
    if args:
        cmd.extend(args.split())

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            cwd=_REPO_DIR,
        )
        stdout = result.stdout.strip()
        if len(stdout) > 5000:
            stdout = stdout[:5000] + "\n... (truncated)"
        stderr = result.stderr.strip()
        if len(stderr) > 2000:
            stderr = stderr[:2000] + "\n... (truncated)"
        return json.dumps({
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": f"Skill command timed out after {_TIMEOUT}s"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def install_skill(url: str) -> str:
    """Install a skill from a trusted external URL.

    Downloads a .sh skill script from a whitelisted URL, validates its metadata
    header, and registers it in the skill registry.

    Only URLs from sources listed in TRUSTED_SKILL_SOURCES are allowed.
    To add a trusted source, set the TRUSTED_SKILL_SOURCES environment variable
    to a comma-separated list of URL prefixes.

    Args:
        url: The URL to download the skill script from.

    Returns:
        JSON string indicating success or failure.
    """
    trusted = _config.trusted_skill_sources
    if not trusted:
        return json.dumps({
            "success": False,
            "error": "No trusted skill sources configured. Pass --trusted-sources to set allowed URL prefixes.",
        })

    is_trusted = any(url.startswith(source) for source in trusted)
    if not is_trusted:
        return json.dumps({
            "success": False,
            "error": f"URL '{url}' is not from a trusted source. Trusted sources: {trusted}. Add the source to TRUSTED_SKILL_SOURCES to allow it.",
        })

    if not url.endswith(".sh"):
        return json.dumps({"success": False, "error": "Skill scripts must be .sh files."})

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DevTeam/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        return json.dumps({"success": False, "error": f"Failed to download: {e}"})

    for blocked in _BLOCKED_PATTERNS:
        if blocked in content:
            return json.dumps({"success": False, "error": f"Skill script contains blocked pattern: '{blocked}'. Rejected for safety."})

    if "#!/" not in content.split("\n")[0]:
        return json.dumps({"success": False, "error": "Skill script must start with a shebang line (#!/usr/bin/env bash)."})

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    meta = _parse_skill_header(tmp_path)
    if "SKILL_NAME" not in meta:
        tmp_path.unlink()
        return json.dumps({"success": False, "error": "Skill script missing SKILL_NAME in header. Required metadata: SKILL_NAME, SKILL_DESC, SKILL_COMMANDS."})

    skill_name = meta["SKILL_NAME"]
    dest = _SKILLS_DIR / f"{skill_name}.sh"
    shutil.move(str(tmp_path), str(dest))
    dest.chmod(0o755)

    commands_str = meta.get("SKILL_COMMANDS", "")
    commands = [{"name": c.strip(), "description": "", "args": ""} for c in commands_str.split(",") if c.strip()]

    registry = _load_registry()
    registry["skills"] = [s for s in registry.get("skills", []) if s["name"] != skill_name]
    registry["skills"].append({
        "name": skill_name,
        "file": f"{skill_name}.sh",
        "description": meta.get("SKILL_DESC", ""),
        "requires": [r.strip() for r in meta.get("SKILL_REQUIRES", "").split(",") if r.strip()],
        "commands": commands,
    })
    _save_registry(registry)

    return json.dumps({
        "success": True,
        "skill": skill_name,
        "description": meta.get("SKILL_DESC", ""),
        "commands": [c["name"] for c in commands],
        "installed_to": str(dest),
    })

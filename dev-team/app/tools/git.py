"""Git operations for dev-team agents."""
from __future__ import annotations

import json
import subprocess

from config import Config

_config = Config.from_env()
_CWD = str(_config.product_repo_dir)
_TIMEOUT = 60


def _run_git(args: list[str], timeout: int = _TIMEOUT) -> dict:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=_CWD,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip()}
        return {"success": True, "output": result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Git operation timed out after {timeout}s"}


def git_commit_and_push(message: str, files: str = ".") -> str:
    """Stage files, commit, and push to the remote repository.

    Args:
        message: Commit message. Prefix with your role tag, e.g. '[Frontend] Add hero section'.
        files: Space-separated file paths to stage, or '.' for all changes.

    Returns:
        JSON string with commit hash and push status.
    """
    add_result = _run_git(["add"] + files.split())
    if not add_result["success"]:
        return json.dumps(add_result)

    commit_result = _run_git(["commit", "-m", message])
    if not commit_result["success"]:
        if "nothing to commit" in commit_result.get("error", ""):
            return json.dumps({"success": True, "message": "Nothing to commit"})
        return json.dumps(commit_result)

    push_result = _run_git(["push", "origin", "HEAD"], timeout=120)

    return json.dumps({
        "success": True,
        "committed": True,
        "pushed": push_result["success"],
        "message": commit_result.get("output", ""),
        "push_error": push_result.get("error", "") if not push_result["success"] else "",
    })


def git_create_branch(branch_name: str) -> str:
    """Create a new git branch and switch to it.

    Args:
        branch_name: The branch name. Use format: role/description (e.g., 'frontend/add-hero').

    Returns:
        JSON string indicating success or failure.
    """
    result = _run_git(["checkout", "-b", branch_name])
    return json.dumps(result)


def git_switch_branch(branch_name: str) -> str:
    """Switch to an existing git branch.

    Args:
        branch_name: The branch to switch to (e.g., 'main', 'frontend/add-hero').

    Returns:
        JSON string indicating success or failure.
    """
    result = _run_git(["checkout", branch_name])
    return json.dumps(result)


def git_current_branch() -> str:
    """Get the name of the current git branch.

    Returns:
        JSON string with the current branch name.
    """
    result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    return json.dumps(result)


def git_pull() -> str:
    """Pull latest changes from the remote repository.

    Returns:
        JSON string indicating success or failure.
    """
    result = _run_git(["pull", "origin", _config.default_branch], timeout=120)
    return json.dumps(result)


def git_delete_branch(branch_name: str) -> str:
    """Delete a local git branch that has been merged.

    Args:
        branch_name: The branch to delete. Cannot delete main or the current branch.

    Returns:
        JSON string indicating success or failure.
    """
    if branch_name in ("master", "main"):
        return json.dumps({"success": False, "error": "Cannot delete the main branch"})
    current = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if current.get("output") == branch_name:
        return json.dumps({"success": False, "error": "Cannot delete the branch you are currently on"})
    result = _run_git(["branch", "-d", branch_name])
    if not result["success"] and "not fully merged" in result.get("error", ""):
        result = _run_git(["branch", "-D", branch_name])
    return json.dumps(result)


def git_list_branches() -> str:
    """List all local git branches.

    Returns:
        JSON string with list of branch names and which one is current.
    """
    result = _run_git(["branch", "--list"])
    if not result["success"]:
        return json.dumps(result)
    branches = []
    current = None
    for line in result["output"].split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("* "):
            name = line[2:].strip()
            current = name
        else:
            name = line.strip()
        branches.append(name)
    return json.dumps({"success": True, "branches": branches, "current": current, "count": len(branches)})


def git_cleanup_branches() -> str:
    """Delete ALL local branches except main and the current branch.

    Returns:
        JSON string with count of deleted branches and any that failed.
    """
    current_result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    current = current_result.get("output", "main").strip()

    list_result = _run_git(["branch", "--list"])
    if not list_result["success"]:
        return json.dumps(list_result)

    protected = {"master", "main", current}
    deleted = []
    failed = []

    for line in list_result["output"].split("\n"):
        name = line.strip().lstrip("* ").strip()
        if not name or name in protected:
            continue
        result = _run_git(["branch", "-D", name])
        if result["success"]:
            deleted.append(name)
        else:
            failed.append({"branch": name, "error": result.get("error", "")})

    return json.dumps({
        "success": True,
        "deleted_count": len(deleted),
        "failed_count": len(failed),
        "deleted": deleted[:20],
        "failed": failed[:5],
    })


def git_cleanup_remote_branches() -> str:
    """Delete ALL remote branches except main/master on the origin remote.

    Returns:
        JSON string with count of deleted remote branches.
    """
    list_result = _run_git(["branch", "-r", "--list"])
    if not list_result["success"]:
        return json.dumps(list_result)

    protected = {"origin/master", "origin/main", "origin/HEAD"}
    deleted = []
    failed = []

    for line in list_result["output"].split("\n"):
        ref = line.strip()
        if not ref or ref in protected or "->" in ref:
            continue
        if not ref.startswith("origin/"):
            continue
        branch_name = ref.replace("origin/", "", 1)
        result = _run_git(["push", "origin", "--delete", branch_name], timeout=30)
        if result["success"]:
            deleted.append(branch_name)
        else:
            failed.append({"branch": branch_name, "error": result.get("error", "")[:100]})

    _run_git(["fetch", "--prune"])

    return json.dumps({
        "success": True,
        "deleted_count": len(deleted),
        "failed_count": len(failed),
        "deleted": deleted[:20],
        "failed": failed[:5],
    })


def git_log(count: int = 10) -> str:
    """Show recent commit history.

    Args:
        count: Number of recent commits to show. Default 10.

    Returns:
        JSON string with recent commit messages and hashes.
    """
    result = _run_git(["log", "--oneline", f"-{count}"])
    return json.dumps(result)


def git_merge_branch(branch_name: str) -> str:
    """Merge a branch into the current branch.

    If there are conflicts, returns the list of conflicting files.
    Use git_show_conflicts and git_resolve_conflict to handle them.

    Args:
        branch_name: The branch to merge into the current branch.

    Returns:
        JSON string with merge result.
    """
    result = _run_git(["merge", branch_name, "--no-edit"])
    if result["success"]:
        return json.dumps({"success": True, "merged": True, "conflicts": []})

    if "CONFLICT" not in result.get("error", "") and "conflict" not in result.get("error", "").lower():
        return json.dumps(result)

    diff_result = _run_git(["diff", "--name-only", "--diff-filter=U"])
    conflicting_files = diff_result.get("output", "").strip().split("\n") if diff_result.get("output") else []
    conflicting_files = [f for f in conflicting_files if f]

    return json.dumps({
        "success": False,
        "has_conflicts": True,
        "conflicting_files": conflicting_files,
        "count": len(conflicting_files),
        "hint": "Use git_show_conflicts(file_path) to see each conflict, then git_resolve_conflict(file_path, strategy) to resolve.",
    })


def git_show_conflicts(file_path: str) -> str:
    """Show the conflict markers in a file that has merge conflicts.

    Args:
        file_path: Path to the conflicting file (relative to repo root).

    Returns:
        JSON with the conflict details.
    """
    import os

    full_path = os.path.join(_CWD, file_path)
    if not os.path.exists(full_path):
        return json.dumps({"success": False, "error": f"File not found: {file_path}"})

    try:
        with open(full_path) as f:
            content = f.read()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

    if "<<<<<<< HEAD" not in content:
        return json.dumps({"success": True, "has_conflicts": False, "message": "No conflict markers found in this file"})

    sections = []
    in_conflict = False
    ours_lines = []
    theirs_lines = []
    in_theirs = False

    for line in content.split("\n"):
        if line.startswith("<<<<<<< "):
            in_conflict = True
            in_theirs = False
            ours_lines = []
            theirs_lines = []
        elif line.startswith("=======") and in_conflict:
            in_theirs = True
        elif line.startswith(">>>>>>> ") and in_conflict:
            sections.append({
                "ours": "\n".join(ours_lines),
                "theirs": "\n".join(theirs_lines),
            })
            in_conflict = False
        elif in_conflict:
            if in_theirs:
                theirs_lines.append(line)
            else:
                ours_lines.append(line)

    truncated = content[:5000] + "\n... (truncated)" if len(content) > 5000 else content

    return json.dumps({
        "success": True,
        "has_conflicts": True,
        "file_path": file_path,
        "conflict_count": len(sections),
        "conflicts": sections,
        "full_content": truncated,
    })


def git_resolve_conflict(file_path: str, strategy: str) -> str:
    """Resolve merge conflicts in a file using a strategy.

    Args:
        file_path: Path to the conflicting file (relative to repo root).
        strategy: Resolution strategy: 'ours', 'theirs', or 'both'.

    Returns:
        JSON string indicating success or failure.
    """
    import os

    if strategy not in ("ours", "theirs", "both"):
        return json.dumps({"success": False, "error": f"Invalid strategy '{strategy}'. Use 'ours', 'theirs', or 'both'."})

    full_path = os.path.join(_CWD, file_path)
    if not os.path.exists(full_path):
        return json.dumps({"success": False, "error": f"File not found: {file_path}"})

    try:
        with open(full_path) as f:
            content = f.read()
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

    if "<<<<<<< HEAD" not in content:
        return json.dumps({"success": True, "message": "No conflict markers found — file is already resolved"})

    resolved_lines = []
    in_conflict = False
    in_theirs = False
    ours_lines = []
    theirs_lines = []

    for line in content.split("\n"):
        if line.startswith("<<<<<<< "):
            in_conflict = True
            in_theirs = False
            ours_lines = []
            theirs_lines = []
        elif line.startswith("=======") and in_conflict:
            in_theirs = True
        elif line.startswith(">>>>>>> ") and in_conflict:
            if strategy == "ours":
                resolved_lines.extend(ours_lines)
            elif strategy == "theirs":
                resolved_lines.extend(theirs_lines)
            else:
                resolved_lines.extend(ours_lines)
                resolved_lines.extend(theirs_lines)
            in_conflict = False
        elif in_conflict:
            if in_theirs:
                theirs_lines.append(line)
            else:
                ours_lines.append(line)
        else:
            resolved_lines.append(line)

    try:
        with open(full_path, "w") as f:
            f.write("\n".join(resolved_lines))
    except Exception as e:
        return json.dumps({"success": False, "error": f"Failed to write resolved file: {e}"})

    add_result = _run_git(["add", file_path])
    if not add_result["success"]:
        return json.dumps({"success": False, "error": f"File resolved but git add failed: {add_result['error']}"})

    return json.dumps({"success": True, "file_path": file_path, "strategy": strategy, "message": f"Conflict resolved using '{strategy}' strategy and staged"})


def git_abort_merge() -> str:
    """Abort a merge in progress and restore the previous state.

    Returns:
        JSON string indicating success or failure.
    """
    result = _run_git(["merge", "--abort"])
    return json.dumps(result)


_BLOCKED_COMMANDS = {"rm -rf /", "rm -rf ~", "sudo", "shutdown", "reboot", "mkfs", "dd if=", ":(){ ", "fork"}


def run_command(command: str) -> str:
    """Run a shell command in the product repository directory.

    Args:
        command: The shell command to execute (e.g., 'npm run build', 'node src/index.js').

    Returns:
        JSON string with stdout, stderr, and return code.
    """
    for blocked in _BLOCKED_COMMANDS:
        if blocked in command:
            return json.dumps({"success": False, "error": f"Blocked command: contains '{blocked}'"})
    try:
        result = subprocess.run(
            command,
            shell=True,
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
            "stderr": result.stderr.strip()[:2000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "Command timed out after 60s"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

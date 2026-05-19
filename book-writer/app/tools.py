from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml
from slugify import slugify


def parse_toc_json(text: str) -> dict:
    return json.loads(text)


def parse_toc_yaml(text: str) -> dict:
    return yaml.safe_load(text)


def parse_toc_text(text: str) -> dict:
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    title = "Untitled Book"
    description = ""
    chapters = []

    if lines and lines[0].startswith("#"):
        title = lines.pop(0).lstrip("# ").strip()

    if lines and not re.match(r"^\d+[\.\)]\s", lines[0]):
        description = lines.pop(0).strip()

    for line in lines:
        m = re.match(r"^(\d+)[\.\)]\s+(.+?)(?:\s*[-–—]\s*(.+))?$", line)
        if m:
            chapters.append({
                "number": int(m.group(1)),
                "title": m.group(2).strip(),
                "description": m.group(3).strip() if m.group(3) else "",
            })

    return {"title": title, "description": description, "chapters": chapters}


def parse_toc(file_path: str) -> dict:
    """Parse a table of contents file (JSON, YAML, or plain text)."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    if path.suffix in (".json",):
        toc = parse_toc_json(content)
    elif path.suffix in (".yaml", ".yml"):
        toc = parse_toc_yaml(content)
    else:
        toc = parse_toc_text(content)

    for i, ch in enumerate(toc.get("chapters", [])):
        if "number" not in ch:
            ch["number"] = i + 1
        if "description" not in ch:
            ch["description"] = ""

    return toc


def save_chapter_to_disk(
    chapter_number: int,
    title: str,
    content: str,
    output_dir: str,
) -> dict:
    """Write a chapter Markdown file to disk."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    slug = slugify(title, max_length=60)
    filename = f"chapter-{chapter_number:02d}-{slug}.md"
    filepath = out / filename

    now = datetime.now(timezone.utc).isoformat()
    front_matter = (
        f"---\n"
        f"chapter: {chapter_number}\n"
        f"title: \"{title}\"\n"
        f"generated_at: \"{now}\"\n"
        f"---\n\n"
    )

    full_content = front_matter + content
    filepath.write_text(full_content, encoding="utf-8")

    word_count = len(content.split())
    return {
        "success": True,
        "file_path": str(filepath),
        "filename": filename,
        "word_count": word_count,
    }


def git_commit_and_push_sync(
    chapter_number: int,
    title: str,
    output_dir: str,
    branch: str = "main",
) -> dict:
    """Git add, commit, and push for a completed chapter."""
    cwd = Path(output_dir)

    if not (cwd / ".git").exists():
        parent = cwd.parent
        while parent != parent.parent:
            if (parent / ".git").exists():
                cwd = parent
                break
            parent = parent.parent
        else:
            return {"success": False, "message": "Not a git repository"}

    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=str(cwd),
            check=True,
            timeout=60,
            capture_output=True,
        )

        msg = f"Add Chapter {chapter_number}: {title}"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(cwd),
            check=True,
            timeout=60,
            capture_output=True,
            text=True,
        )

        commit_hash = ""
        for line in result.stdout.splitlines():
            if line.strip().startswith("["):
                parts = line.split()
                for p in parts:
                    if len(p) >= 7 and p.replace("]", "").isalnum():
                        commit_hash = p.replace("]", "")
                        break

        push_result = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=str(cwd),
            timeout=120,
            capture_output=True,
            text=True,
        )

        if push_result.returncode != 0:
            return {
                "success": True,
                "commit_hash": commit_hash,
                "pushed": False,
                "message": f"Committed but push failed: {push_result.stderr.strip()}",
            }

        return {
            "success": True,
            "commit_hash": commit_hash,
            "pushed": True,
            "message": f"Committed and pushed Chapter {chapter_number}",
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Git operation timed out"}
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
        return {"success": False, "message": f"Git error: {stderr.strip()}"}


def load_progress(output_dir: str) -> dict:
    """Load progress from .progress.json."""
    path = Path(output_dir) / ".progress.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"completed": [], "failed": {}, "in_progress": None}


def save_progress(output_dir: str, progress: dict) -> None:
    """Save progress to .progress.json."""
    path = Path(output_dir) / ".progress.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

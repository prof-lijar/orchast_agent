from __future__ import annotations

import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml
from slugify import slugify

logger = logging.getLogger("scie_paper_writer")

# --- Structure Templates ---

STRUCTURE_TEMPLATES = {
    "generic": [
        {"name": "Abstract", "description": "Brief summary of the paper's purpose, methods, results, and conclusions"},
        {"name": "Introduction", "description": "Background, motivation, problem statement, and contributions"},
        {"name": "Related Work", "description": "Review of relevant prior work and how this paper differs"},
        {"name": "Methodology", "description": "Detailed description of the proposed approach or method"},
        {"name": "Experiments", "description": "Experimental setup, datasets, metrics, and results"},
        {"name": "Discussion", "description": "Analysis and interpretation of results, limitations"},
        {"name": "Conclusion", "description": "Summary of contributions and future work directions"},
        {"name": "References", "description": "Bibliography of cited works"},
    ],
    "ieee": [
        {"name": "Abstract", "description": "Concise summary (150-250 words) of the paper"},
        {"name": "Introduction", "description": "Problem context, motivation, and paper organization"},
        {"name": "Literature Review", "description": "Survey of related work in the field"},
        {"name": "System Model", "description": "System architecture and theoretical framework"},
        {"name": "Proposed Method", "description": "Detailed description of the proposed approach"},
        {"name": "Experimental Results", "description": "Evaluation methodology, setup, and quantitative results"},
        {"name": "Discussion", "description": "Analysis, comparison with baselines, and limitations"},
        {"name": "Conclusion", "description": "Summary and future research directions"},
        {"name": "References", "description": "IEEE-formatted bibliography"},
    ],
    "acm": [
        {"name": "Abstract", "description": "Summary of the paper (up to 300 words)"},
        {"name": "CCS Concepts and Keywords", "description": "ACM Computing Classification System concepts and keywords"},
        {"name": "Introduction", "description": "Motivation, problem statement, contributions"},
        {"name": "Background", "description": "Foundational concepts and definitions"},
        {"name": "Related Work", "description": "Comparison with existing approaches"},
        {"name": "Design", "description": "System design and architecture"},
        {"name": "Implementation", "description": "Implementation details and technical choices"},
        {"name": "Evaluation", "description": "Experimental methodology, metrics, and results"},
        {"name": "Discussion", "description": "Interpretation, limitations, and threats to validity"},
        {"name": "Conclusion", "description": "Summary and future work"},
        {"name": "References", "description": "ACM-formatted bibliography"},
    ],
}


def get_structure_template(name: str) -> list[dict]:
    name = name.lower().strip()
    if name not in STRUCTURE_TEMPLATES:
        available = ", ".join(STRUCTURE_TEMPLATES.keys())
        raise ValueError(f"Unknown structure template '{name}'. Available: {available}")
    return STRUCTURE_TEMPLATES[name]


# --- Spec Parsing ---

def parse_spec(file_path: str) -> dict:
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    if path.suffix in (".json",):
        spec = json.loads(content)
    elif path.suffix in (".yaml", ".yml"):
        spec = yaml.safe_load(content)
    else:
        raise ValueError(f"Unsupported spec format: {path.suffix}. Use .json or .yaml")

    if "title" not in spec:
        raise ValueError("Spec must include a 'title' field")

    if "sections" not in spec:
        structure = spec.get("structure", "generic")
        spec["sections"] = get_structure_template(structure)
    else:
        for section in spec["sections"]:
            if "name" not in section:
                raise ValueError("Each section must have a 'name' field")
            section.setdefault("description", "")

    spec.setdefault("authors", [])
    spec.setdefault("sources", [])
    spec.setdefault("target_word_count", "5000-8000")
    spec.setdefault("language", "en")
    spec.setdefault("writing_guidelines", [])
    spec.setdefault("structure", "custom")

    return spec


# --- Source Collection ---

GITHUB_BLOB_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)"
)
GITHUB_TREE_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)(?:/tree/(?P<branch>[^/]+)(?:/(?P<path>.+))?)?$"
)

COLLECTIBLE_EXTENSIONS = {
    ".md", ".txt", ".rst", ".tex", ".csv", ".json", ".yaml", ".yml",
    ".py", ".ipynb", ".log", ".bib",
}

MAX_FILE_SIZE = 512 * 1024  # 512 KB per file


def is_github_url(s: str) -> bool:
    return s.startswith("https://github.com/") or s.startswith("http://github.com/")


def resolve_github_source(url: str, clone_base: str = "./repos") -> dict:
    m = GITHUB_BLOB_RE.match(url)
    if m:
        owner, repo, branch, file_path = m.group("owner"), m.group("repo"), m.group("branch"), m.group("path")
        repo_url = f"https://github.com/{owner}/{repo}.git"
        repo_dir = Path(clone_base) / repo
        _clone_or_pull(repo_url, repo_dir, branch)
        return {"type": "file", "path": str(repo_dir / file_path), "repo_dir": str(repo_dir)}

    m = GITHUB_TREE_RE.match(url)
    if m:
        owner, repo = m.group("owner"), m.group("repo")
        branch = m.group("branch") or "main"
        sub_path = m.group("path") or ""
        repo_url = f"https://github.com/{owner}/{repo}.git"
        repo_dir = Path(clone_base) / repo
        _clone_or_pull(repo_url, repo_dir, branch)
        target = repo_dir / sub_path if sub_path else repo_dir
        return {"type": "directory", "path": str(target), "repo_dir": str(repo_dir)}

    owner_repo = url.rstrip("/").replace("https://github.com/", "").replace("http://github.com/", "")
    parts = owner_repo.split("/")
    if len(parts) >= 2:
        owner, repo = parts[0], parts[1]
        repo_url = f"https://github.com/{owner}/{repo}.git"
        repo_dir = Path(clone_base) / repo
        _clone_or_pull(repo_url, repo_dir, "main")
        return {"type": "directory", "path": str(repo_dir), "repo_dir": str(repo_dir)}

    raise ValueError(f"Cannot parse GitHub URL: {url}")


def _clone_or_pull(repo_url: str, repo_dir: Path, branch: str) -> None:
    if (repo_dir / ".git").exists():
        logger.info("Repo already cloned at %s — pulling latest", repo_dir)
        subprocess.run(
            ["git", "pull", "origin", branch],
            cwd=str(repo_dir),
            check=True,
            timeout=120,
            capture_output=True,
        )
    else:
        logger.info("Cloning %s into %s", repo_url, repo_dir)
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "-b", branch, repo_url, str(repo_dir)],
            check=True,
            timeout=120,
        )


def _read_file_safe(path: Path) -> str | None:
    if path.stat().st_size > MAX_FILE_SIZE:
        logger.warning("Skipping large file: %s (%d bytes)", path, path.stat().st_size)
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return None


def _collect_from_path(path: Path) -> list[tuple[str, str]]:
    results = []
    if path.is_file():
        if path.suffix.lower() in COLLECTIBLE_EXTENSIONS:
            content = _read_file_safe(path)
            if content:
                results.append((str(path), content))
    elif path.is_dir():
        for f in sorted(path.rglob("*")):
            if f.is_file() and f.suffix.lower() in COLLECTIBLE_EXTENSIONS:
                if ".git" in f.parts or ".venv" in f.parts or "__pycache__" in f.parts:
                    continue
                content = _read_file_safe(f)
                if content:
                    results.append((str(f.relative_to(path)), content))
    return results


def collect_sources(sources: list[str], clone_dir: str = "./repos") -> str:
    all_materials = []

    for source in sources:
        if is_github_url(source):
            resolved = resolve_github_source(source, clone_base=clone_dir)
            target = Path(resolved["path"])
        else:
            target = Path(source)

        if not target.exists():
            logger.warning("Source not found: %s", source)
            continue

        collected = _collect_from_path(target)
        for filepath, content in collected:
            all_materials.append(f"=== SOURCE: {filepath} ===\n{content}")
            logger.info("Collected source: %s (%d chars)", filepath, len(content))

    if not all_materials:
        logger.warning("No source materials collected")
        return "(No source materials provided)"

    logger.info("Total sources collected: %d", len(all_materials))
    return "\n\n".join(all_materials)


# --- Output ---

def save_paper_to_disk(title: str, content: str, output_dir: str) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    slug = slugify(title, max_length=60)
    filename = f"{slug}.md"
    filepath = out / filename

    now = datetime.now(timezone.utc).isoformat()
    front_matter = (
        f"---\n"
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


# --- Progress Tracking ---

def load_progress(output_dir: str) -> dict:
    path = Path(output_dir) / ".progress.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"completed_agents": [], "failed": {}, "in_progress": None}


def save_progress(output_dir: str, progress: dict) -> None:
    path = Path(output_dir) / ".progress.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(progress, indent=2), encoding="utf-8")


# --- Git ---

def git_commit_and_push_sync(
    title: str,
    output_dir: str,
    branch: str = "main",
    message: str | None = None,
) -> dict:
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

        msg = message or f"Add paper: {title}"
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

        pull_result = subprocess.run(
            ["git", "pull", "--rebase", "origin", branch],
            cwd=str(cwd),
            timeout=120,
            capture_output=True,
            text=True,
        )

        if pull_result.returncode != 0:
            return {
                "success": True,
                "commit_hash": commit_hash,
                "pushed": False,
                "message": f"Committed but pull --rebase failed: {pull_result.stderr.strip()}",
            }

        push_result = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=str(cwd),
            timeout=120,
            capture_output=True,
            text=True,
        )

        if push_result.returncode == 0:
            return {
                "success": True,
                "commit_hash": commit_hash,
                "pushed": True,
                "message": f"Committed and pushed paper: {title}",
            }

        return {
            "success": True,
            "commit_hash": commit_hash,
            "pushed": False,
            "message": f"Committed but push failed: {push_result.stderr.strip()}",
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Git operation timed out"}
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
        return {"success": False, "message": f"Git error: {stderr.strip()}"}

"""Project status and polyglot stack detection for dev-team agents."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from config import Config

_config = Config.from_env()


def _detect_stack(repo_dir: Path) -> dict:
    stack: dict = {
        "languages": [],
        "frameworks": [],
        "package_manager": None,
        "build_tool": None,
        "test_runner": None,
        "recommended_skills": [],
    }

    # Node.js / TypeScript / JavaScript
    pkg_path = repo_dir / "package.json"
    if pkg_path.exists():
        stack["languages"].append("typescript/javascript")
        stack["recommended_skills"].append("node")
        try:
            pkg = json.loads(pkg_path.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                stack["frameworks"].append("nextjs")
            if "react" in deps and "next" not in deps:
                stack["frameworks"].append("react")
            if "vue" in deps:
                stack["frameworks"].append("vue")
            if "svelte" in deps or "@sveltejs/kit" in deps:
                stack["frameworks"].append("svelte")
            if "angular" in deps or "@angular/core" in deps:
                stack["frameworks"].append("angular")
            if "express" in deps:
                stack["frameworks"].append("express")
            if "nestjs" in deps or "@nestjs/core" in deps:
                stack["frameworks"].append("nestjs")
            if "astro" in deps:
                stack["frameworks"].append("astro")

            if (repo_dir / "pnpm-lock.yaml").exists():
                stack["package_manager"] = "pnpm"
            elif (repo_dir / "yarn.lock").exists():
                stack["package_manager"] = "yarn"
            elif (repo_dir / "bun.lockb").exists():
                stack["package_manager"] = "bun"
            else:
                stack["package_manager"] = "npm"

            if "jest" in deps:
                stack["test_runner"] = "jest"
            elif "vitest" in deps:
                stack["test_runner"] = "vitest"
            elif "mocha" in deps:
                stack["test_runner"] = "mocha"
        except (json.JSONDecodeError, KeyError):
            pass

    # Python
    pyproject = repo_dir / "pyproject.toml"
    requirements = repo_dir / "requirements.txt"
    if pyproject.exists() or requirements.exists():
        stack["languages"].append("python")
        stack["recommended_skills"].append("python")
        if (repo_dir / "poetry.lock").exists():
            stack["package_manager"] = "poetry"
        elif (repo_dir / "uv.lock").exists():
            stack["package_manager"] = "uv"
        elif (repo_dir / "Pipfile").exists():
            stack["package_manager"] = "pipenv"
        else:
            stack["package_manager"] = stack["package_manager"] or "pip"
        stack["test_runner"] = stack["test_runner"] or "pytest"

        if pyproject.exists():
            try:
                content = pyproject.read_text()
                if "fastapi" in content.lower():
                    stack["frameworks"].append("fastapi")
                if "django" in content.lower():
                    stack["frameworks"].append("django")
                if "flask" in content.lower():
                    stack["frameworks"].append("flask")
                if "starlette" in content.lower():
                    stack["frameworks"].append("starlette")
            except Exception:
                pass
        if requirements.exists():
            try:
                content = requirements.read_text().lower()
                if "fastapi" in content:
                    stack["frameworks"].append("fastapi")
                if "django" in content:
                    stack["frameworks"].append("django")
                if "flask" in content:
                    stack["frameworks"].append("flask")
            except Exception:
                pass

    # Go
    if (repo_dir / "go.mod").exists():
        stack["languages"].append("go")
        stack["recommended_skills"].append("go")
        stack["build_tool"] = stack["build_tool"] or "go"
        stack["test_runner"] = stack["test_runner"] or "go test"
        try:
            content = (repo_dir / "go.mod").read_text()
            if "github.com/gin-gonic/gin" in content:
                stack["frameworks"].append("gin")
            if "github.com/labstack/echo" in content:
                stack["frameworks"].append("echo")
            if "github.com/gofiber/fiber" in content:
                stack["frameworks"].append("fiber")
        except Exception:
            pass

    # Rust
    if (repo_dir / "Cargo.toml").exists():
        stack["languages"].append("rust")
        stack["recommended_skills"].append("rust")
        stack["build_tool"] = stack["build_tool"] or "cargo"
        stack["test_runner"] = stack["test_runner"] or "cargo test"
        try:
            content = (repo_dir / "Cargo.toml").read_text()
            if "actix-web" in content:
                stack["frameworks"].append("actix")
            if "axum" in content:
                stack["frameworks"].append("axum")
            if "rocket" in content:
                stack["frameworks"].append("rocket")
        except Exception:
            pass

    # Java / Kotlin
    if (repo_dir / "pom.xml").exists():
        stack["languages"].append("java")
        stack["build_tool"] = "maven"
    elif (repo_dir / "build.gradle").exists() or (repo_dir / "build.gradle.kts").exists():
        stack["languages"].append("java/kotlin")
        stack["build_tool"] = "gradle"

    # Docker
    if (repo_dir / "Dockerfile").exists():
        stack["recommended_skills"].append("docker")
    if (repo_dir / "docker-compose.yml").exists() or (repo_dir / "compose.yml").exists():
        stack["recommended_skills"].append("docker")

    # CI/CD
    if (repo_dir / ".github" / "workflows").is_dir():
        stack["recommended_skills"].append("ci")

    # Deploy targets
    if (repo_dir / "vercel.json").exists():
        stack["recommended_skills"].append("deploy")
    if (repo_dir / "fly.toml").exists():
        stack["recommended_skills"].append("deploy")

    stack["recommended_skills"] = list(dict.fromkeys(stack["recommended_skills"]))
    return stack


def get_project_status() -> str:
    """Get a comprehensive summary of the current project state.

    Reads open issues, recent PRs, recent commits, directory structure,
    and detects the project's tech stack (languages, frameworks, tools).

    Returns:
        JSON string with project status snapshot including detected stack.
    """
    repo_dir = _config.product_repo_dir
    status: dict = {
        "open_issues": [],
        "open_prs": [],
        "recent_commits": [],
        "repo_structure": [],
        "detected_stack": {},
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
        cwd=str(repo_dir),
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        status["recent_commits"] = result.stdout.strip().split("\n")

    result = subprocess.run(
        ["find", ".", "-maxdepth", "2",
         "-not", "-path", "./.git/*", "-not", "-path", "./node_modules/*",
         "-not", "-path", "./.venv/*", "-not", "-path", "./__pycache__/*",
         "-not", "-path", "./.next/*", "-not", "-path", "./target/*",
         "-not", "-name", ".*"],
        cwd=str(repo_dir),
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        status["repo_structure"] = [
            f for f in result.stdout.strip().split("\n") if f and f != "."
        ]

    status["detected_stack"] = _detect_stack(repo_dir)

    return json.dumps(status)

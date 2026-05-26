#!/usr/bin/env bash
# SKILL_NAME="python"
# SKILL_DESC="Python project management — pip, poetry, uv, venv, pytest, ruff, mypy"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="python3"
# SKILL_COMMANDS="install,build,test,lint,format,typecheck,venv_create,run,init"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

_detect_pm() {
    if [[ -f "$REPO_DIR/poetry.lock" ]]; then echo "poetry"
    elif [[ -f "$REPO_DIR/uv.lock" ]]; then echo "uv"
    elif [[ -f "$REPO_DIR/Pipfile" ]]; then echo "pipenv"
    else echo "pip"
    fi
}

_python() {
    if [[ -d "$REPO_DIR/.venv" ]]; then
        "$REPO_DIR/.venv/bin/python" "$@"
    else
        python3 "$@"
    fi
}

cmd_install() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    case "$pm" in
        poetry)
            poetry install "$@"
            ;;
        uv)
            uv sync "$@"
            ;;
        pipenv)
            pipenv install "$@"
            ;;
        *)
            if [[ $# -gt 0 ]]; then
                _python -m pip install "$@"
            elif [[ -f requirements.txt ]]; then
                _python -m pip install -r requirements.txt
            elif [[ -f pyproject.toml ]]; then
                _python -m pip install -e .
            fi
            ;;
    esac
}

cmd_build() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    case "$pm" in
        poetry) poetry build ;;
        uv)     uv build ;;
        *)      _python -m build 2>/dev/null || echo "No build system configured" ;;
    esac
}

cmd_test() {
    cd "$REPO_DIR"
    if [[ $# -gt 0 ]]; then
        _python -m pytest "$@"
    else
        _python -m pytest
    fi
}

cmd_lint() {
    cd "$REPO_DIR"
    if command -v ruff &>/dev/null || [[ -f "$REPO_DIR/.venv/bin/ruff" ]]; then
        _python -m ruff check "${@:-.}"
    elif command -v flake8 &>/dev/null; then
        _python -m flake8 "${@:-.}"
    else
        echo "No linter found. Install ruff: pip install ruff"
        exit 1
    fi
}

cmd_format() {
    cd "$REPO_DIR"
    if command -v ruff &>/dev/null || [[ -f "$REPO_DIR/.venv/bin/ruff" ]]; then
        _python -m ruff format "${@:-.}"
    elif command -v black &>/dev/null; then
        _python -m black "${@:-.}"
    else
        echo "No formatter found. Install ruff: pip install ruff"
        exit 1
    fi
}

cmd_typecheck() {
    cd "$REPO_DIR"
    if command -v mypy &>/dev/null || [[ -f "$REPO_DIR/.venv/bin/mypy" ]]; then
        _python -m mypy "${@:-.}"
    elif command -v pyright &>/dev/null; then
        pyright "${@:-.}"
    else
        echo "No type checker found. Install mypy: pip install mypy"
        exit 1
    fi
}

cmd_venv_create() {
    cd "$REPO_DIR"
    local name="${1:-.venv}"
    python3 -m venv "$name"
    echo "Virtual environment created at $name"
    echo "Activate with: source $name/bin/activate"
}

cmd_run() {
    cd "$REPO_DIR"
    _python "$@"
}

cmd_init() {
    cd "$REPO_DIR"
    local name="${1:?Project name required}"
    local framework="${2:-}"

    mkdir -p "$name/src/$name" "$name/tests"

    cat > "$name/pyproject.toml" <<PYPROJ
[project]
name = "$name"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"
PYPROJ

    cat > "$name/src/$name/__init__.py" <<INIT
"""$name package."""
INIT

    cat > "$name/tests/__init__.py" <<INIT
INIT

    echo "Python project '$name' initialized."

    if [[ "$framework" == "fastapi" ]]; then
        echo 'fastapi[standard]' >> "$name/pyproject.toml"
        cat > "$name/src/$name/main.py" <<MAIN
from fastapi import FastAPI

app = FastAPI(title="$name")

@app.get("/")
async def root():
    return {"message": "Hello from $name"}
MAIN
        echo "FastAPI app scaffolded."
    elif [[ "$framework" == "flask" ]]; then
        cat > "$name/src/$name/app.py" <<APP
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return {"message": "Hello from $name"}
APP
        echo "Flask app scaffolded."
    fi
}

"cmd_${1}" "${@:2}"

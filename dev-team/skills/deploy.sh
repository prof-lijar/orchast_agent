#!/usr/bin/env bash
# SKILL_NAME="deploy"
# SKILL_DESC="Deployment management — Vercel, Fly.io, Docker-based deploy, static hosting"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES=""
# SKILL_COMMANDS="vercel_deploy,vercel_list,vercel_logs,vercel_env_set,vercel_env_list,fly_deploy,fly_status,detect_platform"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_vercel_deploy() {
    cd "$REPO_DIR"
    if [[ "${1:-}" == "--prod" ]]; then
        vercel deploy --prod --yes
    else
        vercel deploy --yes
    fi
}

cmd_vercel_list() {
    cd "$REPO_DIR"
    vercel ls --yes "${@}"
}

cmd_vercel_logs() {
    local url="${1:?Deployment URL required}"
    vercel logs "$url" --yes --limit 100
}

cmd_vercel_env_set() {
    local key="${1:?Key required}"
    local value="${2:?Value required}"
    local env="${3:-production}"
    cd "$REPO_DIR"
    echo "$value" | vercel env add "$key" "$env"
}

cmd_vercel_env_list() {
    cd "$REPO_DIR"
    vercel env ls --yes
}

cmd_fly_deploy() {
    cd "$REPO_DIR"
    fly deploy "$@"
}

cmd_fly_status() {
    cd "$REPO_DIR"
    fly status "$@"
}

cmd_detect_platform() {
    cd "$REPO_DIR"
    local platform="unknown"

    if [[ -f "vercel.json" ]] || command -v vercel &>/dev/null; then
        platform="vercel"
    elif [[ -f "fly.toml" ]]; then
        platform="fly"
    elif [[ -f "Dockerfile" ]]; then
        platform="docker"
    elif [[ -f "package.json" ]]; then
        platform="vercel"
    elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
        platform="fly"
    elif [[ -f "go.mod" ]]; then
        platform="fly"
    fi

    echo "$platform"
}

"cmd_${1}" "${@:2}"

#!/usr/bin/env bash
# SKILL_NAME="docker"
# SKILL_DESC="Docker container management — build, run, push, compose"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="docker"
# SKILL_COMMANDS="build,run,push,compose_up,compose_down,ps,logs,exec"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_build() {
    cd "$REPO_DIR"
    local tag="${1:-app:latest}"
    local context="${2:-.}"
    shift 2 2>/dev/null || true
    docker build -t "$tag" "$context" "$@"
}

cmd_run() {
    cd "$REPO_DIR"
    local image="${1:?Image name required}"
    shift
    docker run "$@" "$image"
}

cmd_push() {
    local tag="${1:?Image tag required}"
    docker push "$tag"
}

cmd_compose_up() {
    cd "$REPO_DIR"
    docker compose up "$@"
}

cmd_compose_down() {
    cd "$REPO_DIR"
    docker compose down "$@"
}

cmd_ps() {
    docker ps "$@"
}

cmd_logs() {
    local container="${1:?Container name/ID required}"
    shift
    docker logs "$@" "$container"
}

cmd_exec() {
    local container="${1:?Container name/ID required}"
    shift
    docker exec "$@" "$container"
}

"cmd_${1}" "${@:2}"

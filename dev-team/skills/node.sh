#!/usr/bin/env bash
# SKILL_NAME="node"
# SKILL_DESC="Node.js project management — npm, pnpm, yarn, build, test, lint, scaffold"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="node,npm"
# SKILL_COMMANDS="install,run,build,test,lint,init,add_package,add_dev_package,remove_package"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

_detect_pm() {
    if [[ -f "$REPO_DIR/pnpm-lock.yaml" ]]; then echo "pnpm"
    elif [[ -f "$REPO_DIR/yarn.lock" ]]; then echo "yarn"
    elif [[ -f "$REPO_DIR/bun.lockb" ]]; then echo "bun"
    else echo "npm"
    fi
}

cmd_install() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    if [[ $# -gt 0 ]]; then
        $pm install "$@"
    else
        $pm install
    fi
}

cmd_run() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    $pm run "$@"
}

cmd_build() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    $pm run build
}

cmd_test() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    if [[ $# -gt 0 ]]; then
        $pm test -- "$@"
    else
        $pm test
    fi
}

cmd_lint() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    $pm run lint
}

cmd_init() {
    cd "$REPO_DIR"
    npx --yes "$@"
}

cmd_add_package() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    case "$pm" in
        pnpm) pnpm add "$@" ;;
        yarn) yarn add "$@" ;;
        bun)  bun add "$@" ;;
        *)    npm install "$@" ;;
    esac
}

cmd_add_dev_package() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    case "$pm" in
        pnpm) pnpm add -D "$@" ;;
        yarn) yarn add -D "$@" ;;
        bun)  bun add -d "$@" ;;
        *)    npm install --save-dev "$@" ;;
    esac
}

cmd_remove_package() {
    cd "$REPO_DIR"
    local pm
    pm=$(_detect_pm)
    case "$pm" in
        pnpm) pnpm remove "$@" ;;
        yarn) yarn remove "$@" ;;
        bun)  bun remove "$@" ;;
        *)    npm uninstall "$@" ;;
    esac
}

"cmd_${1}" "${@:2}"

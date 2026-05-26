#!/usr/bin/env bash
# SKILL_NAME="rust"
# SKILL_DESC="Rust project management — cargo build, test, clippy, fmt"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="cargo"
# SKILL_COMMANDS="build,test,lint,fmt,run,add,init,check"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_build() {
    cd "$REPO_DIR"
    cargo build "$@"
}

cmd_test() {
    cd "$REPO_DIR"
    if [[ $# -gt 0 ]]; then
        cargo test "$@"
    else
        cargo test
    fi
}

cmd_lint() {
    cd "$REPO_DIR"
    cargo clippy "$@" -- -D warnings
}

cmd_fmt() {
    cd "$REPO_DIR"
    cargo fmt
}

cmd_run() {
    cd "$REPO_DIR"
    cargo run "$@"
}

cmd_add() {
    cd "$REPO_DIR"
    cargo add "$@"
}

cmd_init() {
    cd "$REPO_DIR"
    local name="${1:?Project name required}"
    shift
    cargo init "$name" "$@"
    echo "Rust project '$name' initialized."
}

cmd_check() {
    cd "$REPO_DIR"
    cargo check "$@"
}

"cmd_${1}" "${@:2}"

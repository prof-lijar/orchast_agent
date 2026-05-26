#!/usr/bin/env bash
# SKILL_NAME="go"
# SKILL_DESC="Go project management — build, test, mod, vet, lint"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="go"
# SKILL_COMMANDS="build,test,lint,mod_tidy,mod_download,run,fmt,init"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_build() {
    cd "$REPO_DIR"
    if [[ $# -gt 0 ]]; then
        go build "$@"
    else
        go build ./...
    fi
}

cmd_test() {
    cd "$REPO_DIR"
    if [[ $# -gt 0 ]]; then
        go test "$@"
    else
        go test ./...
    fi
}

cmd_lint() {
    cd "$REPO_DIR"
    if command -v golangci-lint &>/dev/null; then
        golangci-lint run "${@:-.}"
    else
        go vet "${@:./...}"
    fi
}

cmd_mod_tidy() {
    cd "$REPO_DIR"
    go mod tidy
}

cmd_mod_download() {
    cd "$REPO_DIR"
    go mod download
}

cmd_run() {
    cd "$REPO_DIR"
    go run "$@"
}

cmd_fmt() {
    cd "$REPO_DIR"
    gofmt -w "${@:.}"
}

cmd_init() {
    cd "$REPO_DIR"
    local module="${1:?Module name required (e.g. github.com/user/project)}"
    go mod init "$module"

    cat > main.go <<'MAIN'
package main

import "fmt"

func main() {
	fmt.Println("Hello, World!")
}
MAIN

    mkdir -p internal
    echo "Go module '$module' initialized."
}

"cmd_${1}" "${@:2}"

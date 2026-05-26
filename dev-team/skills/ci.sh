#!/usr/bin/env bash
# SKILL_NAME="ci"
# SKILL_DESC="CI/CD configuration — GitHub Actions workflow generation and management"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="gh"
# SKILL_COMMANDS="generate,list_runs,view_run,rerun"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_generate() {
    cd "$REPO_DIR"
    local stack="${1:-}"

    if [[ -z "$stack" ]]; then
        if [[ -f "package.json" ]]; then stack="node"
        elif [[ -f "pyproject.toml" ]] || [[ -f "requirements.txt" ]]; then stack="python"
        elif [[ -f "go.mod" ]]; then stack="go"
        elif [[ -f "Cargo.toml" ]]; then stack="rust"
        else stack="generic"
        fi
    fi

    mkdir -p .github/workflows

    case "$stack" in
        node)
            cat > .github/workflows/ci.yml <<'WORKFLOW'
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - run: npm test
WORKFLOW
            ;;
        python)
            cat > .github/workflows/ci.yml <<'WORKFLOW'
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]" 2>/dev/null || pip install -r requirements.txt
      - run: python -m ruff check . 2>/dev/null || true
      - run: python -m pytest
WORKFLOW
            ;;
        go)
            cat > .github/workflows/ci.yml <<'WORKFLOW'
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go build ./...
      - run: go vet ./...
      - run: go test ./...
WORKFLOW
            ;;
        rust)
            cat > .github/workflows/ci.yml <<'WORKFLOW'
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt
      - run: cargo fmt --check
      - run: cargo clippy -- -D warnings
      - run: cargo test
WORKFLOW
            ;;
        *)
            cat > .github/workflows/ci.yml <<'WORKFLOW'
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: echo "Add build steps here"
      - name: Test
        run: echo "Add test steps here"
WORKFLOW
            ;;
    esac

    echo "Generated .github/workflows/ci.yml for stack: $stack"
}

cmd_list_runs() {
    cd "$REPO_DIR"
    local limit="${1:-10}"
    gh run list --limit "$limit"
}

cmd_view_run() {
    local run_id="${1:?Run ID required}"
    gh run view "$run_id"
}

cmd_rerun() {
    local run_id="${1:?Run ID required}"
    gh run rerun "$run_id" --failed
}

"cmd_${1}" "${@:2}"

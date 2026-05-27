# dev-team

Autonomous AI software engineering team. Point it at any GitHub repo and a team of six AI agents will plan, build, test, and deploy your project — in any language or framework.

## How it works

dev-team runs a continuous cycle of six specialized agents powered by a local LLM via Ollama:

| Agent | Role |
|-------|------|
| **PM** | Decides what to build, chooses the tech stack, creates issues, writes the work plan |
| **Architect** | Designs system architecture, initializes the project, merges approved PRs |
| **Frontend** | Builds UI — React, Vue, Svelte, templates, or whatever the stack requires |
| **Backend** | Builds APIs, server logic, data layer — Python, Go, Rust, Node.js, Java |
| **QA** | Reviews PRs, runs build/test/lint, approves or requests changes |
| **DevOps** | Deploys to Vercel/Fly.io/Docker, sets up CI/CD, manages infrastructure |

Each cycle, the PM assesses the project state, creates GitHub issues for the team, and writes a `work_plan.json` that controls which agents run and how many turns they get. Agents communicate exclusively through GitHub issues, PRs, and labels.

## Quick start

```bash
# 1. Install dependencies
uv sync

# 2. Start Ollama with a model
ollama serve
ollama pull gemma4:31b

# 3. Run on any GitHub repo
uv run python run.py owner/repo-name
```

## Usage

```
dev-team [-h] [--model MODEL] [--branch BRANCH] [--timeout TIMEOUT]
         [--interval INTERVAL] [--cycles CYCLES] [--no-think] [--stream] [--goals GOALS]
         [repo]
```

| Argument | Short | Description |
|----------|-------|-------------|
| `repo` | | GitHub repo slug (`owner/name`). Overrides `PRODUCT_REPO` env var. |
| `--model` | `-m` | Ollama model name (default: `gemma4:31b`) |
| `--branch` | `-b` | Default branch (default: `main`) |
| `--timeout` | `-t` | Per-agent timeout in seconds (default: `1800`) |
| `--interval` | `-i` | Seconds between cycles (default: `0` = continuous) |
| `--cycles` | `-n` | Max cycles to run (default: `0` = unlimited) |
| `--no-think` | | Disable model thinking mode for all agents |
| `--stream` | | Stream agent thought/text/tool activity live |
| `--goals` | | Path to a Markdown file with human-defined initial goals/requirements |

### Examples

```bash
# Run on a repo, unlimited cycles
uv run python run.py myorg/my-api

# Run 3 cycles then stop
uv run python run.py myorg/my-api -n 3

# Use a different model with 5-minute breaks between cycles
uv run python run.py myorg/my-api -m qwen3:32b -i 300

# Override the default branch
uv run python run.py myorg/my-api -b develop

# Disable think mode
uv run python run.py myorg/my-api --no-think

# Show live agent thought/text/tool stream
uv run python run.py myorg/my-api --stream

# Anchor planning/build to a human goals file
uv run python run.py myorg/my-api --goals ./goals.md
```

## Environment variables

You can also configure via `.env` (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `PRODUCT_REPO` | GitHub repo slug | — |
| `PRODUCT_REPO_DIR` | Local clone path (auto-generated if unset) | `./repos/{owner-name}` |
| `DEFAULT_BRANCH` | Default branch | `main` |
| `AGENT_MODEL` | Ollama model name | `gemma4:31b` |
| `AGENT_THINK` | Enable think mode (`true`/`false`) | `true` |
| `AGENT_STREAM` | Stream verbose agent activity (`true`/`false`) | `false` |
| `CYCLE_INTERVAL` | Seconds between cycles | `0` |
| `AGENT_TIMEOUT` | Per-agent timeout (seconds) | `1800` |
| `NUM_CTX` | Context window size | `32768` |
| `SKILLS_DIR` | Path to skill scripts | `./skills` |
| `TRUSTED_SKILL_SOURCES` | Comma-separated URL prefixes for `install_skill` | — |
| `INITIAL_GOALS_FILE` | Path to Markdown goals/requirements file used by all agents | — |

CLI arguments override env vars, which override defaults.

## Guiding agents with human goals

To prevent random planning, provide an explicit goals file:

```markdown
# goals.md
Build a website that hosts books from https://github.com/prof-lijar/ai-generated-books.

Requirements:
- Public library page listing books
- PDF viewer page for each book
- Search by title/filename
- Mobile-friendly UI
```

Run with:

```bash
uv run python run.py prof-lijar/ai-generated-books-web --goals ./goals.md
```

When provided, this file is injected into every agent's instructions and treated as the highest-priority source of truth.

## Skills

Skills are shell scripts that give agents capabilities for any language and tool. Each skill wraps a CLI tool and exposes commands that agents call via `run_skill()`.

### Bundled skills

| Skill | What it wraps |
|-------|---------------|
| `node` | npm/pnpm/yarn — install, build, test, lint, scaffold (npx) |
| `python` | pip/poetry/uv — install, build, pytest, ruff, mypy, venv |
| `go` | go build, test, vet, mod tidy, fmt, golangci-lint |
| `rust` | cargo build, test, clippy, fmt, add |
| `docker` | docker build, run, push, compose up/down |
| `deploy` | Vercel deploy, Fly.io deploy, platform detection |
| `ci` | GitHub Actions workflow generation for any stack |
| `db` | SQLite/Postgres queries, schema, migrations (Alembic, Prisma, Knex, Goose) |

### Writing a custom skill

Skills are bash scripts with a metadata header:

```bash
#!/usr/bin/env bash
# SKILL_NAME="myskill"
# SKILL_DESC="What this skill does"
# SKILL_VERSION="1.0.0"
# SKILL_REQUIRES="binary1,binary2"
# SKILL_COMMANDS="cmd1,cmd2,cmd3"

set -euo pipefail
REPO_DIR="${SKILL_REPO_DIR:-.}"

cmd_cmd1() {
    cd "$REPO_DIR"
    # implementation
}

cmd_cmd2() {
    cd "$REPO_DIR"
    # implementation
}

cmd_cmd3() {
    cd "$REPO_DIR"
    # implementation
}

"cmd_${1}" "${@:2}"
```

Drop it in `skills/` and add it to `skills/registry.json`, or install from a trusted URL at runtime via `install_skill()`.

### Installing skills from external sources

Agents can install skills from URLs at runtime, but only from **whitelisted sources** (security first):

```bash
# In .env
TRUSTED_SKILL_SOURCES=https://raw.githubusercontent.com/myorg/skills/main/
```

Then agents can call `install_skill("https://raw.githubusercontent.com/myorg/skills/main/terraform.sh")` and the skill becomes available immediately.

## How agents communicate

```
PM creates issues → Agents pick up issues by role label
                  → Frontend/Backend create PRs
                  → QA reviews PRs (adds qa:approved / qa:changes-requested labels)
                  → Architect merges approved PRs
                  → DevOps deploys
                  → PM assesses progress and creates new issues
```

Labels used:
- **Role**: `role:pm`, `role:architect`, `role:frontend`, `role:backend`, `role:qa`, `role:devops`
- **Priority**: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- **Status**: `status:todo`, `status:in-progress`, `status:done`, `status:blocked`
- **Review**: `qa:approved`, `qa:changes-requested`

## Stack detection

When pointed at an existing repo, dev-team auto-detects the tech stack from project files:

| File | Detected as |
|------|-------------|
| `package.json` | Node.js (+ Next.js, React, Vue, Svelte, etc. from deps) |
| `pyproject.toml` / `requirements.txt` | Python (+ FastAPI, Django, Flask from deps) |
| `go.mod` | Go (+ Gin, Echo, Fiber from deps) |
| `Cargo.toml` | Rust (+ Actix, Axum, Rocket from deps) |
| `pom.xml` / `build.gradle` | Java/Kotlin |
| `Dockerfile` | Docker |

For new repos, the PM chooses the best stack for the project requirements.

## Prerequisites

- [Ollama](https://ollama.ai) running locally with a model pulled
- [GitHub CLI](https://cli.github.com) (`gh`) authenticated
- [Node.js](https://nodejs.org) (for Node.js projects)
- Python 3.11+ (for the agent runtime)
- Optional: Go, Rust, Docker (for those stacks)

## Project structure

```
dev-team/
├── run.py                  # CLI entrypoint and cycle runner
├── config.py               # Configuration (env + CLI args)
├── app/
│   ├── agents.py           # Agent definitions and tool wiring
│   ├── prompts/            # Agent system prompts (one per role)
│   │   ├── pm.py
│   │   ├── architect.py
│   │   ├── frontend.py
│   │   ├── backend.py
│   │   ├── qa.py
│   │   └── devops.py
│   └── tools/              # Tools available to agents
│       ├── skills.py       # Dynamic skill system
│       ├── build.py        # Auto-detecting build/test/lint
│       ├── project_state.py # Stack detection + project status
│       ├── github.py       # GitHub issue/PR operations
│       ├── git.py          # Git operations
│       ├── files.py        # File read/write
│       └── web.py          # Web search and content extraction
├── skills/                 # Skill scripts (bash)
│   ├── registry.json       # Skill manifest
│   ├── node.sh
│   ├── python.sh
│   ├── go.sh
│   ├── rust.sh
│   ├── docker.sh
│   ├── deploy.sh
│   ├── ci.sh
│   └── db.sh
└── repos/                  # Auto-created: cloned product repos
```

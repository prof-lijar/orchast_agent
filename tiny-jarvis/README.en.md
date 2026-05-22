# Tiny Jarvis

> [한국어 버전](README.md) | [Detailed Tuning Guide](docs/guide.en.md)

**Autonomous AI Dev Team** — 4 AI agents collaborate like a real software engineering team
to autonomously build a personal Telegram scheduling agent.

## Overview

Tiny Jarvis is not a project where you write code directly.
AI agents communicate through GitHub Issues and Pull Requests,
**designing, coding, reviewing, and merging the product themselves**.

```
User: runs python run.py
         ↓
┌─────────────────────────────────────────────┐
│              Orchestrator (run.py)           │
│                                             │
│  ┌─────────┐   Repeats every cycle:         │
│  │   PM    │─→ Observe state → Create issues│
│  │ Agent   │   → Write work_plan.json       │
│  └────┬────┘                                │
│       ↓ Executes based on work_plan.json    │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐   │
│  │Architect │  │ Backend  │  │   QA    │   │
│  │  Agent   │  │  Agent   │  │  Agent  │   │
│  └──────────┘  └──────────┘  └─────────┘   │
│       │              │             │        │
│  Merge PRs/     Implement       Review     │
│  Design         code            PRs        │
└─────────────────────────────────────────────┘
         ↓
   GitHub Product Repo (output)
```

## Agent Roles

| Agent | Role | Key Tools |
|-------|------|-----------|
| **PM** | Work planning, issue creation, `work_plan.json` | `create_issue`, `write_file` |
| **Architect** | System design, project init, merge approved PRs | `uv_init`, `merge_pull_request` |
| **Backend** | Primary coder — implements all Python modules | `write_file`, `run_pytest`, `create_pull_request` |
| **QA** | PR code review, test execution, approve/reject labels | `run_pytest`, `run_ruff`, `add_label_to_pr` |

## The Product Being Built

What the agents build — the **Tiny Jarvis product**:

```
Natural language command ("Tell Jisoo tomorrow at 9 AM that I finished the report")
  → Gemma local parser (Ollama)
  → Pydantic-validated JSON
  → SQLite scheduled task
  → APScheduler background worker
  → Telethon sends Telegram message
  → Logs + status update
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.ai/) + `gemma4:31b` model
- [GitHub CLI](https://cli.github.com/) (run `gh auth login`)
- Create a product repo: `gh repo create prof-lijar/mytelegent --public --clone`

### 2. Environment Setup

```bash
cd tiny-jarvis

# Create .env file
cp .env.example .env

# Edit .env — set these values:
# PRODUCT_REPO=prof-lijar/mytelegent
# PRODUCT_REPO_DIR=/absolute/path/to/tiny-jarvis/product-repo
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Prepare the Ollama Model

```bash
ollama pull gemma4:31b
ollama serve  # Run in a separate terminal
```

### 5. Run the Agent Team

```bash
uv run python run.py
```

The agents will autonomously run cycles and build the product.
Press `Ctrl+C` to gracefully stop after the current agent turn (press twice to force quit).

## Project Structure

```
tiny-jarvis/
├── run.py                  # Main orchestration loop
├── config.py               # Configuration (model, repo, timeouts)
├── .env                    # Environment variables (gitignored)
├── app/
│   ├── agents.py           # Agent definitions + tool assignments
│   ├── prompts/            # Role-specific system prompts ← tuning point
│   │   ├── pm.py
│   │   ├── architect.py
│   │   ├── backend.py
│   │   └── qa.py
│   └── tools/              # Tools available to agents
│       ├── files.py        # File read/write
│       ├── git.py          # Git branch/commit/merge
│       ├── github.py       # GitHub issues/PRs (gh CLI)
│       ├── project_state.py # Project status snapshot
│       ├── python_dev.py   # uv, pytest, ruff
│       └── web.py          # Web search/extraction
├── product-repo/           # Cloned product repo (agents work here)
└── pyproject.toml
```

## Tuning Guide

See the [Detailed Tuning Guide](docs/guide.en.md) for customization instructions.

Key tuning points:
- **Prompt modification**: `app/prompts/*.py` — change agent behavior instructions
- **Tool assignment**: `app/agents.py` — adjust which tools each agent can use
- **Model change**: `AGENT_MODEL` in `.env` — use a different Ollama model
- **Add/remove agents**: `config.py` + `app/agents.py` + `app/prompts/`

## Working with Claude Code / Codex

This project includes a `CLAUDE.md` file with full project context,
so Claude Code or Codex can immediately understand and work on the project.

```bash
# Open project with Claude Code
cd tiny-jarvis
claude

# Example requests:
# "Add error handling guidelines to the Backend agent prompt"
# "Add a new DevOps agent"
# "Add coverage options to the run_pytest tool"
```

See the [Tuning Guide](docs/guide.en.md) for details.

## License

This project was created for educational and research purposes.

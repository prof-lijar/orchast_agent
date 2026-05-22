# Tiny Jarvis

Autonomous AI dev team (4 agents) that builds a personal Telegram scheduling agent.
PM plans work, Architect designs and merges, Backend codes, QA reviews.

## Priorities

**Security > Speed > Performance.** Every change must respect this order.

## Architecture

```
Orchestrator (run.py)
├── PM Agent → plans work, creates issues, writes work_plan.json
├── Architect Agent → designs system, initializes project, merges PRs
├── Backend Agent → implements Python modules (the primary coder)
└── QA Agent → reviews PRs, runs tests, labels approval
```

Agents coordinate via GitHub issues and PRs on a separate product repository.
Each cycle: PM plans → agents execute → flush & push → repeat.

## Project Structure

```
tiny-jarvis/
├── run.py                      # Main orchestration loop
├── config.py                   # Centralized config (model, repo, timeouts)
├── app/
│   ├── agents.py               # Agent definitions with tool/prompt assignments
│   ├── prompts/
│   │   ├── pm.py               # PM: work planning, issue creation
│   │   ├── architect.py        # Architect: design, init, merge
│   │   ├── backend.py          # Backend: Python module implementation
│   │   └── qa.py               # QA: code review, testing
│   └── tools/
│       ├── files.py            # Read/write/search files in product repo
│       ├── git.py              # Branch, commit, merge, conflict resolution
│       ├── github.py           # Issues, PRs, labels via gh CLI
│       ├── project_state.py    # Aggregated project status snapshot
│       ├── web.py              # DuckDuckGo search + trafilatura extraction
│       └── python_dev.py       # uv, pytest, ruff (replaces nextjs.py)
├── pyproject.toml
├── .env.example
└── .gitignore
```

## Commands

| Command | Purpose |
|---------|---------|
| `uv run python run.py` | Start the autonomous agent team |
| `uv run pytest tests/ -v` | Run tests |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PRODUCT_REPO` | GitHub repo slug for the product | `user/tiny-jarvis-product` |
| `PRODUCT_REPO_DIR` | Local path to cloned product repo | `./product-repo` |
| `DEFAULT_BRANCH` | Default branch name | `main` |
| `AGENT_MODEL` | Ollama model name | `gemma4:31b` |
| `CYCLE_INTERVAL` | Seconds between cycles | `0` |
| `AGENT_TIMEOUT` | Max seconds per agent turn | `1800` |
| `NUM_CTX` | Context window size | `32768` |

## The Product Being Built

The agents build **Tiny Jarvis** — a local personal AI agent:
- Natural language → local Gemma parser → validated JSON
- SQLite scheduled task storage
- APScheduler background worker
- Telethon sends Telegram messages
- Full logging and status tracking

Tech: Python, Pydantic, SQLite, APScheduler, Telethon, Ollama, python-dotenv

## Agent Workflow

1. **PM** runs first every cycle: observes state, creates issues, writes `work_plan.json`
2. **work_plan.json** controls which agents run and for how many turns
3. Agents pick up issues labeled `role:X`, do work, create PRs
4. **QA** reviews PRs, labels `qa:approved` or `qa:changes-requested`
5. **Architect** merges approved PRs, cleans branches
6. Uncommitted changes auto-flushed after each agent turn

## Safety Rules

- Product must not support mass/bulk messaging
- Product must add random delay before Telegram sends
- Product must require user confirmation before scheduling
- Product must never log Telegram API hash
- Tests must never send real Telegram messages or call real LLM
- Parameterized SQL only in all database operations

## Operational Rules

- **Run Python with `uv`**: `uv run python script.py`, `uv run pytest`
- **Code preservation**: Only modify code directly targeted by the request
- **NEVER change the model** unless explicitly asked
- **Stop on repeated errors**: Fix root cause after 3+ occurrences
- **No unnecessary abstractions**: Keep modules simple and testable
- **No comments unless WHY is non-obvious**
- **Do not add Co-Authored-By** lines to commit messages

## Skills Reference

When working on this project, the following Claude Code skills are available:

- `/google-agents-cli-workflow` — Full ADK development lifecycle
- `/google-agents-cli-adk-code` — ADK Python API patterns and code examples
- `/google-agents-cli-scaffold` — Project scaffolding and enhancement
- `/google-agents-cli-eval` — Evaluation methodology and evalsets
- `/google-agents-cli-deploy` — Deployment workflows (not needed for local)
- `/google-agents-cli-observability` — Tracing and monitoring
- `/google-agents-cli-publish` — Publishing agents

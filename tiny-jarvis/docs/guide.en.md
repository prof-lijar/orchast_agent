# Tiny Jarvis Detailed Tuning Guide

> [한국어 버전](guide.ko.md)

This document explains how the Tiny Jarvis multi-agent system works
and how to customize agent behavior.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Cycle Execution Flow](#2-cycle-execution-flow)
3. [File Structure Map](#3-file-structure-map)
4. [Agent Prompt Tuning](#4-agent-prompt-tuning)
5. [Tool Modification](#5-tool-modification)
6. [Adding/Removing Agents](#6-addingremoving-agents)
7. [Changing the Model](#7-changing-the-model)
8. [Environment Variable Reference](#8-environment-variable-reference)
9. [Using Claude Code / Codex](#9-using-claude-code--codex)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Architecture

### Core Concept

Tiny Jarvis is an **agent orchestration system**.
Instead of writing code yourself, AI agents operate like a real software development team.

```
┌──────────────────────────────────────────────────────┐
│                    run.py (Orchestrator)              │
│                                                      │
│  1. Check Ollama status                              │
│  2. Clone product repository                         │
│  3. Create GitHub labels                             │
│  4. Create bootstrap issue (first run only)          │
│  5. Start cycle loop:                                │
│     ┌─────────────────────────────────────────┐      │
│     │  Run PM Agent (planning)                │      │
│     │       ↓                                 │      │
│     │  Read work_plan.json                    │      │
│     │       ↓                                 │      │
│     │  Run assigned agents sequentially       │      │
│     │  (Architect → Backend → QA etc.)        │      │
│     │       ↓                                 │      │
│     │  Auto-push uncommitted changes          │      │
│     └─────────────────────────────────────────┘      │
│     → Repeat next cycle                              │
└──────────────────────────────────────────────────────┘
```

### Data Flow

```
Agent → Google ADK Runner → LiteLLM → Ollama → Local Gemma Model
  ↕                                                    ↕
Tool calls (functions)                           Response text
  ↕
GitHub (Issues/PRs)  ←→  Product Repo (files/commits)
```

### Key Components

| Component | File | Role |
|-----------|------|------|
| Orchestrator | `run.py` | Cycle loop, agent turn management, graceful shutdown |
| Configuration | `config.py` | Model, repo, timeout settings |
| Agent Definitions | `app/agents.py` | Each agent's model, prompt, tool assignments |
| Prompts | `app/prompts/*.py` | Per-agent behavior instructions (system prompts) |
| Tools | `app/tools/*.py` | Functions agents can call |

---

## 2. Cycle Execution Flow

### Detailed Flow of One Cycle

```
Cycle N Start
│
├─ Step 1: Checkout main branch + pull
│
├─ Step 2: Run PM Agent
│   ├─ Call get_project_status() → observe current state
│   ├─ Call list_open_issues() → check unresolved issues per role
│   ├─ Create new issues if needed (create_issue)
│   ├─ Write work_plan.json (write_file)
│   ├─ Update docs/progress.md
│   └─ git_commit_and_push
│
├─ Step 3: Parse work_plan.json
│   └─ e.g., [{"role":"backend","turns":3}, {"role":"qa","turns":1}]
│
├─ Step 4: Run assigned agents sequentially
│   ├─ Backend Turn 1/3:
│   │   ├─ Checkout main + pull
│   │   ├─ list_open_issues(label='role:backend') → find work
│   │   ├─ Write code, commit, create PR
│   │   └─ flush_and_push (auto-push uncommitted changes)
│   ├─ Backend Turn 2/3: ...
│   ├─ Backend Turn 3/3: ...
│   └─ QA Turn 1/1:
│       ├─ list_pull_requests → check open PRs
│       ├─ Switch to PR branch, review code
│       ├─ Run run_pytest, run_ruff
│       └─ Add qa:approved or qa:changes-requested label
│
└─ Cycle N End → Wait → Cycle N+1
```

### Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| Tool call limit | Max 30 tool calls per agent turn |
| Idle loop detection | 2 consecutive text-only responses → end turn |
| Token leakage detection | Control tokens like `<\|im_start\|>` → end turn |
| Timeout | Default 1800 seconds (30 min) per agent |
| Graceful shutdown | Ctrl+C once → stop after current turn, twice → force quit |

---

## 3. File Structure Map

```
tiny-jarvis/
│
├── run.py                          ← Modify: cycle logic, bootstrap issue
├── config.py                       ← Modify: defaults, role list
├── .env                            ← Modify: runtime settings (model, repo)
├── .env.example                    ← Reference: .env template
├── pyproject.toml                  ← Modify: add/remove dependencies
├── CLAUDE.md                       ← Modify: AI assistant context
│
├── app/
│   ├── agents.py                   ← ★ Core: agent definitions + tool mapping
│   │
│   ├── prompts/                    ← ★ Tuning point: change agent behavior
│   │   ├── pm.py                   ← PM prompt (work planning logic)
│   │   ├── architect.py            ← Architect prompt (design/merge rules)
│   │   ├── backend.py              ← Backend prompt (coding guidelines)
│   │   └── qa.py                   ← QA prompt (review criteria)
│   │
│   └── tools/                      ← Tool implementations (functions)
│       ├── files.py                ← File read/write/search
│       ├── git.py                  ← Git branch/commit/merge/conflict resolution
│       ├── github.py               ← GitHub issues/PRs (gh CLI wrapper)
│       ├── project_state.py        ← Aggregated project status snapshot
│       ├── python_dev.py           ← Python dev tools (uv, pytest, ruff)
│       └── web.py                  ← Web search (DuckDuckGo) + content extraction
│
├── product-repo/                   ← Product repo where agents work (auto-cloned)
├── docs/                           ← This guide
└── tests/                          ← Tests for the agent system itself
```

### Which Files Should I Modify?

| Goal | Files to Modify |
|------|----------------|
| Change agent behavior | `app/prompts/*.py` |
| Add/remove tools from an agent | `app/agents.py` |
| Create a new tool function | `app/tools/newfile.py` + import in `app/agents.py` |
| Add a new agent role | `config.py` + `app/prompts/newrole.py` + `app/agents.py` |
| Change LLM model | `AGENT_MODEL` in `.env` |
| Adjust timeout/cycle interval | `AGENT_TIMEOUT`, `CYCLE_INTERVAL` in `.env` |
| Change product repository | `PRODUCT_REPO`, `PRODUCT_REPO_DIR` in `.env` |
| Modify bootstrap issue | `bootstrap_repo()` function in `run.py` |

---

## 4. Agent Prompt Tuning

Prompts are the agent's **brain**. They determine behavior, priorities, and workflow.

### File Location

```
app/prompts/
├── pm.py           # PM_INSTRUCTION variable
├── architect.py    # ARCHITECT_INSTRUCTION variable
├── backend.py      # BACKEND_INSTRUCTION variable
└── qa.py           # QA_INSTRUCTION variable
```

### Prompt Structure

Each prompt follows the same pattern:

```python
# app/prompts/backend.py
BACKEND_INSTRUCTION = """\
You are the Backend Developer of tiny-jarvis — an autonomous AI software engineering team.

IDENTITY:
- Role: Backend Developer
- Tag: [Backend]
...

CYCLE WORKFLOW (follow these steps IN ORDER):
1. CHECK FOR REJECTED PRs ...
2. CHECK YOUR ISSUES ...
3. FOR EACH ISSUE — STANDARD WORKFLOW: ...

CODING STANDARDS:
...

RULES:
...
"""
```

### Prompt Modification Examples

**Example 1: Add coding guidelines to Backend agent**

```python
# In CODING STANDARDS section of app/prompts/backend.py:

CODING STANDARDS:
- Write REAL working code. No stubs, no "pass", no "TODO".
- Type hints on all function signatures.
+ - Use async/await for all I/O-bound operations.
+ - All database functions must be wrapped in try/except with specific exceptions.
```

**Example 2: Change PM's work allocation strategy**

```python
# Modify TURN ALLOCATION GUIDELINES in app/prompts/pm.py:

TURN ALLOCATION GUIDELINES:
- Backend implementing Python modules → 3-4 turns
+ - Backend implementing Python modules → 4-5 turns (increase for complex modules)
- QA reviewing PRs and running tests → 1-2 turns
+ - QA reviewing PRs and running tests → 2-3 turns (more thorough reviews)
```

### Prompt Writing Tips

1. **Be specific**: "Write good code" → "Add type hints to all function signatures"
2. **Specify order**: "Follow these steps IN ORDER" + numbering
3. **State prohibitions**: "NEVER ..." format for constraints
4. **Use exact label names**: `role:backend` (correct) vs `backend` (wrong)
5. **Specify tool calls**: "call `function_name`" to tell agents which tools to use

---

## 5. Tool Modification

### What Are Tools?

Tools are **Python functions** that agents can call.
When an agent decides "I need to read a file," it calls `read_file("main.py")`.

### Modifying Existing Tools

**Example: Add coverage option to `run_pytest`**

```python
# app/tools/python_dev.py

def run_pytest(args: str = "tests/ -v", coverage: bool = False) -> str:
    """Run pytest in the product repository via uv.

    Args:
        args: Arguments to pass to pytest (default: 'tests/ -v').
        coverage: If True, add --cov flag for coverage report.
    """
    cmd = ["uv", "run", "pytest"] + args.split()
    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])
    # ... rest stays the same
```

### Creating New Tools

**Step 1: Write the tool function**

```python
# app/tools/docker.py (new file)
"""Docker tools — container build/run"""
from __future__ import annotations

import json
import subprocess

from config import Config

_config = Config.from_env()
_CWD = str(_config.product_repo_dir)


def docker_build(tag: str = "tiny-jarvis:latest") -> str:
    """Build a Docker image for the product.

    Args:
        tag: Docker image tag. Default 'tiny-jarvis:latest'.

    Returns:
        JSON string with build output.
    """
    try:
        result = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            cwd=_CWD, capture_output=True, text=True, timeout=300,
        )
        return json.dumps({
            "success": result.returncode == 0,
            "stdout": result.stdout.strip()[:3000],
            "stderr": result.stderr.strip()[:1000],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

**Step 2: Import and assign in `app/agents.py`**

```python
# Add to app/agents.py:

from app.tools.docker import docker_build  # noqa: E402

# Add to the desired agent's tools list:
backend_agent = Agent(
    ...
    tools=[
        *_shared_tools,
        # ... existing tools ...
        docker_build,  # ← new tool added
    ],
)
```

### Tool Design Rules

1. **Always return JSON strings**: `json.dumps({"success": True/False, ...})`
2. **Docstrings required**: Google ADK passes docstrings to the LLM as tool descriptions
3. **Type hints required**: Parameter types must be specified for ADK to pass correctly
4. **Set timeouts**: Always set timeout for subprocess calls
5. **Handle errors**: Return `{"success": False, "error": "..."}` on exceptions

---

## 6. Adding/Removing Agents

### Adding a New Agent (Example: DevOps)

**Step 1: Add role to config.py**

```python
# config.py
agent_roles: tuple[str, ...] = (
    "pm", "architect", "backend", "qa", "devops",  # ← added
)

role_labels: dict[str, str] = field(default_factory=lambda: {
    ...
    "devops": "role:devops",  # ← added
})
```

**Step 2: Create prompt file**

```python
# app/prompts/devops.py
DEVOPS_INSTRUCTION = """\
You are the DevOps Engineer of tiny-jarvis...

IDENTITY:
- Role: DevOps Engineer
- Tag: [DevOps]
...
"""
```

**Step 3: Register agent in agents.py**

```python
# app/agents.py

from app.prompts.devops import DEVOPS_INSTRUCTION

devops_agent = Agent(
    name="devops_agent",
    model=_model,
    instruction=DEVOPS_INSTRUCTION,
    tools=[*_shared_tools, close_issue, write_file, ...],
)

AGENTS = {
    ...
    "devops": devops_agent,  # ← added
}
```

**Step 4: Update PM prompt to recognize the new role**

Add `role:devops` to the valid label list in `app/prompts/pm.py`.

### Removing an Agent

Reverse the above process:
1. Remove from `AGENTS` dictionary
2. Remove from `config.py` (`agent_roles` and `role_labels`)
3. Optionally delete the prompt file

---

## 7. Changing the Model

### Changing the Ollama Model

```bash
# Edit .env
AGENT_MODEL=qwen3:32b    # or any other Ollama model

# Download the model
ollama pull qwen3:32b
```

### Supported Model Examples

| Model | Size | Notes |
|-------|------|-------|
| `gemma4:31b` | 31B | Default, balanced performance |
| `qwen3:32b` | 32B | Strong code generation |
| `llama3.3:70b` | 70B | High quality, slower speed |
| `gemma4:12b` | 12B | Fast speed, lower quality |

### Adjusting Context Window

```bash
# .env
NUM_CTX=32768    # default
NUM_CTX=65536    # longer context (more VRAM needed)
NUM_CTX=16384    # save memory
```

---

## 8. Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PRODUCT_REPO` | Yes | `user/tiny-jarvis-product` | GitHub repository slug |
| `PRODUCT_REPO_DIR` | Yes | `./product-repo` | Local path for product repo |
| `DEFAULT_BRANCH` | No | `main` | Default branch name |
| `AGENT_MODEL` | No | `gemma4:31b` | Ollama model name |
| `CYCLE_INTERVAL` | No | `0` | Wait time between cycles (seconds) |
| `AGENT_TIMEOUT` | No | `1800` | Agent turn timeout (seconds) |
| `NUM_CTX` | No | `32768` | LLM context window size |

---

## 9. Using Claude Code / Codex

This project includes a `CLAUDE.md` file that gives Claude Code or OpenAI Codex
instant understanding of the project structure and rules.

### Working with Claude Code

```bash
# Run Claude Code in the project directory
cd tiny-jarvis
claude
```

#### Useful Request Examples

**Modify prompts:**
```
"Add async/await pattern guidelines to the Backend agent's
coding standards section"
```

**Create new tools:**
```
"Create a db_query tool in app/tools/database.py that lets agents
query a SQLite database directly"
```

**Add new agents:**
```
"I want to add a Frontend agent. Set up config.py, agents.py,
and prompts/ for writing React components"
```

**Debugging:**
```
"The flush_and_push function in run.py doesn't seem to work
after agent turns end. Check and fix the code"
```

### Working with Codex

OpenAI Codex (or Codex CLI) works the same way.
Running from the project root leverages `CLAUDE.md` context.

### Customizing CLAUDE.md

`CLAUDE.md` is the file AI assistants use to understand the project.
Update it when the project changes:

```markdown
# Example additions:

## New Tools Added
- `app/tools/database.py` — SQLite direct query tool

## Changed Rules
- Backend agent must use async/await patterns
```

---

## 10. Troubleshooting

### Common Issues

**Problem: "Cannot reach Ollama"**
```
Solution: Ensure ollama serve is running
          In a separate terminal: ollama serve
```

**Problem: "Failed to clone"**
```
Solution: Check GitHub auth with: gh auth status
          Verify repo exists: gh repo view PRODUCT_REPO
```

**Problem: Agent can't find issues**
```
Solution: Verify labels are correctly created on GitHub
          role:backend (correct) vs role: backend (wrong) vs backend (wrong)
          Re-running run.py will auto-create labels
```

**Problem: Agent stuck in infinite loop**
```
Solution: The 30 tool call limit + idle loop detection auto-terminates turns.
          If still stuck, press Ctrl+C to stop.
```

**Problem: PermissionError: '/product/...'**
```
Solution: Change PRODUCT_REPO_DIR in .env to a writable absolute path
          e.g., /home/user/tiny-jarvis/product-repo
```

**Problem: Agent writes poor code**
```
Solution:
1. Use a larger model: AGENT_MODEL=qwen3:32b or llama3.3:70b
2. Increase context window: NUM_CTX=65536
3. Add more specific coding guidelines to prompts
4. Increase Backend agent turns (adjust turns in work_plan.json)
```

### Reading Logs

```
16:20:11 [INFO] --- Cycle 1 | PM (planning) ---       ← PM turn starts
16:20:15 [INFO] [PM] 🔧 get_project_status()          ← Tool call
16:20:16 [INFO] [PM] ← get_project_status: {"open...  ← Tool response
16:20:20 [INFO] [PM] 🔧 create_issue({"title":"..."}) ← Issue creation
16:21:00 [INFO] [PM] Done in 49.2s                     ← PM turn ends
16:21:00 [INFO] Work plan: backendx3, qax1 (4 total)  ← Work plan loaded
16:21:01 [INFO] --- Cycle 1 | BACKEND (turn 1/3) ---   ← Backend starts
```

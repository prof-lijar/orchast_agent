# ADK Tutorial & Debug Agent

An AI agent built with [Google ADK](https://adk.dev/) that teaches developers how to build
AI agents step by step and diagnoses terminal errors on the spot.

## What It Does

**Tutorial Mode** — walks you through the full ADK development lifecycle:
- Installing uv, agents-cli, and gcloud
- Authenticating with GCP
- Scaffolding a new agent project
- Writing agent code, tools, and instructions
- Running locally with `agents-cli run` and `agents-cli playground`
- Writing and running evaluations
- Deploying to Agent Runtime, Cloud Run, or GKE
- Using Codex CLI to write and fix agent code alongside ADK

**Debug Mode** — paste any terminal output and the agent will:
- Identify the error type (ImportError, AuthError, 403, 404, etc.)
- Explain the root cause in plain language
- Give you one specific, copy-paste-ready fix
- Tell you exactly what command to run to verify

## Quick Start

**Prerequisites:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install agents-cli
uv tool install google-agents-cli

# Authenticate with GCP
gcloud auth application-default login
```

**Install dependencies:**
```bash
cd tutorial-debug-agent
agents-cli install
```

**Run a single prompt:**
```bash
# Tutorial example
agents-cli run "How do I create my first ADK agent?"

# Debug example — paste your error
agents-cli run "I'm getting: ModuleNotFoundError: No module named 'google.adk'"

# Ask about Codex CLI
agents-cli run "How do I use Codex CLI to write my agent tools?"
```

**Interactive playground (browser UI):**
```bash
agents-cli playground
# Opens at http://localhost:8000
```

## Project Structure

```
tutorial-debug-agent/
├── app/
│   ├── __init__.py             # App registration
│   ├── agent.py                # Root agent — instruction, tools, model
│   └── app_utils/              # Telemetry and typing helpers
├── tests/
│   └── eval/
│       ├── eval_config.json    # Eval rubrics and thresholds
│       └── evalsets/
│           └── basic.evalset.json  # 9 tutorial + debug eval cases
├── pyproject.toml              # Dependencies and agents-cli config
└── README.md
```

## Running Evaluations

```bash
agents-cli eval run
```

Covers 9 cases: greeting, install tutorial, scaffold tutorial, add-tool tutorial,
`ModuleNotFoundError` debug, auth error debug, model 404 debug, Codex CLI tutorial,
and full workflow walkthrough.

## Example Conversations

**Tutorial:**
```
User: I want to build my first AI agent from scratch. Walk me through it.
Agent: Let's start from the beginning. First, let's make sure you have the
       prerequisites installed...
       [calls get_tutorial_step("install"), then guides through each step]
```

**Debug:**
```
User: agents-cli run fails with DefaultCredentialsError
Agent: [calls analyze_terminal_error(...)]
       Root cause: No GCP credentials found in your environment.
       Fix: Run `gcloud auth application-default login`
       Verify: Run `agents-cli login --status`
```

## Tools

| Tool | Purpose |
|------|---------|
| `analyze_terminal_error` | Parses terminal output → returns error type, root cause, fix |
| `get_tutorial_step` | Returns step-by-step instructions for a given ADK topic |

**Supported tutorial topics:** `install`, `auth`, `scaffold`, `build-agent`, `add-tool`,
`run-locally`, `eval`, `deploy`, `codex-cli`, `multi-agent`

**Supported error types:** `ImportError`, `AuthenticationError`, `PermissionDenied`,
`ModelNotFound`, `ResourceConflict`, `CLINotFound`, `AppNameMismatch`, `SyntaxError`,
`NetworkError`, `UvNotFound`

## Development Commands

| Command | Description |
|---------|-------------|
| `agents-cli install` | Install Python dependencies |
| `agents-cli run "prompt"` | Run agent with a single prompt |
| `agents-cli playground` | Interactive browser playground at localhost:8000 |
| `agents-cli eval run` | Run all evaluation cases |
| `agents-cli lint` | Check code quality |
| `agents-cli lint --fix` | Auto-fix formatting |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |

## Deploying (Optional)

```bash
# Add a deployment target when ready
agents-cli scaffold enhance . --deployment-target agent_runtime
# Options: agent_runtime | cloud_run | gke

# Deploy (requires explicit approval)
agents-cli deploy
```

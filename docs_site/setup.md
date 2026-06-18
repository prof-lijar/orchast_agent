# Getting Started

This guide will help you set up your environment and get your first AI agent from the `orchast_agent` monorepo running locally.

## Prerequisites

Before you begin, ensure you have the following tools installed on your system:

| Requirement | Version/Link | Installation Command / Note |
| :--- | :--- | :--- |
| **Python** | 3.11+ | [python.org](https://www.python.org/) |
| **uv** | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Google Cloud SDK** | Latest | [Install gcloud CLI](https://cloud.google.com/sdk/docs/install) |
| **Ollama** | Latest | [ollama.com](https://ollama.com/) (Required for local agents) |
| **Agents-CLI** | Latest | `uv tool install google-agents-cli` |

## Quick Start Steps

### 1. Authentication
If you plan to use Gemini (Cloud LLMs), you must authenticate your Google Cloud environment:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Choose Your Agent
Navigate into the directory of the agent you wish to run. For example, to try the **Self-Evolving Agent**:

```bash
cd self-evolving-agent
```

### 3. Install and Run
The `uv` package manager is used across this monorepo for fast, reproducible environments.

```bash
# Sync dependencies
uv sync

# Start the agent (e.g., opening the playground UI)
agents-cli playground
```
*The browser UI will typically be available at `http://localhost:8000`.*

## Local Development Workflow
Each agent is independent. To contribute or modify an agent:
1. Enter the agent's specific directory.
2. Review its local `README.md` for agent-specific configurations.
3. Use `uv run <script>.py` to execute logic directly.

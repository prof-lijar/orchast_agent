**[한국어](README.ko.md)**

# Orchast Agent

A monorepo of purpose-built AI agents. Each agent lives in its own directory with independent dependencies, deployment, and documentation. Built primarily with [Google ADK](https://adk.dev/) and powered by Gemini and local LLMs.

<img width="1254" height="1254" alt="Orchast Agent" src="https://github.com/user-attachments/assets/f7f090c3-6d47-4e09-b1f4-b3afcf57fdc1" />

## Agents

| Agent | Description | Models |
|-------|-------------|--------|
| [self-evolving-agent](./self-evolving-agent/) | Designs, generates, tests, and registers its own tools at runtime. Includes a desktop GUI (Zig + Svelte). | Gemini Flash, Ollama |
| [book-writer](./book-writer/) | Writes entire books overnight from a table of contents, committing chapters to GitHub as it goes. | Ollama (local) |
| [course-generator](./course-generator/) | Produces complete multilingual course packages — lectures, assignments, and assessments — from a topic description. | Gemini Flash |
| [caveman-compressor](./caveman-compressor/) | Compresses verbose text into terse, technical caveman-style grunts. | Gemini Flash |
| [tutorial-debug-agent](./tutorial-debug-agent/) | Step-by-step ADK tutorials and paste-your-error terminal debugging. | Gemini Flash |

## Quick Start

```bash
# Prerequisites: uv, gcloud CLI

# 1. Authenticate
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 2. Pick an agent
cd self-evolving-agent  # or any agent directory

# 3. Install and run
uv sync
agents-cli playground   # browser UI at localhost:8000
```

Each agent's README has specific setup instructions and usage details.

## Repo Structure

```
orchast_agent/
├── self-evolving-agent/   # Tool-creating agent + desktop app
├── book-writer/           # Overnight book generation via Ollama
├── course-generator/      # Multi-agent course pipeline
├── caveman-compressor/    # Text compression agent
├── tutorial-debug-agent/  # ADK tutorial & error debugger
└── assets/                # Shared images
```

## Prerequisites

| Tool | Install |
|------|---------|
| [uv](https://docs.astral.sh/uv/) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [google-agents-cli](https://pypi.org/project/google-agents-cli/) | `uv tool install google-agents-cli` |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | See link |

## References

- [Google ADK](https://adk.dev/)
- [google-agents-cli](https://pypi.org/project/google-agents-cli/)
- [ADK GitHub](https://github.com/google/adk-python)

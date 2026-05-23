# Book Writer Agent

An AI agent that writes entire books overnight using locally-running LLM models via [Ollama](https://ollama.com/). Give it a table of contents, start it before bed, and wake up to a finished book committed to GitHub chapter by chapter.

Built with [Google ADK](https://github.com/google/adk-python) (Agent Development Kit).

---

## How It Works

For each chapter in your table of contents, a **4-phase sequential pipeline** runs:

```
Table of Contents (JSON / YAML / text)
          ↓
    ┌─────────────────────────────────────────┐
    │  For each chapter:                      │
    │                                         │
    │  1. Outline Agent                       │
    │     → Detailed section-by-section plan  │
    │                                         │
    │  2. Writer Agent                        │
    │     → Full chapter draft (--words)      │
    │                                         │
    │  3. Reviewer Agent                      │
    │     → Revised draft with improvements   │
    │                                         │
    │  4. Finalizer Agent                     │
    │     → Polished final Markdown           │
    │                                         │
    │  → Save chapter-XX.md                   │
    │  → git commit + push                    │
    └─────────────────────────────────────────┘
```

Each chapter runs in a **fresh ADK session** to prevent context overflow across long books (20+ chapters). Progress is tracked in `.progress.json`, so you can resume after interruptions.

---

## Architecture

### Agents

The system uses **4 ADK agents** chained in a `SequentialAgent` pipeline:

| Agent | Role | Output Key |
|-------|------|------------|
| **Outline Agent** | Creates a detailed hierarchical outline with sections, key points, and transition notes | `chapter_outline` |
| **Writer Agent** | Writes the full chapter as polished prose following the outline | `chapter_draft` |
| **Reviewer Agent** | Reviews and improves the draft for clarity, flow, completeness, and consistency | `chapter_review` |
| **Finalizer Agent** | Produces the final polished chapter with clean Markdown formatting | `chapter_final` |

Data flows through ADK session state via `output_key` → `{placeholder}` syntax:

```
outline_agent (output_key="chapter_outline")
       ↓
writer_agent → reads {chapter_outline}
       ↓ (output_key="chapter_draft")
reviewer_agent → reads {chapter_outline}, {chapter_draft}
       ↓ (output_key="chapter_review")
finalizer_agent → reads {chapter_outline}, {chapter_draft}, {chapter_review}
       ↓ (output_key="chapter_final")
```

### Runner

The overnight runner (`run_book.py`) drives the pipeline programmatically rather than using ADK's `LoopAgent`, because it needs:

- Per-chapter state injection (chapter number, title, description)
- Fresh sessions per chapter (preventing context overflow)
- Progress persistence to disk (surviving crashes)
- Per-chapter retry with configurable attempts
- Git commit/push after each chapter

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/download) installed and running
- An Ollama model pulled (e.g. `ollama pull gemma4:31b`, `ollama pull qwen3.5:0.8b`)

### Install

```bash
cd book-writer
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
cd book-writer
uv sync
```

---

## Usage

### 1. Create a Table of Contents

**JSON** (recommended):

```json
{
  "title": "Mastering Python",
  "description": "A comprehensive guide to Python programming",
  "chapters": [
    {
      "number": 1,
      "title": "The Python Philosophy",
      "description": "History of Python, the Zen of Python, and why design choices matter"
    },
    {
      "number": 2,
      "title": "Advanced Data Structures",
      "description": "Deques, namedtuples, defaultdict, Counter, and when to use each"
    },
    {
      "number": 3,
      "title": "Decorators and Metaclasses",
      "description": "Function decorators, class decorators, and the metaclass protocol"
    }
  ]
}
```

**YAML**:

```yaml
title: Mastering Python
description: A comprehensive guide to Python programming
chapters:
  - number: 1
    title: The Python Philosophy
    description: History and design choices
  - number: 2
    title: Advanced Data Structures
    description: Beyond lists and dicts
```

**Plain text**:

```
# Mastering Python
A comprehensive guide to Python programming

1. The Python Philosophy - History and design choices
2. Advanced Data Structures - Beyond lists and dicts
3. Decorators and Metaclasses - The metaclass protocol
```

### 2. Run the Agent

**Basic run** (writes to `./book/`):

```bash
python run_book.py --toc my-book-toc.json --model gemma4:31b
```

**From a GitHub URL** (auto-clones the repo):

```bash
python run_book.py --toc https://github.com/user/repo/blob/main/my-book/toc.json --model gemma4:31b
```

**Push to GitHub as chapters complete**:

```bash
python run_book.py --toc my-book-toc.json --model gemma4:31b --repo https://github.com/user/my-book.git
```

**Custom output directory and branch**:

```bash
python run_book.py --toc my-book-toc.json --model gemma4:31b --output-dir ./my-book --branch draft
```

**Resume after interruption**:

```bash
python run_book.py --toc my-book-toc.json --model gemma4:31b --resume
```

**Local only (no git push)**:

```bash
python run_book.py --toc my-book-toc.json --model gemma4:31b --no-push
```

### 3. Interactive Mode (ADK Playground)

For testing individual chapters interactively:

```bash
agents-cli playground --port 8080
```

Open `http://localhost:8080` and select the `app` agent.

---

## CLI Reference

```
python run_book.py --toc TOC --model MODEL [options]

Required:
  --toc TOC              Path or GitHub URL to table of contents file (JSON, YAML, or text)
  --model MODEL          Ollama model name (e.g. gemma4:31b, qwen3.5:0.8b)

Options:
  --output-dir DIR       Output directory (default: ./book, auto-detected from GitHub URL)
  --branch BRANCH        Git branch name (default: main, auto-detected from GitHub URL)
  --repo URL             Git remote repository URL (auto-detected from GitHub URL)
  --clone-dir DIR        Base directory for cloned repos (default: ./repos)
  --retry N              Retries per chapter on failure (default: 3)
  --words RANGE          Target word count per chapter (default: 3000-5000)
  --timeout SECONDS      Timeout per chapter in seconds (default: 1800)
  --stream               Stream LLM output to console in real-time
  --no-think             Disable model thinking (recommended for qwen3 models)
  --num-ctx N            Context window size (default: 32768, use 4096-8192 for small models)
  --repeat-penalty N     Repetition penalty (default: 1.2, use 1.5+ for small models)
  --resume               Resume from .progress.json (skip completed chapters)
  --no-push              Skip git operations (save files only)
```

---

## Output

Each chapter is saved as a Markdown file with YAML front matter:

```
book/
├── chapter-01-the-python-philosophy.md
├── chapter-02-advanced-data-structures.md
├── chapter-03-decorators-and-metaclasses.md
├── .progress.json
└── book-writer.log
```

Chapter file format:

```markdown
---
chapter: 1
title: "The Python Philosophy"
generated_at: "2026-05-19T22:15:00+00:00"
---

# Chapter 1: The Python Philosophy

## The Birth of Python
...
```

---

## Robustness

The agent is designed for overnight unattended operation:

| Feature | Detail |
|---------|--------|
| **Fresh sessions** | Each chapter gets its own ADK session — no context overflow across 20+ chapters |
| **Retry logic** | Failed chapters retry up to N times (default 3) with a fresh session each attempt |
| **Skip on failure** | After exhausting retries, the failed chapter is logged and skipped — remaining chapters continue |
| **Resume** | `.progress.json` tracks completed/failed chapters; `--resume` picks up where you left off |
| **Timeout** | 30-minute default timeout per chapter prevents infinite hangs |
| **Git tolerance** | Push failures don't block progress — chapters are saved locally regardless |
| **Ollama health check** | Verifies Ollama is running and the model is loaded before starting |
| **Logging** | All activity logged to `book-writer.log` with timestamps |

---

## Model Configuration

Specify the model with the required `--model` flag. Any model available in your local Ollama instance will work.

The agent connects to Ollama through its OpenAI-compatible endpoint using ADK's `LiteLlm` wrapper:

```python
LiteLlm(
    model="openai/gemma4:31b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",
    num_ctx=32768,
    repeat_penalty=1.2,
    temperature=0.7,
)
```

### Tested Models

| Model | Quality | Speed | Notes |
|-------|---------|-------|-------|
| **gemma4:31b** | High | ~5-15 min/chapter | Recommended for GPU servers |
| **gemma4:27b** | Good | Faster | Good balance |
| **gemma3:27b** | Good | Moderate | Also works well |
| **qwen3.5:0.8b** | Lighter | Fast | Good for low-resource devices (e.g. Raspberry Pi); use `--words 800-1500 --timeout 7200 --no-think --num-ctx 4096 --repeat-penalty 1.5` |

### Remote GPU Server

If Ollama runs on a remote machine, use SSH port forwarding:

```bash
# Forward Ollama port from GPU server
ssh -L 11434:localhost:11434 user@gpu-server

# Run the agent
python run_book.py --toc my-book-toc.json --model gemma4:31b
```

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ALLOW_ORIGINS` | CORS origins for FastAPI (comma-separated) | none |

---

## Project Structure

```
book-writer/
├── app/
│   ├── __init__.py              # App export
│   ├── agent.py                 # Model config, 4 sub-agents, SequentialAgent pipeline
│   ├── tools.py                 # TOC parsing, file saving, git ops, progress tracking
│   └── fast_api_app.py          # FastAPI wrapper + /api/progress endpoint
├── run_book.py                  # Overnight runner (main entry point)
├── sample-toc.json              # Example 2-chapter TOC
├── tests/
│   └── unit/
├── pyproject.toml
└── README.md
```

---

## Technology Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent framework (Agent, SequentialAgent, App, Runner)
- **[Ollama](https://ollama.com/)** — Local LLM inference server
- **Ollama models** — Any locally available model (Gemma, Qwen, Llama, etc.)
- **LiteLlm** — Model provider abstraction (connects ADK to Ollama's OpenAI-compatible API)
- **FastAPI** — Optional web interface for interactive use and progress monitoring

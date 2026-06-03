# SciePaperWriter

A multi-agent scientific paper writer that generates research papers from your source materials using locally-running LLM models via [Ollama](https://ollama.com/). Feed it your research notes, data, markdown files, or even a GitHub repo — and it produces a publication-ready academic paper.

Built with [Google ADK](https://github.com/google/adk-python) (Agent Development Kit).

---

## How It Works

Given a paper specification (title, sections, sources), a **5-phase sequential pipeline** runs:

```
Paper Spec (JSON / YAML) + Source Materials
                ↓
  ┌──────────────────────────────────────────────┐
  │                                              │
  │  1. Ingestion Agent                          │
  │     → Analyzes all sources, extracts key     │
  │       findings, methodology, data, gaps      │
  │                                              │
  │  2. Outline Agent                            │
  │     → Creates section-by-section outline     │
  │       with arguments, evidence, word counts  │
  │                                              │
  │  3. Writer Agent                             │
  │     → Writes the full paper as academic      │
  │       prose following the outline            │
  │                                              │
  │  4. Reviewer Agent                           │
  │     → Reviews for clarity, flow, rigor,      │
  │       completeness — outputs revised paper   │
  │                                              │
  │  5. Finalizer Agent                          │
  │     → Final polish, clean Markdown,          │
  │       consistent formatting                  │
  │                                              │
  │  → Save paper.md                             │
  │  → git commit + push                         │
  └──────────────────────────────────────────────┘
```

All configuration is passed via CLI arguments. The Ollama API endpoint (`http://localhost:11434`) is hardcoded — no `.env` files needed.

---

## Architecture

### Agents

The system uses **5 ADK agents** chained in a `SequentialAgent` pipeline (configurable via `--agents`):

| Agent | Role | Output Key |
|-------|------|------------|
| **Ingestion Agent** | Reads all source materials, extracts key findings, methodology, data, and gaps | `research_context` |
| **Outline Agent** | Creates a detailed section-by-section outline with target word counts | `paper_outline` |
| **Writer Agent** | Writes the full paper as publication-ready academic prose | `paper_draft` |
| **Reviewer Agent** | Reviews and improves clarity, flow, completeness, academic rigor | `paper_revised` |
| **Finalizer Agent** | Final formatting polish, clean Markdown, consistent headings | `paper_final` |

Data flows through ADK session state via `output_key` → `{placeholder}` syntax:

```
ingestion_agent (output_key="research_context")
       ↓
outline_agent → reads {research_context}
       ↓ (output_key="paper_outline")
writer_agent → reads {paper_outline}, {research_context}
       ↓ (output_key="paper_draft")
reviewer_agent → reads {paper_outline}, {paper_draft}
       ↓ (output_key="paper_revised")
finalizer_agent → reads {paper_revised}
       ↓ (output_key="paper_final")
```

### Source Collection

The ingestion agent receives all source materials pre-loaded into its prompt. The runner collects sources from:

- **Local files** — `.md`, `.txt`, `.rst`, `.tex`, `.csv`, `.json`, `.yaml`, `.py`, `.ipynb`, `.bib`
- **Local directories** — Recursively collects all supported files (skips `.git/`, `.venv/`, `__pycache__/`)
- **GitHub repos** — Clones the repo and collects files from the specified path

Files larger than 512 KB are skipped automatically.

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/download) installed and running
- An Ollama model pulled (e.g. `ollama pull gemma4:31b`)

### Install

```bash
cd scie_paper_writer
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
cd scie_paper_writer
uv sync
```

---

## Usage

### 1. Create a Paper Specification

**JSON** (recommended):

```json
{
  "title": "Self-Evolving Agents for Manufacturing AI",
  "description": "A framework for agents that autonomously design and register their own tools",
  "authors": ["Author Name", "Co-Author Name"],
  "structure": "generic",
  "sources": [
    "./research-notes/",
    "./data/experiment-results.md",
    "https://github.com/user/agent-framework"
  ],
  "target_word_count": "5000-8000",
  "language": "en",
  "writing_guidelines": [
    "Use formal academic tone",
    "Include quantitative results where available",
    "Cite relevant prior work in multi-agent systems"
  ]
}
```

**YAML**:

```yaml
title: Self-Evolving Agents for Manufacturing AI
description: A framework for agents that autonomously design and register their own tools
authors:
  - Author Name
  - Co-Author Name
structure: ieee
sources:
  - ./research-notes/
  - ./data/experiment-results.md
target_word_count: "6000-10000"
writing_guidelines:
  - Use formal academic tone
  - Include quantitative results where available
```

### Spec Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Paper title |
| `description` | No | Brief description of the paper's scope |
| `authors` | No | List of author names |
| `structure` | No | Built-in template name: `generic`, `ieee`, or `acm` (default: `generic`) |
| `sections` | No | Custom section list (overrides `structure`). Each section needs `name` and optional `description` |
| `sources` | No | List of source paths: local files, directories, or GitHub URLs |
| `target_word_count` | No | Target word count range (default: `"5000-8000"`) |
| `language` | No | ISO 639-1 language code (default: `"en"`) |
| `writing_guidelines` | No | List of style instructions injected into every agent's prompt |

### Built-in Structure Templates

**`generic`** (default) — Abstract, Introduction, Related Work, Methodology, Experiments, Discussion, Conclusion, References

**`ieee`** — Abstract, Introduction, Literature Review, System Model, Proposed Method, Experimental Results, Discussion, Conclusion, References

**`acm`** — Abstract, CCS Concepts and Keywords, Introduction, Background, Related Work, Design, Implementation, Evaluation, Discussion, Conclusion, References

Use `"sections"` in your spec to define a fully custom structure:

```json
{
  "title": "My Paper",
  "sections": [
    {"name": "Abstract", "description": "Brief summary"},
    {"name": "Introduction", "description": "Background and motivation"},
    {"name": "Our Approach", "description": "Novel method description"},
    {"name": "Results", "description": "Experimental evaluation"},
    {"name": "Conclusion", "description": "Summary and future work"}
  ]
}
```

### 2. Run the Agent

**Basic run:**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b
```

**With streaming output (see each agent's output in real-time):**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --stream
```

**From a GitHub-hosted spec:**

```bash
python run_paper.py --spec https://github.com/user/repo/blob/main/paper/spec.json --model gemma4:31b
```

**Custom output directory:**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --output-dir ./my-paper
```

**Skip ingestion (when sources are already summarized in the spec description):**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --agents outline,writer,reviewer,finalizer
```

**Draft only (skip review and finalization):**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --agents ingestion,outline,writer
```

**Resume after interruption:**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --resume
```

**Local only (no git push):**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --no-push
```

**Write in Korean:**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --lang ko
```

**Override word count:**

```bash
python run_paper.py --spec paper-spec.json --model gemma4:31b --words 8000-12000
```

**Small model with adjusted parameters:**

```bash
python run_paper.py --spec paper-spec.json --model qwen3.5:0.8b \
    --no-think --num-ctx 8192 --repeat-penalty 1.5 --words 2000-4000
```

### 3. Interactive Mode (ADK Playground)

For testing the pipeline interactively:

```bash
adk web
```

---

## CLI Reference

```
python run_paper.py --spec SPEC --model MODEL [options]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--spec SPEC` | Path or GitHub blob URL to the paper specification file (JSON or YAML) |
| `--model MODEL` | Ollama model name (e.g. `gemma4:31b`, `llama3:8b`, `qwen3.5:0.8b`) |

### Pipeline Control

| Argument | Default | Description |
|----------|---------|-------------|
| `--agents STAGES` | `ingestion,outline,writer,reviewer,finalizer` | Comma-separated pipeline stages to run. Use this to skip stages or run a partial pipeline |
| `--retry N` | `3` | Number of retry attempts on failure |
| `--timeout SECONDS` | `1800` | Timeout per agent in seconds. Total timeout = timeout x number of agents |
| `--resume` | off | Resume from `.progress.json`, skipping previously completed runs |

### Model Tuning

| Argument | Default | Description |
|----------|---------|-------------|
| `--num-ctx N` | `32768` | Context window size in tokens. Use `4096`–`8192` for small models |
| `--repeat-penalty N` | `1.2` | Repetition penalty. Use `1.5`+ for small models to reduce loops |
| `--no-think` | off | Disable model thinking/reasoning. Recommended for `qwen3` models |

### Output Control

| Argument | Default | Description |
|----------|---------|-------------|
| `--output-dir DIR` | `./paper` | Directory where the paper and logs are saved |
| `--words RANGE` | spec value or `5000-8000` | Target word count range (overrides spec) |
| `--lang CODE` | spec value or `en` | Language for the paper (ISO 639-1 code, overrides spec) |
| `--stream` | off | Stream each agent's output to the console in real-time |
| `--no-push` | off | Skip git commit and push |
| `--clone-dir DIR` | `./repos` | Base directory for cloned GitHub repos |

---

## Output

The paper is saved as a Markdown file with YAML front matter:

```
paper/
├── self-evolving-agents-a-framework-for-dynamic-tool.md
├── .progress.json
└── scie_paper_writer.log
```

Paper file format:

```markdown
---
title: "Self-Evolving Agents for Manufacturing AI"
generated_at: "2026-06-04T10:30:00+00:00"
---

# Self-Evolving Agents for Manufacturing AI

**Author Name, Co-Author Name**

## Abstract

This paper proposes a self-evolving agent architecture...

## Introduction
...
```

---

## Robustness

| Feature | Detail |
|---------|--------|
| **Retry logic** | Failed runs retry up to N times (default 3) with a fresh session each attempt |
| **Resume** | `.progress.json` tracks completion state; `--resume` picks up where you left off |
| **Timeout** | Configurable per-agent timeout prevents infinite hangs |
| **Git tolerance** | Push failures don't block progress — the paper is saved locally regardless |
| **Ollama health check** | Verifies Ollama is running and the model is loaded before starting |
| **Logging** | All activity logged to `scie_paper_writer.log` with timestamps |
| **Graceful fallback** | If the final agent fails, the runner retrieves the best available output from earlier stages |

---

## Project Structure

```
scie_paper_writer/
├── app/
│   ├── __init__.py         # App export
│   ├── agent.py            # 5 sub-agents, build_pipeline(), SequentialAgent
│   └── tools.py            # Source collection, spec parsing, structure templates,
│                           #   file saving, git ops, progress tracking
├── run_paper.py            # CLI runner (main entry point)
├── sample-spec.json        # Example paper specification
├── pyproject.toml
└── README.md
```

---

## Technology Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent framework (Agent, SequentialAgent, App, Runner)
- **[Ollama](https://ollama.com/)** — Local LLM inference server (hardcoded to `http://localhost:11434`)
- **LiteLlm** — Model provider abstraction (connects ADK to Ollama's OpenAI-compatible API)

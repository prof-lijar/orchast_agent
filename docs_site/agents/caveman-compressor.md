# Caveman Compressor

The **Caveman Compressor** is a specialized agent that transforms verbose, complex text into terse, "caveman-style" technical grunts, stripping away fluff while preserving core meaning. It supports both cloud LLMs (Gemini Flash) and local models via Ollama.

## Purpose
To provide extremely concise summaries of technical information, making it easier to scan and understand the "bottom line" without reading through professional prose.

## How it Works
The agent is a single-purpose LLM agent configured with specific system instructions to act as a technical caveman. It identifies the core technical entities and actions in a text and replaces everything else with minimal, grunt-like language.

## Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.
- `agents-cli` installed via `uv tool install google-agents-cli`.
- Google Cloud SDK configured for GCP services (for Gemini).
- [Ollama](https://ollama.com/) installed and running (for local models).

## Usage Example

### Setup
```bash
cd caveman-compressor
agents-cli install
```

### Running the Agent
Launch the local development environment:
```bash
agents-cli playground
```

**Example Input:**
> "The implementation of the distributed consensus algorithm utilizes a Raft-based approach to ensure that all nodes in the cluster maintain a consistent state across asynchronous network partitions."

**Example Output:**
> "Raft use. Nodes stay same. Network break, still work."

**To switch between Gemini and Ollama**, configure your environment variables or specify the model in the `agents-cli` configuration.

## Configuration Options
- **Model**: Configured via `agents-cli` and project environment settings (supports Gemini Flash and Ollama).
- **Logic**: The core compression logic is defined in `app/agent.py`.

## Output Format
- **Text Response**: A highly compressed string of text in the style of a technical caveman.

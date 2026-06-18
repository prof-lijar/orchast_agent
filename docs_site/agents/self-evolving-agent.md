# Self-Evolving Agent

The **Self-Evolving Agent** is an advanced AI system capable of autonomously extending its own capabilities. Unlike traditional agents that rely on a fixed set of tools, this agent can identify missing functionality, design new tools, generate the necessary Python code, and register those tools for future use. It leverages both cloud LLMs (Gemini Flash) and flexible local models via Ollama to power its evolutionary loop.

## Purpose
To create a system that evolves over time by building its own toolset to solve increasingly complex tasks without manual developer intervention.

## How it Works
The agent operates on a decision loop managed by a **Root Orchestrator**. When a request is received:
1. **Search**: It checks the Tool Registry for an existing tool that can handle the request.
2. **Creation Pipeline**: If no tool exists, it triggers a `SequentialAgent` pipeline:
   - **Tool Spec Agent**: Defines the tool's purpose, inputs, and outputs in JSON.
   - **Tool Coder Agent**: Writes safe Python code based on the spec.
   - **Tool Test Agent**: Generates pytest cases to verify correctness.
3. **Validation**: The generated code undergoes a 3-stage safety check:
   - **Static Analysis (AST)**: Blocks dangerous imports (e.g., `os`, `subprocess`) and keywords (`eval`).
   - **Sandbox Execution**: Runs the tool and its tests in an isolated subprocess with a timeout.
   - **Risk Classification**: Only "Low" risk tools are auto-registered.
4. **Registration**: Validated tools are written to `app/tools/generated/` and added to `app/registry/registry.json`.

## Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud credentials (`gcloud auth auth application-default login`) (for Gemini).
- [Ollama](https://ollama.com/) installed and running (for local models).

## Usage Example

### Setup
```bash
cd self-evolving-agent
uv sync
```

### Running the Agent
**With Gemini (Cloud):**
```bash
agents-cli playground --port 8080
```

**With Ollama (Local):**
```bash
AGENT_MODEL=qwen3:32b agents-cli playground --port 8080
```

### Example Prompt
> "Count the number of sentences in this text: Hello world. How are you? I am fine."

The agent will realize it lacks a `sentence_count_tool`, create it, validate it, and then provide the answer.

## Configuration Options
- **`AGENT_MODEL`**: Environment variable to specify the LLM (e.g., `qwen3:32b` for Ollama or `gemini-1.5-flash` for Cloud).
- **Tool Registry**: Managed in `app/registry/registry.json`.
- **Safety Policy**: Configured in `app/safety/policy.py` (defines blocked imports and keywords).

## Output Format
- **Direct Response**: The result of the executed tool provided as a text response to the user.
- **New Tool**: A Python file in `app/tools/generated/` and a corresponding entry in the registry JSON.

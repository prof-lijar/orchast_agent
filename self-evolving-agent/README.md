# Self-Evolving Agent

A **Self-Evolving Agent** is an AI agent system that can identify missing capabilities, design new tools, generate Python code, test the generated tools in a sandbox, register them into a tool registry, and reuse them to solve future user requests.

Unlike conventional agent systems that rely only on predefined tools, this agent **creates its own tools on demand** — extending its own capabilities through a safe, validated pipeline.

Built with [Google ADK](https://github.com/google/adk-python) (Agent Development Kit).

---

## Research Context

This project implements a **Self-Evolving Agent** architecture proposed by [Professor Jeonghoon Kang](https://github.com/jeonghoonkang). The system demonstrates continuous capability expansion — instead of being limited to predefined tools, the agent autonomously identifies gaps and extends itself.

The architecture follows a multi-agent design:

- **Root Orchestrator** coordinates the system and maintains the tool registry
- **Specialized sub-agents** handle tool specification, code generation, and test generation
- **Safety-first pipeline** ensures all generated code is validated before execution

Long-term applications target **semiconductor manufacturing** and **process control** environments (BerePi, K-CTDM architecture), where the agent could dynamically create tools for sensor data processing, statistical analysis, and quality monitoring — all within strict safety constraints.

---

## How It Works

When a user sends a request, the agent follows this decision loop:

```
User Request
     ↓
Root Orchestrator Agent
     ↓
┌─── What action? ───────────────────────────────────────┐
│                                                         │
│  USE             CREATE           UPDATE        DELETE   │
│   ↓                ↓                ↓             ↓     │
│  Search         Tool Creation   Tool Creation   Delete  │
│  Registry       Pipeline        Pipeline        from    │
│   ↓             (Spec→Code      (update_mode)   Registry│
│  Execute         →Test→Register)     ↓          + File  │
│  Tool                ↓          Overwrite                │
│   ↓             Safety+Sandbox  Entry+File               │
│  Return         Validation      (version++)              │
│  Result              ↓                                   │
│                 Register/Retry                           │
└─────────────────────────────────────────────────────────┘

```

### Diagram
<img width="1448" height="1086" alt="ChatGPT Image May 12, 2026, 11_25_26 AM" src="https://github.com/user-attachments/assets/2cd106d8-496c-4bb1-b626-91ca2d305fca" />


The key insight: the agent **doesn't just answer questions** — it builds, updates, and manages reusable tools that persist across sessions. Once a tool is created and registered, it's available for all future requests without regeneration.

---

## Architecture

### Agents

The system uses **6 ADK agents** coordinated by a root orchestrator:

| Agent | Type | Role |
|-------|------|------|
| **Root Orchestrator** | `Agent` | Receives requests, searches registry, decides whether to use existing tools, create, update, or delete them |
| **Tool Spec Agent** | `Agent` | Converts a user need into a formal JSON tool specification (name, inputs, outputs, risk level, test cases) |
| **Tool Coder Agent** | `Agent` | Generates safe Python code from the specification with type hints and docstrings |
| **Tool Test Agent** | `Agent` | Creates pytest tests covering normal cases, edge cases, and invalid inputs |
| **Tool Registrar Agent** | `Agent` | Calls register or update depending on mode, handles pipeline completion |
| **Tool Review & Fix Agent** | `Agent` | Diagnoses and fixes failed tool code or tests for retry |

The creation agents are wired into a **SequentialAgent** pipeline that passes data through ADK session state (`output_key`):

```
tool_spec_agent (output_key="tool_spec")
       ↓
tool_coder_agent (output_key="tool_code")  ← reads {tool_spec}
       ↓
tool_test_agent (output_key="tool_tests")  ← reads {tool_spec} and {tool_code}
       ↓
tool_registrar_agent  ← calls register or update based on session state
```

### Tool Functions

Registry operations and tool execution are **deterministic tool functions** on the root agent (not LLM agents):

- `search_registry(query)` — keyword search across tool names and descriptions
- `list_available_tools()` — list all registered tools
- `execute_registered_tool(tool_name, input_data)` — dynamically import and call a registered tool
- `register_validated_tool()` — safety check → sandbox test → register new tool
- `update_registered_tool()` — safety check → sandbox test → overwrite existing tool (version incremented)
- `delete_registered_tool(tool_name)` — remove tool from registry and delete its source file

### Supporting Modules

| Module | What it does |
|--------|-------------|
| **Registry Manager** (`app/registry/manager.py`) | JSON-based tool storage with load, save, find, search, register, update, delete, list operations |
| **Safety Policy** (`app/safety/policy.py`) | AST-based import checking, keyword scanning, risk classification |
| **Sandbox Runner** (`app/sandbox/runner.py`) | Subprocess-based restricted code execution with timeout and isolation |

---

## Safety

Every generated tool passes through a **3-stage validation pipeline** before it can be registered:

### 1. Static Safety Analysis (AST)

The safety policy parses generated code using Python's `ast` module and rejects any code that imports blocked modules or uses dangerous functions.

**Blocked imports:**
`os`, `subprocess`, `socket`, `shutil`, `pathlib`, `paramiko`, `ftplib`, `smtplib`, `sys`, `ctypes`

**Allowed network imports:** `requests`, `httpx`, `urllib` (for web-fetching tools)

**Blocked keywords:**
`eval()`, `exec()`, `open()`, `__import__()`, `system()`, `popen()`, `compile()`, `globals()`, `locals()`

### 2. Sandbox Test Execution

Generated code and its tests run in an **isolated subprocess** with:
- Execution timeout (30 seconds)
- Separate working directory
- Process-level isolation from the main agent

### 3. Risk Classification

| Risk Level | Policy | Examples |
|------------|--------|----------|
| **Low** | Auto-allowed | Text transformation, word counting, JSON formatting, math |
| **Medium** | Requires approval (future) | File reading, API requests, database reads |
| **High** | Blocked | Shell execution, file deletion, credential access |

Only `low` risk tools can be auto-registered in v0.1.

**Core rule:** *Never execute or register generated code without validation.*

---

## Tool Registry

The registry is a JSON file (`app/registry/registry.json`) that stores metadata for each validated tool:

```json
{
  "word_count_tool": {
    "name": "word_count_tool",
    "description": "Counts words in a text string.",
    "module": "app.tools.generated.word_count_tool",
    "function": "word_count_tool",
    "input_schema": { "text": "string" },
    "output_schema": { "word_count": "integer" },
    "risk_level": "low",
    "created_at": "2026-05-10T00:00:00+00:00",
    "version": 1
  }
}
```

When a tool is registered, its Python source file is written to `app/tools/generated/` and loaded dynamically via `importlib` at execution time.

---

## Tool Lifecycle

### Creating a Tool

```
1. User asks: "Count the sentences in this paragraph."
2. Root agent searches registry → no match found
3. Root agent transfers to tool_creation_pipeline
4. Tool Spec Agent generates JSON specification
5. Tool Coder Agent generates Python function from spec
6. Tool Test Agent generates pytest tests
7. Tool Registrar Agent calls register_validated_tool:
   a. Safety policy checks code (AST import scan + keyword scan)
   b. Sandbox runs tests in isolated subprocess
   c. If all pass: writes .py file, adds to registry
   d. If tests fail: Review & Fix Agent diagnoses and retries (up to 3 attempts)
8. Root agent calls execute_registered_tool with user's input
9. User gets the result — and the tool is now permanently available
```

### Updating a Tool

```
1. User asks: "Update the web_search_tool to also return snippets."
2. Root agent verifies the tool exists in registry
3. Root agent sets update_mode and transfers to tool_creation_pipeline
4. Pipeline generates new spec, code, and tests
5. Tool Registrar Agent calls update_registered_tool:
   a. Same safety + sandbox validation as creation
   b. Overwrites existing .py file and registry entry
   c. Version number is incremented automatically
6. User sees the updated tool with its new version
```

### Deleting a Tool

```
1. User asks: "Delete the fake_error_generator_tool."
2. Root agent verifies the tool exists
3. Root agent calls delete_registered_tool
4. Tool's .py file is removed and registry entry is deleted
```

---

## Project Structure

```
self-evolving-agent/
├── app/
│   ├── __init__.py                 # App export
│   ├── agent.py                    # All agents, tool functions, instructions
│   ├── fast_api_app.py             # FastAPI server wrapper
│   ├── app_utils/
│   │   ├── typing.py               # Pydantic models (ToolSpec, RegistryEntry, SandboxResult)
│   │   └── telemetry.py            # OpenTelemetry setup
│   ├── registry/
│   │   ├── manager.py              # Registry CRUD operations
│   │   └── registry.json           # Tool registry data
│   ├── sandbox/
│   │   └── runner.py               # Isolated code execution
│   ├── safety/
│   │   └── policy.py               # Static analysis + risk classification
│   └── tools/
│       └── generated/              # Auto-generated tool Python files
│           └── word_count_tool.py   # Example: pre-registered tool
├── tests/
│   ├── unit/
│   │   ├── test_registry.py        # Registry CRUD tests
│   │   ├── test_safety.py          # Safety policy tests
│   │   ├── test_sandbox.py         # Sandbox execution tests
│   │   └── test_tools.py           # Tool execution + dynamic import tests
│   ├── integration/
│   └── eval/
├── pyproject.toml
├── CLAUDE.md
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud credentials configured (`gcloud auth application-default login`)

### Install

```bash
cd self-evolving-agent
uv sync
```

### Run Tests

```bash
uv run pytest tests/unit/ -v
```

### Run the Agent (Interactive Playground)

```bash
uv run adk web . --port 8765
```

Then open `http://localhost:8765` in your browser and select the `app` agent.

### Example Prompts

Try these in the playground:

```
List all available tools.
```

```
Count the words in: The quick brown fox jumps over the lazy dog.
```

```
Count the number of sentences in this text: Hello world. How are you? I am fine. Thanks for asking.
```

```
Update the word_count_tool to also return the character count.
```

```
Delete the fake_error_generator_tool.
```

```
Search the web for "how to deploy an agent"
```

The first prompt uses the pre-registered `word_count_tool`. The third prompt triggers the full tool creation pipeline. The fourth demonstrates tool updating with automatic version incrementing. The fifth deletes a tool from the registry and disk.

---

## Technology Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent framework (Agent, SequentialAgent, App)
- **Gemini** — LLM backbone for tool specification, code generation, and test generation
- **Python `ast` module** — Static safety analysis of generated code
- **`subprocess`** — Sandbox isolation for test execution
- **Pydantic** — Data models and validation
- **pytest** — Testing framework (both project tests and generated tool tests)

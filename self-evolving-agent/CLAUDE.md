# Self-Evolving Agent

A self-evolving agent that dynamically creates, tests, registers, and reuses tools.
Built with Google ADK, agents-cli, and zero-native desktop shell.

## Priorities

**Security > Speed > Performance.** Every change must respect this order.

- Never execute generated code without sandbox validation
- Never introduce OWASP top-10 vulnerabilities (injection, XSS, etc.)
- Minimize allocations, avoid blocking the main thread, prefer in-place mutation over copies
- Use `requestAnimationFrame` over `setTimeout` for UI updates; throttle high-frequency events

## Architecture

```
Root Agent (orchestrator)
├── Tools: search_registry, execute_registered_tool, delete_registered_tool, ...
├── Sub-agent: tool_creation_pipeline (SequentialAgent)
│   ├── tool_spec_agent    → output_key: "tool_spec"
│   ├── tool_coder_agent   → output_key: "tool_code"
│   ├── tool_test_agent    → output_key: "tool_tests"
│   └── tool_registrar_agent
└── Sub-agent: tool_review_fixer_agent
```

- **Registry**: JSON at `app/registry/registry.json`, CRUD via `app/registry/manager.py`
- **Sandbox**: subprocess isolation in `app/sandbox/runner.py` (30s timeout, 10K char output cap)
- **Safety**: AST import checking + keyword scanning in `app/safety/policy.py`
- **Generated tools**: Python modules in `app/tools/generated/`

## Project Structure

```
app/
├── agent.py              # All agents, tool functions, callbacks, root instruction
├── fast_api_app.py       # FastAPI server + custom endpoints (/api/models, /api/registry)
├── app_utils/
│   ├── typing.py         # Pydantic models: TestCase, ToolSpec, RegistryEntry, SandboxResult
│   └── telemetry.py      # OpenTelemetry + GCS log upload
├── registry/
│   ├── manager.py        # Registry CRUD (load, save, find, search, register, update, delete)
│   └── registry.json     # Tool metadata store
├── safety/
│   └── policy.py         # Blocked/allowed imports, keyword scanning, code fence stripping
├── sandbox/
│   └── runner.py         # Subprocess execution, pytest runner, smoke test generation
└── tools/generated/      # Auto-generated tool .py files

desktop/                  # zero-native desktop app (Zig + Svelte)
├── build.zig             # Zig build system
├── app.zon               # zero-native manifest (permissions, platforms, bridge commands)
├── src/
│   ├── main.zig          # Entry point, bridge handlers (agent.backend_status, agent.notify)
│   └── runner.zig        # zero-native runner integration
└── frontend/             # Svelte 5 + Vite SPA
    ├── src/lib/
    │   ├── api.js         # ADK session/run API + model/registry endpoints
    │   ├── ChatPanel.svelte    # Chat UI with SSE streaming
    │   ├── LeftSidebar.svelte  # Session management
    │   ├── RegistryPanel.svelte # Tool browser
    │   └── StatusBar.svelte     # Health + model switcher
    └── vite.config.js     # Proxy: /run, /run_sse, /apps, /api → :8081

tests/
├── unit/                 # test_registry, test_safety, test_sandbox, test_tools
├── integration/
└── eval/                 # ADK evaluation: eval_config.json + evalsets/
```

## Commands

| Command | Purpose |
|---------|---------|
| `uv run python -m app.fast_api_app` | Start backend (port 8081) |
| `cd desktop/frontend && npm run dev` | Start frontend dev server (port 5173) |
| `zig build dev` (in desktop/) | Start desktop app with hot-reload |
| `agents-cli playground` | ADK interactive playground |
| `uv run pytest tests/unit -v` | Run unit tests |
| `agents-cli eval run` | Run ADK evaluations |
| `agents-cli lint` | Check code quality (ruff + codespell) |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | Backend listen port | `8081` |
| `ALLOW_ORIGINS` | CORS origins (comma-separated) | none |
| `AGENT_MODEL` | Switch to local LLM (e.g. `qwen3:32b`) | Gemini Flash |
| `LOGS_BUCKET_NAME` | GCS bucket for telemetry upload | none (disabled) |
| `COMMIT_SHA` | Service version in telemetry | none |

## Safety Rules

### Blocked (never allow in generated code)
- **Imports**: subprocess, socket, sys, ctypes, paramiko, ftplib, smtplib
- **Keywords**: eval(), exec(), \_\_import\_\_(), system(), popen(), compile(), globals(), locals()

### Allowed
- **Imports**: os, pathlib, shutil, csv, pandas, requests, httpx, urllib, re, json, math, string, collections, statistics, textwrap, itertools

### Validation Pipeline
1. Strip markdown code fences → extract raw Python
2. AST parse → check imports against blocklist
3. Regex scan → check for blocked keywords
4. Risk level check → only `"low"` allowed in v0.1
5. Run tests in subprocess sandbox (30s timeout)
6. On pass → write .py to `app/tools/generated/`, add to `registry.json`

## Key Patterns

### ADK Agent Definition
Agents are defined in `app/agent.py` using `google.adk.agents.Agent` and `SequentialAgent`.
Tool functions are async, receive a `ToolContext`, and access session state via `tool_context.state`.

### Dual Model Mode
- **Cloud**: Gemini Flash via `google.adk.models.Gemini` (full features, sub-agents transfer)
- **Local**: Ollama via `google.adk.models.LiteLlm` (simplified instruction, registry embedded in prompt)

### SSE Streaming
- Backend: ADK's built-in `POST /run_sse` endpoint (no custom code needed)
- Frontend: `sendMessageStream()` in `api.js` using `fetch` + `ReadableStream`
- Protocol: partial events (`partial: true`) = incremental text chunks; skip aggregated events to avoid duplicates

### Desktop Bridge
- zero-native provides JS↔Zig bridge via `app.zon` command declarations
- Bridge commands: `agent.backend_status`, `agent.notify`
- Security: navigation restricted to `zero://app`, `zero://inline`, localhost origins

## Frameworks & Docs

| Framework | Purpose | Docs |
|-----------|---------|------|
| [Google ADK](https://adk.dev/) | Agent framework (agents, tools, sessions, runners) | https://adk.dev/ |
| [agents-cli](https://google.github.io/agents-cli/) | CLI for scaffold, deploy, eval, lint, playground, publish | https://google.github.io/agents-cli/ |
| [zero-native](https://zero-native.dev/) | Desktop shell (Zig backend + WebView frontend) | https://zero-native.dev/ |
| Svelte 5 | Frontend UI framework (reactive `$state`, `$props`) | https://svelte.dev/ |
| FastAPI | Python API server (async, Pydantic models) | https://fastapi.tiangolo.com/ |

## Operational Rules

- **Code preservation**: Only modify code directly targeted by the request
- **NEVER change the model** unless explicitly asked
- **Run Python with `uv`**: `uv run python script.py`, `uv run pytest`
- **Stop on repeated errors**: Fix root cause after 3+ occurrences
- **No unnecessary abstractions**: Three similar lines > a premature helper
- **No comments unless WHY is non-obvious**: Well-named identifiers are the documentation
- **Performance-first frontend**: In-place mutation during streaming, `requestAnimationFrame` for scroll, throttle high-frequency callbacks
- **Security-first generated code**: Every tool goes through safety policy + sandbox before registration

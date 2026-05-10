# Self-Evolving Agent - Coding Guide

## Overview

A self-evolving agent that dynamically creates, tests, registers, and reuses tools.
Uses Google ADK with a multi-agent architecture: Root Orchestrator → Tool Creation Pipeline (Spec → Coder → Test) → Sandbox → Registry.

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run tests |
| `agents-cli eval run` | Run evaluations |
| `agents-cli lint` | Check code quality |

## Key Architecture

- **Root Agent**: Orchestrator with registry tools + sub_agents for tool creation
- **Tool Creation Pipeline**: SequentialAgent(tool_spec_agent → tool_coder_agent → tool_test_agent)
- **Registry**: JSON-based tool storage at `app/registry/registry.json`
- **Sandbox**: subprocess-based restricted execution for generated code
- **Safety Policy**: AST-based import checking + keyword scanning

## Safety Rules

- Never execute generated code without sandbox validation
- Blocked imports: os, subprocess, socket, shutil, pathlib, requests, httpx, urllib
- All generated tools must pass tests before registration
- Only low-risk tools allowed in v0.1

## Operational Guidelines

- **Code preservation**: Only modify code directly targeted by the request
- **NEVER change the model** unless explicitly asked
- **Run Python with `uv`**: `uv run python script.py`
- **Stop on repeated errors**: Fix root cause after 3+ occurrences

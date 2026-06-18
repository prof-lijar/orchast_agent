# Architecture Overview

This page provides a technical deep dive into the architecture of `orchast_agent`, a monorepo of purpose-built AI agents.

## Monorepo Structure & Agent Independence

`orchast_agent` is organized as a monorepo where each agent resides in its own top-level directory (e.g., `/course-generator`, `/self-evolving-agent`). 

### Key Principles:
- **Independence**: Each agent is designed to be self-contained with its own `pyproject.toml` and dependencies, allowing them to be deployed or scaled independently.
- **Shared Patterns**: While independent, agents follow common architectural patterns for consistency in development and orchestration.

## Common Agent Patterns

### SequentialAgent Pipelines
Many complex agents are implemented using the `SequentialAgent` pattern from the Google ADK. This allows a high-level task to be broken down into a pipeline of specialized sub-agents.

**Example: Course Generator Pipeline**
1. **Curriculum Designer**: Validates inputs and creates a high-level plan.
2. **Content Developer**: Generates detailed lecture content based on the plan.
3. **Assessment Designer**: Creates quizzes and assignments grounded in the content.
4. **Course Assembler**: Polishes and assembles all outputs into a final Markdown document.

### Session State & Data Flow
Data is passed between agents in a pipeline using `output_key`. Each agent produces an output associated with a specific key, which becomes available to subsequent agents in the sequence. This ensures a structured flow of information from one specialized role to the next.

### Progress Persistence
To handle long-running tasks or potential failures, agents implement progress persistence via `.progress.json` files. This allows an agent to resume from the last successful step rather than restarting the entire pipeline.

## LLM Integration & Abstraction

The system is designed to be model-agnostic, supporting both cloud and local LLMs through a unified abstraction layer (LiteLlm).

- **Cloud**: Primary use of **Gemini Flash** for high speed and large context windows.
- **Local**: Support for **Ollama**, allowing developers to run agents locally for privacy or offline development.
- **Abstraction**: By using an abstraction layer, the underlying model can be swapped via configuration without changing the core agent logic.

## Safety Mechanisms (Self-Evolving Agent)

The `self-evolving-agent` is capable of generating and executing code. To prevent malicious or accidental system damage, it employs a multi-layered safety architecture:

### 1. AST Static Analysis
Before any generated code is executed, the agent performs static analysis using Python's `ast` (Abstract Syntax Tree) module. It checks for:
- **Blocked Imports**: Prevents imports of dangerous modules like `subprocess`, `socket`, or `ctypes`.
- **Blocked Keywords**: Scans for prohibited functions such as `eval()`, `exec()`, and `__import__()`.

### 2. Risk Classification
Code is analyzed to determine its risk profile. Only code that passes the static safety checks and falls within an acceptable risk category is permitted to proceed to execution.

### 3. Sandbox Execution
Safe-classified code is executed within a restricted sandbox environment. This isolates the execution from the host system, ensuring that even if a safety check is bypassed, the potential impact on the underlying infrastructure is minimized.

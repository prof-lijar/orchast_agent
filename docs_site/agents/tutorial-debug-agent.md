# Tutorial & Debug Agent

The **Tutorial & Debug Agent** serves as an interactive mentor for developers using the Google ADK (Agent Development Kit), providing both step-by-step guidance and real-time error diagnosis.

## Purpose
To lower the barrier to entry for new ADK developers by automating the "onboarding" process and reducing the time spent debugging common environment and API errors.

## How it Works
The agent operates in two distinct modes:
1. **Tutorial Mode**: Uses a tool `get_tutorial_step` to retrieve structured guidance on topics such as installation, authentication, scaffolding, and deployment. It walks users through the ADK lifecycle chronologically.
2. **Debug Mode**: Uses a tool `analyze_terminal_error` to parse terminal output. It identifies common error types (e.g., `ModuleNotFoundError`, `AuthenticationError`) and provides a plain-language explanation and a copy-pasteable fix.

## Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.
- `agents-cli` installed via `uv tool install google-agents-cli`.
- Google Cloud SDK configured for GCP services.

## Usage Example

### Setup
```bash
cd tutorial-debug-agent
agents-cli install
```

### Running the Agent
You can run a single prompt using the CLI:
```bash
# Tutorial example
agents-cli run "How do I create my first ADK agent?"

# Debug example
agents-cli run "I'm getting: ModuleNotFoundError: No module named 'google.adk'"
```

Or launch the interactive playground:
```bash
agents-cli playground
```

## Configuration Options
- **Tutorial Content**: The tutorial steps are managed within the agent's tools and instructions in `app/agent.py`.
- **Error Library**: The supported error types (e.g., `ImportError`, `PermissionDenied`) are defined in the logic of `analyze_terminal_error`.

## Output Format
- **Tutorial Response**: A step-by-step guide with code blocks and verification commands.
- **Debug Response**: A structured report containing:
  - Root cause identification.
  - A specific, one-line fix.
  - A command to verify the fix.

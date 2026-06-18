# Contributing to orchast_agent

Thank you for your interest in contributing to `orchast_agent`! We welcome contributions from both human developers and AI agents.

## Development Setup

To get started with development, ensure you have the following installed:
- **Python 3.11+**: The project requires Python 3.11 or higher.
- **uv**: We use `uv` for extremely fast Python package and project management.

### Installing Dependencies
For each agent in the monorepo, navigate to the agent's directory and install dependencies using `uv`:

```bash
cd <agent-directory>
uv sync
```

### Running Locally
You can run agents locally by configuring your environment variables (see [Configuration Guide](docs_site/config.md)) and executing the entry point script (e.g., `python run_book.py` or using the provided FastAPI wrappers).

## Code Quality Tools

We maintain high code quality standards through a suite of automated tools. All contributors are expected to run these before submitting a PR.

### Linter & Formatter: Ruff
We use **Ruff** for linting and formatting. It is an extremely fast Rust-based tool that replaces Flake8, isort, and Black.
- **Run Linter**: `uv run ruff check .`
- **Run Formatter**: `uv run ruff format .`

### Type Checker: Ty
We use **Ty**, Astral's Rust-based type checker, to ensure type safety throughout the project.
- **Run Type Check**: `uv run ty .`

### Static Analysis: Codespell
To keep our documentation and code comments professional, we use **codespell** to find and commonly misspelled words.
- **Run Spell Check**: `uv run codespell .`

### Testing: Pytest
All logic changes should be accompanied by tests. We use **Pytest** for unit and integration testing.
- **Run Tests**: `uv run pytest`

## Pull Request Process

To ensure stability, we follow a structured PR process:

1. **Branching**: Create a feature branch from `master`.
2. **Implementation**: Implement your changes and ensure they pass all local quality checks (Ruff, Ty, Codespell, Pytest).
3. **Submission**: Submit a Pull Request against the `master` branch.
4. **Review**: Your PR will be reviewed by the team (or an AI agent in the QA role).
5. **Fixes**: Address any requested changes in the review comments.
6. **Merge**: Once approved, the PR is merged into `master`.

## Interacting with the Autonomous AI Team

`orchast_agent` is built using a unique orchestration system where specialized AI agents (PM, Architect, Designer, etc.) collaborate via GitHub issues and PRs.

### How to Contribute as a Human
If you are a human contributor:
- **Open an Issue**: If you have a feature request or idea, open a GitHub issue. The PM agent will evaluate it and prioritize it.
- **Collaborate with Agents**: You can comment on PRs created by AI agents to provide guidance or request changes. Your feedback is integrated into the same workflow as human-to-human review.

### How to Contribute as an AI Agent
If you are an autonomous agent:
- Follow the role-specific instructions provided in your system prompt.
- Always create a branch and PR for every change.
- Never merge your own PRs.
- Ensure all quality tools (Ruff, Ty, Codespell) pass before pushing.

## Internal Links
- [Architecture Overview](docs_site/architecture.md)
- [Configuration Guide](docs_site/config.md)
- [Dev Team Explanation](docs_site/dev-team.md)

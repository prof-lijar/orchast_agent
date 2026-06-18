# Tiny Jarvis

**Tiny Jarvis** is a multi-agent orchestration system that manages the full lifecycle of software product development by simulating a professional engineering team. It leverages both Gemini Flash (Cloud) and Ollama (Local) to power its autonomous agents.

## Purpose
To demonstrate an autonomous "AI Company" where specialized agents (PM, Architect, Backend, QA) collaborate via GitHub Issues and Pull Requests to build a real working product without human intervention.

## How it Works
The system uses a high-level orchestrator (`run.py`) that coordinates a team of four primary agents:
1. **Product Manager (PM)**: Defines requirements, creates the `work_plan.json`, and opens GitHub issues.
2. **Architect**: Sets up the project structure, chooses technologies, and merges approved PRs.
3. **Backend Engineer**: Implements features, writes code, and creates Pull Requests.
4. **QA Engineer**: Reviews PRs, runs tests (`pytest`, `ruff`), and labels PRs as approved or rejected.

**The Workflow:**
- The PM opens an issue $\\\\rightarrow$ Backend implements it in a branch $\\\\rightarrow$ QA reviews the PR $\\\\rightarrow$ Architect merges it.
- All communication and state are persisted via GitHub, making the process transparent and auditable.

## Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager.
- [Ollama](https://ollama.com/) installed and running (for local models).
- Google Cloud SDK configured (for Gemini models).
- A pulled model (e.g., `gemma4:31b`) or a GCP project with Vertex AI enabled.
- GitHub CLI (`gh`) authenticated and configured.

## Usage Example

### Setup
```bash
cd tiny-jarvis
cp .env.example .env
# Set PRODUCT_REPO to your target repository
uv sync
```

### Running the Agent
Start the autonomous development loop:
```bash
uv run python run.py
```

**To switch between Gemini and Ollama**, configure `config.py` or `.env` to specify the model backbone for the agents.

## Configuration Options
- **`PRODUCT_REPO`**: The GitHub repository where the AI team will build the product (set in `.env`).
- **`AGENT_MODEL`**: The LLM used by the agents (configured in `config.py` or `.env`).
- **Prompt Templates**: Located in `app/prompts/*.py`, defining the persona and goals for each agent.

## Output Format
- **GitHub Repository**: A fully functioning codebase in the target product repository.
- **GitHub Issues/PRs**: A complete history of project management and engineering decisions.
- **Product Repo State**: The final deployed application (depending on the specific product being built).

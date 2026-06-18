# Tiny Company

**Tiny Company** is an autonomous multi-agent experiment where a simulated AI corporate structure builds a real, working software product from the ground up.

## Purpose
To explore the limits of autonomous collaboration by simulating a full company hierarchy (CEO, CTO, PM, Designer, Marketing, Legal) to architect and implement a complex web application.

## How it Works
The system simulates a professional organization where agents coordinate through GitHub issues and pull requests:
- **Product Management**: Defines the product vision and creates a roadmap via `work_plan.json`.
- **Engineering**: Architects the system and implements features using a multi-agent team (Backend, Frontend, etc.).
- **Support Functions**: Legal and Marketing agents ensure compliance and prepare launch materials.

The project is an implementation of this simulation, where the AI company built the **TOPIK Learning Assistant** web app.

## Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager.
- [Ollama](https://ollama.com/) (for local LLM orchestration).
- GitHub CLI (`gh`) authenticated for repository management.

## Usage Example

### Setup
```bash
cd tiny-company
uv sync
```

### Running the Agents
Start the autonomous company loop:
```bash
python run.py
```

## Configuration Options
- **Model Selection**: Configured in `config.py` or via environment variables for the LLM backbone.
- **Product Repository**: The target repository where the product is being built (specified in `.env`).

## Output Format
- **The Product**: A fully deployed web application (e.g., the TOPIK Learning Assistant).
- **Company Artifacts**: a `work_plan.json`, marketing materials, and legal documents stored within the company directories.
- **GitHub History**: A complete audit trail of all decisions made by the AI agents via issues and PRs.

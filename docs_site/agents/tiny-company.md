# Tiny Company

**Tiny Company** is an autonomous multi-agent experiment where a simulated AI corporate structure builds a real, working software product from the ground up. It utilizes both Gemini Flash (Cloud) and Ollama (Local) to orchestrate its complex company hierarchy.

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
- [Ollama](https://ollama.com/) installed and running (for local models).
- Google Cloud SDK configured (for Gemini models).
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

**To switch between cloud and local LLMs**, configure your environment variables or `config.py` to specify the model backbone for the various roles in the company.

## Configuration Options
- **Model Selection**: Configured in `config.py` or via environment variables for the LLM backbone (supports Gemini Flash and Ollama).
- **Product Repository**: The target repository where the product is being built (specified in `.env`).

## Output 포인트 Format
## Output Format
The agent produces:
- **The Product**: A fully deployed web application (e.g., the TOPIK Learning Assistant).
- **Company Artifacts**: a `work_plan.json`, marketing materials, and legal documents stored within the company directories.
- **GitHub History**: A complete audit trail of all decisions made by the AI agents via issues and PRs.

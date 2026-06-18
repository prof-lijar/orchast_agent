# SciePaperWriter

**SciePaperWriter** is a professional multi-agent pipeline designed to generate high-quality, publication-ready scientific papers from raw source materials.

## Purpose
To automate the transition from research notes and data to a structured academic paper, ensuring that the final output follows rigorous academic standards and formal tone.

## How it Works
The agent uses a **5-phase sequential pipeline** powered by local LLMs via Ollama:
1. **Ingestion Agent**: Analyzes diverse source materials (local files, GitHub repos) and extracts key findings, methodology, and gaps.
2. **Outline Agent**: Creates a detailed section-by-section outline with target word counts for each part.
3. **Writer Agent**: Generates the full paper as academic prose following the outline.
4. **Reviewer Agent**: Checks for clarity, flow, and academic rigor, producing a revised version.
5. **Finalizer Agent**: Performs final polishing and ensures consistent formatting.

**Source Handling:**
The system can ingest data from local directories, specific files (`.md`, `.txt`, `.tex`, etc.), or even entire GitHub repositories.

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) installed and running.
- A pulled model (e.g., `ollama pull gemma4:31b`).
- [uv](https://docs.astral.sh/uv/) package manager.

## Usage Example

### Setup
```bash
cd scie_paper_writer
uv sync
```

### Running the Agent
Create a paper specification (`spec.json`) and run the agent:
```bash
python run_paper.py --spec spec.json --model gemma4:31b
```

**To write in another language (e.g., Korean):**
```bash
python run_paper.py --spec spec.json --model gemma4:31b --lang ko
```

### Example Specification (JSON)
```json
{
  "title": "Autonomous Agents in Healthcare",
  "sources": ["./research-notes/", "./data/results.csv"],
  "structure": "ieee",
  "target_word_count": "6000-8000"
}
```

## Configuration Options
- `--model`: The Ollama model to use (e.g., `gemma4:31b`, `llama3:8b`).
- `--structure`: Choose a template (`generic`, `ieee`, or `acm`).
- `--words`: Override the target word count range.
- `--agents`: Control which stages of the pipeline to run (e.g., skipping ingestion if sources are already provided in the spec).

## Output Format
- **Scientific Paper**: A Markdown file with YAML front matter containing the final academic paper.
- **Logs**: Execution logs in `scie_paper_writer.log`.

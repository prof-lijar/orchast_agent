# Course Generator

The **Course Generator** is a multi-agent system that transforms high-level course goals into comprehensive, learner-ready educational packages. It leverages both cloud LLMs (Gemini Flash) and flexible local models via Ollama to ensure pedagogical rigor and completeness.

## Purpose
To automate the creation of professional courses, including prerequisites, lecture content, assessments, and grading rubrics, reducing the manual effort required by instructional designers.

## How it Works
The system employs a **SequentialAgent** architecture consisting of four specialized agents:
1. **Curriculum Designer**: Validates inputs and builds the high-level course outline and learning path.
2. **Content Developer**: Generates detailed lecture objectives and 300-500 word content summaries for each module.
3. **Assessment Designer**: Creates quizzes (mapped to Bloom's taxonomy), scaffolded assignments, and rubrics.
4. **Course Assembler**: Aggregates all previous outputs into a final structured Markdown document.

## Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.
- `agents-cli` installed via `uv tool install google-agents-cli`.
- Google Cloud SDK configured for GCP services (for Gemini).
- [Ollama](https://ollama.com/) installed and running (for local models).

## Usage Example

### Setup
```bash
cd course-generator
agents-cli install
```

### Running the Agent
Launch the interactive playground:
```bash
agents-cli playground
```

**Example Prompt:**
> "Generate a complete course package for: Building AI Agents with LLMs. Target Learners: Software engineers. Duration: 8 weeks."

**To use local models via Ollama**, configure your environment variables to point to the Ollama endpoint and specify the model in your prompt or configuration.

## Configuration Options
- **Model Selection**: Configured via `agents-cli` and the project's environment settings (supports Gemini Flash and Ollama).
- **Evaluation Rubrics**: The system includes an `eval/` directory with 9 quality rubrics (e.g., "Lecture content depth", "Alignment") used to judge generated courses via LLM-as-judge.

## Output Format
The agent produces a **10-section Markdown course document** containing:
1. Course Overview
2. Prerequisites & Self-Assessment
3. Course Outline
4. Learning Path Guide
5. Lectures (with summaries)
6. Recommended Resources
7. Assessments (Quizzes)
8. Assignments
9. Grading Rubric
10. Feedback Templates

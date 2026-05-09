# Course Generator — Multi-Agent Pipeline

A learner-ready course generation system built with [Google ADK](https://adk.dev/) using a **SequentialAgent** architecture. Given a course title, description, target audience, and learning goals, it produces a complete 10-section course package — including prerequisites, detailed lecture content, scaffolded assignments, and comprehensive assessments.

Supports **multilingual** course generation (English, Burmese, Korean, etc.).

## Demo

[![Course Generator Demo](https://img.youtube.com/vi/s9GeHQhVFhM/maxresdefault.jpg)](https://youtu.be/s9GeHQhVFhM)

## Architecture

```
root_agent (SequentialAgent: course_generator)
│
├─ 1. curriculum_designer
│     Tools: validate_course_inputs, estimate_structure
│     → Prerequisites, course outline, learning path guide
│
├─ 2. content_developer
│     Reads: {curriculum}
│     → Lecture list, objectives, 300-500 word summaries, resources
│
├─ 3. assessment_designer
│     Reads: {curriculum}, {content}
│     → 5-10 quizzes/module, scaffolded assignments, rubric, feedback
│
└─ 4. course_assembler
       Reads: {curriculum}, {content}, {assessments}
       → Final 10-section Markdown course document
```

Each sub-agent writes output to session state via `output_key`, enabling downstream agents to build on prior context.

## Output Sections

| # | Section | Description |
|---|---------|-------------|
| 1 | Course Overview | Title, description, target learners, duration, difficulty |
| 2 | Prerequisites & Self-Assessment | Prerequisite skills with self-check questions and remedial resources |
| 3 | Course Outline | Module breakdown with topics, time allocation, learning outcomes |
| 4 | Learning Path Guide | Linear path, accelerated path, module dependencies |
| 5 | Lectures | Per-module lecture list, objectives, and 300-500 word content summaries |
| 6 | Recommended Resources | Specific chapters/sections with reading schedules |
| 7 | Assessments | 5-10 quiz questions per module across Bloom's taxonomy |
| 8 | Assignments | Step-by-step instructions, starter hints, common pitfalls |
| 9 | Grading Rubric | 4-6 criteria with weights (sum to 100%) and performance descriptors |
| 10 | Feedback Templates | 3-4 comments per performance level |

## Project Structure

```
course-generator/
├── app/
│   ├── agent.py               # Multi-agent pipeline (4 sub-agents + orchestrator)
│   ├── fast_api_app.py         # FastAPI server with SSE streaming
│   └── app_utils/
│       ├── telemetry.py        # OpenTelemetry configuration
│       └── typing.py           # Pydantic models
├── tests/
│   ├── unit/
│   ├── integration/
│   │   ├── test_agent.py       # Agent streaming tests
│   │   └── test_server_e2e.py  # FastAPI e2e tests
│   └── eval/
│       ├── eval_config.json    # 9 LLM-as-judge rubrics
│       └── evalsets/           # 5 diverse test scenarios
├── DESIGN_SPEC.md              # Architecture and requirements
├── pyproject.toml              # Dependencies
└── Dockerfile                  # Container build
```

## Requirements

- **uv**: Python package manager — [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **agents-cli**: Google Agents CLI — `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services — [Install](https://cloud.google.com/sdk/docs/install)

## Quick Start

```bash
# Install dependencies
agents-cli install

# Launch interactive playground
agents-cli playground
```

### Example Prompt

```
Generate a complete course package for:
Course Title: Building AI Agents with Large Language Models
Course Description: A hands-on course covering the design, implementation, and deployment of autonomous AI agents powered by LLMs
Target Learners: Software engineers with Python experience and basic familiarity with LLM APIs
Duration: 8 weeks
Difficulty Level: Intermediate
Learning Goals: Design and implement ReAct-based AI agents with tool calling, Build RAG pipelines for knowledge-grounded agents, Architect multi-agent systems with orchestration patterns, Deploy and monitor agents in production with observability
```

## Commands

| Command | Description |
|---------|-------------|
| `agents-cli install` | Install dependencies |
| `agents-cli playground` | Launch local development server |
| `agents-cli eval run` | Run evaluation against 5 test scenarios |
| `agents-cli lint` | Run code quality checks |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |

## Evaluation

The eval system uses **LLM-as-judge** with 9 quality rubrics:

- **Tool use**: Validates correct tool call sequence (validate → estimate → generate)
- **Completeness**: All 10 sections present and substantive
- **Lecture content depth**: 300-500 word summaries with concepts, examples, takeaways
- **Quiz coverage**: 5-10 questions per module across Bloom's taxonomy
- **Assignment scaffolding**: Step-by-step instructions and starter hints
- **Resource specificity**: Specific chapters with reading schedules
- **Grading rubric quality**: Criteria weights sum to 100%
- **Clarity**: Consistent formatting and structure
- **Alignment**: Content matches course parameters

```bash
agents-cli eval run
```

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform infrastructure:
```bash
agents-cli scaffold enhance
```

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging via OpenTelemetry.

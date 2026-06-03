from __future__ import annotations

import os

os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "local")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models import LiteLlm

OLLAMA_API_BASE = "http://localhost:11434"

# --- Sub-Agent Instructions ---

INGESTION_INSTRUCTION = """You are a research material analyst.

You are analyzing source materials for a research paper titled "{paper_title}".
Paper description: {paper_description}

Authors: {authors}

The following source materials have been provided:

{source_materials}

Sections planned for this paper:
{sections_list}
{writing_guidelines}{language_instruction}

Analyze ALL the provided source materials and produce a structured research context summary. Include:

1. **Key Findings**: The main results, discoveries, or contributions found in the sources
2. **Methodology**: Research methods, experimental setups, or approaches described
3. **Data & Results**: Quantitative data, metrics, benchmarks, or experimental results
4. **Technical Details**: Important technical concepts, algorithms, architectures, or implementations
5. **Gaps & Limitations**: What the sources don't cover or areas that need additional context
6. **Connections**: How different sources relate to each other and to the planned paper sections

Be thorough and specific — extract concrete numbers, method names, and technical details.
This summary will guide all subsequent writing agents."""

OUTLINE_INSTRUCTION = """You are an academic paper outline specialist.

You are creating an outline for a research paper titled "{paper_title}".
Paper description: {paper_description}

Research context from source analysis:

{research_context}

Paper sections to outline:
{sections_list}
{writing_guidelines}{language_instruction}

Create a detailed, hierarchical outline for this paper. For each section:

1. List the main points to cover (3-5 per section)
2. Note which source materials support each point
3. Suggest key arguments, evidence, or data to include
4. Indicate transitions between sections
5. Estimate word count per section (target total: {target_word_count} words)

For the Abstract: outline what should be summarized (do not write it yet).
For References: list the key works that should be cited.

Write the outline in Markdown with clear hierarchy. Be specific and substantive."""

WRITER_INSTRUCTION = """You are an expert academic paper writer.

You are writing a research paper titled "{paper_title}".
Authors: {authors}

Use the following outline as your guide:

{paper_outline}

Research context:

{research_context}
{writing_guidelines}{language_instruction}

Write the COMPLETE paper as polished, publication-ready academic prose. Requirements:

- Follow the outline structure exactly
- Write substantive prose paragraphs, NOT bullet points or lists (unless presenting data)
- Target {target_word_count} words total
- Use formal academic tone throughout
- Use level-1 heading (#) for the paper title
- Use level-2 headings (##) for main sections (Abstract, Introduction, etc.)
- Use level-3 headings (###) for sub-sections where appropriate
- Include smooth transitions between sections
- Ground claims in the source materials — cite specific findings and data
- The Abstract should be a single paragraph summarizing purpose, methods, results, and conclusions
- Include a References section at the end with properly formatted citations

Output ONLY the paper content in Markdown. No meta-commentary."""

REVIEWER_INSTRUCTION = """You are a senior academic reviewer and editor.

You are reviewing a research paper titled "{paper_title}".

Original outline:
{paper_outline}

Draft to review:
{paper_draft}
{writing_guidelines}{language_instruction}

Review the draft and produce an IMPROVED version of the entire paper. Focus on:

1. **Clarity** — Simplify convoluted sentences, ensure each paragraph has a clear point
2. **Flow** — Smooth transitions between sections and paragraphs
3. **Completeness** — Fill gaps where the outline was not fully addressed
4. **Consistency** — Uniform terminology, notation, and style throughout
5. **Academic rigor** — Strengthen claims with evidence, qualify uncertain statements
6. **Structure** — Ensure logical progression of arguments
7. **Abstract quality** — Verify it accurately summarizes the full paper

Output the COMPLETE revised paper in Markdown. Do NOT output review notes or commentary —
output only the improved paper text, ready for the finalizer."""

FINALIZER_INSTRUCTION = """You are an academic paper production editor performing the final polish.

You are finalizing a research paper titled "{paper_title}".
Authors: {authors}

Reviewed draft:
{paper_revised}
{language_instruction}

Produce the FINAL version of this paper. Ensure:

1. The paper starts with: # {paper_title}
2. Author names appear below the title
3. Consistent heading hierarchy (## for sections, ### for sub-sections)
4. No orphaned headings (every heading has content below it)
5. Clean Markdown formatting (proper spacing, no double blank lines)
6. Professional academic tone maintained throughout
7. No meta-commentary, review notes, or TODO markers remain
8. References are consistently formatted
9. The paper reads as a cohesive, publication-ready work

Output ONLY the final paper content in clean Markdown."""


# --- Builder ---

def build_pipeline(
    model: str,
    num_ctx: int = 32768,
    repeat_penalty: float = 1.2,
    timeout: int = 1800,
    no_think: bool = False,
    agents: list[str] | None = None,
) -> SequentialAgent:
    llm = LiteLlm(
        model=f"ollama_chat/{model}",
        api_base=OLLAMA_API_BASE,
        think=not no_think,
        num_ctx=num_ctx,
        repeat_penalty=repeat_penalty,
        temperature=0.7,
        timeout=timeout,
    )

    registry = {
        "ingestion": Agent(
            name="ingestion_agent",
            model=llm,
            instruction=INGESTION_INSTRUCTION,
            output_key="research_context",
        ),
        "outline": Agent(
            name="outline_agent",
            model=llm,
            instruction=OUTLINE_INSTRUCTION,
            output_key="paper_outline",
        ),
        "writer": Agent(
            name="writer_agent",
            model=llm,
            instruction=WRITER_INSTRUCTION,
            output_key="paper_draft",
        ),
        "reviewer": Agent(
            name="reviewer_agent",
            model=llm,
            instruction=REVIEWER_INSTRUCTION,
            output_key="paper_revised",
        ),
        "finalizer": Agent(
            name="finalizer_agent",
            model=llm,
            instruction=FINALIZER_INSTRUCTION,
            output_key="paper_final",
        ),
    }

    if agents is None:
        agents = ["ingestion", "outline", "writer", "reviewer", "finalizer"]

    pipeline_agents = [registry[name] for name in agents if name in registry]

    return SequentialAgent(
        name="paper_pipeline",
        sub_agents=pipeline_agents,
    )


# --- Default pipeline for ADK web UI / adk run ---

_model = LiteLlm(
    model="ollama_chat/gemma4:31b",
    api_base=OLLAMA_API_BASE,
    think=True,
    num_ctx=32768,
    repeat_penalty=1.2,
    temperature=0.7,
    timeout=1800,
)

paper_pipeline = SequentialAgent(
    name="paper_pipeline",
    sub_agents=[
        Agent(name="ingestion_agent", model=_model, instruction=INGESTION_INSTRUCTION, output_key="research_context"),
        Agent(name="outline_agent", model=_model, instruction=OUTLINE_INSTRUCTION, output_key="paper_outline"),
        Agent(name="writer_agent", model=_model, instruction=WRITER_INSTRUCTION, output_key="paper_draft"),
        Agent(name="reviewer_agent", model=_model, instruction=REVIEWER_INSTRUCTION, output_key="paper_revised"),
        Agent(name="finalizer_agent", model=_model, instruction=FINALIZER_INSTRUCTION, output_key="paper_final"),
    ],
)

ROOT_INSTRUCTION = """You are a research paper writing orchestrator.

You help researchers write academic papers by processing their source materials
through a multi-agent pipeline: ingest → outline → write → review → finalize.

For interactive use, guide the user through providing their paper specification
including title, source materials, and preferred structure.

The paper title is: {paper_title}
Total sections: {total_sections}
"""

root_agent = Agent(
    name="root_agent",
    model=_model,
    instruction=ROOT_INSTRUCTION,
    sub_agents=[paper_pipeline],
)

app = App(root_agent=root_agent, name="app")

from __future__ import annotations

import os

os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"

from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models import LiteLlm

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "local")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

# --- Model Configuration ---

_agent_model = os.environ.get("AGENT_MODEL", "gemma4:31b")
_current_model_name = _agent_model


def _make_ollama_model(name: str) -> LiteLlm:
    return LiteLlm(
        model=f"openai/{name}",
        api_base="http://localhost:11434/v1",
        api_key="ollama",
        think=False,
        num_ctx=32768,
        repeat_penalty=1.2,
        temperature=0.7,
    )


_model = _make_ollama_model(_agent_model)

# --- Sub-Agent Instructions ---

OUTLINE_INSTRUCTION = """You are a book chapter outline specialist.

You are writing an outline for a chapter of the book "{book_title}".
Book description: {book_description}

Current chapter:
- Chapter {current_chapter_number}: {current_chapter_title}
- Description: {current_chapter_description}

Create a detailed, hierarchical outline for this chapter. Include:
1. A compelling opening hook or introduction concept
2. Main sections (3-6 sections) with clear headings
3. Key points and sub-topics under each section (2-4 per section)
4. Transition notes between sections
5. A conclusion or chapter summary concept
6. Estimated word count per section (target total: {target_word_count} words)

Write the outline in Markdown with clear hierarchy using headings and bullet points.
Be specific and substantive — this outline guides the writer agent."""

WRITER_INSTRUCTION = """You are an expert book writer.

You are writing a chapter for the book "{book_title}".
Chapter {current_chapter_number}: {current_chapter_title}

Use the following outline as your guide:

{chapter_outline}

Write the FULL chapter as polished, publication-ready prose. Requirements:
- Follow the outline structure exactly
- Write substantive prose paragraphs, NOT bullet points or lists (unless they serve the content)
- Target {target_word_count} words total
- Use a clear, engaging, and authoritative tone
- Start with the chapter title as a level-1 heading: # Chapter {current_chapter_number}: {current_chapter_title}
- Use level-2 headings (##) for main sections
- Use level-3 headings (###) for sub-sections where appropriate
- Include smooth transitions between sections
- End with a strong conclusion that ties back to the chapter's theme

Output ONLY the chapter content in Markdown. No meta-commentary."""

REVIEWER_INSTRUCTION = """You are a professional book editor and reviewer.

You are reviewing a chapter for the book "{book_title}".
Chapter {current_chapter_number}: {current_chapter_title}

Original outline:
{chapter_outline}

Draft to review:
{chapter_draft}

Review the draft and produce an IMPROVED version of the entire chapter. Focus on:
1. Clarity and readability — simplify convoluted sentences
2. Flow — ensure smooth transitions between sections and paragraphs
3. Completeness — fill any gaps where the outline was not fully addressed
4. Consistency — uniform terminology, tone, and style throughout
5. Engagement — strengthen the opening hook and conclusion
6. Accuracy — flag and fix any factual inconsistencies

Output the COMPLETE revised chapter in Markdown. Do NOT output review notes or commentary —
output only the improved chapter text, ready for the finalizer."""

FINALIZER_INSTRUCTION = """You are a book production editor performing the final polish.

You are finalizing a chapter for the book "{book_title}".
Chapter {current_chapter_number}: {current_chapter_title}

Reviewed draft:
{chapter_review}

Produce the FINAL version of this chapter. Ensure:
1. The chapter starts with: # Chapter {current_chapter_number}: {current_chapter_title}
2. Consistent heading hierarchy (## for sections, ### for sub-sections)
3. No orphaned headings (every heading has content below it)
4. Clean Markdown formatting (proper spacing, no double blank lines)
5. Professional tone maintained throughout
6. No meta-commentary, review notes, or TODO markers remain
7. The chapter reads as a cohesive, standalone piece

Output ONLY the final chapter content in clean Markdown."""

# --- Agent Definitions ---

outline_agent = Agent(
    name="outline_agent",
    model=_model,
    instruction=OUTLINE_INSTRUCTION,
    output_key="chapter_outline",
)

writer_agent = Agent(
    name="writer_agent",
    model=_model,
    instruction=WRITER_INSTRUCTION,
    output_key="chapter_draft",
)

reviewer_agent = Agent(
    name="reviewer_agent",
    model=_model,
    instruction=REVIEWER_INSTRUCTION,
    output_key="chapter_review",
)

finalizer_agent = Agent(
    name="finalizer_agent",
    model=_model,
    instruction=FINALIZER_INSTRUCTION,
    output_key="chapter_final",
)

chapter_pipeline = SequentialAgent(
    name="chapter_pipeline",
    sub_agents=[outline_agent, writer_agent, reviewer_agent, finalizer_agent],
)

# --- Root Agent ---

ROOT_INSTRUCTION = """You are a book-writing orchestrator.

You help users write books by processing their table of contents chapter by chapter.
For interactive use, guide the user through providing their book's table of contents
and any preferences about style, tone, or target audience.

For automated overnight runs, the chapter_pipeline sub-agent handles each chapter
through a 4-phase process: outline → write → review → finalize.

The book title is: {book_title}
Total chapters: {total_chapters}
"""

root_agent = Agent(
    name="root_agent",
    model=_model,
    instruction=ROOT_INSTRUCTION,
    sub_agents=[chapter_pipeline],
)

app = App(root_agent=root_agent, name="app")

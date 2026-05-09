# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import math

from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


def estimate_structure(
    duration: str,
    difficulty_level: str,
) -> str:
    """Estimate the number of lectures, quizzes, and assignments appropriate for a course.

    Args:
        duration: The course duration (e.g., "16 weeks", "2 weeks", "3 days").
        difficulty_level: The difficulty level (Beginner, Intermediate, or Advanced).

    Returns:
        A JSON string with recommended counts for lectures, quizzes, and assignments.
    """
    duration_lower = duration.lower().strip()
    weeks = 0
    if "week" in duration_lower:
        try:
            weeks = int("".join(c for c in duration_lower.split("week")[0] if c.isdigit()))
        except ValueError:
            weeks = 8
    elif "day" in duration_lower:
        try:
            days = int("".join(c for c in duration_lower.split("day")[0] if c.isdigit()))
            weeks = max(1, math.ceil(days / 5))
        except ValueError:
            weeks = 1
    elif "month" in duration_lower:
        try:
            months = int("".join(c for c in duration_lower.split("month")[0] if c.isdigit()))
            weeks = months * 4
        except ValueError:
            weeks = 8
    elif "semester" in duration_lower:
        weeks = 16
    else:
        weeks = 8

    if weeks <= 2:
        lectures_per_week = 5
        quizzes = weeks * 2
        assignments = weeks
    elif weeks <= 6:
        lectures_per_week = 3
        quizzes = weeks
        assignments = max(2, weeks // 2)
    else:
        lectures_per_week = 2
        quizzes = max(4, weeks // 2)
        assignments = max(3, weeks // 3)

    total_lectures = weeks * lectures_per_week

    diff = difficulty_level.lower().strip()
    if diff == "advanced":
        quizzes = max(quizzes, 4)
        assignments = max(assignments, 4)

    return json.dumps({
        "estimated_weeks": weeks,
        "total_lectures": total_lectures,
        "recommended_quizzes": quizzes,
        "recommended_assignments": assignments,
        "lectures_per_week": lectures_per_week,
    })


def validate_course_inputs(
    course_title: str,
    course_description: str,
    target_learners: str,
    duration: str,
    difficulty_level: str,
    learning_goals: str,
) -> str:
    """Validate course inputs and return a structured summary.

    Args:
        course_title: The name of the course.
        course_description: Brief description of what the course covers.
        target_learners: Who the course is designed for.
        duration: The length of the course (e.g., "16 weeks", "2 weeks", "3 days").
        difficulty_level: Beginner, Intermediate, or Advanced.
        learning_goals: Comma-separated list of learning objectives.

    Returns:
        A JSON string with validated and structured course inputs.
    """
    errors = []
    if not course_title or len(course_title.strip()) < 3:
        errors.append("course_title must be at least 3 characters")
    if not course_description or len(course_description.strip()) < 10:
        errors.append("course_description must be at least 10 characters")
    if not target_learners or len(target_learners.strip()) < 3:
        errors.append("target_learners must be specified")
    if not duration or len(duration.strip()) < 1:
        errors.append("duration must be specified")

    valid_levels = ["beginner", "intermediate", "advanced"]
    if difficulty_level.lower().strip() not in valid_levels:
        errors.append(f"difficulty_level must be one of: {', '.join(valid_levels)}")

    goals_list = [g.strip() for g in learning_goals.split(",") if g.strip()]
    if len(goals_list) < 1:
        errors.append("At least one learning goal is required")

    if errors:
        return json.dumps({"valid": False, "errors": errors})

    return json.dumps({
        "valid": True,
        "course_title": course_title.strip(),
        "course_description": course_description.strip(),
        "target_learners": target_learners.strip(),
        "duration": duration.strip(),
        "difficulty_level": difficulty_level.strip().capitalize(),
        "learning_goals": goals_list,
        "num_goals": len(goals_list),
    })


# ---------------------------------------------------------------------------
# Sub-agent instructions
# ---------------------------------------------------------------------------

CURRICULUM_DESIGNER_INSTRUCTION = """You are a Curriculum Designer agent. Your job is to validate course inputs, estimate the course structure, and produce a high-level curriculum plan.

## WORKFLOW

1. **First**, call `validate_course_inputs` with ALL six parameters the instructor provided.
   - If validation fails, report errors and stop.
2. **Second**, call `estimate_structure` with the duration and difficulty_level to get recommended counts.
3. **Third**, generate the curriculum plan below using the validated inputs and estimated structure.

## REQUIRED INPUT PARAMETERS

You need these six inputs from the instructor:
- **Course Title**: Name of the course
- **Course Description**: What the course covers
- **Target Learners**: Who the course is for
- **Duration**: How long the course runs (e.g., "16 weeks", "2 weeks", "3 days")
- **Difficulty Level**: Beginner, Intermediate, or Advanced
- **Learning Goals**: What students should learn (comma-separated)

If any input is missing, ask the instructor for it before proceeding.

## OUTPUT FORMAT

Generate ALL of the following sections. Be thorough and specific to the course subject.

### PREREQUISITES & SELF-ASSESSMENT
List 3-5 prerequisite skills or knowledge areas the learner should have. For each prerequisite:
- State the skill clearly
- Provide a self-assessment question (e.g., "Can you explain what a variable is in programming?")
- Suggest a remedial resource if the learner cannot answer (e.g., "If not, review Chapter 1 of 'Automate the Boring Stuff with Python'")

### COURSE OUTLINE
Create a module-by-module or week-by-week breakdown. Each module should have:
- Module number and title
- Key topics covered (3-5 bullet points per module)
- Estimated time allocation (hours)
- Module learning outcomes (what the learner will be able to do after this module)
The number of modules must be realistic for the duration.

### LEARNING PATH GUIDE
Provide guidance for learners with different backgrounds:
- **Linear path**: The default sequential order for learners starting from scratch
- **Accelerated path**: For learners with some background — which modules can be skimmed or skipped, with conditions (e.g., "Skip Module 2 if you can already implement X")
- **Key dependencies**: Which modules build on which (e.g., "Module 5 requires concepts from Modules 2 and 3")
"""

CONTENT_DEVELOPER_INSTRUCTION = """You are a Content Developer agent. Using the curriculum plan provided, generate detailed lecture content, objectives, and curated resources.

## CURRICULUM PLAN
{curriculum}

## OUTPUT FORMAT

Generate ALL of the following sections based on the curriculum above.

### LECTURE LIST
A numbered list of ALL lectures for the entire course. Each entry:
- Lecture number
- Lecture title
- Which module it belongs to

### LECTURE OBJECTIVES
For EACH lecture, provide 2-4 specific, measurable learning objectives using action verbs (explain, implement, analyze, design, evaluate, compare, demonstrate, etc.).

### LECTURE CONTENT
For EACH lecture, generate a structured summary of 300-500 words containing:
- **Key Concepts**: Core ideas, definitions, and principles covered in this lecture
- **Example or Analogy**: A concrete, relatable example that illustrates the main concept
- **Key Takeaways**: 2-3 bullet points summarizing what the learner should remember

The content must be specific to the course subject — avoid generic filler. Write at a level appropriate for the target learners specified in the curriculum.

### RECOMMENDED RESOURCES
For each module, suggest 2-4 resources. For EACH resource include:
- Resource type (Textbook, Online Tutorial, Paper, Tool/Software, Documentation)
- Title (use real, well-known titles only — do NOT invent fake book titles, ISBNs, or DOIs)
- **Specific section**: Chapter number, section name, or page range (e.g., "Chapter 3: Sorting Algorithms, pp. 45-78")
- **Reading schedule**: When to consume it relative to lectures (e.g., "Read before Lecture 5" or "Reference during Assignment 2")
"""

ASSESSMENT_DESIGNER_INSTRUCTION = """You are an Assessment Designer agent. Using the curriculum and lecture content provided, create comprehensive assessments that test learner understanding at multiple levels.

## CURRICULUM PLAN
{curriculum}

## LECTURE CONTENT
{content}

## OUTPUT FORMAT

Generate ALL of the following sections. All assessments must be grounded in the actual lecture content above.

### QUIZ QUESTIONS
Generate 5-10 quiz questions PER MODULE. Distribute questions across Bloom's taxonomy:
- ~30% Recall/Comprehension (define, list, describe, identify)
- ~40% Application (implement, calculate, demonstrate, use)
- ~30% Analysis/Synthesis (compare, evaluate, design, critique)

For each question:
- Tag it with the module number and Bloom's level (e.g., "[Module 3 — Application]")
- For multiple-choice: provide exactly 4 options labeled A, B, C, D with EXACTLY ONE correct answer marked with ✓
- For short-answer: provide the expected answer (2-4 sentences)
- Questions must be directly answerable from the lecture content

### ASSIGNMENT IDEAS
Design hands-on, progressively challenging assignments. For EACH assignment include:
- **Assignment title**
- **Description**: What the learner will build or accomplish
- **Step-by-step instructions**: A numbered walkthrough (5-10 steps) guiding the learner through the task
- **Starter hints**: What to begin with, initial setup, or scaffolding code/structure
- **Expected deliverables**: What the learner should submit
- **Common pitfalls and tips**: 2-3 mistakes learners typically make and how to avoid them
- **Estimated effort**: Time in hours
- **Learning goals addressed**: Which course learning goals this assignment covers

Assignments should be practical and progressively challenging — each building on skills from earlier ones.

### GRADING RUBRIC
Create a detailed grading rubric with:
- 4-6 criteria relevant to the course type (e.g., Technical Accuracy, Code Quality, Analysis Depth, Presentation)
- Weight for each criterion (must sum to 100%)
- Performance descriptors for each level:
  - Excellent (90-100%)
  - Good (75-89%)
  - Satisfactory (60-74%)
  - Needs Improvement (below 60%)

### FEEDBACK COMMENT TEMPLATES
Write template feedback comments for instructors to use. Provide 3-4 specific, constructive comments for each performance level:
- **Excellent**: Student exceeded expectations
- **Good**: Student met expectations
- **Satisfactory**: Student met minimum requirements
- **Needs Improvement**: Student did not meet expectations

Comments should be encouraging, actionable, and specific to the course subject matter.
"""

COURSE_ASSEMBLER_INSTRUCTION = """You are a Course Assembler agent. Your job is to take the outputs from the curriculum designer, content developer, and assessment designer, and assemble them into a single, polished, learner-ready Markdown course document.

## CURRICULUM PLAN
{curriculum}

## LECTURE CONTENT & RESOURCES
{content}

## ASSESSMENTS, RUBRIC & FEEDBACK
{assessments}

## YOUR TASK

Assemble all the above into ONE coherent Markdown document with the following sections, in this exact order. Use clear Markdown formatting with headers, tables, numbered lists, and consistent styling throughout.

1. **COURSE OVERVIEW** — Course title, description, target learners, duration, difficulty level, and learning goals. Present as a clean summary.

2. **PREREQUISITES & SELF-ASSESSMENT** — From the curriculum plan. Format as a checklist learners can work through.

3. **COURSE OUTLINE** — Module breakdown table with module numbers, titles, topics, and time allocation.

4. **LEARNING PATH GUIDE** — From the curriculum plan. Include the linear path, accelerated path, and dependency notes.

5. **LECTURES** — Organized by module. For each module, include:
   - Module header
   - Lecture list (number, title)
   - Learning objectives for each lecture
   - Lecture content summaries (the 300-500 word structured summaries)

6. **RECOMMENDED RESOURCES** — Organized by module, with specific chapters and reading schedules.

7. **ASSESSMENTS** — Quiz questions organized by module, with Bloom's taxonomy tags.

8. **ASSIGNMENTS** — All assignments with full step-by-step instructions, scaffolding, and tips.

9. **GRADING RUBRIC** — Format as a table with criteria, weights, and performance descriptors.

10. **FEEDBACK COMMENT TEMPLATES** — Organized by performance level.

## FORMATTING RULES

- Use consistent header levels: # for document title, ## for main sections, ### for subsections
- Use tables where appropriate (outline, rubric, resources)
- Ensure cross-references are correct (e.g., "as covered in Lecture 5" should match actual lecture numbers)
- Use professional, inclusive language throughout
- Do NOT add new content — only organize and format what was generated by the other agents
- Fix any inconsistencies between sections (e.g., module names, lecture counts, topic references)
"""


# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------

_model = Gemini(
    model="gemini-flash-latest",
    retry_options=types.HttpRetryOptions(attempts=3),
)

curriculum_designer = Agent(
    name="curriculum_designer",
    model=_model,
    instruction=CURRICULUM_DESIGNER_INSTRUCTION,
    tools=[validate_course_inputs, estimate_structure],
    output_key="curriculum",
)

content_developer = Agent(
    name="content_developer",
    model=_model,
    instruction=CONTENT_DEVELOPER_INSTRUCTION,
    tools=[],
    output_key="content",
)

assessment_designer = Agent(
    name="assessment_designer",
    model=_model,
    instruction=ASSESSMENT_DESIGNER_INSTRUCTION,
    tools=[],
    output_key="assessments",
)

course_assembler = Agent(
    name="course_assembler",
    model=_model,
    instruction=COURSE_ASSEMBLER_INSTRUCTION,
    tools=[],
)

root_agent = SequentialAgent(
    name="course_generator",
    sub_agents=[
        curriculum_designer,
        content_developer,
        assessment_designer,
        course_assembler,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)

# DESIGN_SPEC.md — Course Generator Agent (v2 — Learner-Ready)

## Overview

An AI-powered multi-agent pipeline that generates comprehensive, **learner-ready** course materials. Given a course title, description, target learners, duration, difficulty level, and learning goals, it produces a complete course package that a learner can work through independently — including prerequisites, detailed lecture content, scaffolded assignments, and comprehensive assessments.

The agent uses a **SequentialAgent architecture** with four specialized sub-agents, each responsible for a distinct phase of course generation. This allows each agent to give deep attention to its section while passing structured context downstream.

## Inputs

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `course_title` | string | Name of the course | "Introduction to Artificial Intelligence" |
| `course_description` | string | Brief description of what the course covers | "A foundational course covering AI concepts..." |
| `target_learners` | string | Who the course is designed for | "Undergraduate CS students with basic programming" |
| `duration` | string | Length of the course | "16 weeks", "2 weeks", "3 days" |
| `difficulty_level` | string | Beginner / Intermediate / Advanced | "Beginner" |
| `learning_goals` | string | Comma-separated list of learning objectives | "Understand ML basics, Build a neural network" |

## Outputs

The agent generates ten sections assembled into a single Markdown document:

1. **Course Overview** — Title, description, target learners, duration, difficulty, and learning goals
2. **Prerequisites & Self-Assessment** — 3-5 prerequisite skills with self-check questions and remedial resources
3. **Course Outline** — Module-by-module breakdown with topics, time allocation, and module learning outcomes
4. **Learning Path Guide** — Linear path, accelerated path for experienced learners, and module dependencies
5. **Lectures** — Per module: lecture list, 2-4 measurable objectives per lecture, and 300-500 word content summaries (key concepts, examples, takeaways)
6. **Recommended Resources** — Per module: 2-4 resources with specific chapters/sections and reading schedules
7. **Assessments** — 5-10 quiz questions per module distributed across Bloom's taxonomy
8. **Assignments** — Hands-on assignments with step-by-step instructions, starter hints, common pitfalls, effort estimates
9. **Grading Rubric** — 4-6 criteria with weights (summing to 100%) and 4-level performance descriptors
10. **Feedback Comment Templates** — 3-4 comments per performance level (Excellent/Good/Satisfactory/Needs Improvement)

## Architecture

Multi-agent pipeline using ADK's `SequentialAgent`. Each sub-agent writes output to session state via `output_key`, which downstream agents read via `{placeholder}` syntax.

```
root_agent (SequentialAgent: course_generator)
│
├─ 1. curriculum_designer (LlmAgent)
│     Tools: validate_course_inputs, estimate_structure
│     output_key: "curriculum"
│     → Prerequisites, course outline, learning path guide
│
├─ 2. content_developer (LlmAgent)
│     Reads: {curriculum}
│     output_key: "content"
│     → Lecture list, objectives, 300-500 word summaries, resources
│
├─ 3. assessment_designer (LlmAgent)
│     Reads: {curriculum}, {content}
│     output_key: "assessments"
│     → Quizzes (5-10/module), scaffolded assignments, rubric, feedback
│
└─ 4. course_assembler (LlmAgent)
       Reads: {curriculum}, {content}, {assessments}
       → Final assembled Markdown document (10 sections)
```

## Tools

| Tool | Used By | Purpose |
|------|---------|---------|
| `validate_course_inputs` | curriculum_designer | Validates and normalizes the 6 input parameters |
| `estimate_structure` | curriculum_designer | Calculates recommended lecture/quiz/assignment counts based on duration and difficulty |

## Example Use Cases

### 1. Beginner AI Course
- **Input**: "Introduction to Artificial Intelligence", 16 weeks, Beginner, undergraduate students
- **Expected**: Gentle progression from search algorithms to ML basics, simple quizzes, coding assignments in Python, prerequisites covering basic programming

### 2. Advanced Cybersecurity Course
- **Input**: "Advanced Cybersecurity", 12 weeks, Advanced, graduate students with security background
- **Expected**: Deep technical content on threat modeling, exploit analysis, CTF-style assignments with step-by-step walkthroughs

### 3. Short Python Bootcamp
- **Input**: "Python Programming Bootcamp", 2 weeks, Beginner, career changers
- **Expected**: Intensive daily schedule, practical projects, rapid assessment cadence, prerequisites noting no prior experience needed

### 4. University Semester Course
- **Input**: "Data Structures and Algorithms", 16 weeks, Intermediate, CS majors
- **Expected**: Standard academic structure with midterm/final, weekly problem sets, accelerated path for students with prior DS exposure

### 5. Corporate Training
- **Input**: "Cloud Architecture for Teams", 3 days, Intermediate, enterprise engineers
- **Expected**: Compressed format, hands-on labs with scaffolding, business-relevant scenarios

## Constraints & Safety Rules

1. **No hallucinated resources**: When suggesting books or papers, use well-known, real titles. Do not invent fake ISBN numbers or DOIs.
2. **Difficulty alignment**: Content difficulty must match the specified difficulty level — a beginner course should not include advanced topics without scaffolding.
3. **Duration realism**: The number of lectures, assignments, and quizzes must be realistic for the specified duration (e.g., a 2-week bootcamp should not have 30 lectures).
4. **Quiz answer accuracy**: All quiz questions must include correct answers. Multiple-choice questions must have exactly one correct answer clearly marked.
5. **Inclusive language**: All generated content must use inclusive, professional language appropriate for educational settings.
6. **No off-topic content**: All outputs must be directly relevant to the course title and description.
7. **Bloom's taxonomy distribution**: Quiz questions must span recall, application, and analysis levels.
8. **Assignment scaffolding**: Every assignment must include step-by-step instructions, not just descriptions.

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Completeness | All 10 output sections are present and non-empty |
| Clarity | Content is well-organized with clear headings and structure |
| Lecture content depth | Each lecture has a 300-500 word summary with concepts, examples, and takeaways |
| Quiz coverage | 5-10 questions per module with Bloom's taxonomy distribution |
| Assignment scaffolding | Assignments include step-by-step instructions, hints, and common pitfalls |
| Resource specificity | Resources include specific chapters and reading schedules |
| Rubric quality | Rubric has clear criteria, weights summing to 100%, and distinct performance levels |
| Alignment | All content matches the specified course parameters |

## Deployment

Prototype only (no deployment target needed for this project).

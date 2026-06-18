# orchast_agent Documentation Website Goals

Build a comprehensive documentation website for `prof-lijar/orchast_agent` using MkDocs + Material theme, deployed to GitHub Pages.

## Core objective

Create a professional, publicly accessible documentation site that serves as the primary entry point for anyone discovering, using, or contributing to the orchast_agent monorepo. The site should clearly explain what the project is, how each agent works, and how to get started with any of them.

The documentation should make the project approachable for newcomers while remaining a useful reference for experienced users.

## Functional requirements

1. Provide a home page that introduces orchast_agent as a monorepo of purpose-built AI agents powered by Google ADK and Gemini/Ollama.
2. Include a quick-start guide covering prerequisites (Python 3.11+, uv, gcloud auth, Ollama) and first-run steps.
3. Provide individual documentation pages for each agent:
   - **self-evolving-agent** — tool-creating agent with desktop GUI (Zig + Svelte), safety-first code generation with AST analysis and sandbox execution.
   - **book-writer** — chapter-by-chapter book generation pipeline with GitHub auto-commit and resume capability.
   - **course-generator** — multilingual course creation with 4-agent sequential pipeline (Curriculum Designer, Content Developer, Assessment Designer, Course Assembler).
   - **caveman-compressor** — text compression into terse technical summaries.
   - **tutorial-debug-agent** — ADK tutorials and paste-your-error terminal debugging.
   - **tiny-jarvis** — Telegram scheduling agent with multi-agent team.
   - **scie_paper_writer** — scientific paper generation with source ingestion, 5-agent pipeline, and publication-ready output.
   - **tiny-company** — multi-agent team building a TOPIK learning assistant web app.
4. Include an architecture overview page explaining:
   - Monorepo structure and agent independence.
   - Common patterns: SequentialAgent pipelines, session state flow via `output_key`, progress persistence with `.progress.json`.
   - LLM integration: Gemini Flash (cloud) and Ollama (local) with LiteLlm abstraction.
   - Safety mechanisms in self-evolving-agent (AST static analysis, sandbox execution, risk classification).
5. Include a configuration reference covering environment variables, model selection, and Ollama setup.
6. Include a contributing guide with development setup, code quality tools (Ruff, Pytest, Ty, codespell), and PR process.
7. Provide a dev-team page explaining the autonomous AI engineering team system and how it orchestrates agents through GitHub issues and PRs.
8. Include navigation that groups pages logically: Home, Getting Started, Agents (sub-pages), Architecture, Configuration, Contributing.
9. Support both light and dark themes via Material theme palette toggle.
10. Include search functionality via Material theme's built-in search plugin.

## Content requirements

1. Write all documentation in clear, concise English.
2. Each agent page should include: purpose, how it works, prerequisites, usage example, configuration options, and output format.
3. Use code blocks for CLI commands, configuration snippets, and example outputs.
4. Include the agents overview table from the README with links to individual agent pages.
5. Reference actual file paths and directory structures from the monorepo.
6. Keep content accurate to the current state of each agent's implementation.

## Technical requirements

1. Use the existing MkDocs configuration in `mkdocs.yml` with Material theme.
2. Source documentation content from the `docs_site/` directory.
3. Maintain the indigo color scheme for both light (default) and dark (slate) modes.
4. Ensure the site builds successfully with `mkdocs build`.
5. Ensure local preview works with `mkdocs serve`.
6. Deploy to GitHub Pages using the `website/` directory or GitHub Actions.
7. Keep all documentation in Markdown format, version-controlled in Git.

## Product constraints

1. Mobile-friendly and desktop-friendly responsive layout (handled by Material theme).
2. Keep the documentation structure simple and navigable.
3. Do not duplicate content that already exists in individual agent READMEs; link to them or consolidate.
4. Avoid generated API documentation for now; focus on user-facing guides.
5. Keep the build process simple: single `mkdocs build` command with no custom plugins.

## Delivery requirements

1. All placeholder content in `docs_site/` replaced with real documentation.
2. Site builds without errors using `mkdocs build`.
3. Local preview works using `mkdocs serve`.
4. GitHub Actions workflow configured for automatic deployment on push to master.
5. Site publicly accessible via GitHub Pages.
6. Navigation structure matches the functional requirements above.

## Definition of done

1. Home page clearly introduces orchast_agent and links to all agents.
2. Quick-start guide covers prerequisites and first-run for at least one agent.
3. Each of the 8 agents has its own documentation page with purpose, usage, and configuration.
4. Architecture page explains monorepo structure, agent patterns, and LLM integration.
5. Configuration reference covers environment setup and model selection.
6. Contributing guide covers development setup and code quality tooling.
7. Site builds and serves locally without errors.
8. GitHub Actions deploys the site to GitHub Pages on push.
9. Site is publicly accessible and all navigation links work.
10. Light and dark theme toggle works correctly.

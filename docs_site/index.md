# orchast_agent

Welcome to **orchast_agent**, a comprehensive monorepo of purpose-built AI agents designed for real-world utility and high performance. 

Built on top of the [Google ADK](https://adk.dev/) framework, `orchast_agent` demonstrates the power of modular agent architecture, leveraging both cutting-edge cloud LLMs (Gemini) and flexible local models (Ollama).

## Why orchast_agent?
The goal of this project is to provide a collection of professional, modular AI agent implementations that serve as both functional tools and reference architectures for building complex agentic workflows. Whether it's automating scientific paper writing or evolving its own toolset at runtime, `orchast_agent` pushes the boundaries of what autonomous agents can achieve.

## The Agent Roster

| Agent | Description | Primary Models |
| :--- | :--- | :--- |
| [Self-Evolving Agent](usage/self-evolving-agent.md) | Designs and registers its own tools at runtime with a desktop GUI. | Gemini Flash, Ollama |
| [Book Writer](usage/book-writer.md) | High-throughput book generation pipeline with GitHub auto-commit. | Ollama (Local) |
| [Course Generator](usage/course-generator.md) | Multilingual course creation via a 4-agent sequential pipeline. | Gemini Flash |
| [Caveman Compressor](usage/caveman-compressor.md) | Compresses verbose technical text into terse, efficient summaries. | Gemini Flash |
| [Tutorial Debug Agent](usage/tutorial-debug-agent.md) | Interactive ADK tutorials and real-time terminal error debugging. | Gemini Flash |
| [Tiny Jarvis](usage/tiny-jarvis.md) | Telegram-based scheduling agent with a multi-agent coordination team. | Gemini Flash, Ollama |
| [Scientific Paper Writer](usage/scie_paper_writer.md) | Publication-ready paper generation using a 5-agent pipeline. | Gemini Flash |
| [Tiny Company](usage/tiny-company.md) | Multi-agent simulation building a TOPIK learning assistant web app. | Gemini Flash |

## Getting Started
New to the project? Start with our [Quick-Start Guide](setup.md) to set up your environment and run your first agent in minutes.

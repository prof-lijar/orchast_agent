# Book Writer Agent

The **Book Writer Agent** is an autonomous pipeline designed to generate full-length books overnight. It leverages local LLMs via Ollama to create high-quality, structured content without context overflow issues.

## Purpose
To automate the end-to-end process of book writing—from a table of contents to a polished Markdown draft or PDF—while maintaining consistency across many chapters.

## How it Works
The agent uses a **4-phase sequential pipeline** for every chapter defined in the Table of Contents (TOC):
1. **Outline Agent**: Creates a detailed section-by-section plan for the chapter.
2. **Writer Agent**: Drafts the full chapter prose based on the outline.
3. **Reviewer Agent**: Refines the draft for clarity, flow, and completeness.
4. **Finalizer Agent**: Polishes the final Markdown formatting.

**Key Technical Features:**
- **Fresh Sessions**: Each chapter runs in a new ADK session to prevent "context drift" or overflow in long books.
- **Progress Tracking**: Uses `.progress.json` to track completed chapters, allowing the process to be resumed after interruptions.
- **Auto-Commit**: Can automatically commit and push each completed chapter to a GitHub repository.

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) installed and running.
- A pulled model (e.g., `ollama pull gemma4:31b`).
- [uv](https://docs.astral.sh/uv/) package manager.

## Usage Example

### Setup
```bash
cd book-writer
uv sync
```

### Running the Agent
Create a `toc.json` file with your book title and chapters, then run:
```bash
python run_book.py --toc toc.json --model gemma4:31b
```

**To push to GitHub as you go:**
```bash
python run_book.py --toc toc.json --model gemma4:31b --repo https://github.com/user/my-book.git
```

### Example TOC (JSON)
```json
{
  "title": "Mastering AI Agents",
  "chapters": [
    {
      "number": 1,
      "title": "Introduction to Autonomous Agents",
      "description": "Basic concepts and history of AI agents"
    }
  ]
}
```

## Configuration Options
- `--model`: The Ollama model to use (e.g., `gemma4:31b`, `qwen3.5:0.8b`).
- `--words`: Target word count per chapter (default: 3000-5000).
- `--agents`: Customize the pipeline stages (e.g., adding `publisher` to generate a PDF).
- `--lang`: Specify the language for the book content (ISO 639-1 code).

## Output Format
- **Chapter Files**: Individual Markdown files (`chapter-XX.md`) in the `./book/` directory.
- **Combined Book**: A single PDF file (if the `publisher` agent is included).
- **Logs**: Detailed execution logs in `book-writer.log`.

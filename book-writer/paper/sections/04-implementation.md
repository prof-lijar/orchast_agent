## Implementation

### Stack and Footprint

Book-Writer is implemented in 1,388 lines of Python across four modules: the
agent definitions (196 lines), the tool library including the publisher (486
lines), the command-line orchestrator (671 lines), and a small FastAPI wrapper
(35 lines) for interactive use. Agents are ADK `Agent` instances composed with
`SequentialAgent` [6]; model access goes through LiteLLM [7] to an Ollama
server [5] on the local host. The default model is `gemma4:31b` from the Gemma
open-weight family [8], with generation configured at temperature 0.7, a
32,768-token context window, and a repetition penalty of 1.2. Three
command-line flags—disabling model thinking, shrinking the context window,
and raising the repetition penalty—adapt the pipeline to models small enough
to run on a Raspberry Pi, the same class of machine that hosts the
orchestrator itself.

### Prompt Design

Each stage's instruction follows a common pattern: a one-sentence professional
role ("You are a book production editor performing the final polish"), the
chapter's coordinates within the book, the upstream stage's output
interpolated from session state, and an explicit output contract. The
contracts do most of the work. The writer must produce "substantive prose
paragraphs, NOT bullet points," must begin with a canonical chapter heading,
and must emit "ONLY the chapter content in Markdown. No meta-commentary."
The finalizer enforces seven mechanical checks, including heading hierarchy,
no orphaned headings, and the absence of leftover review notes or TODO
markers. User-supplied writing guidelines from the TOC are injected into the
outline, writer, and reviewer prompts, and a language directive supporting 23
languages forces non-English books to be written entirely in the target
language while permitting code and technical terms to remain in English.

### Robustness Machinery

A striking property of the implementation is how much of it exists to keep an
unattended run alive rather than to generate text. Table II summarizes the
mechanisms; together they account for the bulk of the orchestrator's 671
lines. Before any generation begins, the runner verifies that Ollama is
reachable and the requested model is available.

*TABLE II — Robustness mechanisms for unattended operation.*

| Mechanism | Behavior |
|-----------|----------|
| Health check | verify Ollama endpoint and model before starting |
| Per-chapter retry | up to 3 attempts, fresh session each attempt |
| Timeout | 1,800 s per chapter attempt via async cancellation |
| Fallback capture | persist best stage output if late stages fail |
| Progress file | completed/failed/in-progress state on disk; resume flag |
| Idempotent restart | chapters already on disk are skipped |
| Incremental git | commit and push after every chapter; 3 pull–rebase retries |
| Failure isolation | a chapter that exhausts retries is logged, loop continues |

### Publishing and Distribution

The publisher reads the chapter files in order, strips their metadata front
matter, converts Markdown to HTML, translates embedded LaTeX math to MathML,
and renders an A4 PDF with WeasyPrint [9]—a CSS-based typesetting path that
avoids a TeX toolchain entirely. The generated document includes a title page
and a table of contents with page references resolved by the layout engine,
and output files are versioned automatically. Finished chapters and PDFs
accumulate in a public repository [10], and a companion web application,
Foliant [11], presents the collection as a browsable library with a public
book-request page, closing the loop from a TOC file to a distributed,
readable book.

## System Architecture

### Design Overview

Book-Writer treats the chapter, not the book, as the unit of generation. The
input is a table of contents (TOC) declaring the book's title, description,
and an ordered list of chapters, each with a title and a short description.
An orchestrator iterates over the chapters and runs each one through a
four-stage pipeline of specialized language-model agents; completed chapters
are written to disk and committed to version control immediately. When all
chapters exist, a deterministic publisher stage typesets them into a versioned
PDF. Fig. 1 shows the complete flow.

<figure>
<svg viewBox="0 0 380 500" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, sans-serif">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#333"/>
    </marker>
  </defs>
  <!-- TOC input -->
  <rect x="55" y="8" width="150" height="30" rx="4" fill="#eef2f8" stroke="#334455" stroke-width="1"/>
  <text x="130" y="21" font-size="10.5" text-anchor="middle" fill="#111">Table of contents</text>
  <text x="130" y="33" font-size="8.5" text-anchor="middle" fill="#445">JSON / YAML / text · local or GitHub</text>
  <line x1="130" y1="38" x2="130" y2="56" stroke="#333" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Orchestrator frame -->
  <rect x="18" y="58" width="224" height="284" rx="6" fill="none" stroke="#334455" stroke-width="1.2" stroke-dasharray="5 3"/>
  <text x="30" y="74" font-size="10" fill="#334455" font-weight="bold">Orchestrator (run_book.py)</text>
  <text x="30" y="86" font-size="8.5" fill="#445">per-chapter loop · fresh session · retry ×3</text>
  <text x="30" y="97" font-size="8.5" fill="#445">timeout · resume from .progress.json</text>

  <!-- Pipeline boxes -->
  <rect x="45" y="106" width="150" height="26" rx="4" fill="#dce6f2" stroke="#334455"/>
  <text x="120" y="123" font-size="10.5" text-anchor="middle" fill="#111">outline_agent</text>
  <line x1="120" y1="132" x2="120" y2="152" stroke="#333" marker-end="url(#arr)"/>
  <text x="128" y="146" font-size="8.5" fill="#445">chapter_outline</text>

  <rect x="45" y="154" width="150" height="26" rx="4" fill="#dce6f2" stroke="#334455"/>
  <text x="120" y="171" font-size="10.5" text-anchor="middle" fill="#111">writer_agent</text>
  <line x1="120" y1="180" x2="120" y2="200" stroke="#333" marker-end="url(#arr)"/>
  <text x="128" y="194" font-size="8.5" fill="#445">chapter_draft</text>

  <rect x="45" y="202" width="150" height="26" rx="4" fill="#dce6f2" stroke="#334455"/>
  <text x="120" y="219" font-size="10.5" text-anchor="middle" fill="#111">reviewer_agent</text>
  <line x1="120" y1="228" x2="120" y2="248" stroke="#333" marker-end="url(#arr)"/>
  <text x="128" y="242" font-size="8.5" fill="#445">chapter_review</text>

  <rect x="45" y="250" width="150" height="26" rx="4" fill="#dce6f2" stroke="#334455"/>
  <text x="120" y="267" font-size="10.5" text-anchor="middle" fill="#111">finalizer_agent</text>
  <line x1="120" y1="276" x2="120" y2="296" stroke="#333" marker-end="url(#arr)"/>
  <text x="128" y="290" font-size="8.5" fill="#445">chapter_final</text>

  <rect x="45" y="298" width="150" height="26" rx="4" fill="#f4f4f0" stroke="#334455"/>
  <text x="120" y="315" font-size="10" text-anchor="middle" fill="#111">chapter-NN-title.md</text>

  <!-- Ollama box -->
  <rect x="272" y="160" width="96" height="64" rx="4" fill="#eef2f8" stroke="#334455"/>
  <text x="320" y="180" font-size="10" text-anchor="middle" fill="#111">Ollama</text>
  <text x="320" y="193" font-size="8.5" text-anchor="middle" fill="#445">local inference</text>
  <text x="320" y="205" font-size="8.5" text-anchor="middle" fill="#445">gemma4:31b</text>
  <text x="320" y="217" font-size="8.5" text-anchor="middle" fill="#445">localhost:11434</text>
  <line x1="272" y1="192" x2="200" y2="192" stroke="#333" stroke-dasharray="3 3" marker-end="url(#arr)"/>

  <!-- git commit annotation -->
  <line x1="195" y1="311" x2="268" y2="311" stroke="#333" marker-end="url(#arr)"/>
  <rect x="270" y="292" width="100" height="38" rx="4" fill="#f4f4f0" stroke="#334455"/>
  <text x="320" y="308" font-size="9.5" text-anchor="middle" fill="#111">git commit + push</text>
  <text x="320" y="321" font-size="8.5" text-anchor="middle" fill="#445">per chapter</text>

  <!-- Publisher -->
  <line x1="120" y1="342" x2="120" y2="362" stroke="#333" marker-end="url(#arr)"/>
  <rect x="35" y="364" width="170" height="40" rx="4" fill="#f0e9d8" stroke="#334455"/>
  <text x="120" y="381" font-size="10.5" text-anchor="middle" fill="#111">Publisher (deterministic)</text>
  <text x="120" y="395" font-size="8.5" text-anchor="middle" fill="#445">Markdown → MathML → WeasyPrint</text>

  <line x1="120" y1="404" x2="120" y2="424" stroke="#333" marker-end="url(#arr)"/>
  <rect x="55" y="426" width="130" height="28" rx="4" fill="#f4f4f0" stroke="#334455"/>
  <text x="120" y="444" font-size="10" text-anchor="middle" fill="#111">book-slug-vN.pdf</text>

  <line x1="185" y1="440" x2="262" y2="440" stroke="#333" marker-end="url(#arr)"/>
  <rect x="264" y="426" width="106" height="28" rx="4" fill="#e4efe4" stroke="#334455"/>
  <text x="317" y="440" font-size="9.5" text-anchor="middle" fill="#111">Foliant web</text>
  <text x="317" y="450" font-size="8.5" text-anchor="middle" fill="#445">library</text>
</svg>
<figcaption>Fig. 1. Book-Writer architecture. The orchestrator runs the
four-stage agent pipeline once per chapter with a fresh session, commits each
completed chapter to version control, and finally invokes the deterministic
publisher, whose PDFs are distributed through the Foliant web library.</figcaption>
</figure>

### Input Model and Operating Modes

The TOC is deliberately the system's entire authoring interface. It is
accepted as JSON or YAML, or as plain numbered text for the lowest-friction
case, and may carry optional fields that shape generation without touching
code: a target language, per-book writing guidelines injected into the
generation prompts, and per-chapter descriptions that seed each outline. The
TOC may also be given as a URL into a hosted repository, in which case the
orchestrator clones the repository and derives the output location and branch
from the TOC's position within it—so a book "lives" in its own repository
from the first chapter.

The pipeline's stages are individually selectable at invocation time, which
turns one program into several tools. Running only the publisher re-typesets
an existing book without any model invocation; omitting the reviewer and
finalizer produces fast draft-quality output for inspecting a TOC's
viability; regeneration flags rewrite selected chapters, or the whole book,
in place. The same mechanism separates concerns during development, since any
stage's behavior can be exercised in isolation against real intermediate
artifacts.

### The Chapter Pipeline

Each chapter passes through four agents composed as a strict sequence.
Writing $s_i$ for the specification of chapter $i$ taken from the TOC, the
produced chapter is $c_i = f_{fin}(f_{rev}(f_{wr}(f_{out}(s_i))))$, where the
four functions are the outline, writer, reviewer, and finalizer agents. The
stages communicate through named session state: each agent writes its full
output under a designated key, and the next agent's prompt template
interpolates that key. Table I lists the stages and their contracts.

*TABLE I — Pipeline stages and their state contracts.*

| Stage | Role | Reads | Writes |
|-------|------|-------|--------|
| outline | plans 3–6 sections, key points, word budget | TOC entry | `chapter_outline` |
| writer | full prose draft following the outline | `chapter_outline` | `chapter_draft` |
| reviewer | rewrites for clarity, flow, completeness | outline + draft | `chapter_review` |
| finalizer | production polish, formatting discipline | `chapter_review` | `chapter_final` |
| publisher | typesets all chapters to PDF (no LLM) | chapter files | versioned PDF |

Two design choices in the pipeline are deliberate. First, the reviewer is a
rewriting editor, not a critic: its instruction requires it to output the
complete improved chapter rather than review notes, which removes a
merge-feedback step that weaker local models handle unreliably. Second, every
stage is forbidden from emitting meta-commentary, so any stage's output is a
usable chapter; this property underpins the orchestrator's degradation
strategy described next.

### Orchestration for Unattended Operation

The orchestrator is an imperative loop rather than a framework-level loop
construct, because the requirements of an overnight run sit outside what
declarative composition offered: chapter-specific state must be injected into
each run, progress must survive process death, and failures must be contained
to a single chapter. Each chapter executes in a brand-new in-memory session,
so context never accumulates across chapters and the memory footprint stays
bounded regardless of book length. A failed or timed-out chapter is retried up
to three times with a fresh session; if every attempt fails, the failure is
recorded and the loop simply proceeds to the next chapter. When a run is
interrupted, a progress file records completed, failed, and in-flight
chapters, and a resume flag skips work that already exists on disk.

The orchestrator also degrades gracefully within a chapter. Because every
stage outputs a complete chapter, the runner can fall back through the state
keys in order—final, review, draft, outline—and persist the best available
text if the tail of the pipeline fails. Finally, each completed chapter is
committed and pushed to the output repository immediately, with pull–rebase
retries on push conflicts; a night's work is therefore preserved
chapter-by-chapter even if the machine dies before morning.

### The Publisher as a Deterministic Stage

The fifth stage contains no language model at all. Typesetting is a
deterministic transformation, and making it one keeps content generation and
presentation independently re-runnable: a book can be re-typeset without
touching a model, and chapters can be regenerated without re-typesetting until
the end. The publisher's output is versioned automatically, so successive
publications of the same book coexist as v1, v2, and so on.

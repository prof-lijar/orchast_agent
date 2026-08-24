# IEEE-Style Paper Structure — Section Guide

Target total: **4,500–6,000 words** (≈ 6–9 two-column A4 pages).
Headings in `paper.md` are plain `##` — numbering (I., II., …) is applied by the
PDF builder. The Abstract and References are special sections and are not numbered.

## Abstract (150–250 words)
Self-contained: one sentence of context, the problem, the approach, what was built,
key quantitative results, and one sentence of significance. No citations, no
abbreviations that aren't expanded, no "in this paper we will".

## I. Introduction (600–800 words)
- Context and motivation: why does this problem matter?
- The gap: what existing approaches don't do.
- The contribution, stated explicitly. End with a short bulleted contribution list
  (the one place bullets are allowed) and a paragraph map of the paper
  ("The remainder of this paper is organized as follows…").
Reviewer complaint to avoid: introductions that describe the system before
motivating the problem.

## II. Related Work / Background (400–600 words)
Group prior work by theme, not by paper. For each theme: what it does, what it
lacks relative to this work. Only cite verifiable work. If genuinely comparable
academic work is uncertain, keep this section short and factual (frameworks, tools,
adjacent systems) rather than padding with invented citations.

## III. System Architecture (800–1,100 words) — the core section
- The design at a glance: components, data flow, one architecture figure (Fig. 1).
- The key design decisions and *why* (e.g. why a sequential pipeline, why fresh
  sessions per unit, why an imperative orchestrator instead of a framework loop).
- Formalize where it helps: pipeline as stage functions, state keys as a table.
Reviewer complaint to avoid: a code walkthrough. Describe the *design*; cite files
only in passing.

## IV. Implementation (500–800 words)
Concrete engineering: languages, frameworks, models, versions, prompts' roles,
robustness machinery (retry, resume, timeouts, fallbacks), publishing pipeline.
This is where file/LOC/dependency facts belong. A table of pipeline stages or CLI
capabilities works well here.

## V. Evaluation / Results (600–900 words)
What was actually produced or measured. Use the real artifact corpus: counts,
sizes, languages, page counts — in a results table (Table I/II). Describe the
evaluation method honestly (e.g. "observational, based on N generated artifacts"
if there is no controlled experiment). Never invent benchmark numbers.

## VI. Discussion and Limitations (400–600 words)
What the results mean; where the design pays off; then concrete limitations
(missing tests, coupling, hardware constraints, no human evaluation, etc.) and
threats to validity. Follow with future work that addresses those limitations.

## VII. Conclusion (150–250 words)
Restate contribution + strongest result. No new information. Do not copy the
abstract.

## References
IEEE numeric style, cited in order of first appearance:
`1. A. Author, "Title," Venue/URL, Year.`
6–12 entries is plenty for a systems paper. Every entry must be real and checkable.

## Figures and tables
- At least one architecture figure (inline SVG) and one results table.
- Every figure/table is referenced from body text before it appears.
- Captions: figures below ("Fig. 1. …"), tables above ("TABLE I — …").

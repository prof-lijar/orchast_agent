# Outline — "Foliant Book-Writer" paper (target 4,800–5,600 words)

**Title:** Book-Writer: An Autonomous Multi-Agent Pipeline for Overnight
Long-Form Book Generation with Locally Hosted Language Models

**Authors:** LI JAR, SuperJAR. Keywords: multi-agent systems, large language
models, long-form text generation, local inference, autonomous agents,
publishing pipeline.

## Abstract (~220 w)
Context (LLM long-form generation hard: coherence, context limits, cost) →
system (4-stage sequential multi-agent pipeline + imperative orchestrator +
deterministic publisher, all on local Ollama models) → results (16 books,
258 chapters, 536k words, 1,886 PDF pages, 3 languages, median 7.1 min/chapter,
public library Foliant) → significance (commodity/edge hardware, unattended
overnight operation).

## I. Introduction (~750 w)
Claims: long-form generation exceeds single-context capabilities; cloud-API
agent systems costly/private-data concerns; contribution = decomposition into
chapter-level pipeline + robustness engineering for unattended runs on local
models. Evidence: facts (architecture, corpus). Contribution bullet list (4
items) + paper map. No figures.

## II. Related Work (~450 w)
Themes: (a) multi-agent LLM frameworks (AutoGen, MetaGPT, ADK) — general
orchestration, not long-form books; (b) long-form generation (Re3, STORM) —
recursive/outline-driven writing, typically cloud models, article/story scale;
(c) local inference (Ollama/LiteLLM) enabling cost-free iteration. Gap: overnight
book-scale generation on local models with production publishing. Cites [1-5,8-12].

## III. System Architecture (~950 w) — Fig. 1 (architecture SVG), Table I (stages/state keys)
Claims: chapter as unit of work; 4-stage generate–refine pipeline (outline →
writer → reviewer → finalize) with state via output_key/placeholder; reviewer
as rewriting editor not critic; imperative orchestrator (why not LoopAgent):
fresh session per chapter (bounded context), retry/timeout, resume, per-chapter
git commit; publisher as deterministic 5th stage. Formalize c_i = (f_fin ∘
f_rev ∘ f_wr ∘ f_out)(s_i) with simple inline math only.

## IV. Implementation (~700 w) — Table II (robustness mechanisms)
Claims: 1,388 lines Python; ADK + LiteLLM + Ollama stack; prompt design (role,
constraints, output discipline); model config (temp 0.7, num_ctx 32768,
repeat_penalty, think toggle; gemma4:31b default; small-model flags for
Raspberry Pi); publisher implementation (markdown→MathML→WeasyPrint, versioned
PDFs); 23-language mechanism; distribution: per-chapter git push +
Foliant web library.

## V. Evaluation (~800 w) — Table III (corpus per-book stats)
Method statement: observational evaluation over the public output corpus;
measurement procedure (git archive snapshot, front-matter timestamps, pypdf).
Results: 16 books, 258 chapters, 536,295 words, 1,886 pages, EN/KO/MY split,
7–29 chapters/book, median 7.1 min/chapter (239 deltas), overnight completion,
per-chapter durability (commit trail), version evolution (weight-of-light v8).

## VI. Discussion and Limitations (~550 w)
What worked: decomposition beats context limits; robustness machinery is the
majority engineering cost; deterministic publisher separates content from
presentation. Limitations (from facts): no automated tests; env-var import-time
coupling & duplicated registry; finalizer drops guidelines; no content-quality
evaluation (no human study); hardcoded endpoint/single machine; silent math
fallback; timing from timestamps not instrumentation. Future work: quality
evals, cross-chapter consistency memory, parallel chapter generation, test suite.

## VII. Conclusion (~180 w)
Restate contribution + strongest numbers. No new claims.

## References (12 entries — facts.md candidate list)

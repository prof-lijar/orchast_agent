# Evidence base — book-writer paper (measured/verified 2026-08-24)

Every fact below carries a `file:line` citation (paths relative to `book-writer/`)
or the measurement method. `docs_site/agents/book-writer.md` was NOT used (known
machine-generated drift: invents Gemini support).

## Architecture
- 4 LLM agents wired as ADK `SequentialAgent` — `app/agent.py:169-172`;
  registry `{outline, writer, reviewer, finalizer}` `app/agent.py:159-164`.
- State flow via `output_key` → `{placeholder}`:
  `chapter_outline` (agent.py:135) → `chapter_draft` (:142) → `chapter_review`
  (:149) → `chapter_final` (:156).
- Stage selection: `PIPELINE_AGENTS` env var read at import time `app/agent.py:166-167`;
  runner sets env before deferred import `run_book.py:487`.
- Agents have no `tools=[...]` — pure text transformers (agent.py:131-157).
- `root_agent` + `App` exist only for the interactive/FastAPI path
  (agent.py:189-196, `app/fast_api_app.py`); the batch runner drives
  `chapter_pipeline` directly.

## Prompts (app/agent.py)
- OUTLINE (:42-61): hook, 3–6 sections, 2–4 key points each, transitions,
  per-section word estimates toward `{target_word_count}`.
- WRITER (:63-84): "substantive prose paragraphs, NOT bullet points";
  starts `# Chapter {n}: {title}`; "Output ONLY the chapter content… No meta-commentary."
- REVIEWER (:86-107): 6 axes (clarity, flow, completeness, consistency,
  engagement, accuracy); **rewrites** — "Do NOT output review notes".
- FINALIZER (:109-127): 7 production checks (heading hierarchy, no orphaned
  headings, no meta-commentary/TODO). Reads only `{chapter_review}` +
  `{language_instruction}` (drops `{writing_guidelines}` — inconsistency).

## Models / inference
- Local Ollama via LiteLLM: `ollama_chat/<name>`, api_base hardcoded
  `http://localhost:11434`, temperature 0.7, num_ctx default 32768,
  repeat_penalty default 1.2, optional think toggle, timeout default 1800 s
  (agent.py:22-35). Default model `gemma4:31b` (agent.py:18).
- Small-model accommodations: `--no-think`, `--num-ctx`, `--repeat-penalty`
  CLI flags (README; run_book.py argparse).

## Orchestrator (run_book.py, 671 L)
- Hand-rolled per-chapter loop (not ADK LoopAgent). Fresh
  `InMemorySessionService` per run (:489), new session per chapter (:200 helper).
- Retry: `for attempt in range(1, args.retry+1)` (:562) around
  `asyncio.wait_for(..., timeout)` (:567); default retry 3, timeout 1800 s.
- Graceful degradation: fallback walks
  `["chapter_final","chapter_review","chapter_draft","chapter_outline"]` (:316).
- Resume: `.progress.json` `{started_at, completed[], failed{}, in_progress}`
  (`app/tools.py:209` load_progress); chapters with existing `chapter-NN-*.md`
  auto-marked complete.
- Git: per-chapter `add/commit` + push with up to 3 `pull --rebase` attempts,
  never raises (`app/tools.py:107`).
- Health check `check_ollama()` against `/api/tags` before starting (:137, :453).
- Input: TOC as JSON/YAML/numbered text (`app/tools.py:48` parse_toc), local
  path or GitHub blob URL (cloned via SSH).
- Languages: `LANGUAGE_NAMES` 23 ISO-639-1 codes (:40); non-en gets a forceful
  language-instruction block.
- Default stages `outline,writer,reviewer,finalizer,publisher` (:371).

## Publisher (app/tools.py)
- `publish_to_pdf` (:368): read `chapter-*.md` sorted → strip front matter →
  `markdown` (extra, toc, codehilite) → `$…$`/`$$…$$` → MathML via
  `latex2mathml` (:349; silent fallback to literal) → title page + dotted-leader
  ToC via CSS `target-counter` (:300) → Pygments highlighting → WeasyPrint A4.
- ~115-line CSS `_PDF_CSS` (:226), DejaVu Serif 11pt.
- Auto-versioned output `{slug}-vN.pdf` (max existing + 1).

## Code size (wc -l)
- run_book.py 671; app/agent.py 196; app/tools.py 486; app/fast_api_app.py 35
  → 1,388 total.
- Dependencies (pyproject.toml): google-adk[extensions]>=1.15,<2.0,
  litellm>=1.50, pyyaml, python-slugify, markdown>=3.6, weasyprint>=62,
  latex2mathml>=3.77. Python >=3.11,<3.14.
- No tests: `tests/unit/` contains only empty `__init__.py`.

## Corpus (github.com/prof-lijar/ai-generated-books @ origin/main ee48180, measured on `git archive` snapshot)
- 16 completed books; generated 2026-05-19 → 2026-08-12.
- 258 chapter files; 536,295 words (front matter stripped, whitespace-split).
- 23 PDFs; latest version per book totals 1,886 pages (pypdf).
  `the-weight-of-light` has 8 published versions (v8 = 71 pp).
- Per book: chapters 7–29; words 10,577–94,770.
  Largest: atomic-theory-of-society… 29 ch / 94,770 w / 264 pp.
- Languages by content: English 8, Korean 5, Burmese 3.
- Timing (239 consecutive `generated_at` deltas < 3 h): median 7.1 min/chapter,
  mean 15.1, range 2.1–171.4. Books complete within ~1 day each.
- Sample per-book rows for Table: see measurement output in session
  (appulsa 28ch/36,488w/134pp KO; the-wave-is-already-here 15ch/47,070w/136pp EN;
  ethical-hacking-for-developers 8ch/21,144w/68pp EN;
  vim-guide-for-lazy-devs 11ch/18,757w/58pp EN;
  quantum-computing… 25ch/47,488w/177pp KO;
  brain-computer-interface… 14ch/39,311w/131pp EN;
  c-programming… 23ch/40,586w/203pp MY;
  html-css-javascript… 20ch/30,183w/162pp MY;
  the-ethics-of-cruelty 21ch/48,856w/144pp EN;
  the-last-generation-of-humans 12ch/33,072w/91pp EN;
  the-weight-of-light 12ch/24,984w/71pp EN;
  hansel-and-gretel 7ch/10,577w/42pp KO;
  keti-eseo-saranamgi 7ch/11,090w/47pp KO;
  pyat-san… 14ch/11,639w/75pp MY;
  ai-wan… 12ch/20,280w/83pp KO;
  atomic-theory 29ch/94,770w/264pp EN).

## Distribution
- Output repo: github.com/prof-lijar/ai-generated-books (per-chapter commits,
  e.g. "Add Chapter 14: The Future of Brain Computer Interfaces";
  "Publish book PDF v1: …").
- Public web library: **Foliant**, https://floriant-press.vercel.app/ —
  "A shelf of books imagined, drafted, and bound entirely by AI agents";
  pages: library (home), /about (describes the 4-phase pipeline, ADK, Ollama,
  publisher), /request (public book requests); links to the GitHub output repo.
  (Fetched 2026-08-24.)

## Hardware context
- Development/orchestration host: Raspberry Pi (Linux 6.18 rpt-rpi-2712,
  aarch64); large models served by Ollama, remote GPU via SSH port-forward
  per README. Small-model flags exist for Pi-only operation.

## Honest limitations (for §VI)
- No automated tests (tests/unit empty).
- Env-var coupling: agent.py reads env at import; stage registry duplicated in
  agent.py and run_book.py (must sync manually).
- Finalizer drops writing_guidelines (prompt inconsistency).
- No quantitative quality evaluation of book content (no human study, no
  benchmark); evaluation is observational (throughput, robustness, scale).
- Single-machine, single-model-per-run; Ollama endpoint hardcoded.
- latex2mathml fallback is silent; math errors can pass through to PDFs.
- Timing estimates derive from commit-adjacent front-matter timestamps, not
  instrumented measurement; deltas > 3 h were excluded as idle gaps.

## Verifiable references (candidates)
1. Google ADK — https://github.com/google/adk-python
2. Ollama — https://ollama.com/
3. LiteLLM — https://github.com/BerriAI/litellm
4. WeasyPrint — https://weasyprint.org/
5. Gemma model family — Google DeepMind, https://ai.google.dev/gemma
6. ai-generated-books repo — https://github.com/prof-lijar/ai-generated-books
7. Foliant — https://floriant-press.vercel.app/
8. Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in LLMs," NeurIPS 2022. (well-known, safe)
9. Wu et al., "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation," 2023. (well-known, safe)
10. Hong et al., "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework," ICLR 2024. (well-known, safe)
11. Shao et al. / "Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models" (STORM), NAACL 2024. (well-known, safe)
12. Yang et al., "Re3: Generating Longer Stories With Recursive Reprompting and Revision," EMNLP 2022. (well-known, safe)

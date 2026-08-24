## Discussion and Limitations

### What the Design Buys

Three observations stand out from operating the system. First, chapter-level
decomposition converts an intractable long-context problem into a sequence of
tractable medium-context problems: no stage ever needs more context than one
chapter's worth of material, which is why 30,000-token-class local models
suffice for 90,000-word books. The cost of this decomposition is that no
agent ever sees the whole book, a trade-off examined below. Second, the
orchestrator—at 671 of the system's 1,388 lines, its largest module—is
dominated by robustness machinery rather than generation logic. For
unattended operation this inversion
appears essential: over a multi-hour run against a local inference server,
timeouts, stalls, and push conflicts are routine events, and the corpus was
produced through them, not in their absence. Third, keeping typesetting
deterministic and model-free made presentation iterable at zero model cost;
the eight published versions of one book were re-typeset and re-published
without regenerating text.

### Limitations

The evaluation measures scale, throughput, and durability—not literary or
technical quality. No human evaluation, readability scoring, or factuality
audit of the generated books has been performed, and for the non-fiction
titles the risk of confidently stated model error is real; the books are
published with an explicit machine-authorship disclaimer. Cross-chapter
consistency is structurally unenforced: because each chapter is generated in
a fresh session, nothing prevents terminology drift or contradiction between
chapters beyond what the shared TOC implies.

The implementation carries known weaknesses. There is no automated test
suite. Configuration passes from orchestrator to agents through environment
variables read at import time, an ordering-sensitive coupling, and the
stage-name registry is duplicated between two modules that must be kept in
sync manually. The finalizer's prompt omits the user's writing guidelines
that the three earlier stages receive—an inconsistency rather than a design
decision. The math converter falls back silently to literal text on
conversion failure, so malformed formulas can reach published PDFs
unnoticed. The Ollama endpoint is hardcoded to the local host, and chapters
are generated strictly sequentially, leaving multi-machine or parallel
generation unexplored. Finally, the reported timing figures inherit the
precision of file timestamps rather than instrumentation.

### Future Work

The natural next steps target the two structural gaps: a lightweight
cross-chapter memory (for example, a running glossary and character or
concept sheet injected into each chapter's session) to address consistency,
and an automated quality pass—readability metrics, factual spot-checks, and
sampled human review—to make the quality of the corpus measurable. On the
engineering side, a test suite around the TOC parser, progress tracking, and
publisher, plus parallel chapter generation across multiple Ollama hosts,
would extend the same design without altering it.

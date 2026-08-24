## Evaluation

### Method

The evaluation is observational: it measures what the system actually produced
during roughly three months of routine operation, rather than a controlled
benchmark. All measurements were taken on 24 August 2026 from a snapshot of
the public output repository [10]. Chapter and word counts were computed from
the chapter source files with metadata front matter removed; PDF page counts
were extracted programmatically from the latest published version of each
book; and per-chapter generation times were derived from the generation
timestamps embedded in consecutive chapters' front matter, discarding gaps
longer than three hours as idle time between sessions. Timing figures are
therefore estimates of wall-clock production time, not instrumented
measurements.

### Corpus Scale

Between 19 May and 12 August 2026 the system produced 16 complete books:
258 chapters totaling 536,295 words, published as PDFs totaling 1,886 pages.
Eight books are in English, five in Korean, and three in Burmese—the
multilingual output exercising the language directive rather than separate
models. Books range from 7 to 29 chapters and from roughly 10,600 to 94,800
words; the largest single volume is a 29-chapter, 264-page treatise. Table III
lists a representative subset spanning the size and language range.

<div class="tablewrap" markdown="1">
*TABLE III — Representative books from the generated corpus.*

| Book | Lang. | Ch. | Words | PDF pages |
|------|-------|-----|-------|-----------|
| Atomic Theory of Society… | EN | 29 | 94,770 | 264 |
| Quantum Computing System Development | KO | 25 | 47,488 | 177 |
| C Programming (introductory) | MY | 23 | 40,586 | 203 |
| The Ethics of Cruelty | EN | 21 | 48,856 | 144 |
| The Wave Is Already Here | EN | 15 | 47,070 | 136 |
| Brain–Computer Interface Technologies | EN | 14 | 39,311 | 131 |
| The Weight of Light | EN | 12 | 24,984 | 71 |
| Ethical Hacking for Developers | EN | 8 | 21,144 | 68 |
| Hansel and Gretel (retelling) | KO | 7 | 10,577 | 42 |
| **Corpus total (16 books)** | — | **258** | **536,295** | **1,886** |
</div>

### Throughput

Across 239 usable consecutive-chapter intervals, the median production time
was 7.1 minutes per chapter and the mean 15.1 minutes, with individual
chapters ranging from 2.1 to 171 minutes. The gap between median and mean
reflects a heavy right tail rather than uniform slowness: most chapters
complete in single-digit minutes, while a minority run long—behavior
consistent with the retry mechanism, which restarts a stalled chapter from
scratch up to three times and therefore multiplies the wall-clock time of
exactly the chapters that misbehave. This distribution is itself an argument
for the per-chapter failure isolation described in Section III: a slow or
failing chapter delays only itself.

At the median rate, a 20-chapter book completes in under three hours of
generation time, and indeed every book in the corpus finished its chapters
within a single day—consistent with the intended overnight usage pattern, in
which the operator supplies a TOC in the evening and finds a committed,
typeset book in the morning. Because inference runs on local hardware, the
marginal cost of this output was electricity.

### Durability in Practice

The corpus also evidences the robustness machinery working as designed. The
output repository's history shows one commit per chapter followed by a
publication commit per book, so every night's partial progress was preserved
incrementally. One title, *The Weight of Light*, exists in eight published PDF
versions, demonstrating regeneration and re-publication of the same book over
time; the automatic version numbering kept all editions addressable. The
publisher stage handled all three scripts in the corpus—Latin, Hangul, and
Burmese—producing paginated PDFs from the same pipeline without
script-specific configuration.

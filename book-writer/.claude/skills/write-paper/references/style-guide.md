# Academic Writing Style Guide

## Voice and tense
- "We" for the authors' actions; the system's name for what the software does.
- Present tense for what the system does ("the reviewer stage rewrites the draft");
  past tense for what was done/observed ("the system generated 13 books").
- Active voice by default; passive only when the actor is irrelevant.

## Claims and evidence
- Every claim carries its evidence in the same or adjacent sentence: a number,
  a mechanism, or a citation. Unsupported superlatives ("highly scalable",
  "extremely robust") are banned — replace with the mechanism ("retries each
  chapter up to three times with a fresh session").
- Hedge only where genuinely uncertain, and say why.
- Distinguish design intent from observed behavior. "Designed to survive
  interruption" vs "resumed successfully after interruption" require different
  evidence.

## Precision
- One name per concept, used consistently (pick "stage" or "agent" or "phase" and
  define the others once). Define every term at first use; expand every acronym once.
- Numbers: give the measurement basis ("671 lines (`wc -l run_book.py`)" in notes;
  "roughly 1,400 lines of Python" in the paper body is fine once grounded).
- Avoid marketing adjectives; prefer measurable statements.

## Paragraphs and flow
- One idea per paragraph; first sentence states it, the rest supports it.
- 3–6 sentences per paragraph. No single-sentence paragraphs except transitions.
- Prose, not bullet lists, in the body (exception: the contribution list in the
  Introduction).

## Citations (IEEE numeric)
- In text: "… as provided by the Agent Development Kit [2]." Bracketed numbers,
  in order of first appearance.
- Software/framework citations: name, "Title/Project," URL, year. This is normal
  and preferable to fake academic citations.

## Figures, tables, math
- Reference every figure/table from the text before it appears.
- Inline math with `$...$`, display math with `$$...$$` (converted to MathML by
  the PDF builder). Use math only where it clarifies (e.g. pipeline composition
  $c_i = f_{fin}(f_{rev}(f_{wr}(f_{out}(s_i))))$), not for decoration.
- Keep SVG figures self-contained: no external fonts/images; explicit `fill`
  colors and `width="100%"` with a `viewBox` so they scale to column width.

## Things reviewers reject
- Abstract that promises what the paper doesn't deliver.
- Results section without a method statement (how were the numbers obtained?).
- Limitations that are actually humble-brags ("our only limitation is that we
  haven't tested at planetary scale").
- Conclusion that introduces new claims.

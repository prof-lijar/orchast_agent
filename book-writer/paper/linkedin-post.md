# LinkedIn post (KAIST-style announcement)

Orchast Agent Project researchers have developed an autonomous system that writes complete, typeset books overnight using only open-weight language models running on local hardware.

The system, called Book-Writer, was developed by researchers LI JAR and SuperJAR, who documented the architecture and a three-month operating history in a newly released paper.

Existing long-form generation systems faced a fundamental set of constraints: a full book exceeds the context window of a single model pass, unattended multi-hour runs fail on routine timeouts and stalls, and iterating against metered cloud APIs makes large-scale experimentation expensive. The research team addressed all three by changing the unit of work — from the book to the chapter.

Book-Writer decomposes each book into chapters and processes every chapter through a four-stage pipeline of specialized agents — an outliner, a writer, a reviewing editor that rewrites rather than critiques, and a production finalizer — with each stage passing its complete output to the next through typed session state. Because no stage ever needs more context than a single chapter, 32k-context open-weight models served locally by Ollama are sufficient for 90,000-word books.

The key advance was separating generation from survival. An orchestrator engineered for unattended operation gives each chapter a fresh model session, retries failures up to three times, falls back to the best available intermediate output when late stages fail, persists resumable progress to disk, and commits every completed chapter to version control the moment it exists — so a night's work is preserved chapter by chapter even if the machine dies before morning. A deterministic, model-free publishing stage then typesets the chapters into versioned PDF books without a TeX toolchain.

In roughly three months of routine operation, the system produced 16 complete books — 258 chapters, 536,295 words, and 1,886 PDF pages — in English, Korean, and Burmese, at a median wall-clock cost of 7.1 minutes per chapter and zero inference cost. Every book was completed within a single day and published to a public web library.

The approach could reduce the cost of long-form content pipelines in education, documentation, and publishing, and demonstrates that book-scale generation no longer requires frontier cloud models — only disciplined systems engineering around models that run on hardware the operator already owns.

The paper was released in August 2026.
🔗 Paper: Book-Writer: An Autonomous Multi-Agent Pipeline for Overnight Long-Form Book Generation with Locally Hosted Language Models
🔗 Code: https://github.com/prof-lijar/orchast_agent (book-writer)
🔗 Library: https://floriant-press.vercel.app/

#MultiAgentSystems #LLM #LocalAI #Ollama #AutonomousAgents #Publishing #AIResearch

---

# ChatGPT image prompt (cover image, human-edited editorial look)

Create a LinkedIn cover image, 1200×627 (1.91:1), designed like an editorial
illustration from a university research magazine or MIT Technology Review —
the kind produced by a professional graphic designer, NOT a generic AI artwork.

Concept: "A book being assembled overnight by a production line." A clean
schematic-style illustration of four small workstations in a row (labeled
OUTLINE, WRITE, REVIEW, FINALIZE), passing pages left to right along a thin
conveyor line, ending at a bound book with a subtle "v2" tag. Above the line,
a small moon and window suggest nighttime; below, a tiny home server box with
a gentle status LED represents local hardware. Keep it diagrammatic and calm.

Art direction (follow strictly):
- Style: flat vector / screen-print editorial illustration with a restrained
  2-color-plus-neutrals palette — deep navy (#1d3557), warm off-white paper
  (#f4f1ea), one muted accent (burnt orange #c1502e). No gradients except a
  faint duotone night sky.
- Composition: generous negative space, strong horizontal flow, grid-aligned
  elements, rule-of-thirds; the conveyor line sits on the lower third.
- Texture: subtle risograph/print grain and slight ink misregistration on
  edges, like a printed poster that was scanned — this is what makes it feel
  human-made.
- Typography: NONE except the four small stage labels and "v2" — set them in
  a clean grotesque (Helvetica-like), all caps, small. No other text, no
  headlines, no gibberish characters anywhere.
- Absolutely avoid: glossy 3D renders, robots, glowing blue circuit brains,
  neon, lens flares, photorealistic humans, floating holograms, any
  "AI-generated" sheen, watermarks, extra unreadable text.
- Lighting/mood: quiet, nocturnal, studious; the feeling of waking up to
  finished work.

The result should look like a commissioned illustration a design editor
approved: simple idea, disciplined palette, printable, slightly imperfect.

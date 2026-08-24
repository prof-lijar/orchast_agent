## Introduction

Large language models produce fluent prose at paragraph and article scale, yet
book-scale generation remains difficult in practice. A complete book of several
hundred pages exceeds the effective context of most models, so a single
generation pass cannot maintain structure from the first chapter to the last.
Quality is equally hard to sustain: a first draft produced in one shot receives
no editorial attention, and errors accumulate silently across tens of thousands
of words. Finally, the economics of iteration matter. Producing, discarding,
and regenerating hundreds of chapters against a metered cloud API is expensive
enough to discourage exactly the experimentation that long-form generation
requires.

Prior work addresses parts of this problem. Recursive prompting and revision
schemes such as Re3 [1] extend story length beyond a single context window, and
outline-driven systems such as STORM [2] ground article-scale writing in a
research-then-write process. General multi-agent frameworks, including AutoGen
[3] and MetaGPT [4], demonstrate that decomposing a task across specialized
model roles improves output quality. However, these systems target stories or
articles rather than complete typeset books, typically assume frontier cloud
models, and give little attention to the systems engineering required for
multi-hour unattended operation: crash recovery, partial-progress persistence,
and publication of the result as a distributable artifact.

This paper presents Book-Writer, an autonomous system that writes complete
books overnight using only locally hosted open-weight models served by Ollama
[5]. The system decomposes a book into chapters and processes each chapter
through a four-stage sequential pipeline of specialized agents—outliner,
writer, reviewer, and finalizer—built on the Google Agent Development Kit
(ADK) [6]. An imperative orchestrator wraps the pipeline with the machinery
that unattended operation demands: a fresh model session per chapter to bound
context growth, per-chapter retry and timeout, disk-persisted progress with
resume, and a version-controlled commit of every chapter as it completes. A
deterministic publisher stage then typesets the accumulated chapters into a
versioned PDF, and the results are distributed through a public web library.
In roughly three months of operation the system produced 16 complete books
comprising 258 chapters, 536,295 words, and 1,886 PDF pages across three
languages, at a median cost of 7.1 minutes of wall-clock time per chapter and
zero inference cost.

The contributions of this work are:

- a chapter-level decomposition of book generation into a four-stage
  generate-and-refine agent pipeline whose stages communicate through typed
  session state;
- an orchestration design for unattended multi-hour runs on local models,
  combining per-chapter sessions, retry with graceful degradation, resumable
  progress, and incremental version-controlled publication;
- a deterministic publishing stage that turns pipeline output into typeset,
  versioned PDF books without a TeX toolchain; and
- an observational evaluation over a public corpus of 16 machine-written
  books in English, Korean, and Burmese.

The remainder of this paper is organized as follows. Section II reviews
related work. Section III describes the system architecture and its design
rationale. Section IV details the implementation. Section V reports the
evaluation over the generated corpus. Section VI discusses findings and
limitations, and Section VII concludes.

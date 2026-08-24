## Conclusion

This paper described Book-Writer, an autonomous system that turns a table of
contents into a complete, typeset, version-controlled book overnight using
only locally hosted open-weight models. Its contribution is less any single
component than the demonstrated combination: a four-stage generate-and-refine
agent pipeline scoped to the chapter, an orchestrator engineered for
unattended multi-hour operation, and a deterministic publishing stage—which
together produced a public corpus of 16 books, 258 chapters, and 536,295
words across English, Korean, and Burmese at a median of 7.1 minutes per
chapter and no inference cost. The system's operating history suggests that
for long-form generation, the binding constraints are no longer model access
or expense but consistency across generated units and the measurement of
output quality; both are tractable extensions of the architecture presented
here.

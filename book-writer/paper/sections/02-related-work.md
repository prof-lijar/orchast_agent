## Related Work

### Long-Form Text Generation

Extending coherent generation beyond a single context window is a recognized
challenge. Re3 [1] generates long stories through recursive reprompting and
revision, alternating drafting with editing passes—an approach the present
work echoes in its writer–reviewer–finalizer chain, though at chapter rather
than passage granularity. STORM [2] shows that separating outline construction
from article writing improves the structure of Wikipedia-like articles;
Book-Writer applies the same outline-first discipline to every chapter. Both
systems, however, target single documents of article or story length and rely
on hosted frontier models, whereas Book-Writer produces multi-hundred-page
typeset books on open-weight models running on local hardware.

### Multi-Agent LLM Frameworks

AutoGen [3] and MetaGPT [4] established that assigning specialized roles to
cooperating model instances yields better results than a single generalist
prompt, particularly when one role reviews another's output. These frameworks
emphasize flexible conversation topologies. Book-Writer deliberately adopts
the simplest possible topology—a fixed sequential chain—on the grounds that
book chapters need a repeatable production line rather than negotiation. The
system is built on the Google Agent Development Kit [6], which supplies the
agent abstraction, sequential composition, and session-state passing, while
model access is routed through LiteLLM [7] to Ollama [5], which serves
open-weight models such as the Gemma family [8] on local hardware.

### Position of This Work

The gap Book-Writer occupies is the combination of scale, autonomy, and cost:
book-length output assembled from chapter-level pipeline runs, produced
unattended overnight, on hardware the operator already owns. To our knowledge,
publicly documented systems that publish complete multilingual, typeset,
version-controlled books from local models are rare, and the engineering
required for that autonomy—recovery, resumption, and incremental
publication—is the least-reported part of comparable systems.

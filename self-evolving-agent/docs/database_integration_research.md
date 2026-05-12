# Database-Backed Tool Lifecycle Management for Self-Evolving LLM Agents

**Mini Research Paper — May 2026**

---

## Abstract

Self-evolving agents — LLM-based systems that dynamically create, test, and register their own tools at runtime — face a critical infrastructure gap: how to persistently store, version, retrieve, and analyze dynamically generated tools across sessions. While existing frameworks (LangChain, CrewAI, AutoGen, Google ADK) rely on in-memory or flat-file tool registration, this paper argues that database-backed tool lifecycle management is essential for production-grade self-evolving agents. We analyze the current landscape, examine storage patterns from VOYAGER, LATM, CREATOR, and ToolLLM, and propose a PostgreSQL-based architecture with pgvector for semantic tool retrieval — applied to our self-evolving agent system built on Google ADK.

---

## 1. Introduction

Large Language Models (LLMs) have progressed beyond static tool usage to dynamic tool creation. Systems like VOYAGER [1], LATM [2], and CREATOR [3] demonstrate that LLMs can generate executable functions to solve tasks they were not explicitly programmed for. However, a survey of these systems reveals a recurring architectural weakness: **tool storage is treated as an afterthought**.

Most self-evolving agent systems store generated tools in-memory (CREATOR, LATM), as append-only entries in vector databases (VOYAGER, CRAFT), or as flat JSON files (ToolLLM). None provide:

- **Version history** with rollback capability
- **Execution analytics** that feed back into tool improvement
- **Semantic retrieval** combined with structured metadata queries
- **Safety audit trails** for generated code

Our system — a self-evolving agent built on Google ADK with a multi-agent architecture — currently uses a JSON file (`registry.json`) for tool metadata and filesystem storage for generated Python code. This paper proposes migrating to a PostgreSQL-based architecture that addresses these gaps.

### 1.1 System Overview

Our self-evolving agent operates through a pipeline of specialized sub-agents:

```
User Request
    |
    v
Root Orchestrator  ──>  search_registry()  ──>  Tool Found? ──> execute_registered_tool()
    |                                               |
    | (no match)                                    v
    v                                           Return Result
Tool Creation Pipeline (SequentialAgent)
    |
    ├── tool_spec_agent      →  JSON specification
    ├── tool_coder_agent     →  Python implementation
    ├── tool_test_agent      →  Pytest test suite
    └── tool_registrar_agent →  Safety check + sandbox test + registration
    |
    v
Registry (currently JSON)  +  Generated .py files
```

Safety enforcement includes AST-based import analysis, keyword scanning for dangerous operations, and sandboxed test execution before any tool is registered.

---

## 2. Related Work

### 2.1 Tool Creation in LLM Agents

| System | Pipeline | Storage | Versioning | Retrieval | Safety |
|--------|----------|---------|------------|-----------|--------|
| VOYAGER [1] | Code gen + verify | ChromaDB | None (append-only) | Semantic | Environment test |
| LATM [2] | Maker + User LLMs | In-memory dict | None | Task-type map | Test cases |
| CREATOR [3] | Abstract + Decide + Implement + Execute | In-memory | None | None | None |
| ToolLLM [4] | API retrieval + DFSDT | JSON flat file | None | Neural retriever | None |
| CRAFT [5] | Create + Retrieve toolsets | Vector DB | Deduplication | Semantic | Verification |
| ToolEvo [6] | MCTS-based evolution | Tree structure | Tree branches | Best-performing | Execution test |
| **Ours** | Spec + Code + Test + Register | JSON file | Integer version | Keyword search | AST + sandbox |

**Key observation**: No existing system combines persistent structured storage, version history, execution analytics, and semantic retrieval in a unified database. VOYAGER uses ChromaDB for semantic search but lacks structured queries. ToolLLM uses JSON for structure but lacks semantic retrieval. Our proposed architecture unifies both via PostgreSQL with pgvector.

### 2.2 Agent Memory and State Persistence

The memory taxonomy proposed by Zhang et al. [7] identifies five categories relevant to self-evolving agents:

1. **Procedural memory** — learned skills and tool code (the primary focus of this work)
2. **Semantic memory** — tool descriptions and schemas
3. **Episodic memory** — execution logs and interaction history
4. **Short-term memory** — current session state (ADK session)
5. **Long-term memory** — cross-session persistence

Current framework support:

| Framework | Session Persistence | Tool Registry DB | Execution Logging |
|-----------|-------------------|-------------------|-------------------|
| LangChain/LangGraph | SQLite/PostgreSQL checkpointers | None (in-memory) | LangSmith (external) |
| Google ADK | DatabaseSessionService (PostgreSQL) | None (code-defined) | Cloud Trace (OTel) |
| OpenAI Assistants | Cloud-hosted (opaque) | Cloud-hosted | Built-in run tracking |
| CrewAI | None native | None | None |
| AutoGen/AG2 | None native | None | Conversation logs |

Google ADK's `DatabaseSessionService` provides PostgreSQL-backed session persistence, but tool registration remains code-defined and static. Our work extends ADK by making the tool registry itself database-backed and queryable.

### 2.3 Observability and Analytics

LangSmith [8] established the standard for LLM agent observability with a schema centered on **runs** — tree-structured records of agent decisions, LLM calls, and tool invocations. Each run stores inputs, outputs, latency, token counts, and error status.

The OpenTelemetry (OTel) ecosystem, via projects like OpenLLMetry [9] and Arize Phoenix [10], provides vendor-neutral agent tracing using the span model: `{trace_id, span_id, operation_name, attributes, status, duration}`.

For self-evolving agents, execution analytics serve a dual purpose: operational observability **and** feedback for tool improvement. A tool with a declining success rate should trigger the review-fix pipeline automatically — a capability that requires queryable execution logs.

---

## 3. Current Architecture Analysis

### 3.1 What's Stored and Where

| Data Type | Current Storage | Persistence | Limitations |
|-----------|----------------|-------------|-------------|
| Tool metadata | `registry.json` (flat file) | File-based | Full file read/write on every operation; no indexing; no concurrent access |
| Tool source code | `.py` files in `tools/generated/` | File-based | No version history; overwritten on update |
| Session state | ADK in-memory (`tool_context.state`) | Ephemeral | Lost when conversation ends |
| Test results | Local variable in `agent.py` | None | Truncated to 3KB; discarded after registration |
| Safety check results | Return value only | None | No audit trail |
| Tool search | Linear keyword scan | N/A | No ranking; no semantic matching; no analytics |
| Uploaded files | `/tmp/adk_uploads/` | OS temp dir | Deleted on reboot; no metadata tracking |
| Generated outputs | `app/output/<project>/` | File-based | No metadata; no access tracking |
| Telemetry | GCS JSONL (optional) | Cloud storage | Not queryable without BigQuery |

### 3.2 Identified Bottlenecks

1. **Registry concurrency**: `load_registry()` reads the entire JSON file and `save_registry()` writes it back. Concurrent agent sessions would cause race conditions and data loss.

2. **Search quality**: The current `search_tools()` implementation splits the query into words and checks for substring matches in name + description. The query "convert text to web-friendly format" fails to find `url_slugifier_tool` because no words overlap.

3. **Lost evolution history**: `update_tool()` overwrites the registry entry and `.py` file. Previous versions are permanently lost — no rollback, no diff analysis, no learning from past versions.

4. **No execution feedback loop**: Tool invocation results (success/failure, latency, error types) are not recorded. The system cannot learn which tools are reliable or which need improvement.

5. **Pipeline state loss**: If the tool creation pipeline fails mid-way (e.g., network disconnect), all intermediate state (spec, code, tests) is lost. There is no recovery mechanism.

---

## 4. Proposed Architecture

### 4.1 Technology Selection: PostgreSQL with pgvector

We propose PostgreSQL as the unified data layer for the following reasons:

| Requirement | PostgreSQL Capability |
|-------------|----------------------|
| Structured tool metadata | Relational tables with JSONB for flexible schemas |
| Version history | `tool_versions` table with full source code snapshots |
| Semantic tool retrieval | pgvector extension for embedding similarity search |
| Execution analytics | `tool_invocations` table with materialized views for metrics |
| Session persistence | Compatible with ADK's `DatabaseSessionService` |
| Concurrent access | MVCC with row-level locking |
| Safety audit trail | Append-only `safety_checks` table |
| Full-text search | Built-in `tsvector` + `tsquery` for hybrid search |

**Why not SQLite?** While simpler, SQLite's single-writer limitation is incompatible with concurrent multi-agent sessions — a requirement for production deployment and multi-user scenarios.

**Why not a separate vector DB?** pgvector eliminates the operational complexity of running two databases (relational + vector) while providing sufficient performance for our scale (hundreds to low thousands of tools). For datasets under ~1M vectors, pgvector with HNSW indexing matches dedicated vector databases in recall and latency [11].

### 4.2 Database Schema

#### Core Tables

```sql
-- Tool registry (replaces registry.json)
CREATE TABLE tools (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(128) UNIQUE NOT NULL,
    description      TEXT NOT NULL,
    module_path      VARCHAR(256) NOT NULL,
    function_name    VARCHAR(128) NOT NULL,
    input_schema     JSONB NOT NULL,
    output_schema    JSONB NOT NULL,
    risk_level       VARCHAR(16) NOT NULL DEFAULT 'low',
    status           VARCHAR(16) NOT NULL DEFAULT 'active',
    current_version  INTEGER NOT NULL DEFAULT 1,
    source_code      TEXT,
    checksum         VARCHAR(64),
    tags             TEXT[],
    description_embedding VECTOR(768),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Version History

```sql
-- Full version history (currently lost on update)
CREATE TABLE tool_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id         UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    source_code     TEXT NOT NULL,
    spec_snapshot   JSONB NOT NULL,
    test_code       TEXT,
    changelog       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tool_id, version)
);
```

#### Execution Logging

```sql
-- Every tool invocation (currently not recorded)
CREATE TABLE tool_invocations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID,
    tool_name       VARCHAR(128) NOT NULL,
    tool_version    INTEGER,
    input_data      JSONB NOT NULL,
    output_data     JSONB,
    success         BOOLEAN NOT NULL,
    error_message   TEXT,
    error_type      VARCHAR(128),
    latency_ms      INTEGER,
    invoked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Aggregated metrics (materialized view)
CREATE MATERIALIZED VIEW tool_metrics AS
SELECT
    tool_name,
    COUNT(*) AS total_invocations,
    ROUND(100.0 * COUNT(*) FILTER (WHERE success) / NULLIF(COUNT(*), 0), 2)
        AS success_rate_pct,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
    MAX(invoked_at) AS last_used_at
FROM tool_invocations
GROUP BY tool_name;
```

#### Creation Pipeline Tracking

```sql
-- Tool creation attempts (currently ephemeral)
CREATE TABLE creation_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID,
    tool_name       VARCHAR(128) NOT NULL,
    attempt_number  INTEGER NOT NULL,
    phase           VARCHAR(32) NOT NULL,
    success         BOOLEAN NOT NULL,
    error_message   TEXT,
    spec_snapshot   JSONB,
    code_snapshot   TEXT,
    test_snapshot   TEXT,
    duration_ms     INTEGER,
    attempted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Safety Audit Trail

```sql
-- Safety check results (currently discarded)
CREATE TABLE safety_checks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name       VARCHAR(128) NOT NULL,
    version         INTEGER,
    check_type      VARCHAR(32) NOT NULL,
    passed          BOOLEAN NOT NULL,
    violations      TEXT[],
    code_snapshot   TEXT NOT NULL,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.3 Semantic Tool Retrieval

Replace the current keyword-based `search_tools()` with hybrid search combining full-text and vector similarity:

```python
def search_tools(query: str, db: Session, top_k: int = 5):
    query_embedding = embed_text(query)  # via Vertex AI or local model

    results = db.execute(text("""
        SELECT name, description,
            0.3 * ts_rank(to_tsvector('english', description),
                          plainto_tsquery('english', :query))
            + 0.7 * (1 - (description_embedding <=> :embedding::vector))
            AS combined_score
        FROM tools
        WHERE status = 'active'
        ORDER BY combined_score DESC
        LIMIT :top_k
    """), {"query": query, "embedding": query_embedding, "top_k": top_k})

    return results.fetchall()
```

This enables queries like "encode a message in dots and dashes" to find `morse_code_encoder_tool` (semantic match) while "morse" still works (keyword match).

### 4.4 Execution Feedback Loop

The execution analytics table enables an automated improvement cycle:

```
                    ┌─────────────────────────┐
                    │   tool_invocations       │
                    │   (every execution)      │
                    └───────────┬──────────────┘
                                │
                                v
                    ┌─────────────────────────┐
                    │   tool_metrics           │
                    │   (materialized view)    │
                    └───────────┬──────────────┘
                                │
                    ┌───────────┴──────────────┐
                    │                          │
           success_rate < 80%          avg_latency regression
                    │                          │
                    v                          v
           Flag for review            Flag for optimization
                    │                          │
                    v                          v
           tool_review_fixer_agent    tool_creation_pipeline
                    │                 (with optimization hints)
                    v
           tool_versions (new version)
```

This closes the loop: the agent's tools improve based on real usage data, not just initial test cases.

---

## 5. Implementation Strategy

### 5.1 Migration Path

| Phase | Storage | Scope | Timeline |
|-------|---------|-------|----------|
| v0.1 (current) | `registry.json` + `.py` files | Tool CRUD, keyword search | Complete |
| v0.2 (proposed) | PostgreSQL + pgvector | Registry, versions, execution logs, semantic search | 2-3 weeks |
| v0.3 (future) | + Redis cache | Session caching, real-time metrics | 1-2 weeks |

### 5.2 Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | PostgreSQL 16+ | pgvector support, JSONB, ADK compatibility |
| Vector extension | pgvector (HNSW index) | Unified DB, sufficient for <10K tools |
| ORM | SQLAlchemy 2.0 | ADK uses it internally; best pgvector support |
| Migrations | Alembic | Standard for SQLAlchemy; auto-generate from models |
| Embeddings | Vertex AI `text-embedding-004` or local `all-MiniLM-L6-v2` | GCP integration vs. offline capability |

### 5.3 Interface Preservation

The key design constraint is **backward compatibility** with the existing agent code. The `registry/manager.py` functions (`find_tool`, `search_tools`, `register_tool`, `update_tool`, `delete_tool`) keep the same signatures — only the internal implementation changes from JSON I/O to SQLAlchemy queries. The `agent.py` root agent and sub-agents require no modification.

```python
# Before (JSON-backed):
def find_tool(name: str) -> RegistryEntry | None:
    registry = load_registry()            # reads entire JSON file
    entry = registry.get(name)
    return RegistryEntry(**entry) if entry else None

# After (PostgreSQL-backed):
def find_tool(name: str) -> RegistryEntry | None:
    with get_session() as db:
        tool = db.query(Tool).filter_by(name=name, status='active').first()
        return tool.to_registry_entry() if tool else None
```

---

## 6. Comparative Analysis

### 6.1 Our Contributions vs. Related Work

| Capability | VOYAGER | LATM | CREATOR | ToolLLM | **Ours (Proposed)** |
|------------|---------|------|---------|---------|---------------------|
| Persistent tool storage | Vector DB | None | None | JSON file | **PostgreSQL** |
| Version history | No | No | No | No | **Full source + spec snapshots** |
| Safety validation | Env test | Test cases | None | None | **AST analysis + sandbox** |
| Semantic retrieval | ChromaDB | No | No | Neural | **pgvector (hybrid)** |
| Execution analytics | No | No | No | No | **Invocation logs + metrics** |
| Creation audit trail | No | No | No | No | **Per-phase tracking** |
| Multi-agent architecture | No | Maker/User | No | No | **Spec/Code/Test/Register pipeline** |
| Automated improvement | No | No | No | No | **Metrics-driven review loop** |

### 6.2 Gap Addressed

No existing self-evolving agent framework provides a **database-backed tool lifecycle** that combines:
1. Structured metadata storage with version history
2. Semantic retrieval via vector embeddings
3. Execution analytics with automated feedback loops
4. Safety audit trails for generated code

Our proposed architecture is the first to unify these capabilities in a single PostgreSQL instance, using pgvector for semantic search and JSONB for flexible schema storage.

---

## 7. Conclusion

The transition from flat-file storage to a database-backed architecture is not merely an engineering improvement — it enables fundamentally new capabilities for self-evolving agents. Execution analytics create a feedback loop where tools improve based on real usage patterns. Version history enables safe experimentation with tool modifications. Semantic retrieval allows the agent to find relevant tools even when the user's language doesn't match the tool's name. And safety audit trails provide the accountability needed for deployment in regulated environments.

PostgreSQL with pgvector emerges as the optimal choice for this use case, combining relational structure, vector search, and JSON flexibility in a single, well-supported system. The proposed architecture maintains full backward compatibility with the existing Google ADK-based agent while opening the path to production-grade tool lifecycle management.

---

## References

[1] Z. Wang et al., "VOYAGER: An Open-Ended Embodied Agent with Large Language Models," arXiv:2305.16291, 2023.

[2] T. Cai et al., "Large Language Models as Tool Makers," arXiv:2305.17126, 2023.

[3] C. Qian et al., "CREATOR: Tool Creation for Disentangling Abstract and Concrete Reasoning of Large Language Models," arXiv:2305.14318, 2023.

[4] Y. Qin et al., "ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs," arXiv:2307.16789, 2023.

[5] Z. Yuan et al., "CRAFT: Customizing LLMs by Creating and Retrieving from Specialized Toolsets," arXiv:2309.17428, 2024.

[6] Y. Guo et al., "ToolEvo: Adaptive Tool Creation for Enhanced LLM Reasoning," 2024.

[7] Z. Zhang et al., "A Survey on the Memory Mechanism of Large Language Model based Agents," arXiv:2404.13501, 2024.

[8] LangSmith Documentation, LangChain Inc., https://docs.smith.langchain.com, 2024.

[9] OpenLLMetry, Traceloop, https://github.com/traceloop/openllmetry, 2024.

[10] Phoenix, Arize AI, https://github.com/Arize-AI/phoenix, 2024.

[11] pgvector: Open-source vector similarity search for PostgreSQL, https://github.com/pgvector/pgvector, 2024.

[12] N. Packer et al., "MemGPT: Towards LLMs as Operating Systems," arXiv:2310.08560, 2023.

[13] N. Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning," arXiv:2303.11366, 2023.

[14] Google Agent Development Kit (ADK), https://google.github.io/adk-python/, 2025.

[15] Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory, https://github.com/mem0ai/mem0, 2024.

# KG Operating System — Complete Reference

**Version:** 1.0.0
**Date:** February 23, 2026
**Status:** Architecture Specification + Implementation Guide
**Scope:** Query intelligence layer for the Multi-AI Agentic Workspace

---

## Table of Contents

1. [Overview](#1-overview)
2. [The Upper Hand — Competitive Advantage](#2-the-upper-hand--competitive-advantage)
3. [Architecture Overview](#3-architecture-overview)
4. [The Flags Toolkit Inventory](#4-the-flags-toolkit-inventory)
5. [The 56 Semantic Dimensions](#5-the-56-semantic-dimensions)
6. [The 12 Ported Query Methods](#6-the-12-ported-query-methods)
7. [The 4-Weight Scoring Formula](#7-the-4-weight-scoring-formula)
8. [Expert Agent Model](#8-expert-agent-model)
9. [Integration Architecture](#9-integration-architecture)
10. [API Reference](#10-api-reference)
11. [Anti-Patterns and Lessons](#11-anti-patterns-and-lessons)
12. [Terminology Glossary](#12-terminology-glossary)
13. [Evolution Timeline](#13-evolution-timeline)
14. [Roadmap / Future Enhancements](#14-roadmap--future-enhancements)

---

## 1. Overview

### What KG-OS Is

**KG-OS** (Knowledge Graph Operating System) is a **query intelligence layer** that sits between the raw KG storage infrastructure (`kg_service`, `embedding_service`, `analytics_service`) and the 8-stage agentic loop. It is not a database. It is not a search engine. It is an orchestration layer that decides *how* to query, *what* to combine, and *which retrieval mechanisms* to invoke for any given user intent.

KG-OS ports 12 battle-tested query methods from the Flags Toolkit (a standalone CLI query system with 172+ flags, 56 semantic dimensions, and 7 retrieval mechanisms) and adapts them for use inside a web-based agentic workspace. On top of the ported methods it adds:

- **Intent classification** — automatically routing queries to the right retrieval strategy
- **Composition planning** — decomposing multi-step goals into tool chains validated by graph edges
- **Impact analysis** — BFS-based forward/backward propagation to assess change risk
- **Dimension filtering** — filtering nodes by interpretable 0.0-1.0 feature vectors instead of opaque embeddings

The result is what we call **Tailored Expert Agents**: AI agents backed by structured knowledge graphs with intent-driven retrieval. An expert is not merely a persona with a system prompt. It is a persona bound to a specific KG (or set of KGs), with a tuned retrieval configuration, playbook skills, dimension filters, and custom goal mappings. When a user chats with an expert, every response is grounded in structured, cited, graph-traversed knowledge — not in whatever the LLM hallucinated from its training data.

### Why It Matters

Without KG-OS, the workspace has 57 KG databases and a hybrid search formula. That is a library with no librarian. You can search, but the search does not understand your goal. It does not know that "reduce costs" should follow `has_limitation` and `has_workaround` edges. It does not know that "build an ETL pipeline" requires composing three tools connected by `feeds_into` edges.

With KG-OS, the workspace gains a librarian who understands the stacks. A query like "I want to reduce my API costs" no longer returns the 10 most semantically similar nodes. It classifies the intent as `cost_optimization`, invokes `want_to("reduce API costs")` which extracts goal-relevant keywords, applies 5x BM25 weighting on intent terms, boosts nodes connected by `enables` and `optimizes` edge types, filters for nodes where `pricing_tier < 0.3`, and returns a structured, ordered result set with citations back to the graph.

### Core Principles

1. **Structure > Training** — Graph topology encodes more reliable knowledge than embedding similarity
2. **Simple beats complex** — Two retrieval strategies combined correctly (88.5% recall) beat seven strategies mixed together (66.7%)
3. **Intent over keywords** — Users query at three levels: literal ("context caching"), goal-based ("reduce costs"), benefit-focused ("90% savings")
4. **Interpretable over opaque** — 56 named dimensions (0.0-1.0 scale) beat 768 opaque embedding dimensions for filtering and debugging
5. **Composition over selection** — The best answer is often a workflow of connected nodes, not a single node

---

## 2. The Upper Hand — Competitive Advantage

### The Competitive Landscape

Every AI platform offers some form of knowledge retrieval. Here is how they compare on the dimensions that matter for expert-grade agents.

#### OpenClaw (200K+ GitHub Stars)

OpenClaw stores knowledge in flat markdown files: `SOUL.md`, `USER.md`, `TOOLS.md`, `SKILL.md` folders. The runtime performs keyword matching to inject relevant skill files per conversation turn. Skills are modular but unstructured — there are no typed relationships between skills, no graph edges connecting prerequisites to outcomes, no semantic dimensions measuring complexity or cost.

| Dimension | OpenClaw | KG-OS |
|-----------|----------|-------|
| Knowledge format | Flat markdown files | Structured SQLite KGs (57 databases) |
| Relationships | None (file-level only) | Typed edges: `requires`, `enables`, `feeds_into`, `has_limitation`, `has_workaround` |
| Search mechanism | Keyword matching on filenames + content | 7 retrieval mechanisms with 4-weight scoring |
| Semantic dimensions | None | 56 interpretable dimensions (0.0-1.0) |
| Composition detection | None — skills are independent | Graph-validated multi-tool workflows via `feeds_into` edges |
| Impact analysis | None | BFS forward/backward propagation with risk scoring |
| Community size | 200K+ stars, ClawHub marketplace | Focused workspace with 57 KGs, 2,057+ nodes |

**The gap:** OpenClaw's skill system is flat. Skill A does not "know" it requires Skill B. There is no graph to traverse, no edge types to boost, no dimensions to filter. When a user asks "how do I build a secure API?", OpenClaw matches the keyword "API" against skill files. KG-OS traverses from `goal:build_secure_api` through `requires` edges to find authentication patterns, follows `has_limitation` edges to flag known gaps, and returns a composition plan with prerequisites ordered by dependency.

#### ChatGPT Custom GPTs

Custom GPTs store knowledge as markdown instructions in the system prompt plus uploaded files processed by a RAG pipeline. The RAG is vector-similarity only — no graph traversal, no edge-type boosting, no intent routing. Instructions are static; there is no query-time adaptation based on user intent.

| Dimension | Custom GPTs | KG-OS |
|-----------|-------------|-------|
| Knowledge format | System prompt + uploaded files | Structured KGs with typed nodes and edges |
| Retrieval | Vector similarity (single strategy) | 7 mechanisms with configurable weights |
| Intent routing | None — same retrieval for every query | 14 intent categories with method selection |
| Composition | None | Sub-goal decomposition + edge-validated workflows |
| Dimensions | Opaque embeddings only | 56 interpretable + opaque embeddings |
| Multi-source | Single GPT = single knowledge scope | Expert can span multiple KGs |

#### LangChain / LlamaIndex RAG

Standard RAG pipelines (LangChain, LlamaIndex, Haystack) combine document chunking + vector embedding + similarity retrieval. Some add reranking or hybrid search. None provide:

- **Graph traversal** — following typed edges to expand context beyond vector similarity
- **Edge-type boosting** — boosting neighbors connected by goal-relevant edge types
- **Intent classification** — routing to different algorithms based on query intent
- **Semantic dimension filtering** — filtering by named dimensions before scoring
- **Composition planning** — multi-tool workflow generation validated by graph structure
- **Impact analysis** — assessing downstream effects of changes via BFS propagation

| Dimension | Standard RAG | KG-OS |
|-----------|-------------|-------|
| Retrieval | Vector similarity + optional BM25 | Embedding + BM25 + FTS5 + graph boost + intent + dimension filter + Jaccard |
| Graph awareness | None | Full graph traversal, neighbor expansion, community detection |
| Edge types | None (documents have no typed relationships) | Multiple typed edges: `requires`, `enables`, `feeds_into`, `similar_to`, `has_limitation` |
| Result format | Ranked chunks | Ranked nodes with edge annotations, composition plans, impact graphs |
| Interpretability | Opaque similarity scores | Named dimensions + hybrid score breakdown |

### The Financial Advisor Example

Consider building a financial advisor expert agent. The goal: help users with investment and tax strategy.

**With flat markdown (OpenClaw/Custom GPTs):**

You write a long markdown document listing tax tips, investment strategies, and regulatory notes. When a user asks "how do I reduce my taxes?", the system does keyword search or vector similarity against this document. It returns chunks about taxes. There is no structure — no way to know that "Roth conversion" *requires* "income threshold check" which *has_limitation* "5-year rule". The agent might suggest a Roth conversion without mentioning the 5-year rule because that text was in a different chunk that did not match.

**With KG-OS:**

You build a financial KG with structured nodes and typed edges:

```
tax_strategy:roth_conversion
  --[requires]--> check:income_threshold
  --[requires]--> check:5_year_rule
  --[has_limitation]--> limitation:5_year_holding_period
  --[enables]--> goal:tax_free_growth
  --[optimizes]--> dimension:tax_efficiency (0.9)
  --[optimizes]--> dimension:long_term_growth (0.8)
```

When the user asks "how do I reduce my taxes?":

1. **Intent classification** identifies `cost_optimization` (mapped to tax reduction)
2. **`want_to("reduce taxes")`** extracts goal keywords, searches with 5x BM25 boost on intent terms
3. **Edge-type boosting** amplifies nodes connected by `enables` and `optimizes` edges to tax-related goals
4. **Graph traversal** follows `requires` edges from `roth_conversion` to find prerequisites
5. **Limitation detection** follows `has_limitation` edges to surface the 5-year rule *automatically*
6. **Dimension filtering** ranks strategies by `tax_efficiency > 0.7`
7. **Result assembly** returns an ordered response with citations: "Consider a Roth conversion (Node: tax_strategy:roth_conversion). Prerequisites: verify your income is below the threshold (Node: check:income_threshold). Important limitation: you must hold the account for 5 years (Node: limitation:5_year_holding_period)."

The agent cannot miss the 5-year rule because it is structurally connected. The graph enforces completeness that flat text cannot.

---

## 3. Architecture Overview

### System Diagram

```
                         USER QUERY
                             |
                             v
                  +---------------------+
                  |  Intent Classifier   |  14 intent categories
                  |  (keyword patterns)  |  via weighted matching
                  +---------------------+
                             |
                   classifies intent
                             |
                             v
+------------------------------------------------------------------+
|                        KG-OS QUERY ENGINE                         |
|                                                                   |
|  +----------------------------------------------------------+    |
|  |                  Method Router                            |    |
|  |  Routes to one or more of 12 query methods:               |    |
|  |                                                           |    |
|  |  want_to | can_it | compose_for | similar_to              |    |
|  |  impact_analysis | dimension_filter | trace_path           |    |
|  |  explore_smart | intent_search | classify_intent           |    |
|  |  _keyword_match_nodes | _edge_type_boost                  |    |
|  +----------------------------------------------------------+    |
|                             |                                    |
|                    invokes retrieval                              |
|                             |                                    |
|  +----------------------------------------------------------+    |
|  |              7 Retrieval Mechanisms                        |    |
|  |                                                           |    |
|  |  1. SQL LIKE (name/type/properties)                       |    |
|  |  2. FTS5 full-text search                                 |    |
|  |  3. BM25 scoring (pure Python)                            |    |
|  |  4. Embedding cosine similarity (numpy)                   |    |
|  |  5. Graph neighbor boosting (outgoing 0.5, incoming 0.3)  |    |
|  |  6. Jaccard similarity (neighbor overlap)                 |    |
|  |  7. Dimension-filtered SQL (json_extract thresholds)      |    |
|  +----------------------------------------------------------+    |
|                             |                                    |
|                    produces scores                                |
|                             |                                    |
|  +----------------------------------------------------------+    |
|  |            4-Weight Score Combiner                         |    |
|  |                                                           |    |
|  |  score = alpha * embedding_score                          |    |
|  |        + beta  * text_score                               |    |
|  |        + gamma * graph_score                              |    |
|  |        + delta * intent_score                             |    |
|  |                                                           |    |
|  |  Default: 0.35 + 0.40 + 0.15 + 0.10                      |    |
|  +----------------------------------------------------------+    |
|                             |                                    |
+------------------------------------------------------------------+
                              |
                     ranked results
                              |
                              v
                 +------------------------+
                 | Expert Context Assembly |
                 |                        |
                 | - Expert persona       |
                 | - Top-K KG nodes       |
                 | - Edge annotations     |
                 | - Dimension hints      |
                 | - Composition plan     |
                 | - Playbook excerpts    |
                 +------------------------+
                              |
                   assembled context
                              |
                              v
+------------------------------------------------------------------+
|                    8-STAGE AGENTIC LOOP                           |
|                                                                   |
|  1. INTAKE      -> detect expert mode, parse messages             |
|  2. MEMORY      -> recall from conversation + workspace memory    |
|  3. SKILL INJ.  -> inject expert's playbook skills                |
|  4. CONTEXT     -> assemble persona + KG context + dimensions     |
|  5. INFERENCE   -> stream from Gemini or Claude                   |
|  6. TOOL EXEC   -> execute function calls if applicable           |
|  7. STREAM      -> yield SSE tokens to frontend                   |
|  8. PERSIST     -> save messages, extract memories, log analytics |
+------------------------------------------------------------------+
                              |
                              v
                    STREAMING RESPONSE
                    (with KG citations)
```

### Layer Positioning

KG-OS does not replace the existing services. It wraps and orchestrates them.

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTIC LOOP (consumer)                   │
│  agentic_loop.py — 8 stages, SSE streaming                  │
├─────────────────────────────────────────────────────────────┤
│                    KG-OS (orchestrator)        <-- NEW LAYER │
│  kgos_service.py — intent routing, composition, scoring      │
├─────────────────────────────────────────────────────────────┤
│                 EXISTING SERVICES (providers)                │
│                                                             │
│  kg_service.py          — CRUD, schema detection, FTS       │
│  embedding_service.py   — BM25, cosine, graph boost         │
│  analytics_service.py   — NetworkX centrality, communities  │
│  rag_chat_service.py    — retrieval + generation            │
│  skill_injector.py      — intent classification, playbooks  │
│  memory_service.py      — conversation + workspace memory   │
├─────────────────────────────────────────────────────────────┤
│               STORAGE (57 SQLite KG databases)               │
│                                                             │
│  6 schema profiles: unified, standard, claude, hal,          │
│                     from_node, entities                      │
│  Auto-detection via column heuristics                        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow for a Single Expert Query

```
1. User sends message to expert "PyGuru"
2. Frontend calls POST /api/experts/{id}/chat
3. Router resolves expert config: kg_db_id="python-kg", retrieval={...}
4. KG-OS intent_search() is invoked:
   a. classify_intent(query) -> "coding_help" (score 1.6)
   b. want_to(db_id, goal) -> 15 candidate nodes
   c. _edge_type_boost(db_id, candidate_ids, ["requires", "enables"]) -> boosted scores
   d. dimension_filter(db_id, {"code_generation_strength": {"min": 0.7}}) -> filtered set
   e. Score combiner: alpha*emb + beta*text + gamma*graph + delta*intent -> final ranking
5. Top 10 nodes + edge annotations + composition plan assembled
6. Expert persona + KG context injected into system prompt
7. Agentic loop streams response from Gemini/Claude
8. Response includes inline citations: [Source: python-kg:decorators_pattern]
```

---

## 4. The Flags Toolkit Inventory

The Flags Toolkit is the standalone CLI predecessor to KG-OS. It was built as a set of Python scripts operating directly on SQLite knowledge graph databases, with 172+ command-line flags spanning 6 query tools. KG-OS ports the most valuable algorithms from this toolkit into the workspace's service layer.

### The 6 Query Tools

| Tool | File | Flags | Primary Algorithm | Purpose |
|------|------|-------|-------------------|---------|
| **query-cookbook.py** | `docs/flags/query-cookbook.py` | 63 | Intent-driven + Jaccard + BFS | Main query interface: discovery, intent, composition, ML |
| **kg-ask.py** | `docs/flags/kg-ask.py` | 10 | Natural language -> graph query | Ask questions in plain English |
| **kg-query-unified.py** | `docs/flags/kg-query-unified.py` | 12 | Cross-KG unified search | Query both manual + auto-extracted KGs simultaneously |
| **kg-pattern-mapper.py** | `docs/flags/kg-pattern-mapper.py` | 11 | Pattern -> code file mapping | Find implementation files for KG patterns |
| **kg-impact-analyzer.py** | `docs/flags/kg-impact-analyzer.py` | 9 | BFS propagation + risk scoring | Analyze upstream/downstream impact of changes |
| **kg-critical-components.py** | `docs/flags/kg-critical-components.py` | 11 | Centrality + dependency analysis | Identify testing priorities and bottlenecks |

### The 172+ CLI Flags by Category

| Category | Count | Representative Flags |
|----------|-------|---------------------|
| **Discovery** | 8 | `--find`, `--emerge`, `--discover`, `--stats`, `--whats-new`, `--list`, `--schema`, `--random` |
| **Intent-Based** | 7 | `--want-to`, `--can-it`, `--how-does`, `--compose-for`, `--alternatives`, `--why-not`, `--optimize-for` |
| **Exploration** | 7 | `--trace`, `--related`, `--dependencies`, `--used-by`, `--explore`, `--depth`, `--max-results` |
| **Analysis** | 6 | `--impact`, `--critical`, `--bottleneck`, `--coverage`, `--gaps`, `--risk` |
| **Filtering** | 8 | `--type`, `--edge-type`, `--min-edges`, `--max-edges`, `--property`, `--has-property`, `--dimension`, `--threshold` |
| **ML Intelligence** | 4 | `--recommend`, `--similar-to`, `--rank`, `--explore-smart` |
| **Export** | 5 | `--format`, `--output`, `--json`, `--csv`, `--markdown` |
| **Cross-KG** | 6 | `--db`, `--manual`, `--auto`, `--unified`, `--merge-results`, `--compare` |
| **Pattern Mapping** | 5 | `--pattern`, `--implementation`, `--arsenal`, `--source-file`, `--coverage` |
| **Impact Analysis** | 5 | `--direction`, `--forward`, `--backward`, `--max-depth`, `--risk-threshold` |
| **Criticality** | 5 | `--metric`, `--degree`, `--betweenness`, `--pagerank`, `--top-k` |
| **Configuration** | 8 | `--verbose`, `--quiet`, `--color`, `--no-color`, `--timeout`, `--cache`, `--parallel`, `--dry-run` |
| **Dimensional** | 5 | `--score-dimensions`, `--dimension-profile`, `--compare-dimensions`, `--dimension-range`, `--auto-dimensions` |
| **Natural Language** | 5 | `--ask`, `--explain`, `--summarize`, `--context`, `--follow-up` |
| **Batch Operations** | 6 | `--batch`, `--pipeline`, `--validate`, `--import`, `--export-graph`, `--estimate-cost` |

### The 7 Retrieval Mechanisms

| # | Mechanism | Implementation | Speed | Recall | Use Case |
|---|-----------|---------------|-------|--------|----------|
| 1 | **SQL LIKE** | `SELECT ... WHERE name LIKE ?` | <1ms | Low | Exact substring match |
| 2 | **FTS5 Full-Text Search** | SQLite FTS5 virtual table with MATCH | <5ms | Medium | Tokenized text search |
| 3 | **BM25 Scoring** | Pure Python TF-IDF with length normalization | <10ms | Medium-High | Keyword relevance ranking |
| 4 | **Embedding Cosine Similarity** | numpy dot product on stored vectors | <50ms | Medium | Semantic similarity |
| 5 | **Graph Neighbor Boosting** | Edge traversal: outgoing +0.5, incoming +0.3 | <10ms | Additive | Structural proximity |
| 6 | **Jaccard Similarity** | `intersection(neighbors) / union(neighbors)` | <10ms | Medium | Structural similarity between nodes |
| 7 | **Dimension-Filtered SQL** | `json_extract(properties, '$.dim') > threshold` | <5ms | Precision | Narrow by interpretable features |

### The 3 KG Databases (Flags Toolkit Source)

| Database | Nodes | Edges | Construction | Schema |
|----------|-------|-------|-------------|--------|
| **claude-cookbook-kg.db** (manual) | 266 | 605 | Hand-curated from 23 playbooks, 26 guides | claude profile |
| **kg-extractor-v2-complete.db** (auto) | 1,791 | 283,166 | AST + regex extraction from codebase | standard profile |
| **unified-kg.db** (merged) | 2,057 | 284,178 | Union merge of manual + auto | unified profile |

### The 3-Tier Extraction Pipeline

```
Tier 1: Structure Extraction
  Input:  Source code files
  Method: AST parsing (Python), regex (JSON, YAML, Markdown)
  Output: Functions, classes, modules, configs as nodes
          Import/call relationships as edges

Tier 2: Pattern Extraction
  Input:  Tier 1 nodes + documentation
  Method: Pattern matching against known templates
  Output: Design patterns, architectural patterns, anti-patterns
          pattern_instance_of, pattern_alternative_to edges

Tier 3: Semantic Extraction
  Input:  Tier 1 + Tier 2 nodes + natural language docs
  Method: AI entity extraction (Gemini) + manual curation
  Output: Concepts, goals, capabilities, limitations
          enables, requires, has_limitation, has_workaround edges
```

### The 12 Validation Rules

| Rule | Check | Severity |
|------|-------|----------|
| 1 | Every node has a non-empty name | ERROR |
| 2 | Every node has a valid type | ERROR |
| 3 | Every edge references existing source and target nodes | ERROR |
| 4 | No self-referencing edges (source != target) | WARNING |
| 5 | No duplicate edges (same source + target + type) | WARNING |
| 6 | Every node is reachable from at least one other node (no orphans) | WARNING |
| 7 | Edge types are from the allowed vocabulary | WARNING |
| 8 | Node properties are valid JSON | ERROR |
| 9 | No circular `requires` chains (A requires B requires A) | ERROR |
| 10 | `has_workaround` edges have a corresponding `has_limitation` edge | WARNING |
| 11 | `feeds_into` chains form a DAG (no cycles) | ERROR |
| 12 | Nodes with `has_limitation` edges have at least one `has_workaround` or explicit "no_workaround" property | INFO |

### Pluggable Embeddings

| Strategy | Dimensions | Dependency | Cost | Offline |
|----------|-----------|------------|------|---------|
| **TF-IDF + LSA** | 384 | scikit-learn (optional) | $0 | Yes |
| **Model2Vec (potion-base-8M)** | 256 | model2vec package | $0 | Yes |
| **Gemini Embedding API** | 768 | google-genai SDK + API key | ~$0.0001/1K tokens | No |
| **Self-supervised (InfoNCE)** | 256 | numpy | $0 | Yes |

The workspace defaults to Model2Vec for 256-dim embeddings (offline, zero cost) and falls back to Gemini API when stored embeddings use higher dimensions.

---

## 5. The 56 Semantic Dimensions

### What Semantic Dimensions Are

Semantic dimensions are **interpretable feature vectors** assigned to knowledge graph nodes. Each dimension is a named float value on a 0.0 to 1.0 scale, representing a specific measurable aspect of the node. Unlike opaque 768-dimensional embeddings from a language model, semantic dimensions are:

1. **Named** — you know what each dimension measures
2. **Interpretable** — `latency_sensitivity: 0.9` means "this tool is very sensitive to latency"
3. **Filterable** — you can query `WHERE pricing_tier < 0.3` (only cheap tools)
4. **Comparable** — you can compare two nodes on specific axes
5. **Debuggable** — when results are wrong, you can see which dimension caused it

### Full Dimension Catalog

#### Performance & Cost (8 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `latency_sensitivity` | How sensitive the tool/pattern is to response time | Tolerant of delays | Requires sub-second responses |
| `throughput_requirement` | Volume of data/requests it needs to handle | Single requests | High-volume batch processing |
| `pricing_tier` | Cost level of the tool or API | Free / very cheap | Expensive per-call pricing |
| `token_efficiency` | How efficiently it uses tokens | Token-heavy | Minimal token usage |
| `batch_suitability` | How well it works with batch processing | Real-time only | Designed for batch |
| `cache_effectiveness` | Benefit from caching strategies | No caching benefit | Massive savings from caching |
| `rate_limit_sensitivity` | Impact of rate limits on functionality | Unaffected | Severely constrained |
| `compute_intensity` | CPU/memory requirements | Lightweight | Heavy compute |

#### Complexity & Effort (6 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `implementation_complexity` | Difficulty to implement correctly | Copy-paste simple | Requires deep expertise |
| `configuration_depth` | Amount of configuration needed | Zero-config | Complex multi-file config |
| `learning_curve` | Time to become proficient | Minutes | Weeks of study |
| `error_handling_need` | Importance of robust error handling | Errors are rare/benign | Errors are common/critical |
| `debugging_difficulty` | How hard it is to debug when broken | Obvious error messages | Silent failures, complex state |
| `maintenance_burden` | Ongoing maintenance required | Set and forget | Frequent updates needed |

#### Interaction Patterns (7 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `streaming_support` | Capability for streaming responses | Batch-only | Full streaming support |
| `batching_capability` | Support for batched operations | Single-item only | Native batch APIs |
| `async_compatibility` | Works with async/await patterns | Sync-only | Fully async |
| `real_time_requirement` | Needs real-time interaction | Offline/async is fine | Must be real-time |
| `multi_turn_depth` | Benefit from multi-turn conversation | Single-turn sufficient | Deep multi-turn needed |
| `context_dependency` | How much context affects behavior | Context-independent | Highly context-dependent |
| `state_management` | Statefulness requirements | Stateless | Complex state tracking |

#### Data Characteristics (6 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `data_volume_sensitivity` | How data size affects performance | Small data only | Handles massive datasets |
| `format_flexibility` | Range of input formats accepted | Single format | Any format |
| `schema_strictness` | How strict the expected schema is | Schema-free | Exact schema required |
| `data_sensitivity_level` | Privacy/security classification of data | Public data | PII/PHI/classified |
| `multimodal_support` | Works with non-text modalities | Text-only | Images, audio, video |
| `structured_vs_unstructured` | Type of data it handles best | Unstructured text | Structured data (JSON, SQL) |

#### API Capabilities (8 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `tool_use_support` | Support for function calling / tool use | No tool use | Rich tool ecosystem |
| `system_prompt_control` | How much system prompts influence behavior | Minimal effect | Full behavioral control |
| `temperature_sensitivity` | Impact of temperature parameter | No effect | Dramatically changes output |
| `max_context_utilization` | How much of the context window it uses | Short prompts | Uses full context window |
| `function_calling_depth` | Sophistication of function calling | None | Multi-step function chains |
| `grounding_support` | Built-in grounding/citation capabilities | No grounding | Native grounding |
| `safety_filter_level` | Aggressiveness of safety filtering | Permissive | Very strict |
| `output_format_control` | Control over response format | Free-form only | JSON, XML, structured |

#### Problem Domains (7 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `code_generation_strength` | Quality of generated code | Poor/no code ability | Excellent, production-ready |
| `analytical_reasoning` | Ability to analyze and reason | Shallow analysis | Deep multi-step reasoning |
| `creative_capability` | Creative writing, brainstorming | Formulaic | Highly creative |
| `instruction_following` | Adherence to complex instructions | Ignores constraints | Precise instruction following |
| `multilingual_support` | Proficiency across languages | English-only | 100+ languages |
| `summarization_quality` | Quality of text summarization | Poor compression | Excellent distillation |
| `extraction_accuracy` | Accuracy of information extraction | Misses entities | Precise, complete extraction |

#### Architectural Patterns (5 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `rag_suitability` | How well it works in RAG pipelines | Not suitable | Designed for RAG |
| `agent_compatibility` | Works as an autonomous agent | Not agentic | Full agent loop |
| `fine_tuning_benefit` | Improvement from fine-tuning | Minimal benefit | Massive improvement |
| `pipeline_composability` | Can be composed into larger pipelines | Standalone only | Highly composable |
| `orchestration_complexity` | Complexity of orchestrating with other tools | Simple integration | Complex orchestration |

#### NLKE Meta-Dimensions (3 dimensions)

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `knowledge_density` | Information density of the node | Sparse, mostly boilerplate | Dense, every word matters |
| `relationship_richness` | Number and quality of graph connections | Isolated node | Hub with many typed edges |
| `emergence_potential` | Likelihood of producing emergent insights | Predictable | Produces unexpected combinations |

#### CLI Tool Characteristics (6 dimensions)

These dimensions were contributed by the gemini-3-pro project to the NLKE ecosystem, specifically modeling command-line tool behaviors.

| Dimension | Description | Low (0.0) | High (1.0) |
|-----------|-------------|-----------|------------|
| `file_system_dependency` | How much the tool depends on filesystem state | No FS access | Heavy FS read/write |
| `git_integration_level` | Coupling with git operations | No git awareness | Deep git integration |
| `shell_command_execution` | Executes shell commands | No shell access | Runs arbitrary commands |
| `sandbox_sensitivity` | Behavior changes in sandboxed environments | Works anywhere | Breaks in sandbox |
| `permission_requirement_level` | System permissions needed | No special permissions | Root/admin required |
| `idempotency_guarantee` | Safe to run multiple times | Side effects on each run | Fully idempotent |

### How Dimensions Enable Filtering

Dimensions are stored in the node's `properties` JSON column. KG-OS can filter on them using SQL:

```sql
-- Find all tools suitable for cost-sensitive batch processing
SELECT * FROM nodes
WHERE json_extract(properties, '$.pricing_tier') < 0.3
  AND json_extract(properties, '$.batch_suitability') > 0.7
  AND json_extract(properties, '$.rate_limit_sensitivity') < 0.5;
```

In the KG-OS API, this becomes:

```python
dimension_filter(
    db_id="python-kg",
    filters={
        "pricing_tier": {"max": 0.3},
        "batch_suitability": {"min": 0.7},
        "rate_limit_sensitivity": {"max": 0.5},
    },
    limit=20
)
```

### Why 56 Named Dimensions Beat 768 Opaque Dimensions

| Aspect | 56 Named Dimensions | 768 Opaque Embeddings |
|--------|--------------------|-----------------------|
| **Filtering** | `WHERE pricing_tier < 0.3` | Cannot filter on a specific axis |
| **Debugging** | "Ranked wrong because `latency_sensitivity` was 0.1" | "Cosine similarity was 0.73" (why?) |
| **Composition** | Combine dimensions from different KGs | Embeddings from different models are incompatible |
| **Human review** | Expert can verify each dimension value | Expert cannot read 768-dim vectors |
| **Updates** | Change one dimension without retraining | Must regenerate entire embedding |
| **Size** | 56 floats = 224 bytes | 768 floats = 3,072 bytes |

The two approaches are complementary. KG-OS uses both: opaque embeddings for broad semantic similarity (alpha weight), and named dimensions for precise filtering and debugging (delta weight via dimension-aware intent scoring).

---

## 6. The 12 Ported Query Methods

### Method Reference Table

| # | Method | Source Tool | Algorithm | Returns |
|---|--------|-------------|-----------|---------|
| 1 | `intent_search` | Master orchestrator | Combines all strategies with configurable weights | Ranked nodes with scores |
| 2 | `want_to` | query-cookbook.py | Keyword extraction + FTS + edge-type boosting | Goal-relevant nodes |
| 3 | `can_it` | query-cookbook.py | Search + limitation/workaround edge traversal | Capability assessment |
| 4 | `compose_for` | query-cookbook.py | Sub-goal decomposition + `feeds_into`/`requires` validation | Workflow plan |
| 5 | `similar_to` | query-cookbook.py | `0.70*Jaccard + 0.20*type + 0.10*name` | Similar nodes |
| 6 | `impact_analysis` | kg-impact-analyzer.py | BFS forward/backward with risk scoring | Impact graph |
| 7 | `dimension_filter` | generative_synthesis_flags | SQL `json_extract()` with thresholds | Filtered node set |
| 8 | `classify_intent` | skill_injector.py (enhanced) | 14 intent categories via keyword patterns | Intent + score |
| 9 | `trace_path` | query-cookbook.py | BFS shortest path with edge annotations | Path with edges |
| 10 | `explore_smart` | query-cookbook.py | BFS with hub detection per level | Exploration tree |
| 11 | `_keyword_match_nodes` | Base layer | SQL LIKE on name/type/properties | Raw matches |
| 12 | `_edge_type_boost` | Graph boost (enhanced) | Edge-type-filtered neighbor boosting | Boosted scores |

### Method 1: `intent_search(db_id, query, config)`

**The master orchestrator.** This is the method called by the expert chat endpoint. It combines all other methods into a single ranked result.

**Algorithm:**

```
1. classify_intent(query) -> top intents
2. For each strategy enabled in config:
   a. Run embedding_service.search() -> embedding scores
   b. Run BM25 scoring -> text scores
   c. Run _keyword_match_nodes() -> exact matches
   d. If intent.type == "goal": Run want_to() -> goal-relevant nodes
   e. If intent.type == "capability": Run can_it() -> capability results
   f. If intent.type == "composition": Run compose_for() -> workflow
3. Merge scores using 4-weight formula
4. Apply dimension_filter() if expert has dimension_filters configured
5. Expand top-3 results with get_neighbors(depth=1)
6. Return ranked results with edge annotations
```

**Signature:**

```python
def intent_search(
    self,
    db_id: str,
    query: str,
    config: RetrievalConfig | None = None,
) -> IntentSearchResult:
    """
    Args:
        db_id: Database identifier
        query: User's natural language query
        config: Optional retrieval config (weights, limits, filters)
    Returns:
        IntentSearchResult with ranked nodes, intent, composition plan
    """
```

**Example:**

```python
result = kgos.intent_search("python-kg", "how do I optimize my database queries?")
# result.intent = ("performance", 1.3)
# result.nodes = [
#     {node: {id: "...", name: "query_optimization", type: "pattern"},
#      score: 0.87, method: "text+graph+intent"},
#     {node: {id: "...", name: "connection_pooling", type: "technique"},
#      score: 0.76, method: "text+graph"},
#     ...
# ]
# result.edges = [{source: "query_optimization", target: "indexing", type: "requires"}, ...]
```

### Method 2: `want_to(db_id, goal, k=10)`

**Goal-based discovery.** Given a user's goal (e.g., "reduce API costs", "build a REST API"), find the nodes that enable achieving that goal.

**Algorithm:**

```
1. Extract goal keywords from the goal string
   - Split on spaces, remove stopwords
   - Identify intent keywords (5x BM25 weight): "reduce", "build", "optimize", "secure"
2. Run FTS5 MATCH with extracted keywords
3. Run BM25 with intent keyword boosting (k1=1.5, b=0.75, intent_weight=5.0)
4. For matching nodes, traverse edges:
   - Follow "enables" edges outward (these nodes enable the goal)
   - Follow "requires" edges inward (these are prerequisites)
   - Follow "optimizes" edges (these improve goal-related metrics)
5. Boost neighbors connected by goal-relevant edge types
6. Return top-k results ranked by combined text + edge-type boost score
```

**Signature:**

```python
def want_to(
    self,
    db_id: str,
    goal: str,
    k: int = 10,
) -> list[dict]:
    """
    Returns list of {node, score, path} dicts ordered by goal relevance.
    """
```

**Example:**

```python
results = kgos.want_to("claude-cookbook-kg", "build autonomous agents")
# Returns nodes like:
#   agent_development_pattern (score: 0.92) -- via "enables" edge
#   react_pattern (score: 0.85) -- via "requires" edge
#   tool_use_capability (score: 0.78) -- via "requires" edge
```

### Method 3: `can_it(db_id, capability)`

**Capability checking with blockers and workarounds.** Given a capability question (e.g., "handle binary files", "process images"), determine if the KG's subject can do it, what limitations exist, and what workarounds are available.

**Algorithm:**

```
1. Search for nodes matching the capability query (FTS + BM25)
2. For each matching node:
   a. Follow "has_limitation" edges -> collect limitations
   b. Follow "has_workaround" edges -> collect workarounds
   c. Follow "requires" edges -> collect prerequisites
3. Classify result:
   - "yes" — capability node found, no blocking limitations
   - "yes_with_limitations" — found but has limitations with workarounds
   - "no" — capability node found with blocking limitations and no workarounds
   - "unknown" — no matching capability node found
4. Return capability assessment with limitations, workarounds, prerequisites
```

**Signature:**

```python
def can_it(
    self,
    db_id: str,
    capability: str,
) -> CapabilityResult:
    """
    Returns:
        CapabilityResult with status, limitations, workarounds, prerequisites
    """
```

**Example:**

```python
result = kgos.can_it("claude-code-tools-kg", "edit binary files")
# result.status = "yes_with_limitations"
# result.limitations = [
#     {name: "binary_edit_limitation", description: "Edit tool works on text only"}
# ]
# result.workarounds = [
#     {name: "base64_workaround", description: "Encode to base64, edit, decode back"}
# ]
```

### Method 4: `compose_for(db_id, goal, max_tools=5)`

**Multi-tool composition planning.** Given a complex goal, decompose it into sub-goals, find the best tool/node for each sub-goal, and validate the composition through graph edges (`feeds_into`, `requires`).

**Algorithm:**

```
1. Decompose goal into sub-goals:
   - Split on conjunctions ("and", "then", "after")
   - Identify action verbs as sub-goal anchors
   - Example: "read CSV files and analyze trends" -> ["read CSV files", "analyze trends"]
2. For each sub-goal:
   a. Run want_to(db_id, sub_goal, k=3) -> candidate tools
   b. Select best candidate by score
3. Validate composition:
   a. Check for "feeds_into" edges between consecutive tools
   b. Check for "requires" edges to identify missing prerequisites
   c. Check for "conflicts_with" edges to flag incompatibilities
4. Build execution plan:
   - Ordered list of tools
   - Edge annotations between steps
   - Missing prerequisites as warnings
   - Alternative paths if conflicts detected
5. Return CompositionPlan
```

**Signature:**

```python
def compose_for(
    self,
    db_id: str,
    goal: str,
    max_tools: int = 5,
) -> CompositionPlan:
    """
    Returns:
        CompositionPlan with steps, edges, prerequisites, warnings
    """
```

**Example:**

```python
plan = kgos.compose_for("claude-cookbook-kg", "refactor Python files and run tests")
# plan.steps = [
#     Step(tool="code_search", action="find files to refactor"),
#     Step(tool="edit_tool", action="apply refactoring"),
#     Step(tool="bash_tool", action="run test suite"),
# ]
# plan.edges = [
#     {from: "code_search", to: "edit_tool", type: "feeds_into"},
#     {from: "edit_tool", to: "bash_tool", type: "feeds_into"},
# ]
# plan.prerequisites = ["git_status_check"]
```

### Method 5: `similar_to(db_id, node_id, k=10)`

**Structural similarity via Jaccard coefficient.** Find nodes that are structurally similar to a given node based on neighbor overlap, type matching, and name similarity.

**Algorithm:**

```
1. Get neighbors of the target node -> set A
2. For every other node in the graph:
   a. Get neighbors -> set B
   b. Compute Jaccard: |A intersection B| / |A union B|
   c. Compute type_match: 1.0 if same node type, 0.0 otherwise
   d. Compute name_overlap: shared_words / total_unique_words
3. Combined score = 0.70 * Jaccard + 0.20 * type_match + 0.10 * name_overlap
4. Return top-k by combined score
```

**Signature:**

```python
def similar_to(
    self,
    db_id: str,
    node_id: str,
    k: int = 10,
) -> list[dict]:
    """
    Returns list of {node, score, jaccard, type_match, name_overlap} dicts.
    """
```

**Why Jaccard instead of embedding cosine:** Jaccard similarity operates on the graph structure itself — two nodes are similar if they connect to the same neighbors. This captures structural roles that embedding similarity might miss. A "configuration" node and a "settings" node might have different embeddings but connect to the same tools, making them structurally equivalent.

### Method 6: `impact_analysis(db_id, node_id, direction="both", max_depth=3)`

**BFS propagation with risk scoring.** Given a node, trace all upstream (what depends on it) and downstream (what it depends on) connections to assess the impact of changing or removing that node.

**Algorithm:**

```
1. Initialize BFS from node_id
2. For each depth level (1 to max_depth):
   a. Follow edges in specified direction:
      - "forward": follow outgoing edges (what this node affects)
      - "backward": follow incoming edges (what affects this node)
      - "both": follow both directions
   b. For each discovered node:
      - risk_score = 1.0 / depth (closer = higher risk)
      - Multiply by edge_weight if available
      - Multiply by node_criticality (degree centrality)
3. Aggregate:
   - total_impacted_nodes: count of all discovered nodes
   - risk_by_depth: {depth: [nodes at this depth with risk scores]}
   - critical_path: the highest-risk chain from root to leaf
   - edge_types_traversed: set of all edge types encountered
4. Return ImpactResult
```

**Signature:**

```python
def impact_analysis(
    self,
    db_id: str,
    node_id: str,
    direction: str = "both",  # "forward" | "backward" | "both"
    max_depth: int = 3,
) -> ImpactResult:
    """
    Returns:
        ImpactResult with impacted_nodes, risk_by_depth, critical_path
    """
```

**Example:**

```python
result = kgos.impact_analysis("python-kg", "authentication_module", direction="forward")
# result.total_impacted = 12
# result.risk_by_depth = {
#     1: [("api_router", 1.0), ("session_handler", 1.0)],
#     2: [("user_endpoint", 0.5), ("admin_endpoint", 0.5)],
#     3: [("frontend_auth", 0.33)],
# }
# result.critical_path = ["authentication_module", "api_router", "user_endpoint"]
```

### Method 7: `dimension_filter(db_id, filters, limit=20)`

**SQL-based filtering on semantic dimensions.** Narrow the search space by interpretable dimension thresholds before applying other retrieval methods.

**Algorithm:**

```
1. Build SQL WHERE clause from filters:
   - For each dimension in filters:
     a. If "min" specified: json_extract(properties, '$.{dim}') >= min
     b. If "max" specified: json_extract(properties, '$.{dim}') <= max
     c. If "exact" specified: json_extract(properties, '$.{dim}') = exact
2. Execute query against node table
3. Return filtered nodes with their dimension values
```

**Signature:**

```python
def dimension_filter(
    self,
    db_id: str,
    filters: dict[str, dict],  # {dimension_name: {min, max, exact}}
    limit: int = 20,
) -> list[dict]:
    """
    Returns list of nodes matching all dimension constraints.
    """
```

**Example:**

```python
results = kgos.dimension_filter("unified-kg", {
    "code_generation_strength": {"min": 0.8},
    "implementation_complexity": {"max": 0.4},
    "pricing_tier": {"max": 0.2},
}, limit=10)
# Returns only nodes that are: great at code gen, simple to implement, and cheap
```

### Method 8: `classify_intent(query)`

**Intent classification via weighted keyword matching.** Enhanced from the workspace's existing `skill_injector.py` with additional intent categories relevant to KG queries.

**Algorithm:**

```
1. Normalize query to lowercase
2. For each of 14 intent categories:
   a. Check phrase matches (exact substring): +1.0 per match
   b. Check keyword matches (word boundary): +0.3 per match
   c. Apply mode boost (if applicable): +boost value
3. Sort by score, return top 3 above threshold (0.3)
```

**The 14 Intent Categories:**

| Intent | Trigger Phrases | Trigger Keywords |
|--------|----------------|-----------------|
| `cost_optimization` | "reduce costs", "save money", "api costs" | cost, expensive, cheap, budget, pricing |
| `coding_help` | "write code", "fix bug", "refactor" | code, function, class, bug, error, debug |
| `knowledge_graph` | "knowledge graph", "entity extraction" | knowledge, graph, nodes, edges, entity |
| `agent_workflow` | "build agent", "autonomous workflow" | agent, workflow, pipeline, automate |
| `prompt_engineering` | "system prompt", "few-shot" | prompt, instruction, persona, template |
| `deployment` | "deploy to production", "docker" | deploy, production, docker, server, monitor |
| `embedding_search` | "semantic search", "vector search" | embedding, search, semantic, vector, similarity |
| `reasoning` | "extended thinking", "chain of thought" | think, reason, analyze, evaluate, compare |
| `security` | "security audit", "vulnerability scan" | security, vulnerability, auth, encrypt |
| `performance` | "optimize performance", "reduce latency" | performance, optimize, fast, latency, cache |
| `composition` | "combine tools", "multi-step workflow" | compose, combine, chain, pipeline, workflow |
| `impact` | "what depends on", "change impact" | impact, depends, dependency, affect, break |
| `comparison` | "compare options", "alternatives" | compare, alternative, versus, better, which |
| `exploration` | "explore", "what's related", "show me" | explore, related, around, nearby, connected |

### Method 9: `trace_path(db_id, node_a, node_b, max_depth=5)`

**BFS shortest path with edge-type annotations.** Find the shortest connection between two nodes in the graph, reporting every edge type along the path.

**Algorithm:**

```
1. BFS from node_a toward node_b (bidirectional for efficiency on large graphs)
2. For each edge in the discovered path:
   - Record edge type (requires, enables, feeds_into, etc.)
   - Record edge direction (forward vs backward)
   - Record intermediate node names and types
3. If no path found within max_depth, return {found: false}
4. Return annotated path
```

**Signature:**

```python
def trace_path(
    self,
    db_id: str,
    node_a: str,
    node_b: str,
    max_depth: int = 5,
) -> PathResult:
    """
    Returns:
        PathResult with found, length, path (annotated with edge types)
    """
```

**Example:**

```python
result = kgos.trace_path("claude-cookbook-kg", "prompt_caching", "cost_reduction")
# result.found = True
# result.length = 2
# result.path = [
#     {node: "prompt_caching", type: "pattern"},
#     {edge: "enables", direction: "forward"},
#     {node: "token_savings", type: "benefit"},
#     {edge: "contributes_to", direction: "forward"},
#     {node: "cost_reduction", type: "goal"},
# ]
```

### Method 10: `explore_smart(db_id, start_node, depth=2)`

**BFS exploration with importance ranking and hub detection.** Unlike simple BFS that returns all neighbors equally, `explore_smart` ranks nodes at each depth level by their graph importance (degree centrality), identifies hubs (nodes with disproportionately many connections), and provides a structured exploration tree.

**Algorithm:**

```
1. BFS from start_node to specified depth
2. At each level:
   a. Compute degree centrality for all nodes at this level
   b. Detect hubs: nodes with degree > 2 * average_degree_at_level
   c. Rank nodes by: 0.6 * degree_centrality + 0.4 * edge_diversity
      (edge_diversity = count of unique edge types connected)
3. Build exploration tree:
   - Level 0: start_node
   - Level 1: ranked neighbors with edge types
   - Level 2: ranked 2nd-degree neighbors
   - Hubs marked with is_hub=True
4. Return ExplorationTree
```

**Signature:**

```python
def explore_smart(
    self,
    db_id: str,
    start_node: str,
    depth: int = 2,
) -> ExplorationTree:
    """
    Returns:
        ExplorationTree with levels, hubs, ranked nodes per level
    """
```

### Method 11: `_keyword_match_nodes(db_id, query)`

**Base layer keyword search.** The simplest retrieval mechanism — SQL LIKE matching on node name, type, and properties. Used as a fallback and as input to other methods.

**Algorithm:**

```
1. Split query into terms
2. For each term:
   SELECT * FROM nodes
   WHERE name LIKE '%term%'
      OR type LIKE '%term%'
      OR properties LIKE '%term%'
3. Score by number of matching terms
4. Return matched nodes with scores
```

### Method 12: `_edge_type_boost(db_id, seed_ids, boost_types=None)`

**Edge-type-filtered neighbor boosting.** Given a set of seed node IDs and optionally a list of edge types to follow, discover neighbors and assign boost scores based on edge direction and type.

**Algorithm:**

```
1. For each seed node:
   a. Query outgoing edges:
      - If boost_types specified: only follow those edge types
      - Boost target node: +0.5 (outgoing = "this enables that")
   b. Query incoming edges:
      - If boost_types specified: only follow those edge types
      - Boost source node: +0.3 (incoming = "that is needed by this")
2. Normalize all boost scores to 0.0-1.0
3. Return {node_id: normalized_boost_score}
```

**The `boost_types` parameter is what makes this different from the existing `_graph_boost` in `embedding_service.py`.** The existing implementation follows all edge types equally. KG-OS's enhanced version lets the caller specify which edge types to follow, enabling goal-directed graph expansion:

```python
# For a "reduce costs" goal, only boost via cost-relevant edge types
_edge_type_boost(db_id, seed_ids, boost_types=["enables", "optimizes", "reduces"])

# For a "debug error" goal, boost via diagnostic edge types
_edge_type_boost(db_id, seed_ids, boost_types=["has_limitation", "has_workaround", "caused_by"])
```

---

## 7. The 4-Weight Scoring Formula

### The Formula

```
score = alpha * embedding_score + beta * text_score + gamma * graph_score + delta * intent_score
```

**Default weights:**

```
alpha = 0.35   (embedding cosine similarity)
beta  = 0.40   (BM25 + FTS5 text matching)
gamma = 0.15   (graph neighbor boost)
delta = 0.10   (intent-based bonus)
```

**Backward compatibility:** When `delta = 0`, the formula reduces to `0.40 * embedding + 0.45 * text + 0.15 * graph`, which is the workspace's existing 3-weight hybrid search formula (the weights are renormalized by the existing `embedding_service.search()` when called without KG-OS).

### Component Breakdown

#### alpha: Embedding Score (0.35)

**Source:** `embedding_service._embedding_search()`

**What it captures:** Semantic similarity between the query and stored node embeddings. Two nodes with similar "meaning" in embedding space will score high even if they share no keywords.

**Normalization:** Divide all cosine similarities by the maximum similarity in the result set.

**Strengths:** Catches semantic synonyms ("reduce expenses" matches "cost optimization"). Handles paraphrasing.

**Weaknesses:** Misses exact terminology. Can hallucinate similarity between unrelated concepts that happen to be close in embedding space.

#### beta: Text Score (0.40)

**Source:** `embedding_service._bm25_score()` combined with `embedding_service._fts_search()`

**What it captures:** Keyword relevance with term frequency / inverse document frequency weighting. BM25 handles length normalization (short, dense nodes are not penalized). FTS5 handles tokenization and stemming.

**Normalization:** BM25 and FTS5 scores are independently normalized, then combined via `max(bm25_normalized, fts5_normalized)`.

**Strengths:** Precise keyword matching. Intent keywords can be boosted with 5x weight.

**Weaknesses:** Misses semantic similarity. "reduce costs" does not match "save money" unless both terms appear in the node.

#### gamma: Graph Score (0.15)

**Source:** `embedding_service._graph_boost()` or `kgos._edge_type_boost()`

**What it captures:** Structural proximity in the knowledge graph. Nodes that are one hop away from high-scoring nodes get a boost. This implements the principle: "if your neighbor is relevant, you might be too."

**Normalization:** Divide all boost values by the maximum boost.

**Direction weights:**
- Outgoing edges: +0.5 (if A points to B and A is relevant, B likely helps with A's goal)
- Incoming edges: +0.3 (if B points to A and A is relevant, B provides context for A)

**Strengths:** Discovers relevant nodes that share no keywords or embedding similarity with the query but are structurally adjacent to nodes that do.

**Weaknesses:** Can introduce noise in highly connected graphs. Hub nodes get boosted for everything.

#### delta: Intent Score (0.10)

**Source:** `kgos.classify_intent()` combined with method-specific scoring

**What it captures:** Query-intent alignment. When the user's intent is classified (e.g., "cost_optimization"), nodes that are tagged with or connected to cost-related concepts get an additional boost.

**Normalization:** Intent score is 0.0 (no intent match) or scaled by intent confidence (0.0-1.0).

**How it works in practice:**

```
Query: "How do I reduce my API costs?"
  classify_intent() -> cost_optimization (confidence: 1.3)
  intent_score calculation:
    - Nodes with type="cost_strategy": +1.0
    - Nodes connected by "optimizes" edge to a cost node: +0.7
    - Nodes with pricing_tier < 0.3 dimension: +0.5
    - Normalized to 0.0-1.0 range
```

### Weight Tuning Guide

| Scenario | alpha | beta | gamma | delta | Rationale |
|----------|-------|------|-------|-------|-----------|
| **Default (balanced)** | 0.35 | 0.40 | 0.15 | 0.10 | Good all-around performance |
| **Goal-oriented queries** | 0.25 | 0.30 | 0.15 | 0.30 | Boost intent routing for "I want to X" queries |
| **Exact term lookup** | 0.10 | 0.65 | 0.15 | 0.10 | Heavy text weight for technical term searches |
| **Exploration/discovery** | 0.25 | 0.25 | 0.40 | 0.10 | Heavy graph weight to discover adjacent concepts |
| **Highly connected KG** | 0.35 | 0.40 | 0.25 | 0.00 | More graph signal available; disable intent overhead |
| **Sparse KG (few edges)** | 0.45 | 0.45 | 0.05 | 0.05 | Barely any graph structure; rely on text + embeddings |
| **Backward compatible** | 0.40 | 0.45 | 0.15 | 0.00 | Exact existing hybrid formula |

### Normalization Strategy

Each component is independently normalized to the 0.0-1.0 range before weighting:

```python
def _normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    max_val = max(scores.values())
    if max_val == 0:
        return scores
    return {k: v / max_val for k, v in scores.items()}
```

This prevents any single component from dominating due to scale differences (e.g., BM25 scores can be 0-20 while cosine similarity is 0-1). After normalization, each component contributes proportionally to its weight.

---

## 8. Expert Agent Model

### What Is an Expert?

An expert is the atomic unit of KG-OS: a persona bound to a knowledge graph with a tuned retrieval configuration. It is the answer to the question: "How do I make an AI agent that is genuinely expert in a specific domain?"

**An expert is NOT:**
- A system prompt (no structured retrieval)
- A RAG pipeline (no intent routing or composition)
- A fine-tuned model (no graph structure)
- A chatbot with a personality (no knowledge grounding)

**An expert IS:**
- `KG + Persona + Retrieval Config + Playbook Skills + Dimension Filters + Goal Mappings`

### Expert Configuration Schema

```json
{
    "id": "expert_python_guru",
    "name": "Python Expert",
    "description": "Deep Python expertise backed by a structured knowledge graph of Python patterns, stdlib, and best practices.",
    "kg_db_id": "python-kg",
    "kg_db_ids": ["python-kg", "stdlib-kg"],
    "persona": {
        "name": "PyGuru",
        "instructions": "You are a senior Python developer with 15 years of experience. You emphasize clean code, type hints, and testing. You cite specific patterns and modules from your knowledge base. When you recommend something, you explain the trade-offs.",
        "style": "professional",
        "greeting": "Hello! I am PyGuru, your Python expert. I have structured knowledge of Python patterns, the standard library, and best practices. Ask me anything about Python development."
    },
    "retrieval": {
        "methods": ["hybrid", "intent"],
        "alpha": 0.35,
        "beta": 0.40,
        "gamma": 0.15,
        "delta": 0.10,
        "limit": 10,
        "expand_depth": 1,
        "boost_types": ["requires", "enables", "implements"]
    },
    "dimension_filters": {
        "code_generation_strength": { "min": 0.7 },
        "implementation_complexity": { "max": 0.6 }
    },
    "playbook_skills": [
        "enhanced-coding",
        "testing-qa"
    ],
    "custom_goal_mappings": {
        "debug": {
            "boost_types": ["has_limitation", "has_workaround", "caused_by"],
            "dimension_boosts": ["error_handling_need", "debugging_difficulty"]
        },
        "optimize": {
            "boost_types": ["optimizes", "enables", "reduces"],
            "dimension_boosts": ["throughput_requirement", "latency_sensitivity"]
        },
        "learn": {
            "boost_types": ["requires", "prerequisite_of", "part_of"],
            "dimension_boosts": ["learning_curve", "implementation_complexity"]
        },
        "build": {
            "boost_types": ["feeds_into", "requires", "composes_with"],
            "dimension_boosts": ["pipeline_composability", "agent_compatibility"]
        }
    },
    "created_at": "2026-02-23T00:00:00Z",
    "updated_at": "2026-02-23T00:00:00Z"
}
```

### Configuration Fields Explained

#### `kg_db_id` / `kg_db_ids`

The primary knowledge graph (or multiple KGs) this expert draws from. When multiple KGs are specified, KG-OS runs the query against each and merges results with deduplication.

```json
"kg_db_id": "python-kg",
"kg_db_ids": ["python-kg", "stdlib-kg", "testing-patterns-kg"]
```

When both fields are present, `kg_db_ids` takes precedence. The `kg_db_id` serves as the default/primary for single-KG operations.

#### `persona`

The AI personality configuration. This is injected as part of the system prompt during context assembly.

- `name`: Display name for the expert
- `instructions`: System prompt instructions (how the AI should behave)
- `style`: Communication style tag (professional, casual, academic, concise)
- `greeting`: Initial message when a conversation starts

#### `retrieval`

Controls how KG-OS retrieves knowledge for this expert.

- `methods`: Which retrieval methods to use (`["hybrid"]`, `["hybrid", "intent"]`, `["intent"]`)
- `alpha`, `beta`, `gamma`, `delta`: The 4-weight formula weights
- `limit`: Maximum number of KG nodes to include in context
- `expand_depth`: How many hops to expand top results (0 = no expansion)
- `boost_types`: Default edge types to follow during graph boosting

#### `dimension_filters`

Pre-filters applied before scoring. Only nodes matching ALL dimension constraints are considered.

```json
"dimension_filters": {
    "code_generation_strength": { "min": 0.7 },
    "pricing_tier": { "max": 0.3 },
    "implementation_complexity": { "min": 0.2, "max": 0.8 }
}
```

#### `playbook_skills`

Names of playbooks whose excerpts should be injected when relevant to the user's query. These are matched by the `skill_injector` service.

#### `custom_goal_mappings`

Maps detected goal keywords to specialized retrieval configurations. When the user's query matches a goal keyword (e.g., "debug" in "help me debug this error"), the corresponding `boost_types` and `dimension_boosts` override the defaults.

### Execution Flow: Expert Chat

When a user sends a message to an expert, the following sequence executes:

```
Step 1: Request Parsing
  POST /api/experts/{expert_id}/chat
  Body: { query: "How do I handle rate limiting in my API?", history: [...] }

Step 2: Expert Config Loading
  Load expert config from SQLite: persona, retrieval, dimensions, goal_mappings

Step 3: Intent Classification + Goal Mapping
  classify_intent("How do I handle rate limiting in my API?")
    -> intent: "performance" (score: 1.0), secondary: "coding_help" (score: 0.6)
  Check custom_goal_mappings: no exact match for "handle" -> use defaults

Step 4: KG-OS Query
  intent_search(
    db_id = "python-kg",
    query = "handle rate limiting in my API",
    config = {
      alpha: 0.35, beta: 0.40, gamma: 0.15, delta: 0.10,
      boost_types: ["requires", "enables", "implements"],
      dimension_filters: { code_generation_strength: {min: 0.7} },
      limit: 10, expand_depth: 1,
    }
  )
  -> 10 ranked nodes with edge annotations

Step 5: Context Assembly
  System prompt = persona.instructions
    + "[KG Context]\n" + formatted top-10 nodes with edges
    + "[Dimension Hints]\n" + relevant dimensions for top nodes
    + "[Playbook Context]\n" + skill_injector excerpts (if matched)
    + "[Memory]\n" + relevant conversation memories

Step 6: Agentic Loop (stages 5-7)
  Stream response from Gemini/Claude with full expert context
  Model generates response grounded in KG citations

Step 7: Persist
  Log conversation, extract memories, store retrieval metadata
```

### Multi-KG Experts

When an expert spans multiple KGs, the query is run against each KG and results are merged:

```python
# Pseudocode for multi-KG query
all_results = []
for db_id in expert.kg_db_ids:
    results = kgos.intent_search(db_id, query, expert.retrieval)
    for r in results.nodes:
        r["source_kg"] = db_id  # Tag which KG it came from
    all_results.extend(results.nodes)

# Deduplicate by node name (same concept in multiple KGs)
deduplicated = deduplicate_by_name(all_results, prefer_higher_score=True)

# Re-rank merged results
final = sorted(deduplicated, key=lambda r: r["score"], reverse=True)[:limit]
```

This enables experts that combine knowledge from complementary domains. A "Full-Stack Python Expert" might span `python-kg`, `flask-kg`, `postgres-kg`, and `testing-kg`.

---

## 9. Integration Architecture

### How Expert Context Flows Through the 8-Stage Agentic Loop

The agentic loop (`backend/services/agentic_loop.py`) already implements an 8-stage pipeline. KG-OS integrates at specific stages without modifying the core loop structure.

#### Stage 1: INTAKE

**Standard behavior:** Parse messages, determine provider, create conversation ID.

**Expert mode addition:** Detect whether the request is an expert chat (via the expert router). If so, load the expert configuration and pass it through the pipeline as metadata.

```python
# In the expert chat endpoint (routers/experts.py):
async def expert_chat(expert_id: str, req: ChatRequest):
    expert = expert_service.get_expert(expert_id)

    # Run KG-OS query BEFORE the agentic loop
    kgos_context = await kgos_service.intent_search(
        db_id=expert.kg_db_id,
        query=req.query,
        config=expert.retrieval,
    )

    # Feed into agentic loop with assembled context
    async for chunk in agentic_loop.run(
        messages=req.messages,
        system_prompt=assemble_expert_prompt(expert, kgos_context),
        persona=expert.persona,
        ...
    ):
        yield chunk
```

#### Stage 2: MEMORY RECALL

**Standard behavior:** `memory_service.recall(user_text, limit=5)` searches the workspace memory KG for relevant conversation history.

**Expert mode addition:** Filter recalled memories by the expert's conversation history. An expert should recall its own past conversations, not unrelated conversations from other experts or the general chat.

```python
# Enhanced recall for experts
memories = memory_service.recall(
    user_text,
    limit=5,
    filter_metadata={"expert_id": expert.id}
)
```

#### Stage 3: SKILL INJECTION

**Standard behavior:** `skill_injector.get_relevant_context(user_text, mode)` classifies intent and injects playbook excerpts.

**Expert mode addition:** Use the expert's `playbook_skills` list to restrict which playbooks are searched. A Python expert should not inject Kubernetes deployment playbook excerpts.

```python
# Enhanced skill injection for experts
skill_section = await skill_injector.get_relevant_context(
    user_text,
    mode="chat",
    allowed_playbooks=expert.playbook_skills,
)
```

#### Stage 4: CONTEXT ASSEMBLY

**Standard behavior:** Combine base prompt + persona + styles + memory + skills.

**Expert mode addition:** Inject the KG-OS context as a structured section. This is the critical integration point where graph knowledge enters the prompt.

```python
def assemble_expert_prompt(expert, kgos_context):
    parts = []

    # Expert persona
    parts.append(expert.persona.instructions)

    # KG context (from KG-OS query)
    if kgos_context.nodes:
        kg_section = "[Knowledge Graph Context]\n"
        kg_section += f"Source: {expert.kg_db_id}\n"
        kg_section += f"Intent: {kgos_context.intent}\n\n"
        for r in kgos_context.nodes[:10]:
            node = r["node"]
            kg_section += f"- [{node['type']}] {node['name']}"
            if node.get("properties"):
                # Include relevant dimension values
                dims = {k: v for k, v in node["properties"].items()
                        if isinstance(v, float) and 0 <= v <= 1}
                if dims:
                    kg_section += f" (dims: {dims})"
            kg_section += "\n"

        # Include edge annotations
        if kgos_context.edges:
            kg_section += "\nRelationships:\n"
            for edge in kgos_context.edges[:15]:
                kg_section += f"  {edge['source_name']} --[{edge['type']}]--> {edge['target_name']}\n"

        parts.append(kg_section)

    # Composition plan (if detected)
    if kgos_context.composition_plan:
        plan_section = "[Composition Plan]\n"
        for step in kgos_context.composition_plan.steps:
            plan_section += f"  Step {step.order}: {step.tool} -> {step.action}\n"
        parts.append(plan_section)

    # Citation instruction
    parts.append(
        "[Citation Instructions]\n"
        "When referencing knowledge from the graph, cite the source node: "
        "[Source: kg_name:node_name]. This helps the user verify your claims."
    )

    return "\n\n".join(parts)
```

#### Stages 5-7: INFERENCE + TOOL EXECUTION + STREAMING

**Standard behavior:** Stream response from Gemini or Claude. Handle function calling if tools are configured.

**Expert mode addition:** No changes. The expert context is already in the system prompt. The LLM generates responses grounded in the injected KG context.

#### Stage 8: PERSIST

**Standard behavior:** Log assistant message, extract memories, store in workspace memory.

**Expert mode addition:** Store additional metadata about which KG nodes were used, which intent was classified, and the retrieval scores. This enables analytics on expert performance.

```python
# Enhanced persistence for experts
memory_service.log_message(
    conversation_id, "assistant", accumulated_text, provider, model,
    metadata={
        "expert_id": expert.id,
        "kg_db_id": expert.kg_db_id,
        "intent": kgos_context.intent,
        "kg_nodes_used": [r["node"]["id"] for r in kgos_context.nodes[:10]],
        "retrieval_scores": {r["node"]["id"]: r["score"] for r in kgos_context.nodes[:10]},
    }
)
```

### Architecture Diagram: Expert Chat Flow

```
Frontend                   Backend                              Services
--------                   -------                              --------

ExpertChat    POST /api/experts/{id}/chat
component  ─────────────────────> experts.py (router)
                                     |
                                     | Load expert config
                                     v
                                  expert_service.get_expert(id)
                                     |
                                     | Run KG-OS query
                                     v
                                  kgos_service.intent_search()
                                     |  ├── classify_intent()
                                     |  ├── embedding_service.search()
                                     |  ├── want_to() or can_it()
                                     |  ├── _edge_type_boost()
                                     |  ├── dimension_filter()
                                     |  └── score_combiner()
                                     |
                                     | Assemble expert context
                                     v
                                  assemble_expert_prompt()
                                     |
                                     | Feed into agentic loop
                                     v
                                  agentic_loop.run(
                                     messages, system_prompt,
                                     persona, ...)
                                     |
              SSE stream            | Stage 1-8
  <──────────────────────────────── |
  data: {type: "token",             v
         content: "Based on       gemini_service.stream_chat()
         the knowledge graph..."}   or claude_service.stream_chat()
```

---

## 10. API Reference

### Expert CRUD Endpoints

#### `GET /api/experts`

List all configured expert agents.

**Request:**
```
GET /api/experts HTTP/1.1
```

**Response:**
```json
[
    {
        "id": "expert_python_guru",
        "name": "Python Expert",
        "description": "Deep Python expertise backed by structured KG",
        "kg_db_id": "python-kg",
        "persona": {
            "name": "PyGuru",
            "style": "professional"
        },
        "created_at": "2026-02-23T00:00:00Z",
        "conversation_count": 12,
        "last_active": "2026-02-23T14:30:00Z"
    },
    {
        "id": "expert_financial",
        "name": "Financial Advisor",
        "description": "Tax and investment strategy expert",
        "kg_db_id": "finance-kg",
        "persona": {
            "name": "FinanceBot",
            "style": "professional"
        },
        "created_at": "2026-02-20T00:00:00Z",
        "conversation_count": 5,
        "last_active": "2026-02-22T09:15:00Z"
    }
]
```

---

#### `POST /api/experts`

Create a new expert agent.

**Request:**
```json
{
    "name": "Python Expert",
    "description": "Deep Python expertise backed by structured KG",
    "kg_db_id": "python-kg",
    "persona": {
        "name": "PyGuru",
        "instructions": "You are a senior Python developer...",
        "style": "professional",
        "greeting": "Hello! I am PyGuru."
    },
    "retrieval": {
        "methods": ["hybrid", "intent"],
        "alpha": 0.35,
        "beta": 0.40,
        "gamma": 0.15,
        "delta": 0.10,
        "limit": 10
    },
    "dimension_filters": {
        "code_generation_strength": { "min": 0.7 }
    },
    "playbook_skills": ["enhanced-coding", "testing-qa"],
    "custom_goal_mappings": {
        "debug": {
            "boost_types": ["has_limitation", "has_workaround"],
            "dimension_boosts": ["error_handling_need"]
        }
    }
}
```

**Response:**
```json
{
    "id": "expert_python_guru",
    "name": "Python Expert",
    "created_at": "2026-02-23T00:00:00Z"
}
```

---

#### `GET /api/experts/{id}`

Get full expert configuration.

**Request:**
```
GET /api/experts/expert_python_guru HTTP/1.1
```

**Response:** Full expert JSON object (same schema as POST body, plus `id`, `created_at`, `updated_at`).

---

#### `PUT /api/experts/{id}`

Update an expert's configuration. Partial updates supported.

**Request:**
```json
{
    "retrieval": {
        "alpha": 0.30,
        "delta": 0.20
    },
    "dimension_filters": {
        "code_generation_strength": { "min": 0.8 }
    }
}
```

**Response:** Updated full expert object.

---

#### `DELETE /api/experts/{id}`

Delete an expert and optionally its conversation history.

**Request:**
```
DELETE /api/experts/expert_python_guru?delete_conversations=true HTTP/1.1
```

**Response:**
```json
{
    "deleted": true,
    "conversations_deleted": 12
}
```

---

#### `POST /api/experts/{id}/duplicate`

Duplicate an expert with a new name. Useful for creating variants with different retrieval configs.

**Request:**
```json
{
    "new_name": "Python Expert (High Intent)",
    "overrides": {
        "retrieval": { "delta": 0.30 }
    }
}
```

**Response:**
```json
{
    "id": "expert_python_guru_copy_1",
    "name": "Python Expert (High Intent)",
    "created_at": "2026-02-23T00:00:00Z"
}
```

---

### Expert Chat Endpoint

#### `POST /api/experts/{id}/chat`

Stream a chat response from an expert agent. Returns SSE (Server-Sent Events).

**Request:**
```json
{
    "query": "How do I implement a connection pool in Python?",
    "conversation_id": "conv_abc123",
    "history": [
        { "role": "user", "content": "What is a connection pool?" },
        { "role": "model", "content": "A connection pool is..." }
    ],
    "provider": "gemini",
    "model": "gemini-2.5-flash"
}
```

**Response (SSE stream):**
```
data: {"type": "conversation_start", "conversation_id": "conv_abc123"}

data: {"type": "injection_meta", "memories": true, "skills": true, "kg_nodes": 8}

data: {"type": "sources", "nodes": [
    {"id": "abc123", "name": "connection_pooling", "type": "pattern", "score": 0.87},
    {"id": "def456", "name": "sqlite_pool", "type": "implementation", "score": 0.72}
]}

data: {"type": "token", "content": "To implement a "}
data: {"type": "token", "content": "connection pool in Python, "}
data: {"type": "token", "content": "you have several options..."}
...
data: {"type": "token", "content": " [Source: python-kg:connection_pooling]"}

data: {"type": "done"}
```

**SSE Event Types:**

| Event Type | Description | Fields |
|-----------|-------------|--------|
| `conversation_start` | Conversation ID for tracking | `conversation_id` |
| `injection_meta` | What context was injected | `memories`, `skills`, `kg_nodes` |
| `sources` | KG nodes used as context | `nodes[]` with id, name, type, score |
| `token` | Streaming text token | `content` |
| `error` | Error occurred | `content` (error message) |
| `done` | Stream complete | (none) |

---

### Expert Conversation Endpoints

#### `GET /api/experts/{id}/conversations`

List all conversations for an expert.

**Request:**
```
GET /api/experts/expert_python_guru/conversations?limit=20&offset=0 HTTP/1.1
```

**Response:**
```json
{
    "conversations": [
        {
            "id": "conv_abc123",
            "started_at": "2026-02-23T14:00:00Z",
            "last_message_at": "2026-02-23T14:30:00Z",
            "message_count": 8,
            "preview": "How do I implement a connection pool..."
        }
    ],
    "total": 12,
    "limit": 20,
    "offset": 0
}
```

---

#### `GET /api/experts/{id}/conversations/{cid}`

Get a conversation with all messages.

**Response:**
```json
{
    "id": "conv_abc123",
    "expert_id": "expert_python_guru",
    "started_at": "2026-02-23T14:00:00Z",
    "messages": [
        {
            "role": "user",
            "content": "How do I implement a connection pool?",
            "timestamp": "2026-02-23T14:00:00Z"
        },
        {
            "role": "assistant",
            "content": "To implement a connection pool in Python...",
            "timestamp": "2026-02-23T14:00:05Z",
            "metadata": {
                "kg_nodes_used": ["abc123", "def456"],
                "intent": "coding_help",
                "retrieval_scores": {"abc123": 0.87, "def456": 0.72}
            }
        }
    ]
}
```

---

#### `DELETE /api/experts/{id}/conversations/{cid}`

Delete a specific conversation.

**Response:**
```json
{ "deleted": true }
```

---

### KG-OS Direct Access Endpoints (Debug/Testing)

These endpoints expose KG-OS methods directly, bypassing the expert layer. Useful for debugging retrieval, testing new query methods, and evaluating KG quality.

#### `POST /api/kgos/query/{db_id}`

Run an `intent_search` directly against a KG.

**Request:**
```json
{
    "query": "How do I reduce API costs?",
    "config": {
        "alpha": 0.35,
        "beta": 0.40,
        "gamma": 0.15,
        "delta": 0.10,
        "limit": 10,
        "methods": ["hybrid", "intent"]
    }
}
```

**Response:**
```json
{
    "intent": { "category": "cost_optimization", "score": 1.3 },
    "results": [
        {
            "node": { "id": "abc", "name": "prompt_caching", "type": "pattern", "properties": {} },
            "score": 0.87,
            "method": "text+graph+intent",
            "edge_annotations": [
                { "type": "enables", "target": "cost_reduction" },
                { "type": "requires", "target": "repeated_prefix" }
            ]
        }
    ],
    "total": 10,
    "query": "How do I reduce API costs?",
    "composition_plan": null
}
```

---

#### `POST /api/kgos/impact/{db_id}/{node_id}`

Run impact analysis on a specific node.

**Request:**
```json
{
    "direction": "forward",
    "max_depth": 3
}
```

**Response:**
```json
{
    "node_id": "authentication_module",
    "direction": "forward",
    "total_impacted": 12,
    "risk_by_depth": {
        "1": [
            { "node": { "id": "...", "name": "api_router" }, "risk": 1.0 },
            { "node": { "id": "...", "name": "session_handler" }, "risk": 1.0 }
        ],
        "2": [
            { "node": { "id": "...", "name": "user_endpoint" }, "risk": 0.5 }
        ],
        "3": [
            { "node": { "id": "...", "name": "frontend_auth" }, "risk": 0.33 }
        ]
    },
    "critical_path": ["authentication_module", "api_router", "user_endpoint"]
}
```

---

#### `POST /api/kgos/compose/{db_id}`

Run composition planning for a multi-step goal.

**Request:**
```json
{
    "goal": "read CSV data, analyze trends, and generate a report",
    "max_tools": 5
}
```

**Response:**
```json
{
    "goal": "read CSV data, analyze trends, and generate a report",
    "steps": [
        { "order": 1, "tool": "csv_reader", "action": "read CSV data", "node_id": "..." },
        { "order": 2, "tool": "data_analyzer", "action": "analyze trends", "node_id": "..." },
        { "order": 3, "tool": "report_generator", "action": "generate report", "node_id": "..." }
    ],
    "edges": [
        { "from": "csv_reader", "to": "data_analyzer", "type": "feeds_into", "validated": true },
        { "from": "data_analyzer", "to": "report_generator", "type": "feeds_into", "validated": true }
    ],
    "prerequisites": [],
    "warnings": [],
    "is_valid": true
}
```

---

#### `POST /api/kgos/similar/{db_id}/{node_id}`

Find structurally similar nodes.

**Request:**
```json
{
    "k": 10
}
```

**Response:**
```json
{
    "source_node": { "id": "...", "name": "prompt_caching", "type": "pattern" },
    "similar": [
        {
            "node": { "id": "...", "name": "context_caching", "type": "pattern" },
            "score": 0.85,
            "jaccard": 0.82,
            "type_match": 1.0,
            "name_overlap": 0.33
        },
        {
            "node": { "id": "...", "name": "response_caching", "type": "pattern" },
            "score": 0.71,
            "jaccard": 0.65,
            "type_match": 1.0,
            "name_overlap": 0.33
        }
    ]
}
```

---

#### `GET /api/kgos/dimensions`

List all 56 standard semantic dimensions with metadata.

**Response:**
```json
{
    "dimensions": [
        {
            "name": "latency_sensitivity",
            "category": "Performance & Cost",
            "description": "How sensitive the tool/pattern is to response time",
            "low_description": "Tolerant of delays",
            "high_description": "Requires sub-second responses",
            "range": [0.0, 1.0]
        },
        {
            "name": "throughput_requirement",
            "category": "Performance & Cost",
            "description": "Volume of data/requests it needs to handle",
            "low_description": "Single requests",
            "high_description": "High-volume batch processing",
            "range": [0.0, 1.0]
        }
    ],
    "total": 56,
    "categories": {
        "Performance & Cost": 8,
        "Complexity & Effort": 6,
        "Interaction Patterns": 7,
        "Data Characteristics": 6,
        "API Capabilities": 8,
        "Problem Domains": 7,
        "Architectural Patterns": 5,
        "NLKE Meta-Dimensions": 3,
        "CLI Tool Characteristics": 6
    }
}
```

---

### Endpoint Summary Table

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `GET` | `/api/experts` | List all experts | None |
| `POST` | `/api/experts` | Create expert | None |
| `GET` | `/api/experts/{id}` | Get expert | None |
| `PUT` | `/api/experts/{id}` | Update expert | None |
| `DELETE` | `/api/experts/{id}` | Delete expert | None |
| `POST` | `/api/experts/{id}/duplicate` | Duplicate expert | None |
| `POST` | `/api/experts/{id}/chat` | Expert chat (SSE) | None |
| `GET` | `/api/experts/{id}/conversations` | List conversations | None |
| `GET` | `/api/experts/{id}/conversations/{cid}` | Get conversation | None |
| `DELETE` | `/api/experts/{id}/conversations/{cid}` | Delete conversation | None |
| `POST` | `/api/kgos/query/{db_id}` | Direct KG-OS query | None |
| `POST` | `/api/kgos/impact/{db_id}/{node_id}` | Impact analysis | None |
| `POST` | `/api/kgos/compose/{db_id}` | Composition planning | None |
| `POST` | `/api/kgos/similar/{db_id}/{node_id}` | Similar nodes | None |
| `GET` | `/api/kgos/dimensions` | List dimensions | None |

---

## 11. Anti-Patterns and Lessons

These lessons were learned the hard way during the Flags Toolkit development (Phases 1-8, spanning 4 months). They are baked into KG-OS's design.

### Lesson 1: Two Strategies Beat Seven

```
2 strategies combined = 88.5% recall
7 strategies combined = 66.7% recall
```

The early `super_query.py` system tried Reciprocal Rank Fusion (RRF) across 7 retrieval strategies: FTS5, BM25, embedding cosine, graph boost, Jaccard, dimension filter, and path-based retrieval. The hypothesis was that more strategies would catch more relevant results. The reality was the opposite: noise from weak strategies drowned out signal from strong ones.

**The fix:** Use 2-3 strong strategies (BM25 + embedding + graph boost) as the core, and add others selectively based on intent. KG-OS's 4-weight formula defaults to 3 components (alpha + beta + gamma) with the fourth (delta) engaged only when intent classification is confident.

### Lesson 2: Intent Keywords Deserve 5x Weight

In BM25 scoring, all tokens are weighted equally by default. But "reduce" in "reduce API costs" is worth far more than "API" — the word "reduce" signals intent (the user wants to *decrease* something), while "API" is just the subject.

**The fix:** KG-OS's `want_to()` method identifies intent verbs (reduce, build, optimize, debug, learn, deploy, secure, automate) and applies 5x BM25 weight to them. This dramatically improves goal-relevant retrieval.

Intent keywords at three levels:
- **Literal**: "context caching", "cache tokens" (exact feature names)
- **Goal-based**: "reduce costs", "save money" (what the user wants to achieve)
- **Benefit-focused**: "90% savings", "cheaper" (what outcome the user expects)

All three levels must be indexed. Users query at all three.

### Lesson 3: Category Filtering Misses Answers

An early version of `query-cookbook.py` filtered results by node type: if the user asked about "cost optimization", only return nodes of type `strategy` or `pattern`. This seemed logical but missed critical answers. The best cost optimization insight was a `use_case` node. The best caching tip was a `configuration` node.

**The fix:** Never pre-filter by category. Let the scoring formula rank across all types. If dimension filtering is needed, use explicit dimension thresholds (which the user or expert config controls), not implicit category assumptions.

### Lesson 4: Pure Embedding Search Hits ~50%

Embeddings alone achieve roughly 50% recall on the benchmark query set. They miss exact terminology ("context caching" matches "caching strategies" but misses "prompt caching" which uses a specific API name). They also generate false positives for semantically similar but functionally unrelated concepts.

**The fix:** Never rely on embeddings alone. The hybrid formula (beta=0.40 for text + alpha=0.35 for embeddings) ensures that both semantic similarity and keyword precision contribute. When embeddings are unavailable (no stored vectors), the formula degrades gracefully to text + graph.

### Lesson 5: RRF with Many Strategies Produces Noise

Reciprocal Rank Fusion (RRF) treats all strategies as equally informative and combines their rankings. But when you have 7 strategies and 5 of them return poor results for a given query, RRF amplifies the noise. A node ranked #1 by BM25 and #50 by the other 6 strategies gets a lower RRF score than a node ranked #10 by all 7.

**The fix:** Weighted combination (the 4-weight formula) instead of RRF. Each component is weighted by its expected contribution, not ranked equally. The weights can be tuned per-expert, per-intent, or per-query.

### Lesson 6: The Color Mixing Metaphor

From `SYNTHESIZED_INSIGHTS.md`:

> Two complementary colors (embedding + BM25) mixed together produce a beautiful purple (88.5% recall). Seven colors mixed together produce muddy brown (66.7% recall). More is not better. The right combination of a few strong signals beats a cocktail of many weak ones.

This metaphor extends to KG-OS design:
- The core formula is 3-4 weights (not 7)
- Additional methods (Jaccard, dimension filter, impact analysis) are invoked selectively by intent, not universally
- Each method should be strong on its own before being combined

### Lesson 7: Graph Structure Is the Curriculum

> "If KG structure is correct, embeddings will be semantically meaningful. If KG structure is wrong, embeddings will learn wrong relationships."

The quality of every KG-OS query depends on the quality of the underlying knowledge graph. No amount of retrieval sophistication compensates for a poorly structured KG. This is why KG-OS includes the 12 validation rules — they enforce structural quality before retrieval operates on it.

Specific structural quality markers:
- `requires` edges must form a DAG (no circular dependencies)
- `has_limitation` edges should have corresponding `has_workaround` edges
- Hub nodes (high degree centrality) should be well-labeled concept nodes, not generic "entity" nodes
- Edge types should be from a controlled vocabulary (not free-form strings)

### Lesson 8: Errors Are Semantic Clues

During evaluation, `workflow_safe_experimentation` was returned instead of the expected `use_case_experiment_safely`. This looked like a retrieval error — wrong node returned. But the workflow IS the use case implemented. They are semantically equivalent.

**The lesson:** Evaluate semantically, not just by exact ID match. KG-OS includes both strict recall (exact ID match) and lenient recall (semantic equivalence) in its evaluation metrics. A system that returns a semantically equivalent node should not be penalized.

### Lesson 9: Composition Detection Is Hard but Critical

Many user queries are inherently multi-step: "read this file, analyze the data, and generate a report." A single-node retrieval system returns the most relevant single node. A composition-aware system recognizes that this requires three tools connected in a pipeline and returns the entire workflow.

**The challenge:** Decomposing natural language goals into sub-goals is ambiguous. "Read and analyze" could be two steps or one. "Generate a report" could require intermediate formatting steps.

**KG-OS's approach:** Conservative decomposition (split on explicit conjunctions) + graph validation (check for `feeds_into` edges between candidate tools). If the graph confirms a connection, the composition is valid. If not, flag it as a warning rather than failing silently.

### Anti-Pattern Summary

| Anti-Pattern | What Happened | The Fix |
|-------------|---------------|---------|
| Mix everything together | 66.7% recall with 7 strategies | 2-3 core strategies + selective additions |
| Equal-weight keywords | Intent verbs lost in noise | 5x weight on intent keywords |
| Pre-filter by category | Missed cross-category answers | Score across all types, filter by dimension |
| Embeddings-only | 50% recall | Hybrid: embedding + text + graph |
| RRF for combination | Noise amplified | Weighted formula with tunable weights |
| Ignore graph quality | Wrong results from wrong edges | 12 validation rules + structural QA |
| Strict-match evaluation | Penalized semantically correct results | Lenient + strict dual evaluation |

---

## 12. Terminology Glossary

**4-Weight Formula**
The scoring equation `score = alpha*embedding + beta*text + gamma*graph + delta*intent` that combines four retrieval signals into a single relevance score. Default weights: 0.35 + 0.40 + 0.15 + 0.10.

**BFS Traversal**
Breadth-First Search on the knowledge graph. Used by `impact_analysis`, `trace_path`, and `explore_smart` to discover connected nodes level by level, ensuring shortest paths are found first.

**Composition Detection**
The ability to recognize that a user's goal requires multiple tools/nodes used in sequence, and to validate the proposed sequence through graph edges (`feeds_into`, `requires`).

**Edge-Type Boosting**
A graph retrieval mechanism that amplifies the scores of neighboring nodes based on the types of edges connecting them. A node connected by an `enables` edge to a goal-relevant node gets boosted more than a node connected by a generic `relates_to` edge.

**Expert Agent**
The atomic unit of KG-OS: a configuration combining a KG, persona, retrieval config, playbook skills, dimension filters, and goal mappings into a domain-specialized AI agent.

**Goal Mapping**
A configuration that maps detected goal keywords (e.g., "debug", "optimize") to specialized retrieval parameters (boost types, dimension boosts). Enables the same expert to use different retrieval strategies based on the user's intent.

**Hub Detection**
Identifying nodes with disproportionately many connections (degree centrality > 2x average). Used by `explore_smart` to highlight important nodes during graph exploration.

**Hybrid Search**
The combination of multiple retrieval mechanisms (embedding similarity, BM25, FTS5, graph boost) into a single ranked result. The workspace's existing `embedding_service.search()` implements 3-weight hybrid; KG-OS extends it to 4-weight.

**Impact Analysis**
BFS-based propagation from a node to discover all upstream and downstream dependencies, with risk scores that decrease with distance. Used to assess the consequences of changing or removing a node.

**Intent Classification**
Weighted keyword matching that categorizes a user's query into one of 14 intent categories (cost_optimization, coding_help, knowledge_graph, etc.). Determines which retrieval methods and edge-type boosts to apply.

**Jaccard Similarity**
A structural similarity metric: `|intersection(neighbors_A, neighbors_B)| / |union(neighbors_A, neighbors_B)|`. Two nodes with the same neighbors are structurally similar, even if they have different names or embeddings.

**KG-OS**
Knowledge Graph Operating System. The query intelligence layer that sits between raw KG storage and the agentic loop, orchestrating intent-driven retrieval across 57 KG databases.

**Playbook Skills**
Named playbook topics (e.g., "enhanced-coding", "testing-qa") associated with an expert. The skill injector searches only these playbooks when injecting context for this expert.

**Retrieval Config**
The set of parameters controlling how KG-OS retrieves knowledge: weights (alpha, beta, gamma, delta), methods, limits, boost types, and expand depth. Each expert has its own retrieval config.

**Semantic Dimension**
A named, interpretable float value (0.0-1.0) assigned to a KG node, representing a specific measurable aspect (e.g., `latency_sensitivity: 0.9`). 56 standard dimensions across 9 categories.

---

## 13. Evolution Timeline

### Phase 1: Foundation (October 2025)
- **78 nodes**, basic embeddings
- Single SQLite database
- Recall: approximately 48%
- Pure embedding search only
- *"Can we put documentation into a graph?"*

### Phase 2: Keyword Enrichment (October 2025)
- **264 nodes**, expanded with intent keywords
- BM25 scoring added alongside embeddings
- Recall improved: 49.7% to 65.8%
- *"Keywords matter as much as embeddings"*

### Phase 3: Hybrid Search (October 2025)
- Hybrid formula: `0.40*embedding + 0.45*BM25 + 0.15*graph`
- **Recall: 88.5% strict**, 100% lenient (with semantic evaluation)
- Graph neighbor boosting added
- The "beautiful purple" discovery: two complementary strategies beat seven
- *"Simple combination is the breakthrough"*

### Phase 4: Semantic Evaluation (October 2025)
- Semantic equivalence detection (workflow_safe_experimentation == use_case_experiment_safely)
- 100% lenient recall achieved
- Evaluation framework with strict + lenient modes
- *"Errors can be semantic clues"*

### Phase 5: Multi-Model Orchestration (November 2025)
- Claude + Gemini routing based on task type
- Claude for complex reasoning, Gemini for large context
- Cross-model validation patterns
- *"Different models for different strengths"*

### Phase 6: Intent-Driven Queries (November 2025)
- 14 intent-driven query methods (Phase 1 of Flags Toolkit)
- `want_to`, `can_it`, `compose_for`, `trace_path`
- Structure > Training principle validated
- *"Graph topology encodes more than embeddings"*

### Phase 7: Semantic Dimensions + Extended Methods (November 2025)
- **56 interpretable dimensions** added to nodes
- 10 extended query methods: `similar_to`, `impact_analysis`, `dimension_filter`, etc.
- 172+ CLI flags across 6 tools
- **3 KG databases**: manual (266 nodes), auto (1,791 nodes), unified (2,057 nodes / 284K edges)
- *"Named dimensions are debuggable; opaque embeddings are not"*

### Phase 8: Meta-Cognition (November 2025)
- 35 meta-cognition tools across 7 phases
- Fact validation, mud detection, synthesis chains
- Persistence layer for cross-session learning
- 64 tests passing
- *"Tools for awareness vs BEING aware"*

### Phase 9: Workspace Integration (December 2025 - February 2026)
- Multi-AI Agentic Workspace built: FastAPI + React 19
- **57 KG databases** imported into workspace
- KG Studio: graph visualization, CRUD, search, RAG chat
- 8-stage agentic loop with memory, skill injection, streaming
- *"From CLI scripts to production workspace"*

### Phase 10: KG-OS Integration (February 2026) — THIS IS NOW
- 12 query methods ported from Flags Toolkit
- 4-weight scoring formula (extending 3-weight hybrid)
- Expert Agent model: KG + Persona + Retrieval Config
- Intent classification enhanced to 14 categories
- Composition planning, impact analysis, dimension filtering
- API endpoints for expert CRUD + expert chat + direct KG-OS access
- *"From 'what is a KG?' to 2,057 nodes / 284K edges to 'Tailored Expert Agents'"*

### The Journey in Numbers

| Metric | Phase 1 | Phase 7 | Phase 10 |
|--------|---------|---------|----------|
| Nodes | 78 | 2,057 | 2,057+ (57 KGs) |
| Edges | ~50 | 284,178 | 284,178+ |
| Retrieval mechanisms | 1 | 7 | 7 + intent routing |
| Query methods | 0 | 14 | 12 ported + enhanced |
| Semantic dimensions | 0 | 56 | 56 |
| Recall (strict) | ~48% | 88.5% | 88.5% (same formula) |
| CLI flags | 0 | 172+ | N/A (web API) |
| KG databases | 1 | 3 | 57 |

---

## 14. Roadmap / Future Enhancements

### Near Term (Next Sprint)

#### Multi-KG Expert Composition
Allow a single expert to query 3+ KGs simultaneously with per-KG weight tuning. Currently, `kg_db_ids` queries each KG independently and merges results. The enhancement would enable cross-KG edge traversal (e.g., following a `requires` edge from a node in `python-kg` to a node in `testing-kg`).

**Design consideration:** Cross-KG edges need a namespace convention (`python-kg:node_id` vs `testing-kg:node_id`) to avoid ID collisions.

#### Dimension Auto-Extraction from New KGs
When a new KG is imported, automatically extract dimension values for its nodes based on node properties and edge patterns:
- `pricing_tier` inferred from "cost" or "price" in properties
- `implementation_complexity` inferred from number of `requires` edges
- `relationship_richness` computed directly from degree centrality

**Implementation:** A post-import pipeline that runs dimension extraction rules and stores results in node properties.

### Medium Term (1-2 Months)

#### Expert Marketplace (Share/Import Expert Configs)
Export an expert configuration (persona + retrieval config + dimension filters + goal mappings) as a portable JSON file. Other workspace instances can import it. The expert config is decoupled from the KG data — the receiving instance needs a compatible KG but not an identical one.

**Schema versioning:** Expert configs include a `schema_version` field. Import validates compatibility before applying.

#### A/B Testing of Retrieval Configs
Create two variants of an expert (e.g., high-intent vs high-graph) and randomly assign user queries to each variant. Track:
- User satisfaction (thumbs up/down)
- Retrieval precision (how many cited sources were actually used)
- Response latency (heavier configs may be slower)
- Intent classification accuracy (did the right method fire?)

**Storage:** A/B test results stored in the workspace memory DB with `test_id`, `variant`, `metrics` columns.

#### Expert Chain-of-Thought Visualization
Show the user not just the response but the retrieval process:
- Which intent was classified
- Which query methods were invoked
- Which nodes scored highest and why (score breakdown by alpha/beta/gamma/delta)
- Which edges were followed during expansion
- Whether a composition plan was generated

**Frontend:** A collapsible "reasoning trace" panel below the chat response, similar to extended thinking display but for retrieval.

### Long Term (3-6 Months)

#### Automatic KG Gap Detection from Chat Failures
When an expert fails to answer a question (user signals dissatisfaction, or the LLM admits it lacks information), log the query and the retrieved nodes. Periodically analyze the failure log to detect:
- Queries with no matching nodes (KG gap)
- Queries where retrieved nodes were irrelevant (retrieval misconfiguration)
- Patterns in failed queries (e.g., all failures relate to "deployment" topics)

Generate a KG enhancement report suggesting nodes and edges to add.

#### Federated Expert Network
Multiple workspace instances, each with their own KGs and experts, form a federation. An expert can delegate sub-queries to experts on other instances:
- "Python Expert" locally handles Python questions
- Delegates "Kubernetes deployment" sub-query to a remote "DevOps Expert"
- Results are aggregated with provenance tracking

**Protocol:** HTTP-based delegation with signed query/response payloads. Each instance advertises its expert capabilities.

#### Real-Time KG Learning from Expert Conversations
When an expert conversation reveals new knowledge (user corrects a wrong answer, provides new information, or asks about something not in the KG), automatically propose new nodes and edges for review:
- Extract entities from the conversation using `ingestion_service`
- Match against existing KG to find gaps
- Queue proposed additions for human review
- On approval, add to KG and re-index

This closes the loop: the KG improves from every expert conversation, making future conversations more accurate.

#### Dimension Drift Detection
Over time, the accuracy of assigned dimension values may degrade as the underlying tools/patterns evolve (e.g., a tool that was expensive becomes cheap after a pricing change). Monitor:
- User queries where dimension filters exclude the correct answer
- Dimension values that contradict recent conversation context
- Temporal patterns in dimension relevance

Alert KG curators when dimension values need updating.

---

## Appendix A: File Reference

| File | Location | Purpose |
|------|----------|---------|
| `kg_service.py` | `backend/services/kg_service.py` | KG CRUD, schema detection, FTS |
| `embedding_service.py` | `backend/services/embedding_service.py` | BM25, cosine, graph boost, hybrid search |
| `analytics_service.py` | `backend/services/analytics_service.py` | NetworkX centrality, communities, paths |
| `rag_chat_service.py` | `backend/services/rag_chat_service.py` | RAG retrieval + generation |
| `agentic_loop.py` | `backend/services/agentic_loop.py` | 8-stage pipeline |
| `skill_injector.py` | `backend/services/skill_injector.py` | Intent classification, playbook injection |
| `memory_service.py` | `backend/services/memory_service.py` | Conversation + workspace memory |
| `ingestion_service.py` | `backend/services/ingestion_service.py` | AI entity extraction |
| `kg.py` | `backend/routers/kg.py` | KG API router (33 endpoints) |
| `query-cookbook.py` | `docs/flags/query-cookbook.py` | Flags Toolkit: main query interface |
| `kg-impact-analyzer.py` | `docs/flags/kg-impact-analyzer.py` | Flags Toolkit: impact analysis |
| `kg-query-unified.py` | `docs/flags/kg-query-unified.py` | Flags Toolkit: cross-KG queries |
| `KG-QUERY-FLAGS-REFERENCE.md` | `docs/flags/KG-QUERY-FLAGS-REFERENCE.md` | Flags Toolkit: complete reference |
| `INTENT-DRIVEN-QUERY-SYSTEM.md` | `docs/flags/INTENT-DRIVEN-QUERY-SYSTEM.md` | Flags Toolkit: intent system spec |

## Appendix B: Schema Profiles

The workspace supports 6 schema profiles for automatic KG database detection. KG-OS works identically across all profiles because `kg_service._detect_profile()` normalizes column names.

| Profile | Node Table | Node ID | Node Name | Edge Table | Edge Source | Edge Target | Edge Type |
|---------|-----------|---------|-----------|-----------|-------------|-------------|-----------|
| `unified` | unified_nodes | node_id | name | unified_edges | source_node_id | target_node_id | edge_type |
| `standard` | nodes | id | name | edges | source | target | type |
| `claude` | nodes | node_id | name | edges | source_node_id | target_node_id | edge_type |
| `hal` | nodes | id | name | edges | source_id | target_id | edge_type |
| `from_node` | nodes | id | name | edges | from_node | to_node | type |
| `entities` | entities | id | name | relations | source_id | target_id | relation_type |
| `heuristic` | (auto-detected) | (auto-detected) | (auto-detected) | (auto-detected) | (auto-detected) | (auto-detected) | (auto-detected) |

The `heuristic` profile is a fallback that probes column names and table structures to find a best-fit mapping when no known profile matches.

## Appendix C: Retrieval Performance Benchmarks

Historical benchmark results from the Flags Toolkit evaluation (10-query benchmark):

| Configuration | Strict Recall@5 | Lenient Recall@5 | Avg Latency |
|--------------|-----------------|-------------------|-------------|
| Embedding only (alpha=1.0) | ~50% | ~60% | 45ms |
| BM25 only (beta=1.0) | ~60% | ~70% | 8ms |
| FTS5 only | ~55% | ~65% | 3ms |
| Graph boost only (gamma=1.0) | ~30% | ~40% | 12ms |
| 3-weight hybrid (0.40/0.45/0.15) | **88.5%** | **100%** | 55ms |
| RRF with 7 strategies | 66.7% | 80% | 120ms |
| 4-weight with intent (0.35/0.40/0.15/0.10) | **88.5%** | **100%** | 65ms |

Notes:
- Benchmarks run on the 266-node manual KG (claude-cookbook-kg.db)
- "Lenient" allows semantic equivalence (same concept, different node ID)
- 4-weight formula maintains recall while adding intent-directed precision
- Latency measured on Celeron N3350 (low-power hardware); faster on modern CPUs

---

*This document is a living reference. It will be updated as KG-OS is implemented, tuned, and extended.*

*Architecture: Multi-AI Agentic Workspace v2.0.0*
*Methodology: NLKE v3.0 — Document AS you build*
*Date: February 23, 2026*

# Domain Report 1: RAG / Graph-Retrieval / Flags

**Author:** Eyal Nof | **Date:** February 8, 2026 | **Scope:** Every retrieval mechanism across the ecosystem

---

## 1. Retrieval Taxonomy

The ecosystem implements **3 distinct retrieval mechanisms** across 4 codebases:

| Mechanism | Location | Algorithm | Threshold |
|-----------|----------|-----------|-----------|
| Intent-based | flags/query-cookbook.py | User intent -> method dispatch (want_to, can_it, how_does, compose_for) -> graph traversal -> structured result | N/A (dispatch) |
| Context-based | soccer-ai/rag.py + kg_integration.py | Entity extraction -> FTS5 text search + KG graph traversal -> weighted fusion (beta=0.60, gamma=0.40) -> deduplication | Match on keywords |
| Semantic-based | flags/kg-ask.py + kg-pattern-mapper.py | Query -> embedding lookup -> cosine similarity over 50D vectors -> threshold filter -> top-K | 0.7 cosine |

---

## 2. Flags KG Toolkit (9,740 lines)

### 2.1 query-cookbook.py (3,507 lines) -- The Reasoning Engine

**Class:** `ClaudeCookbookKG`
**Database:** SQLite with `nodes` and `edges` tables
**Connection:** `sqlite3.connect(db_path)` with `row_factory = sqlite3.Row`

#### Core Query Methods

**`find_nodes(search_term) -> List[Dict]`**
SQL: `WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(id) LIKE ?`
Pattern: `%{search_term.lower()}%` wrapped in wildcards

**`get_edges_from(node_id, edge_type=None) -> List[Dict]`**
JOINs `edges` with `nodes` on `e.to_node = n.id` (target enrichment). Filters by `from_node` and optionally by `type`.

**`get_edges_to(node_id, edge_type=None) -> List[Dict]`**
Reverse direction: JOINs on `e.from_node = n.id` (source enrichment).

#### 12 Intent-Based Methods

| Method | Input | Algorithm | Output |
|--------|-------|-----------|--------|
| `want_to(desc)` | "I want to build X" | find use_case nodes -> get enabling capabilities -> get examples | `{use_cases, capabilities, examples}` |
| `can_it(desc)` | "Can Claude do X?" | find capability/feature nodes -> get enabled use cases | `{capabilities, use_cases}` |
| `how_does(desc)` | "How does X work?" | find node -> query depends_on, feeds_into, has_component, enables, demonstrates edges | `{prerequisites, flow, components, use_cases, examples}` |
| `compose_for(desc)` | "I need X" | find use_case -> get enabling capabilities -> detect sequential vs parallel via feeds_into edges -> get dependencies | `{use_case, capabilities, pattern, examples}` |
| `discover_emergent_capabilities()` | None | find use_cases with >= 2 enabling capabilities -> build co-occurrence matrix -> discover sequences | `{patterns, combinations}` |
| `optimize_for(criteria)` | "Optimize for cost" | keyword scoring across all nodes -> ranked results | `{strategies}` |
| `alternatives(desc)` | "What else does X?" | find same-type nodes with shared edges | `{alternatives}` |
| `compare_nodes(a, b)` | Two node IDs | dual lookup -> shared/unique edges | `{comparison}` |
| `trace_relationship(type, from)` | Edge type + start node | linear chain traversal, first-edge-only, 20-step limit | `{chain}` |
| `get_provenance(node)` | Node ID | metadata extraction: phase, source, discovery_method | `{provenance}` |
| `get_orchestration_meta(node)` | Node ID | metadata: trade_offs, best_for, complementary | `{meta}` |
| `get_arsenal_status()` | None | Full KG stats: node types, edge types, connectivity, hubs | `{stats}` |

#### compose_for() Pipeline Detection (lines 753-909)

```
1. Find matching use_case nodes (fallback: pattern, workflow)
2. Get enabling capabilities via 'enables' edges
3. For each capability: check for outgoing 'feeds_into' edges
   IF any exist -> "Sequential Pipeline" (data flows between capabilities)
   ELSE -> "Parallel/Composite" (independent capabilities merged)
4. Resolve dependencies via 'depends_on' edges
5. Find examples via 'demonstrates' edges
```

#### discover_emergent_capabilities() Algorithm (lines 1216-1332)

```
1. Get all use_case nodes
2. For each: count enabling capabilities (incoming 'enables' edges)
3. Filter: keep only use_cases with >= 2 enabling capabilities
4. Sort by capability count (descending)
5. Build co-occurrence matrix:
   For each emergent pattern with N capabilities:
     For all C(N,2) pairs: increment co_occurrence[(cap_i, cap_j)]
6. Discover sequences: follow 'feeds_into' chains of 3+ steps
7. Return patterns + top 5 co-occurring pairs
```

**Mathematical formalization:**
```
CoOccurrence(c_a, c_b) = |{p in Patterns : c_a in C(p) AND c_b in C(p)}|
```

#### Constants and Magic Numbers

| Constant | Value | Used In |
|----------|-------|---------|
| BFS edge limit per node | 5 | explore_node() |
| Minimum chain length | 2 | _discover_sequences() |
| Emergent threshold | 2 capabilities | discover_emergent_capabilities() |
| Trace chain limit | 20 steps | trace_relationship() |
| Compose capability limit | 5 | compose_for() |
| Example limit | 3 | compose_for(), how_does() |

#### Edge Types Used
`enables`, `feeds_into`, `depends_on`, `demonstrates`, `has_component`, `is_type_of`, `requires`, `guided_creation`

---

### 2.2 kg-ask.py (770 lines) -- Natural Language KG Interface

**Three-stage pipeline:** QueryUnderstanding -> KGQueryExecutor -> ResultFormatter

#### QueryUnderstanding (lines 94-172)

6 query types detected via regex patterns:

| Type | Patterns | Example |
|------|----------|---------|
| `pattern_implementation` | 3 regex | "which code implements the X pattern" |
| `code_understanding` | 4 regex | "what does X do" |
| `dependency_analysis` | 4 regex | "what depends on X" |
| `semantic_search` | 3 regex | "find similar to X" |
| `cross_reference` | 3 regex | "which patterns does X implement" |
| `capability_query` | 3 regex | "what can X do" |

**Confidence levels:** 0.9 (regex match), 0.5 (keyword fallback), 0.3 (default = semantic_search)

#### KGQueryExecutor (lines 178-478)

**Embedding loading:**
- Pattern embeddings: `.npz` format, prefixed `"manual:"` namespace
- Code embeddings: `embeddings_full.json` with `{nodes: [{node_id, dimensions: {dim: float}}]}`, prefixed `"auto:"` namespace
- Both are 50D vectors stored as `np.float32`

**Semantic search algorithm (lines 350-405):**
```
1. Find code node by name LIKE query, source_kg='auto', LIMIT 1
2. Get embedding for found node
3. Compute cosine_similarity against ALL other code embeddings
4. Filter: similarity >= 0.7
5. Sort descending, take top 20
```

**Cosine similarity (lines 472-478):**
```python
dot(v1, v2) / (norm(v1) * norm(v2))  # Returns 0.0 if either norm is zero
```

---

### 2.3 kg-merger.py (642 lines) -- Dual KG Merge

**Source KGs:**
- Manual: claude-cookbook-kg.db (266 nodes, 605 edges)
- Auto: kg-extractor-v2-complete.db (1,791 nodes, 283K edges)

**Namespace isolation:**
- Manual nodes get `"manual:"` prefix
- Auto nodes get `"auto:"` prefix
- Edge endpoints updated to match

**Three-tier deduplication:**
1. Exact name match: confidence = 1.0
2. Case-insensitive match: confidence = 0.9
3. Fuzzy substring match (>= 5 chars): confidence = 0.7
- Default merge threshold: 0.9 (ignores fuzzy matches)
- Strategy: keeps manual node, redirects auto node

**Cross-reference building:**
- For each manual node with embedding, compute cosine similarity against all auto nodes with embeddings
- Threshold: 0.7 -> creates `implements` edge with similarity as weight
- Edge type: `source_kg = 'cross_reference'`

---

### 2.4 kg-validate-rules.py (994 lines) -- Architecture Validation

**RuleRegistry pattern:** register(), get_rule(id), get_rules_by_category(), get_all_rules()

**16 built-in validation rules:**

| Rule ID | Category | Severity | What It Checks |
|---------|----------|----------|----------------|
| STR001+ | structure | error | Circular dependencies (DFS + recursion stack) |
| | structure | warning | Orphaned nodes (no edges) |
| | consistency | error | Dangling references (edge to missing node) |
| | consistency | warning | Symmetric relationship validation |
| | consistency | warning | Namespace consistency (manual: -> auto: only) |
| | consistency | warning | Edge type validity |
| | completeness | info | Pattern coverage (patterns without implementations) |
| | completeness | info | Documentation coverage |
| | quality | warning | Required metadata fields |
| | quality | info | Minimum edge weight thresholds |
| | quality | info | Naming conventions |
| | quality | warning | Duplicate node detection |

**CI/CD integration:** GitHub Actions output format, severity determines exit code

---

### 2.5 Other Flags Tools

| File | Lines | Purpose | Key Algorithm |
|------|-------|---------|--------------|
| kg-critical-components.py | 689 | Centrality metrics | In-degree, out-degree, betweenness (sampled BFS, 50 nodes) |
| kg-impact-analyzer.py | 658 | Change impact | BFS forward/reverse traversal, risk scoring: `in*0.5 + out*0.2 + deps*0.3` |
| kg-pattern-mapper.py | 625 | Pattern-code mapping | 50D cosine similarity, opportunity detection (0.5-0.7 range) |
| kg-query-unified.py | 601 | Dual-KG interface | Jaccard word similarity: `name*0.3 + desc*0.5 + keyword*0.3`, threshold 0.3 |
| query-cookbook-enhanced.py | 890 | Enhanced cookbook | Extended query methods |
| kg-importer.py | 364 | Schema + import | SQLite table creation, tier3 JSON ingestion |

---

## 3. Soccer-AI Retrieval (Hybrid FTS5 + KG)

### 3.1 rag.py (1,344 lines) -- Main RAG Module

#### Entity Extraction
- `TEAM_ALIASES`: 15 mappings (e.g., "man utd" -> "Manchester United")
- `TIME_PATTERNS`: 8 temporal expressions ("yesterday" -> -1 day)
- Player detection: capitalized words not in aliases, combined consecutive capitals, verified against database

#### Intent Detection (lines 162-222)
Priority order (first match wins):
1. score (7 keywords)
2. injury (6 keywords)
3. transfer (7 keywords)
4. fixture (14 phrases + 4 single words)
5. standing (16 keywords including "top 4", "relegation zone")
6. stats, player_info, team_info
7. Default: "general"

#### KG Intent Detection (lines 802-836)
Secondary intent for graph traversal: rivalry, moment, legend, emotional, discovery, relationship, multi_hop

#### retrieve_hybrid() -- Core Function (lines 1053-1181)

```
1. extract_kg_entities(query)     -> entities with KG node resolution
2. retrieve_context(query)        -> FTS5 results (standard RAG)
3. retrieve_kg_context(entities)  -> graph traversal results
4. get_enhanced_context(query)    -> 500-node KG enrichment (if available)
5. Club persona enrichment       -> legends, rivalries, mood
6. fuse_contexts(fts, kg, mood)  -> KG first, then FTS5, then mood
7. deduplicate_sources()          -> composite keys: (type, id/name/rival)
```

**Fusion formula:** Documented as `beta=0.60 (FTS5) + gamma=0.40 (KG)`, but actual implementation is **concatenation in priority order** (KG first, FTS5 second, mood third). The weights are a design intent annotation, not applied numerically.

#### Source Deduplication (lines 68-100)
Three-tier tuple keys: `(type, "id", id)` > `(type, "name", name)` > `(type, "rival", rival)`

### 3.2 kg_integration.py (462 lines) -- KG Bridge

**KGIntegration class** (singleton via `get_kg()`):
- `_load_entities()`: Loads all KG nodes into memory dict, builds 50+ club aliases
- `find_entities(text)`: Alias-first, then full name matching
- `get_entity_context(name, include_relationships=True)`: Full node profile with outgoing/incoming edges
- `search_facts(query, limit)`: FTS5 search on KB facts table
- `get_enhanced_context(query, club)`: Combined KG+KB entry point -- finds entities, gets contexts (up to 5), searches facts, builds combined string with `kg_stats`

### 3.3 database.py (1,946 lines) -- Data Layer

**Key retrieval functions:**
- `escape_fts_query(query)`: Remove null bytes, HTML, special chars; wrap tokens in quotes; handle OR/AND/NOT/NEAR reserved words
- `traverse_kg(node_id, depth, relationship=None)`: BFS with depth limiting, returns `[{node, edge, depth}]`
- `export_kg_to_vis_json()`: vis.js format with node colors (team=#e74c3c, legend=#f39c12, moment=#3498db)

---

## 4. NLKE Current Retrieval (rag_kg_query.py, 296 lines)

### Current Algorithm

```
analyze(query):
  1. Keyword extraction: regex split + 20 stopwords + min 3 chars
  2. Query ALL registered KGs (4 from KG_DATABASES + auto-discovered .db files)
     SQL: WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?
     Relevance: min(1.0, keyword_hits / total_keywords + 0.3)
  3. Search documents: recursive .md/.txt search, line-level keyword match
     Threshold: hits >= 2 OR (hits >= 1 AND len > 50)
     Relevance: min(1.0, hits / total_keywords + 0.2)
  4. Merge, dedup by node_id, sort by relevance
```

### Gap Analysis

| Capability | rag_kg_query (296 LOC) | Flags toolkit (9,740 LOC) | Gap |
|------------|----------------------|--------------------------|-----|
| Query understanding | Regex tokenize + stopwords | 6-type regex detection with confidence scoring | No intent classification |
| Similarity search | Keyword substring match | 50D cosine similarity with 0.7 threshold | No embeddings |
| Result composition | Flat list merge | Progressive discovery (nodes -> edges -> examples -> next steps) | No structured composition |
| Validation | 4 string rule IDs | RuleRegistry with 16+ typed rules, severity, CI/CD | No rule engine |
| Multi-KG | Queries each independently | Namespace isolation, cross-referencing, dedup | No cross-referencing |
| Intent routing | None | 12 specialized methods | No dispatch |
| Emergent discovery | None | Co-occurrence matrix, sequence chains | No emergence |

---

## 5. unified-complete.db Structure

**Path:** `/storage/emulated/0/Download/77/KGs/unified-complete.db`
**Size:** 151.6 MB

| Metric | Value |
|--------|-------|
| Nodes | 4,828 |
| Edges | 676,950 |
| Average edges/node | ~140 |
| Connected nodes | 88.5% |
| Source KGs merged | 12 |
| Edge types | 160+ |
| FTS5 coverage | 100% |
| Domain split | Claude 56.4%, Bridge 36.6%, Gemini 5.8% |

**Dual embedding system:**
- 64D hash embeddings: 78.7% node coverage
- 44D dimension score embeddings: 21.3% coverage

**PNP subsystem:** 83 research/hypothesis nodes

---

## 6. KG JSON Format (NLKE-native)

Files at NLKE root: `master-kg-combined.json`, `claude-api-kg-combined-nodes.json`, `integrated-kg-combined.json`, `master-kg-best-practice-nodes.json`, `master-kg-emergent-nodes.json`, `master-kg-relationships.json`, `master-kg-tool-nodes.json`, `master-kg-workflow-nodes.json`

```json
{
  "nodes": [{
    "id": "cap_classification",
    "type": "capability",
    "name": "Classification with Claude",
    "description": "...",
    "complexity": "medium",
    "use_cases": ["..."],
    "prerequisites": ["..."],
    "best_practices": ["..."],
    "performance_metrics": {"baseline_accuracy": "70%", "with_rag": "94%"}
  }]
}
```

---

## 7. Similarity/Relevance Scoring Summary

| System | Method | Threshold | Formula |
|--------|--------|-----------|---------|
| kg-ask.py | 50D cosine similarity | 0.7 | dot(v1,v2)/(norm1*norm2) |
| kg-merger.py | 50D cosine similarity | 0.7 | dot(v1,v2)/(norm1*norm2) |
| kg-query-unified.py | Jaccard word overlap | 0.3 | name*0.3 + desc*0.5 + kw*0.3 |
| kg-pattern-mapper.py | 50D cosine + keyword boost | 0.7 | cos(a,b) + 0.1*keyword_match |
| rag_kg_query.py | Keyword hit ratio | any match | min(1.0, hits/total + 0.3) |
| soccer-ai rag.py | FTS5 + KG concatenation | N/A | Priority ordering (KG first) |

---

## 8. Universal KG Schema

```sql
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    metadata TEXT,              -- JSON blob
    [source_kg TEXT],           -- unified KGs only
    [original_id TEXT],         -- unified KGs only
    [created_at TIMESTAMP]
);

CREATE TABLE edges (
    [id INTEGER PRIMARY KEY AUTOINCREMENT],
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    type TEXT,
    [weight REAL],
    [source_kg TEXT],
    [created_at TIMESTAMP],
    FOREIGN KEY (from_node) REFERENCES nodes(id),
    FOREIGN KEY (to_node) REFERENCES nodes(id)
);
```

---

## 9. Integration Points Map

```
JSON KG Files (master-kg-*.json)
      |  (ingested by kg-importer.py)
      v
SQLite KGs (.db)
      |
  +---+----+
  |        |
  v        v
Manual KG    Auto KG
  |        |
  v        v
kg-merger.py ----> unified-kg.db ----> unified-complete.db (151.6 MB)
  |                     |
  v                     v
kg-query-unified.py   kg-ask.py (embeddings + REPL)
                        |
query-cookbook.py        |
(intent dispatch)       |
                        v
              rag_kg_query.py (NLKE agent, queries ALL KGs)
                        |
              soccer-ai/rag.py (FTS5 + KG + mood + live data)
```

# KG Studio Libraries & Capabilities Guide

Reference for the new libraries powering the Graph-RAG Knowledge Graph workspace.

---

## Installed Libraries

### 1. NetworkX 3.6.1 (`networkx`)
**Purpose:** Graph algorithms and analytics engine

**What it gives us:**
- **Centrality metrics** — Identify the most important nodes in any KG
  - `degree_centrality`: Most connected nodes
  - `betweenness_centrality`: Bridge nodes between clusters
  - `pagerank`: Google-style importance ranking
- **Community detection** — Discover clusters of related knowledge
  - Greedy modularity communities (Louvain-like)
  - Groups nodes into thematic communities automatically
- **Path finding** — Trace relationships between any two concepts
  - `shortest_path`: How are two nodes connected?
  - `all_simple_paths`: All possible routes between nodes
- **Graph metrics** — Structural health of your KGs
  - Density, clustering coefficient, connected components
  - Average degree, isolated nodes, diameter
- **Subgraph extraction** — Pull neighborhoods for visualization

**Used in:** `backend/services/analytics_service.py`
- Loads KG SQLite data into `nx.DiGraph` for computation
- Approximate betweenness for large graphs (>1K nodes) to stay fast
- All results cached per-database

**Key capability unlocked:** The Analytics tab — run PageRank on any of your 57 KGs, detect communities, find shortest paths between concepts, get structural summaries.

---

### 2. Model2Vec 0.7.0 (`model2vec`)
**Purpose:** Offline embedding generation (no API calls needed)

**What it gives us:**
- **Static word embeddings** from distilled transformer models
- **potion-base-8M** model: 8 million parameters, ~30MB, runs on CPU
- Generates 256-dimensional vectors for any text
- Pure NumPy inference — no PyTorch/TensorFlow required
- ~1000 embeddings/second on CPU

**Dependencies installed with it:**
- `safetensors` 0.7.0 — Fast, safe tensor serialization (Rust-based, built from source on aarch64)
- `tokenizers` 0.22.2 — HuggingFace fast tokenizers (Rust-based, built from source on aarch64)
- `joblib` 1.5.3 — Parallel processing utilities

**Used in:** `backend/services/embedding_service.py`
- Strategy 3 (offline fallback) in the multi-strategy search pipeline
- Generates embeddings when Gemini API is unavailable or for batch operations
- No API key or internet required

**Key capability unlocked:** The Embeddings tab — generate embeddings for entire KGs offline. Also enables hybrid search to work without an API key by falling back to Model2Vec vectors + BM25 text search.

---

### 3. LightRAG-HKU 1.4.9.11 (`lightrag-hku`)
**Purpose:** Automated entity/relation extraction + Graph-RAG pipeline

**What it gives us:**
- **Entity extraction from text** — Feed it any document, it outputs structured entities and relationships
- **Graph-RAG construction** — Automatically builds knowledge graphs from unstructured text
- **Community summaries** — Generates high-level summaries of graph clusters for global questions
- **Multi-level retrieval** — Local (entity-specific), global (theme-level), and hybrid modes
- Uses Gemini as the LLM backend (via google-genai)

**Dependencies installed with it:**
- `tiktoken` 0.12.0 — OpenAI's fast BPE tokenizer (token counting)
- `nano-vectordb` 0.0.4.3 — Lightweight in-memory vector store
- `json-repair` 0.58.0 — Fixes malformed JSON from LLM outputs
- `google-api-core` 2.30.0 — Google API utilities
- `configparser`, `python-dotenv`, `pypinyin`, `xlsxwriter`, `pipmaster`

**Used in:** `backend/services/ingestion_service.py`
- The "lightrag" ingestion method in the Ingest tab
- Takes raw text (paste an article, documentation, notes) and extracts a KG automatically
- Entities get inserted as nodes, relationships as edges

**Key capability unlocked:** The Ingest tab's "LightRAG" mode — paste any text and watch it automatically extract entities and relationships into your KG. Also powers the optional GraphRAG index building for community-level summaries.

**Note:** Installed with `--no-deps` due to pandas version conflict (requires <2.4, Termux has 3.0). Works fine at runtime since pandas 3.0 is backward-compatible for LightRAG's usage.

---

### 4. d3-force (npm)
**Purpose:** Force-directed graph layout computation

**What it gives us:**
- **Physics simulation** for node positioning — nodes repel each other, edges act as springs
- `forceSimulation` — Main simulation engine
- `forceLink` — Edge-based attraction (connected nodes pull together)
- `forceManyBody` — Node repulsion (prevents overlap)
- `forceCenter` — Gravity toward canvas center
- `forceCollide` — Collision detection (minimum spacing)
- Runs in a web worker or useEffect — computes positions, React Flow renders

**Used in:** `frontend/src/components/kg/KGCanvas.tsx`
- Computes x,y positions for graph nodes based on their connections
- Runs simulation on subgraph load, settles positions, then freezes
- React Flow handles all interactivity (drag, zoom, pan, minimap)

**Key capability unlocked:** The Explore tab's graph visualization — when you click a node and load its neighborhood, d3-force arranges them in a natural, readable layout where connected nodes cluster together.

---

### 5. sqlite-vec (NOT INSTALLED)
**Purpose:** Vector similarity search inside SQLite

**Status:** No pre-built wheel for aarch64/Android. Would provide:
- `vec0` virtual tables for KNN search
- Cosine similarity, L2 distance in pure SQL
- Sub-millisecond vector lookups

**Graceful degradation:** The embedding service falls back to:
1. NumPy cosine similarity (load embeddings into memory, compute distances)
2. BM25/FTS5 text search (always available in SQLite)

**Future:** When you have the RTX 3060 build running x86_64 Linux, `pip install sqlite-vec` will work and vector search will automatically activate.

---

## How They Work Together

```
User pastes text into Ingest tab
            |
            v
  [LightRAG / Gemini] -----> Extracts entities + relations
            |
            v
  [kg_service.py] ----------> Stores in SQLite KG
            |
            v
  [Model2Vec / Gemini] -----> Generates embeddings for new nodes
            |
            v
  [embedding_service.py] ---> Indexes for hybrid search
            |
            v
  User searches in Search tab
            |
            v
  [Hybrid Formula] ----------> 0.40*embedding + 0.45*BM25 + 0.15*graph_boost
            |
            v
  [NetworkX] ----------------> Expands results via graph neighbors
            |
            v
  [d3-force + React Flow] ---> Visualizes subgraph on canvas
            |
            v
  [rag_chat_service.py] -----> RAG Chat uses retrieved context + Gemini streaming
```

## Search Strategy Comparison

| Strategy | Requires | Speed | Quality | Offline? |
|----------|----------|-------|---------|----------|
| BM25/FTS5 | SQLite only | Instant | Good for exact terms | Yes |
| Gemini Embeddings | API key | ~200ms/query | Best semantic quality | No |
| Model2Vec Embeddings | model2vec | ~1ms/query | Good (256-dim distilled) | Yes |
| Hybrid (all combined) | Any above | Varies | Best overall (88.5% recall) | Partially |

## RTX 3060 Build Upgrades

When your desktop build is running, these become available:

| Upgrade | What Changes |
|---------|-------------|
| `sqlite-vec` | Native vector search in SQLite — faster than NumPy fallback |
| GPU-accelerated embeddings | Model2Vec runs faster, can use larger models |
| Larger KG operations | 677K-edge graphs load faster with more RAM |
| CUDA inference | LightRAG entity extraction speeds up significantly |
| Full pandas | No version conflict, all LightRAG features available |
| Potential local LLMs | Ollama + Gemma/Llama for offline RAG chat |

---

*Last updated: 2026-02-23*

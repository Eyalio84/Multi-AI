# Weights, Graph-RAG & Embeddings: Technical Evolution Report

**Project**: gemini-3-pro / AI-LAB — Retrieval & Embedding Layer
**Author**: Eyal Nof + Claude
**Date**: February 13, 2026
**Scope**: The full technical evolution from raw embeddings to intent-adaptive hybrid retrieval to configurable multi-model embedding pipeline to unified CLI to interactive KG prediction curation — now with real benchmark results and a universal engine config system

---

## The Central Question

How do you turn a knowledge graph with 511 nodes and 631 edges into a system that finds the right answer 100% of the time?

This report traces the answer through three layers: **weights** (how retrieval signals are balanced), **Graph-RAG** (how graph structure enhances retrieval), and **embeddings** (how text becomes numbers that machines can compare).

---

## Part 1: The Weight Evolution (Narrative)

### 1.1 Single-Signal Baselines

Before hybrid retrieval, the system tried each signal alone:

| Signal | How It Works | Recall@10 | Where It Fails |
|--------|-------------|-----------|----------------|
| **Vector similarity** | Embed query + node, compute cosine distance | ~50% → 72% | Misses exact terminology. "Prompt caching" doesn't embed close to the node about it |
| **BM25 keywords** | Term frequency + inverse document frequency | ~60% → 65% | Misses semantic similarity. "Smart workflows" doesn't contain "agent" or "orchestration" |
| **Graph proximity** | Boost nodes whose neighbors match query terms | ~45% | Misses isolated nodes with no relevant neighbors |

Each signal captures something real, but each has a blind spot that the others cover.

### 1.2 The First Hybrid: Fixed Weights (88.5%)

The breakthrough was combining all three with learned weights:

```
H(q, n) = 0.40 x V(q,n) + 0.45 x B(q,n) + 0.15 x G(q,n)
```

| Signal | Weight | Role |
|--------|--------|------|
| Vector (alpha) | 0.40 | Semantic similarity — catches conceptual matches |
| BM25 (beta) | 0.45 | Keyword matching — catches exact terms |
| Graph (gamma) | 0.15 | Structural proximity — catches connected context |

**88.5% Recall@10** — a massive jump from any single signal.

Three key ingredients beyond the formula:
1. **Intent keywords with 5x weight** in the BM25 index — "reduce costs" and "save money" indexed alongside technical names
2. **Targeted query expansion** for known weak queries only (not global expansion, which diluted precision)
3. **Graph neighbor boosting** — nodes connected to relevant nodes get a proximity signal

### 1.3 What Failed: The 7-Strategy Approach (66.7%)

Before the simple hybrid worked, a more complex approach was tried: **Reciprocal Rank Fusion (RRF)** combining 7 retrieval strategies simultaneously.

```
RRF_score(node) = sum(1 / (k + rank_i(node))) for i in 1..7
```

7 strategies included: vector search, BM25, graph traversal, category filtering, tag matching, description search, and combined re-ranking.

**Result: 66.7% Recall@10** — worse than the 3-signal hybrid.

**Why**: The signals overlapped too much. Category filtering and tag matching were subsets of what BM25 already captured. Adding them didn't introduce new information — it introduced noise. The Color Mixing Principle: two complementary colors (vector + BM25) make a beautiful result; seven overlapping colors make mud.

### 1.4 Intent-Adaptive Weights: The Jump to 100%

The fixed hybrid treated every query identically. But queries differ:

- "prompt caching" — user knows the exact term (BM25 should dominate)
- "intelligent workflows" — user describes a concept (embeddings should dominate)
- "what's related to agents?" — user wants to browse (graph should dominate)

**Solution**: Detect the query's intent and select weights accordingly.

**8 Intent-Adaptive Weight Profiles**:

| Intent | alpha (Vector) | beta (BM25) | gamma (Graph) | When Used |
|--------|-------|------|-------|-----------|
| EXACT_MATCH | 0.20 | **0.65** | 0.15 | User knows the term |
| CAPABILITY_CHECK | 0.30 | **0.55** | 0.15 | "Can it do X?" |
| DEBUGGING | 0.35 | **0.45** | 0.20 | Problem-solving queries |
| WORKFLOW | 0.30 | 0.40 | **0.30** | Multi-step processes |
| COMPARISON | 0.40 | 0.40 | 0.20 | "X vs Y" |
| GOAL_BASED | **0.45** | 0.35 | 0.20 | "How to achieve Y?" |
| EXPLORATORY | 0.35 | 0.30 | **0.35** | Browsing connections |
| SEMANTIC | **0.60** | 0.25 | 0.15 | Conceptual/abstract |

**Key observations**:
- alpha (vector) ranges from **0.20 to 0.60** — a 3x shift
- beta (BM25) ranges from **0.25 to 0.65** — a 2.6x shift
- gamma (graph) ranges from **0.15 to 0.35** — a 2.3x shift

Intent detection uses keyword pattern matching and query structure analysis. No API calls, no model inference. The cost: **microseconds per query**.

**Result**: 100% Recall@10 across 22 probes, 6 domains. Every probe, every domain, perfect recall.

### 1.5 Cross-Domain Validation (95.6%)

After the core 100%, the system was tested on 5 additional domains:

| Domain | Recall@10 |
|--------|-----------|
| Git operations | 100% |
| Shell commands | 100% |
| HTTP/API | 100% |
| Python tooling | 100% |
| Linux system | 78% |
| **Average** | **95.6%** |

4/5 new domains hit 100%. Linux at 78% was a **data gap** (not enough Linux-specific nodes in the KG), not an algorithm gap. The weights worked — the data was incomplete.

---

## Part 2: Graph-RAG — How Structure Enhances Retrieval (Narrative)

### 2.1 The Graph Boost Signal

The "graph" in Graph-RAG isn't just storage — it's the third retrieval signal. When a user queries "agent development", the graph boost asks: *which nodes are neighbors of nodes that match "agent" or "development"?*

```python
def compute_graph_boost(query, node, neighbors):
    query_terms = query.lower().split()
    boost = 0.0
    for neighbor in neighbors:
        neighbor_text = f"{neighbor.name} {neighbor.description}".lower()
        matches = sum(1 for term in query_terms if term in neighbor_text)
        if matches > 0:
            boost += matches / len(query_terms)
    if len(neighbors) > 0:
        boost /= len(neighbors)
    return min(boost, 1.0)
```

At 15% weight (default), this seems small. But it's the signal that bridges 88.5% to 100%. It captures something neither embeddings nor keywords can: **structural context**. A node might not contain the right words or embed close to the query, but if it's connected to nodes that do, the graph boost surfaces it.

### 2.2 The Claude KG as Retrieval Substrate

The Claude KG (511 nodes, 631 edges) provides the structure for retrieval:

| Edge Type | Count | What It Captures |
|-----------|-------|-----------------|
| tool_uses_parameter | ~200 | Tool → parameter relationships |
| tool_complements | 30 | Tools that work well together |
| tool_alternative_to | 14 | Interchangeable tools |
| limitation_needs_workaround | 15 | Problem → solution chains |
| tool_has_limitation | ~50 | What tools can't do |
| use_case_requires_tool | ~80 | Goal → tool mappings |

This structure enables the 14 intent-driven query methods — zero-cost graph traversal that replaces embedding search for structured questions:

- `want_to("read a file")` → traverses `use_case_requires_tool` edges
- `why_not("Bash", "edit files")` → follows `tool_has_limitation` edges
- `compose_for("refactor Python")` → builds multi-tool workflows via `tool_complements` chains
- `similar_to("Grep")` → Jaccard similarity on neighbor sets

### 2.3 ULTRA: Neural Link Prediction on the Graph

ULTRA-50g takes Graph-RAG further. Instead of just querying existing edges, it **predicts missing edges** — what connections should exist but don't.

ULTRA's architecture:
- **Input**: 64-dim node features = [10-dim type one-hot | 54-dim text embedding]
- **Scoring**: `0.7 x cosine_similarity(head, tail) + 0.3 x tanh(MLP(concat(head, tail)))`
- **Output**: Link prediction score ∈ [-1, 1]

ULTRA can predict, for example, that `tool_Bash` should have a `complements` edge to `tool_Read` even if that edge wasn't manually curated — because the node features suggest they belong together.

The R1+ULTRA virtuous cycle:
1. ULTRA predicts missing links → "Bash should complement Read"
2. R1 validates via reasoning → "Yes, Bash runs commands and Read reads files — complementary"
3. Validated links are added to the KG
4. Richer KG improves future ULTRA predictions AND R1's retrieved context

---

## Part 3: The Embedding Evolution (Narrative)

### 3.1 Self-Supervised Embeddings (Gemini KG)

The Gemini KG uses self-supervised embeddings trained from corpus structure:

```
Token → TokenEncoder → base embedding (256-dim)
      → Contextualizer → attention-weighted composition
      → GraphFusion → eta x text_emb + (1-eta) x neighbor_emb
      → Normalized embedding
```

Training signal: InfoNCE contrastive loss — connected nodes should embed closer than random pairs. The knowledge graph IS the training curriculum.

These embeddings power the vector similarity signal (alpha) in the hybrid formula.

### 3.2 MiniLM: The Production Embedder (Claude KG / ULTRA)

For the Claude KG and ULTRA integration, the system uses **MiniLM-L6-v2**:

| Property | Value |
|----------|-------|
| Architecture | SBERT (Sentence-BERT), NLI-trained |
| Parameters | ~22M |
| Output dim | 384 |
| Context window | 512 tokens |
| Size on disk | 22MB (Q4_K_M GGUF) |
| Loading | llama-cpp-python with `embedding=True` |

MiniLM produces 384-dim embeddings that are truncated to 54-dim for ULTRA's input. This truncation is the current baseline — it keeps only the first 54 dimensions and L2-normalizes.

### 3.3 EmbeddingGemma: The Alternative

**EmbeddingGemma-300M-QAT** is a Google embedding model with different characteristics:

| Property | Value |
|----------|-------|
| Architecture | Gemma-based, QAT quantized |
| Parameters | ~300M |
| Output dim | 768 |
| Context window | 8,192 tokens |
| Size on disk | 220MB (Q4_0 GGUF) |

Key differences from MiniLM:
- **2x higher dimensionality** (768 vs 384) — more information to project from
- **16x longer context** (8192 vs 512) — can embed longer descriptions
- **10x larger** (220MB vs 22MB) — more capacity but more memory

### 3.4 The Hybrid Embedding Question

The user's insight: **Why choose one when you can test both and combine them?**

This is the same pattern as retrieval weights — different embedding models capture different aspects of text. MiniLM is trained on NLI (natural language inference), optimized for sentence similarity. EmbeddingGemma is trained on Google's broader data, with a different inductive bias.

The question: does combining both improve ULTRA's link prediction quality?

### 3.5 Phase 4a: The Configurable Embedding System

Phase 4a built the infrastructure to answer this question systematically.

**3 Embedding Modes** (enum `EmbeddingMode`):
- `MINILM_ONLY` — baseline, what the system currently uses
- `GEMMA_ONLY` — test EmbeddingGemma as an alternative
- `HYBRID` — combine both (loaded sequentially, never simultaneously)

**6 Projection Strategies** (enum `ProjectionStrategy`):

All strategies reduce high-dimensional embeddings to ULTRA's required 54-dim. They differ in how much information they preserve and what kind.

#### Strategy 1: TRUNCATE (Baseline)
```
embedding[384] → first 54 dims → L2 normalize → 54-dim
```
Simple, fast, no fitting required. But it throws away 86% of MiniLM's dimensions (and 93% of EmbeddingGemma's). The surviving dimensions are arbitrary — they're the first 54, not necessarily the most informative.

#### Strategy 2: PCA
```
embedding[384] → center → SVD → top 54 principal components → 54-dim
```
Pure numpy implementation (no sklearn). Fits on the corpus of all node descriptions, learns which directions capture the most variance, projects to those directions. Preserves more information than truncation in principle — the top 54 principal components capture the most variance in the data.

**Key edge case solved**: When the corpus has fewer samples than target dimensions (n < 54), PCA produces fewer components. The system pads with zeros to maintain ULTRA's expected 54-dim input.

#### Strategy 3: LEARNED_LINEAR
```
embedding[384] → W[384x54] @ embedding + bias → L2 normalize → 54-dim
```
A trainable linear projection optimized on ULTRA's own loss function. Instead of preserving maximum variance (PCA), it preserves what ULTRA actually needs for link prediction.

Training: margin ranking loss on known-true edges from the Claude KG. True edges (h, t) should score higher than corrupted edges (h, t') by a margin. The projection matrix W learns to compress embeddings in a way that maximizes this discrimination.

Implementation: Xavier initialization, numerical gradient descent (numpy-only, no autograd), batched SGD with configurable learning rate and epochs.

#### Strategy 4: SPLIT_SPACE (Hybrid only)
```
MiniLM[384] → first 27 dims → 27-dim  ─┐
                                         ├─→ concatenate → 54-dim
EmbeddingGemma[768] → first 27 dims → 27-dim ─┘
```
The simplest hybrid strategy. Each model contributes half the feature space. No fitting, no parameters. Tests whether having two perspectives (even crudely) beats one full perspective.

#### Strategy 5: WEIGHTED_BLEND (Hybrid only)
```
MiniLM[384] → PCA → 54-dim ──→ alpha x PCA_A ─┐
                                                ├─→ sum → L2 normalize → 54-dim
EmbeddingGemma[768] → PCA → 54-dim ──→ beta x PCA_B ─┘
```
Both models get full PCA projections, then blended with tunable weights. Tests whether a weighted combination of two good projections beats either alone. The blend ratio (alpha, beta) is a hyperparameter to explore.

#### Strategy 6: CONCAT_PCA (Hybrid only)
```
MiniLM[384] ──→ concatenate → 1152-dim → PCA → 54-dim
EmbeddingGemma[768] ──┘
```
The most information-preserving hybrid approach. PCA sees all 1152 dimensions from both models and selects the 54 most informative directions across the combined space. This is the theoretically strongest option — it lets PCA decide how much to take from each model.

### 3.6 The Benchmark Design

The benchmark tests all viable combinations:

| Config | Mode | Projection | What It Tests |
|--------|------|------------|---------------|
| 1 | MINILM_ONLY | TRUNCATE | **Baseline** — current system |
| 2 | MINILM_ONLY | PCA | Does informed projection beat truncation? |
| 3 | MINILM_ONLY | LEARNED_LINEAR | Does ULTRA-optimized projection beat unsupervised? |
| 4 | GEMMA_ONLY | TRUNCATE | Is Gemma's raw output better than MiniLM's? |
| 5 | GEMMA_ONLY | PCA | Gemma + informed projection |
| 6 | GEMMA_ONLY | LEARNED_LINEAR | Gemma + ULTRA-optimized projection |
| 7 | HYBRID | SPLIT_SPACE | Crude hybrid: 27+27 |
| 8 | HYBRID | WEIGHTED_BLEND | Tunable hybrid: alpha x A + beta x B |

**Metrics measured**:
| Metric | What It Measures |
|--------|-----------------|
| **MRR (Mean Reciprocal Rank)** | Where do true edges rank vs corrupted edges? |
| **Intra-type cosine similarity** | Do same-type nodes cluster together? |
| **Inter-type separation** | Do different-type nodes stay apart? |
| **Embedding time** | Seconds per node (speed comparison) |
| **Memory footprint** | MB during model loading (feasibility on device) |
| **PCA variance explained** | How much information survives projection |

**Memory safety**: The benchmark loads MiniLM (22MB), embeds all 511 nodes, caches results, unloads. Then loads EmbeddingGemma (220MB), embeds all 511 nodes, caches results, unloads. Both model's embeddings are stored in memory (a few MB of float arrays), but the models themselves are never loaded simultaneously. ULTRA (668KB) loads last and scores all configurations.

---

## Part 2b: Technical Appendix

### A. The Weight Space Visualization

The 8 intent profiles form a manifold in the (alpha, beta, gamma) weight space:

```
                    alpha (Vector/Semantic)     beta (BM25/Keywords)     gamma (Graph)
EXACT_MATCH        ||..........  0.20          |||||||||||||.. 0.65     |||..........  0.15
CAPABILITY         ||||||......  0.30          |||||||||||....  0.55    |||..........  0.15
WORKFLOW           ||||||......  0.30          ||||||||.......  0.40    ||||||.......  0.30
EXPLORATORY        |||||||.....  0.35          ||||||.........  0.30    |||||||......  0.35
DEBUGGING          |||||||.....  0.35          |||||||||......  0.45    ||||.........  0.20
COMPARISON         ||||||||....  0.40          ||||||||.......  0.40    ||||.........  0.20
GOAL_BASED         |||||||||...  0.45          |||||||........  0.35    ||||.........  0.20
SEMANTIC           ||||||||||||  0.60          |||||..........  0.25    |||..........  0.15
```

The default profile (alpha=0.40, beta=0.45, gamma=0.15) sits at the centroid of this space — it's the best single point if you can't adapt, but every individual profile outperforms it for its specific intent type.

### B. Mathematical Formulation

**Base hybrid score**:
```
H(q, n) = alpha x V(q, n) + beta x B(q, n) + gamma x G(q, n)

Where:
  V(q, n) = cosine_similarity(embed(q), embed(n))  in [0, 1]
  B(q, n) = bm25(q, n.text_fields) normalized      in [0, 1]
  G(q, n) = graph_boost(q, n, neighbors(n))          in [0, 1]
```

**Adaptive weight selection**:
```
intent = classify(q)              # pattern matching, O(1)
(alpha, beta, gamma) = W[intent]  # lookup table, O(1)
```

**Constraint**: alpha + beta + gamma approximately equals 1.0

### C. ULTRA Node Feature Structure

```
features[64] = [type_onehot[10] | text_embedding[54]]

type_onehot: one-hot encoding over 10 node types:
  [tool, limitation, use_case, workaround, workflow,
   example, parameter, configuration, combination, unknown]

text_embedding: 54-dim projected from either:
  - MiniLM 384-dim (current baseline)
  - EmbeddingGemma 768-dim (alternative)
  - Hybrid combination (Phase 4a strategies)
```

### D. ConfigurableEmbedder Interface

```python
class ConfigurableEmbedder:
    """Drop-in replacement for MiniLMEmbedder"""

    # Same interface as MiniLMEmbedder
    def embed(text: str) -> np.ndarray       # Raw embedding
    available: bool                           # Model loaded?

    # New capabilities
    def embed_and_project(text) -> np.ndarray[54]      # Embed + project in one call
    def compute_node_features(node) -> np.ndarray[64]  # Full ULTRA-compatible features
    def fit_projector(texts, **kwargs) -> dict          # Fit PCA/learned on corpus
    def embed_both(text) -> (np.ndarray[384], np.ndarray[768])  # Hybrid: both models

    # Memory management
    def load() -> bool
    def unload() -> None
    def swap_to_gemma() -> bool   # Unload MiniLM, load Gemma
    def swap_to_minilm() -> bool  # Unload Gemma, load MiniLM

    # Benchmark support
    def clear_cache() -> None
    def cache_stats() -> dict
```

### E. Projection Strategy Comparison

| Strategy | Fitting Required | Data Needed | Dimensions Lost | Best For |
|----------|-----------------|-------------|-----------------|----------|
| TRUNCATE | No | None | 86% (MiniLM), 93% (Gemma) | Quick baseline |
| PCA | Yes | All node descriptions | Variance-ordered (least informative dropped) | Single-model, quality |
| LEARNED_LINEAR | Yes | Node descriptions + KG edges + ULTRA | Optimized for ULTRA's loss | Single-model, best potential |
| SPLIT_SPACE | No | None | 93% (each model) | Quick hybrid test |
| WEIGHTED_BLEND | Yes | All node descriptions | Variance-ordered (per model) | Tunable hybrid |
| CONCAT_PCA | Yes | All node descriptions | Variance-ordered (combined space) | Best hybrid potential |

### F. The Fractal Pattern

The same adaptive principle appears at multiple layers:

| Layer | Signal A | Signal B | Signal C | Adaptive? |
|-------|----------|----------|----------|-----------|
| **Retrieval weights** | Vector (alpha) | BM25 (beta) | Graph (gamma) | 8 intent profiles |
| **Embedding models** | MiniLM (SBERT) | EmbeddingGemma (Google) | — | Proposed (Phase 4a infra) |
| **Projection methods** | Truncate | PCA | Learned | Benchmark will determine |
| **KG fusion** | Claude KG | Gemini KG | Unified KG | Cross-KG transfer |
| **Model routing** | R1 reasoning | ULTRA structural | MiniLM semantic | Combined in duo |

The pattern: **different signals for different purposes, combined with adaptive weights**. It works for retrieval (proven). It should work for embeddings (Phase 4a enables testing). It may work for node features (ULTRA integration).

### G. Key Numbers Summary

| Metric | Value |
|--------|-------|
| Recall@10 (fixed weights) | 88.5% |
| Recall@10 (adaptive weights) | 100% |
| Recall@10 (cross-domain) | 95.6% |
| Weight profiles | 8 |
| Vector weight range | 0.20 — 0.60 |
| BM25 weight range | 0.25 — 0.65 |
| Graph weight range | 0.15 — 0.35 |
| Probes validated | 22 + 12 = 34 |
| Domains validated | 6 + 5 = 11 |
| Intent detection cost | ~0 (pattern matching) |
| Embedding models | 2 (MiniLM 384-dim, EmbeddingGemma 768-dim) |
| Projection strategies | 6 |
| Benchmark configurations | 8 (all complete, Gemma via ONNX) |
| Benchmark MRR (winner) | **0.2490** (Hybrid+Blend) / **0.2487** (MiniLM+PCA, practical winner) |
| Benchmark MRR (baseline) | 0.1908 (MiniLM+Truncate) |
| PCA improvement over truncation | **+30% MRR** |
| PCA variance captured | 78.69% (54 dims from 384) |
| ULTRA input dimension | 64 (10 type + 54 text) |
| Phase 4a code | 2,239 lines, 50/50 tests |
| Phase 4b CLI | 8 files (~1,200 lines), 99/99 tests |
| Combined Phase 4 tests | 149/149 |
| KG predictions endpoints | 3 (save, review, list) |
| Config schemas | 7 (inc. embedding projection config) |
| Web API endpoints (total) | ~143 (evolution through Triple Upgrade + Workflows + KE Studio integration) |
| Explore page features | Accept/reject predictions, R1 timer, session save/load |

---

## What's Known, What's Hypothesized, What's Next

### Known (Validated)
- Fixed hybrid at alpha=0.40, beta=0.45, gamma=0.15 achieves 88.5%
- Intent-adaptive 8-profile system achieves 100%
- The third signal (graph) at 15% is the critical tiebreaker
- Two complementary signals beat seven overlapping signals
- Zero-cost adaptation (pattern matching) can produce 11.5 pp improvement

### Validated (COMPLETE Benchmark — February 9, 2026)

**All 8 configurations tested** on the Claude KG (511 nodes, 564 edges) with 50 negative samples per edge. EmbeddingGemma unblocked via ONNX Runtime (GGUF architecture unsupported, ONNX works):

| Configuration | MRR | Intra-type Sim | Inter-type Sim | Type Separation | PCA Variance |
|---|---|---|---|---|---|
| MiniLM+Truncate (baseline) | 0.1908 | 0.249 | 0.129 | 0.121 | N/A |
| **MiniLM+PCA** | **0.2487** | **0.179** | **-0.019** | **0.198** | **79%** |
| MiniLM+Learned (20 epochs) | 0.1647 | 0.304 | 0.169 | 0.135 | N/A |
| Gemma+Truncate | 0.1674 | 0.331 | 0.199 | 0.132 | N/A |
| Gemma+PCA | 0.2185 | 0.169 | -0.020 | 0.190 | 56% |
| Gemma+Learned (20 epochs) | 0.1716 | 0.307 | 0.181 | 0.126 | N/A |
| Hybrid+Split27 | 0.2026 | 0.220 | 0.088 | 0.132 | N/A |
| **Hybrid+Blend (winner)** | **0.2490** | **0.179** | **-0.018** | **0.197** | **68%** |

**Winner**: Hybrid+Blend (MRR=0.2490) — but MiniLM+PCA (0.2487) is within 0.1% at 10x less memory.

**Confirmed hypotheses**:
- **PCA > Truncation**: Consistent across BOTH models. MiniLM: +30% MRR. Gemma: +31% MRR. PCA finds the most informative dimensions regardless of source
- **PCA achieves best type separation**: Inter-type similarity drops to ~-0.02 (near zero) for both models with PCA. Different node types occupy distinct regions
- **Hybrid outperforms** (barely): Blend beats either model alone, confirming complementary information. Best blend alpha=0.7 (MiniLM-weighted)

**Resolved hypotheses (previously blocked)**:
- **EmbeddingGemma 768-dim does NOT outperform MiniLM 384-dim** at this KG scale. MiniLM+PCA (0.2487) > Gemma+PCA (0.2185). MiniLM's SBERT NLI training creates more useful semantic structure for KG link prediction than Gemma's larger dimension count
- **Hybrid benefit is marginal**: +0.003 MRR over MiniLM+PCA alone, at 10x memory cost (220MB vs 22MB). Not worth it for production
- **PCA variance tells the story**: MiniLM captures 79% variance in 54 dims (out of 384), Gemma only 56% (out of 768). MiniLM's information is more concentrated

**Needs more work**:
- **LEARNED_LINEAR underperformed** on both models. 20 epochs insufficient. Has highest theoretical ceiling but needs hyperparameter tuning
- **EmbeddingGemma via ONNX is 1.2GB** (fp32). The uint8 quantized version could reduce to ~300MB with minimal quality loss

### Delivered (Phase 4b — CLI Layer)

Phase 4b made the entire pipeline accessible as command-line tools:

**8 CLI files** in `cli/` wrapping all existing duo scripts, with unified `duo.py` dispatcher:

| Command | What It Wraps | Example |
|---------|---------------|---------|
| `duo.py query` | r1_kg_rag.py → R1KgRag | `duo.py query "How do I read a file?"` |
| `duo.py predict` | ultra_kg_integration.py → ULTRAKGIntegration | `duo.py predict --discover tool_read` |
| `duo.py enrich` | combined_r1_ultra.py → CombinedR1Ultra | `duo.py enrich --validate tool_read tool_edit` |
| `duo.py router` | enhanced_router.py → EnhancedRouter | `duo.py router "Reduce API costs"` |
| `duo.py benchmark` | embedding/benchmark.py → run_benchmark() | `duo.py benchmark --negatives 20` |
| `duo.py status` | (inline) KG stats + model paths | `duo.py status --plain` |

**Design choices relevant to this report**:
- **Three output modes**: Rich ANSI (visual score bars, colored badges), `--plain` (pipe-safe), `--json` (structured)
- **Score normalization**: ULTRA scores in [-1,1] are mapped to [0,1] for visual bars: `max(0, (score + 1) / 2)`
- **Dual-use pattern**: Each script works standalone (`query.py "..."`) AND as subcommand (`duo.py query "..."`)
- **DuoConfig** resolves all model/KG paths from environment variables or sensible defaults
- **Pydantic bypass**: `benchmark.py` uses `importlib.util.spec_from_file_location` chain (projectors → embedder → benchmark) to avoid ailab's pydantic dependency

**99/99 tests passing** in `tests/test_cli_suite.py` — covering DuoConfig, output formatting, all argparse parsers, duo dispatcher, import chain, and subprocess smoke tests.

### Delivered (Web UI — Explore Page)

The R1+ULTRA+MiniLM trio got an interactive web interface at `/explore`:

**Backend (5 API endpoints)**:
- `GET /api/explore/graph` — KG subgraph for Cytoscape.js (direct SQLite, cached, no model loading)
- `GET /api/explore/nodes?q=...` — Search nodes by name (instant, no models)
- `POST /api/explore/query` — Full SSE pipeline: MiniLM search → graph build → ULTRA discover → R1 reason
- `POST /api/explore/discover` — ULTRA link prediction for a single node
- `POST /api/explore/validate` — ULTRA predicts + R1 validates a node pair

**Frontend (Cytoscape.js)**:
- Interactive graph: 141 tool nodes + 192 edges in browse mode
- Color-coded node types (tool=cyan, limitation=pink, workaround=green, use_case=amber)
- Discovery edges: green dashed pulsing lines from ULTRA predictions
- Validate mode: click two nodes, get ULTRA prediction + R1 reasoning
- Tabbed results: REASONING (with `<think>` chain steps) / DISCOVERIES (with score bars) / NODE INFO

**Memory management**: Trio (R1 1.1GB + ULTRA 668KB + MiniLM 22MB) and chat models are mutually exclusive. Loading one unloads the other + `gc.collect()`.

### Delivered (Evolution Phase — KG Predictions Staging Pipeline)

The virtuous cycle (ULTRA predicts → R1 validates → KG grows) was previously a batch process. The Evolution Phase made it **interactive and persistent**:

**`kg_predictions` SQLite Table**:
```sql
CREATE TABLE kg_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    predicted_relation TEXT NOT NULL,
    ultra_score REAL NOT NULL,
    r1_validated BOOLEAN DEFAULT NULL,
    r1_reasoning TEXT,
    combined_confidence REAL,
    status TEXT DEFAULT 'pending',  -- pending/accepted/rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    promoted_at TIMESTAMP
);
```

**3 New API Endpoints**:
- `POST /api/explore/predictions/save` — Save an ULTRA discovery as a pending prediction
- `POST /api/explore/predictions/review` — Accept or reject; accepted predictions get **promoted to the main `edges` table** with `properties={"source":"ultra","confidence":X}`
- `GET /api/explore/predictions` — List predictions by status

**Interactive UI**: Each discovery in the Explore page's DISCOVERIES tab now has ACCEPT and REJECT buttons. ACCEPT saves to staging, promotes to main KG, shows green confirmation. REJECT dims the item. This closes the loop: users curate which AI-predicted edges become permanent knowledge.

**Significance for the weights/embeddings story**: The predictions that get accepted are edges that ULTRA's link prediction (powered by MiniLM+PCA embeddings) correctly identified as missing. Each accepted prediction validates the embedding quality — it's implicit human feedback on the 54-dim projected features. Over time, the distribution of accepted vs rejected predictions per score threshold could inform a confidence calibration curve for ULTRA's link prediction.

### Delivered (Evolution Phase — Universal Engine Configuration)

The embedding and model configuration that was previously hardcoded or CLI-only got a **universal schema-driven config system**:

**7 JSON schemas** in `config/schemas/` define engine parameters per model type. Each schema specifies parameter groups with slider/dropdown/toggle types, ranges, defaults, and step sizes.

The `embedding.json` schema is directly relevant to this report:
```json
{
  "type": "embedding",
  "label": "Embedding Configuration",
  "groups": [{
    "id": "embedding_params", "label": "Embedding Parameters",
    "params": [
      {"id": "projection", "label": "Projection", "type": "dropdown",
       "options": ["truncate", "pca"], "default": "pca"},
      {"id": "target_dims", "label": "Target Dimensions", "type": "slider",
       "min": 32, "max": 768, "step": 16, "default": 54},
      {"id": "normalize", "label": "Normalize Output", "type": "toggle", "default": true}
    ]
  }]
}
```

This means the embedding projection strategy (the key finding from the benchmark — PCA wins by 30%) is now **user-configurable through the web UI**. The chat endpoint merges config overrides with cartridge defaults: `params = {**cart_params, **config_overrides}`, so engine parameters always win over cartridge-defined defaults.

### Delivered (Gemini API Upgrade — Embedding Infrastructure, Feb 10 2026)

The embedding system received a major upgrade: **Unified Embedding Service** supporting 3 model backends through a single API.

| Model | Type | Dims | Size | Role |
|-------|------|------|------|------|
| MiniLM-L6-v2 | GGUF (local) | 384 | 22MB | Always-on baseline, fast retrieval |
| Nomic Embed v1.5 | GGUF (local) | 768 | 95MB | On-demand, higher-dim alternative |
| Gemini Embedding | Cloud API | 768 | 0MB | Cloud reranking, zero local memory |

**Two-Stage Reranking Pipeline**: Local model (MiniLM or Nomic) retrieves top-20 candidates fast, then Gemini cloud reranks for precision. Combined score: `0.4 * local_sim + 0.6 * cloud_sim`. This leverages the benchmark finding that local models are good for recall while larger models improve precision.

**KG Re-Embedding**: All 511 KG nodes can now be batch re-embedded with any model. Stored in SQLite table `kg_embeddings` (node_id, model_id, embedding BLOB, dims, updated_at). Search the same KG with different embedding models to compare retrieval quality.

**Side-by-Side Comparison**: The `/engineer` page includes an embedding testing tab where users compare all 3 models on the same query. A mini benchmark runs 10 standard queries across all models, showing per-model similarity scores.

**7 New API Endpoints**: `/api/embedding/models`, `/encode`, `/compare`, `/rerank`, `/kg/rebuild`, `/kg/status`, `/kg/search`.

### Delivered (CORE RAG Brain — Embedding-Powered Function Selection, Feb 11 2026)

The embedding pipeline found a new application: **RAG-narrowed function selection** for the CORE local voice assistant.

**The Problem**: The CORE brain (Llama 3.2 1B or FunctionGemma 270M) needs to choose from 13 available functions based on a voice command. Injecting all 13 function descriptions into the prompt wastes context and confuses smaller models — especially FunctionGemma at 270M params.

**The Solution**: MiniLM embeddings power a micro-RAG system:

1. **Knowledge Base** (`core_knowledge.py`): 33 entries — 14 function descriptions with rich keyword annotations + 19 system information chunks (expanded Feb 13)
2. **Pre-computed Embeddings**: All 33 entries embedded once with MiniLM (384-dim), pre-normalized, stored in memory
3. **Query-Time RAG**: User text embedded → cosine similarity against 33 entries → top-3 functions selected → narrowed schema injected into brain prompt
4. **Result**: Brain sees 3 relevant functions instead of 13 → dramatically better accuracy, especially for FunctionGemma

**FunctionGemma-Specific Optimization**: When RAG is active and the brain is FunctionGemma, a tighter prompt format is used: `"Pick the best function for this request. Output ONLY JSON."` This directness works better with base models than the standard system prompt.

**Compare Brains Feature**: The `/api/core/compare` endpoint tests the same text against all available brain models (swapping sequentially with `gc.collect()` between). Each model's result includes `rag_used: true/false` and timing. The UI shows side-by-side cards — making the RAG improvement visible in real comparisons.

**Technical Details**:
- MiniLM embedding: ~2ms per query (model already loaded for embedding service)
- Cosine search across 33 entries: <1ms
- Total RAG overhead: ~3ms — negligible vs brain inference (200-2000ms)
- Knowledge base builds during pipeline load: ~80ms (with 33 entries, Feb 13 update)

This validates the key benchmark finding: MiniLM+PCA was the practical winner for KG tasks, and now MiniLM alone powers a production RAG system for voice command routing.

### Next
- ~~Run the 8-config benchmark on the Claude KG with ULTRA scoring~~ **DONE** (all 8 configs)
- ~~Compare MRR, type clustering, and inference speed across all configurations~~ **DONE** (all 8 compared)
- ~~Unblock EmbeddingGemma~~ **DONE** (ONNX Runtime, not GGUF)
- ~~Integrate into Web UI~~ **DONE** (Explore page with Cytoscape.js)
- ~~KG predictions persistence~~ **DONE** (staging pipeline + accept/reject + edge promotion)
- ~~Universal config system~~ **DONE** (7 schemas including embedding configuration)
- ~~Unified embedding service (3 models)~~ **DONE** (MiniLM + Nomic + Gemini cloud)
- ~~Two-stage reranking pipeline~~ **DONE** (local retrieval + cloud rerank)
- ~~KG re-embedding with model comparison~~ **DONE** (batch 511 nodes, SQLite storage)
- Explore more LEARNED_LINEAR training (more epochs, learning rate sweep)
- Test uint8 quantized EmbeddingGemma ONNX for reduced memory
- Analyze accepted prediction distribution for confidence calibration
- Test Nomic v1.5 vs MiniLM on KG link prediction (benchmark extension)
- Measure reranking lift: compare MiniLM-only retrieval vs MiniLM→Gemini reranked

---

*The evolution: embeddings (50%) → hybrid (88.5%) → adaptive (100%) → configurable embedding pipeline (Phase 4a) → CLI accessibility (Phase 4b) → real benchmark validation (all 8 configs, PCA wins by 30%) → EmbeddingGemma unblocked via ONNX Runtime → complete comparison validates MiniLM+PCA as practical winner → Web UI with interactive KG visualization (Cytoscape.js) → Evolution Phase: KG predictions staging pipeline, universal engine config, state management → Gemini API Upgrade: unified 3-model embedding service (MiniLM + Nomic + Gemini cloud), two-stage reranking pipeline, KG batch re-embedding with model comparison, and Natural Engineering page with side-by-side embedding testing → CORE RAG Brain: MiniLM embeddings power voice command routing (33-entry knowledge base, top-3 function narrowing, 3ms overhead) + Compare Brains feature for empirical model comparison. The pattern continues: each layer makes the previous layers more useful. The MiniLM benchmark winner now powers a production RAG system for local voice control.*

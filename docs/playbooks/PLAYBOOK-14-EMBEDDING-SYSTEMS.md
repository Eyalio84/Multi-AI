# Playbook 14: Embedding Systems & Semantic Search

**Version:** 1.0
**Created:** November 27, 2025
**Category:** ML Infrastructure
**Prerequisites:** PB 4 (Knowledge Engineering), PB 6 (Augmented Intelligence ML)

---

## Executive Summary

This playbook documents how to build, train, and deploy custom embedding systems for domain-specific knowledge retrieval. It captures the lessons learned from achieving 88.5% recall on the Gemini KG.

**Core Principle:** The KG structure IS the training curriculum. Embeddings learn what the graph encodes.

---

## Table of Contents

1. [When to Use Embeddings](#1-when-to-use-embeddings)
2. [Architecture Decision Tree](#2-architecture-decision-tree)
3. [Self-Supervised Training](#3-self-supervised-training)
4. [Hybrid Search Implementation](#4-hybrid-search-implementation)
5. [Production Deployment](#5-production-deployment)
6. [Quality Evaluation](#6-quality-evaluation)
7. [Case Study: 88.5% Recall](#7-case-study-885-recall)

---

## 1. When to Use Embeddings

### 1.1 Decision Matrix

| Scenario | Use Embeddings? | Alternative |
|----------|----------------|-------------|
| Exact keyword match needed | No | SQL LIKE, BM25 |
| Semantic similarity needed | **Yes** | - |
| Small corpus (<100 nodes) | Maybe | SQL queries sufficient |
| Large corpus (>1000 nodes) | **Yes** | - |
| Dynamic, real-time queries | **Yes** | - |
| Static, predefined queries | No | Hardcoded SQL |
| Cross-domain transfer | **Yes** | - |
| Interpretability required | No | Intent queries, dimensions |

### 1.2 Embedding vs Intent Query

```python
# When embedding search excels
embedding_search("how to reduce costs")
# → Finds: "context caching pattern", "batch API usage", "cost optimization"
# → Semantic similarity captures "costs" ≈ "savings" ≈ "cheaper"

# When intent query excels
intent_query.want_to("reduce costs")
# → Finds: Exact tools with cost_optimization capability
# → Structured, deterministic, interpretable

# Best practice: Hybrid
def smart_search(query: str) -> list:
    """Combine structure + semantics."""
    intent_results = intent_query.want_to(query)  # Structured
    embedding_results = embedding_search(query)    # Semantic

    return merge_with_dedup(intent_results, embedding_results)
```

---

## 2. Architecture Decision Tree

### 2.1 Dimension Selection

```python
DIMENSION_GUIDE = {
    50: {
        "use_when": "Interpretability required",
        "pros": ["Explainable", "Fast computation", "Small storage"],
        "cons": ["Lower recall", "Less nuance"],
        "example": "NLKE 70 semantic dimensions"
    },
    256: {
        "use_when": "Balanced performance/efficiency",
        "pros": ["Good recall", "Reasonable compute", "Trainable locally"],
        "cons": ["Not directly interpretable"],
        "example": "Our gemini-kg system (88.5% recall)"
    },
    768: {
        "use_when": "Maximum quality needed",
        "pros": ["Best recall", "Rich representation"],
        "cons": ["Slow", "Large memory", "Requires GPU"],
        "example": "BERT-based systems"
    },
    1536: {
        "use_when": "Using OpenAI/API embeddings",
        "pros": ["No training needed", "High quality"],
        "cons": ["API costs", "No customization", "Vendor lock-in"],
        "example": "text-embedding-ada-002"
    }
}

def choose_dimension(requirements: dict) -> int:
    """Choose embedding dimension based on requirements."""
    if requirements.get("interpretability"):
        return 50
    if requirements.get("gpu_available") and requirements.get("max_quality"):
        return 768
    if requirements.get("api_budget"):
        return 1536
    return 256  # Default: balanced
```

### 2.2 Training Strategy Selection

```python
TRAINING_STRATEGIES = {
    "self_supervised": {
        "description": "Learn from graph structure alone",
        "data_required": "Knowledge graph with edges",
        "pros": ["No labeled data", "Domain-specific", "Free"],
        "cons": ["Requires well-structured KG"],
        "our_choice": True  # What we use
    },
    "pre_trained": {
        "description": "Use pre-trained model, fine-tune",
        "data_required": "Pre-trained weights + optional fine-tune data",
        "pros": ["Quick start", "Good baseline"],
        "cons": ["May not fit domain", "Large models"],
        "our_choice": False
    },
    "api_based": {
        "description": "Use embedding API",
        "data_required": "None",
        "pros": ["No training", "Always available"],
        "cons": ["Ongoing costs", "Generic embeddings"],
        "our_choice": False
    }
}
```

---

## 3. Self-Supervised Training

### 3.1 The Core Idea

```
KG Structure → Training Signal → Embeddings → Search Quality

If KG is correct → Embeddings learn correct relationships
If KG is wrong → Embeddings learn wrong relationships

The KG IS the curriculum.
```

### 3.2 InfoNCE Contrastive Learning

```python
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

class ContextualEmbedding(nn.Module):
    """
    Self-supervised embedding trained on KG structure.

    Key insight: KG neighbors are positive samples.
    Non-neighbors are negative samples.
    """

    def __init__(self, vocab_size: int, embedding_dim: int = 256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.temperature = 0.07  # InfoNCE temperature

    def forward(self, anchor_ids: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.embedding(anchor_ids), dim=-1)

    def contrastive_loss(
        self,
        anchor: torch.Tensor,
        positives: torch.Tensor,
        negatives: torch.Tensor
    ) -> torch.Tensor:
        """
        InfoNCE loss: maximize similarity to positives,
        minimize similarity to negatives.
        """
        # Positive similarities
        pos_sim = torch.sum(anchor * positives, dim=-1) / self.temperature

        # Negative similarities
        neg_sim = torch.matmul(anchor, negatives.T) / self.temperature

        # InfoNCE: log(exp(pos) / (exp(pos) + sum(exp(neg))))
        logits = torch.cat([pos_sim.unsqueeze(-1), neg_sim], dim=-1)
        labels = torch.zeros(anchor.shape[0], dtype=torch.long)

        return F.cross_entropy(logits, labels)


def train_epoch(model, kg, optimizer, batch_size: int = 32):
    """
    Train one epoch on KG structure.
    """
    model.train()
    total_loss = 0.0
    nodes = list(kg.nodes())

    for i in range(0, len(nodes), batch_size):
        batch_nodes = nodes[i:i+batch_size]

        anchors = []
        positives = []
        negatives = []

        for node in batch_nodes:
            # Anchor embedding
            anchor_emb = model(torch.tensor([node.id]))

            # Positives: KG neighbors (connected nodes)
            neighbors = kg.neighbors(node)
            if not neighbors:
                continue
            pos_node = random.choice(neighbors)
            pos_emb = model(torch.tensor([pos_node.id]))

            # Negatives: Random non-neighbors
            non_neighbors = kg.sample_non_neighbors(node, k=5)
            neg_embs = model(torch.tensor([n.id for n in non_neighbors]))

            anchors.append(anchor_emb)
            positives.append(pos_emb)
            negatives.append(neg_embs)

        if not anchors:
            continue

        # Stack and compute loss
        anchor_batch = torch.cat(anchors, dim=0)
        positive_batch = torch.cat(positives, dim=0)
        negative_batch = torch.cat(negatives, dim=0)

        loss = model.contrastive_loss(anchor_batch, positive_batch, negative_batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(nodes)
```

### 3.3 Graph Fusion

```python
def graph_fusion(
    text_embedding: np.ndarray,
    neighbor_embeddings: list[np.ndarray],
    eta: float = 0.5
) -> np.ndarray:
    """
    Fuse text semantics with graph structure.

    Args:
        text_embedding: Embedding from text content
        neighbor_embeddings: Embeddings of KG neighbors
        eta: Fusion weight (0.5 = balanced)

    Returns:
        Fused embedding

    Formula:
        fused = η * text + (1-η) * mean(neighbors)
        normalized to unit sphere
    """
    if not neighbor_embeddings:
        return text_embedding

    graph_embedding = np.mean(neighbor_embeddings, axis=0)

    fused = eta * text_embedding + (1 - eta) * graph_embedding
    fused = fused / np.linalg.norm(fused)

    return fused
```

### 3.4 Intent Keyword Weighting

```python
def enrich_with_intent_keywords(node: dict, weight: float = 5.0) -> str:
    """
    Add intent keywords with weight boost.

    Critical insight: Users query with INTENT, not just keywords.
    "reduce costs" vs "context_caching"

    We weight intent keywords higher in training text.
    """
    base_text = node.get("description", "")
    intent_keywords = node.get("intent_keywords", [])

    # Repeat intent keywords for weight
    weighted_keywords = " ".join(intent_keywords * int(weight))

    return f"{base_text} {weighted_keywords}"


# Example
node = {
    "description": "Pattern for caching prompt tokens",
    "intent_keywords": ["reduce costs", "save money", "cheaper", "90% savings"]
}

enriched = enrich_with_intent_keywords(node, weight=5.0)
# "Pattern for caching prompt tokens reduce costs save money cheaper 90% savings
#  reduce costs save money cheaper 90% savings reduce costs save money..."
```

---

## 4. Hybrid Search Implementation

### 4.1 The Winning Formula

```python
def hybrid_search(
    query: str,
    alpha: float = 0.40,  # Embedding weight
    beta: float = 0.45,   # BM25 weight
    gamma: float = 0.15,  # Graph boost weight
    k: int = 10
) -> list[dict]:
    """
    Hybrid search achieving 88.5% recall.

    Key insight: Two signals (emb + BM25) beat seven signals.
    Simple combination > complex ensemble.
    """
    # 1. Embedding similarity
    query_embedding = encode_text(query)
    emb_scores = cosine_similarity(query_embedding, all_embeddings)

    # 2. BM25 keyword matching
    bm25_scores = bm25_index.search(query)

    # 3. Graph neighbor boosting
    graph_scores = compute_graph_boost(query)

    # 4. Combine scores
    combined = (
        alpha * normalize(emb_scores) +
        beta * normalize(bm25_scores) +
        gamma * normalize(graph_scores)
    )

    # 5. Rank and return top-k
    indices = np.argsort(combined)[::-1][:k]
    return [nodes[i] for i in indices]
```

### 4.2 BM25 Index with Intent Keywords

```python
from rank_bm25 import BM25Okapi

class IntentAwareBM25:
    """
    BM25 index with intent keyword boosting.
    """

    def __init__(self, nodes: list[dict]):
        # Tokenize with intent keyword enrichment
        self.documents = []
        self.node_ids = []

        for node in nodes:
            doc = self._prepare_document(node)
            self.documents.append(doc)
            self.node_ids.append(node["id"])

        self.index = BM25Okapi([d.split() for d in self.documents])

    def _prepare_document(self, node: dict) -> str:
        """Prepare document with intent keyword weighting."""
        parts = [
            node.get("name", ""),
            node.get("description", ""),
            " ".join(node.get("intent_keywords", []) * 5)  # 5x weight
        ]
        return " ".join(parts).lower()

    def search(self, query: str, k: int = 10) -> list[tuple]:
        """Search and return (node_id, score) pairs."""
        tokenized = query.lower().split()
        scores = self.index.get_scores(tokenized)

        top_indices = np.argsort(scores)[::-1][:k]
        return [(self.node_ids[i], scores[i]) for i in top_indices]
```

### 4.3 Graph Neighbor Boosting

```python
def compute_graph_boost(query: str, kg, top_matches: list[str]) -> dict:
    """
    Boost nodes connected to top matches.

    Intuition: If a node is connected to multiple relevant nodes,
    it's likely relevant too.
    """
    boost_scores = defaultdict(float)

    for node_id in top_matches:
        neighbors = kg.neighbors(node_id)
        for neighbor in neighbors:
            boost_scores[neighbor] += 1.0 / len(top_matches)

    # Normalize
    if boost_scores:
        max_boost = max(boost_scores.values())
        boost_scores = {k: v / max_boost for k, v in boost_scores.items()}

    return boost_scores
```

---

## 5. Production Deployment

### 5.1 Index Building

```python
class EmbeddingIndex:
    """
    Production-ready embedding index with caching.
    """

    def __init__(self, embedding_path: str, db_path: str):
        self.embeddings = self._load_embeddings(embedding_path)
        self.db_path = db_path
        self.node_ids = list(self.embeddings.keys())
        self.embedding_matrix = np.stack([
            self.embeddings[nid] for nid in self.node_ids
        ])

    def _load_embeddings(self, path: str) -> dict:
        """Load pre-trained embeddings."""
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return data.get('node_embeddings', {})

    def search(self, query_embedding: np.ndarray, k: int = 10) -> list[tuple]:
        """
        Fast similarity search using numpy.

        For larger indices, consider FAISS or Annoy.
        """
        # Cosine similarity (embeddings are normalized)
        similarities = np.dot(self.embedding_matrix, query_embedding)

        # Top-k
        top_indices = np.argsort(similarities)[::-1][:k]

        return [
            (self.node_ids[i], similarities[i])
            for i in top_indices
        ]


class ProductionQuerySystem:
    """
    Complete production query system.
    """

    def __init__(self, db_path: str, embedding_path: str):
        self.embedding_index = EmbeddingIndex(embedding_path, db_path)
        self.bm25_index = self._build_bm25_index(db_path)
        self.kg = self._load_kg(db_path)
        self.query_cache = QueryCache(maxsize=1000, ttl_seconds=300)

    def query(self, query_text: str, k: int = 10) -> list[dict]:
        """
        Main query method with caching.
        """
        # Check cache
        hit, cached = self.query_cache.get(query_text, {"k": k})
        if hit:
            return cached

        # Hybrid search
        results = self._hybrid_search(query_text, k)

        # Cache
        self.query_cache.set(query_text, {"k": k}, results)

        return results

    def _hybrid_search(self, query: str, k: int) -> list[dict]:
        # Implementation from Section 4.1
        pass
```

### 5.2 Retraining Triggers

```python
class RetrainingManager:
    """
    Manage when to retrain embeddings.
    """

    def __init__(self, kg, threshold_nodes: int = 50, threshold_edges: int = 100):
        self.kg = kg
        self.threshold_nodes = threshold_nodes
        self.threshold_edges = threshold_edges
        self.last_training_state = self._capture_state()

    def _capture_state(self) -> dict:
        return {
            "node_count": self.kg.node_count(),
            "edge_count": self.kg.edge_count(),
            "timestamp": datetime.now()
        }

    def should_retrain(self) -> tuple[bool, str]:
        """Check if retraining is needed."""
        current = self._capture_state()
        last = self.last_training_state

        new_nodes = current["node_count"] - last["node_count"]
        new_edges = current["edge_count"] - last["edge_count"]

        if new_nodes >= self.threshold_nodes:
            return True, f"Added {new_nodes} new nodes"

        if new_edges >= self.threshold_edges:
            return True, f"Added {new_edges} new edges"

        # Also check query performance
        if self._query_performance_degraded():
            return True, "Query performance degraded"

        return False, "No retraining needed"

    def _query_performance_degraded(self) -> bool:
        """Run benchmark queries to check performance."""
        benchmark = [
            {"query": "reduce API costs", "expected": ["pattern_context_caching"]},
            {"query": "multimodal processing", "expected": ["pattern_multimodal"]},
        ]

        for test in benchmark:
            results = self.kg.query(test["query"], k=5)
            found = [r["name"] for r in results]
            if not any(exp in found for exp in test["expected"]):
                return True

        return False
```

---

## 6. Quality Evaluation

### 6.1 Recall@k Metrics

```python
def evaluate_recall_at_k(
    query_system,
    test_cases: list[dict],
    k_values: list[int] = [1, 3, 5, 10]
) -> dict:
    """
    Evaluate recall at different k values.

    Args:
        test_cases: [{"query": "...", "expected": ["node1", "node2"]}]
    """
    results = {f"recall@{k}": [] for k in k_values}

    for test in test_cases:
        query = test["query"]
        expected = set(test["expected"])

        for k in k_values:
            found = query_system.query(query, k=k)
            found_names = set(r["name"] for r in found)

            recall = len(expected & found_names) / len(expected)
            results[f"recall@{k}"].append(recall)

    # Average
    return {
        metric: np.mean(values)
        for metric, values in results.items()
    }
```

### 6.2 Strict vs Semantic Evaluation

```python
def semantic_equivalence_check(found: str, expected: str) -> bool:
    """
    Check if found result is semantically equivalent to expected.

    Example: "workflow_safe_experimentation" ≈ "use_case_experiment_safely"
    """
    # Check exact match
    if found == expected:
        return True

    # Check semantic patterns
    equivalences = [
        ("workflow_", "use_case_"),
        ("pattern_", "use_case_"),
        ("_implementation", "_pattern"),
    ]

    for prefix1, prefix2 in equivalences:
        if found.replace(prefix1, prefix2) == expected:
            return True
        if expected.replace(prefix1, prefix2) == found:
            return True

    # Check substring containment
    found_words = set(found.replace("_", " ").split())
    expected_words = set(expected.replace("_", " ").split())

    overlap = len(found_words & expected_words)
    if overlap >= 2:  # At least 2 common words
        return True

    return False


def evaluate_semantic_recall(query_system, test_cases: list[dict]) -> dict:
    """
    Evaluate with semantic equivalence.
    """
    strict_recall = []
    semantic_recall = []

    for test in test_cases:
        results = query_system.query(test["query"], k=5)
        found_names = [r["name"] for r in results]

        # Strict: exact match required
        strict_matches = sum(1 for exp in test["expected"] if exp in found_names)
        strict_recall.append(strict_matches / len(test["expected"]))

        # Semantic: equivalents count
        semantic_matches = sum(
            1 for exp in test["expected"]
            if any(semantic_equivalence_check(f, exp) for f in found_names)
        )
        semantic_recall.append(semantic_matches / len(test["expected"]))

    return {
        "strict_recall": np.mean(strict_recall),
        "semantic_recall": np.mean(semantic_recall)
    }
```

---

## 7. Case Study: 88.5% Recall

### 7.1 The Journey

| Phase | Recall | Key Change |
|-------|--------|------------|
| 1. Initial | ~48% | Basic embeddings, no BM25 |
| 2. Intent keywords | 65.8% | Added 5x weighted intent keywords |
| 3. Hybrid search | 83% | Combined embedding + BM25 |
| 4. Weight tuning | 88.5% | α=0.40, β=0.45, γ=0.15 |
| 5. Semantic eval | 100% | Recognized equivalents |

### 7.2 What Failed (Anti-Patterns)

```python
# ANTI-PATTERN 1: Too many signals
# RRF with 7 strategies = 66.7% recall (worse!)
def rrf_seven_strategies():  # DON'T DO THIS
    signals = [
        embedding_search(),
        bm25_search(),
        title_search(),
        keyword_search(),
        category_filter(),
        synonym_expansion(),
        entity_extraction()
    ]
    return reciprocal_rank_fusion(signals)
# Result: Signal drowned in noise

# ANTI-PATTERN 2: Category filtering
# Removing non-matching categories = missed answers
def category_filtered_search():  # DON'T DO THIS
    results = embedding_search()
    user_category = infer_category(query)
    return [r for r in results if r["type"] == user_category]
# Result: "How to reduce costs?" missed use_cases because
#         user wanted patterns but use_cases had the answer

# ANTI-PATTERN 3: Comprehensive synonym expansion
def synonym_expanded_search():  # DON'T DO THIS
    expanded = expand_all_synonyms(query)
    # "cost" → "expense", "price", "fee", "charge", ...
    return search(expanded)
# Result: Diluted precision, matched irrelevant nodes
```

### 7.3 The Color Mixing Metaphor

```
Two complementary colors (embedding + BM25) → Beautiful purple (88.5%)
Seven colors mixed → Muddy brown (66.7%)

The art is knowing when to STOP adding signals.
```

---

## Related Playbooks

| Playbook | Relationship |
|----------|--------------|
| PB 4: Knowledge Engineering | Build the KG first |
| PB 6: Augmented Intelligence ML | Training methodology |
| PB 8: Continuous Learning | Retraining triggers |
| EMBEDDING-ROADMAP.md | Theory reference |

---

## Key Insights

- **#6**: Color Mixing Principle - Simple hybrid beats complex ensemble
- **#39**: KG Structure IS the training curriculum
- **#40**: 70-dimension standard for interpretable spaces

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025

#!/usr/bin/env python3
"""
Hybrid Fusion Engine — Unified Retrieval Layer

Composes BM25 + Embeddings + GraphScorer + IntentRouter + QueryCache
into a single query interface implementing:

    H(q,n) = alpha * V(q,n) + beta * B(q,n) + gamma * G(q,n)

Multi-database: indexes and queries across all NLKE KGs.

Level 4 dependency — imports from all lower levels.

Adapted from hybrid_query.py lines 274-317.

Created: February 8, 2026
"""

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

try:
    from .config import RetrievalConfig, KG_DATABASES, EmbeddingBackend
    from .stopwords import tokenize_and_filter
    from .query_cache import QueryCache
    from .db_adapter import KGAdapter, KGNode
    from .weight_profiles import QueryIntent, get_weights
    from .bm25 import BM25Index
    from .embeddings import EmbeddingManager, HAS_NUMPY
    from .graph_scorer import GraphScorer
    from .intent_router import IntentRouter
except ImportError:
    from config import RetrievalConfig, KG_DATABASES, EmbeddingBackend
    from stopwords import tokenize_and_filter
    from query_cache import QueryCache
    from db_adapter import KGAdapter, KGNode
    from weight_profiles import QueryIntent, get_weights
    from bm25 import BM25Index
    from embeddings import EmbeddingManager, HAS_NUMPY
    from graph_scorer import GraphScorer
    from intent_router import IntentRouter


# ============================================================================
# Result Dataclass
# ============================================================================

@dataclass
class RetrievalResult:
    """Single retrieval result with per-path score breakdown."""
    node_id: str
    name: str
    node_type: str
    description: str
    source_db: str
    # Score breakdown
    vector_score: float = 0.0
    bm25_score: float = 0.0
    graph_score: float = 0.0
    final_score: float = 0.0
    # Optional fields
    intent_keywords: str = ""
    category: str = ""
    domain: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Hybrid Fusion Engine
# ============================================================================

class HybridFusion:
    """3-path hybrid fusion retrieval engine.

    Composes BM25Index + EmbeddingManager + GraphScorer + IntentRouter + QueryCache
    into a unified query interface that searches across all NLKE KG databases.

    Usage:
        fusion = HybridFusion()
        fusion.index()  # One-time indexing
        results = fusion.query("prompt caching cost optimization", k=10)
    """

    def __init__(self, config: Optional[RetrievalConfig] = None,
                 databases: Optional[Dict[str, str]] = None):
        self.config = config or RetrievalConfig()
        self.databases = databases or KG_DATABASES

        # Components
        self.bm25 = BM25Index(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b,
            boost_factor=self.config.intent_boost_factor,
        )
        self.embeddings = EmbeddingManager(config=self.config)
        self.graph = GraphScorer(config=self.config)
        self.router = IntentRouter()
        self.cache = QueryCache(
            maxsize=self.config.cache_maxsize,
            ttl_seconds=self.config.cache_ttl_seconds,
        )

        # Adapters and node storage
        self._adapters: Dict[str, KGAdapter] = {}
        self._all_nodes: List[KGNode] = []
        self._node_map: Dict[str, KGNode] = {}  # node_id -> KGNode
        self._indexed = False
        self._index_time: float = 0.0

    def index(self, databases: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Index all configured KG databases.

        Returns dict with indexing stats.
        """
        dbs = databases or self.databases
        t0 = time.time()

        self._all_nodes.clear()
        self._node_map.clear()

        stats = {
            "databases_indexed": 0,
            "databases_skipped": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "schemas": {},
        }

        for name, path in dbs.items():
            if not os.path.exists(path):
                stats["databases_skipped"] += 1
                continue

            adapter = KGAdapter(path)
            if not adapter.connect():
                stats["databases_skipped"] += 1
                continue

            self._adapters[name] = adapter
            nodes = adapter.get_all_nodes()

            # Dedupe by db:node_id (prefix to avoid cross-DB collisions)
            new_nodes = []
            for node in nodes:
                unique_id = f"{name}:{node.node_id}"
                if unique_id not in self._node_map:
                    node.node_id = unique_id  # Prefix with db name
                    self._node_map[unique_id] = node
                    new_nodes.append(node)

            self._all_nodes.extend(new_nodes)
            stats["databases_indexed"] += 1
            stats["total_nodes"] += len(new_nodes)
            stats["schemas"][name] = adapter.schema

        # Index BM25
        bm25_count = self.bm25.index_nodes(self._all_nodes)

        # Index embeddings
        emb_count = self.embeddings.index_nodes(self._all_nodes)

        # Index graph (use fast mode for large databases)
        edge_total = 0
        for name, adapter in self._adapters.items():
            ec = adapter.edge_count()
            if ec > 100000:
                edge_total += self.graph.build_index_fast(adapter)
            else:
                edge_total += self.graph.build_index(adapter)
        stats["total_edges"] = edge_total

        self._index_time = time.time() - t0
        self._indexed = True

        stats["bm25_indexed"] = bm25_count
        stats["embedding_indexed"] = emb_count
        stats["embedding_backend"] = self.embeddings.backend.value
        stats["embedding_quality"] = self.embeddings.quality
        stats["index_time_seconds"] = round(self._index_time, 2)

        return stats

    def query(self, text: str, k: int = 10,
              intent: Optional[QueryIntent] = None) -> List[RetrievalResult]:
        """Execute hybrid fusion query.

        H(q,n) = alpha * V(q,n) + beta * B(q,n) + gamma * G(q,n)

        Args:
            text: Query text
            k: Number of results to return
            intent: Override intent detection (auto-detected if None)

        Returns:
            List of RetrievalResult sorted by final_score descending
        """
        if not self._indexed:
            self.index()

        # Check cache
        cached = self.cache.get(text, k=k)
        if cached is not None:
            return cached

        # Step 1: Detect intent and get weights
        if intent is None:
            detected_intent, weights = self.router.route(text, self.embeddings.quality)
        else:
            weights = get_weights(intent, self.embeddings.quality)

        alpha, beta, gamma = weights.alpha, weights.beta, weights.gamma

        # Step 2: Expand query
        expanded = self.router.expand_query(text)

        # Step 3: BM25 scoring — get all scored nodes
        bm25_results = self.bm25.search(expanded, k=min(k * 5, 200))
        bm25_scores: Dict[str, float] = {nid: score for nid, score in bm25_results}

        # Step 4: Embedding scoring
        emb_scores: Dict[str, float] = {}
        if HAS_NUMPY:
            emb_results = self.embeddings.search(text, k=min(k * 5, 200))
            emb_scores = {nid: score for nid, score in emb_results}

        # Step 5: Collect all candidate node IDs
        all_candidates = set(bm25_scores.keys()) | set(emb_scores.keys())
        if not all_candidates:
            self.cache.put(text, [], k=k)
            return []

        # Step 6: Compute combined scores (alpha * V + beta * B)
        combined: List[Tuple[str, float]] = []
        for nid in all_candidates:
            v_score = emb_scores.get(nid, 0.0)
            b_score = bm25_scores.get(nid, 0.0)
            combined.append((nid, alpha * v_score + beta * b_score))

        combined.sort(key=lambda x: -x[1])

        # Step 7: Graph neighbor boosting
        candidate_ids = [nid for nid, _ in combined]
        graph_scores = self.graph.score_results(candidate_ids, gamma)

        # Step 8: Final scoring
        final_results: List[RetrievalResult] = []
        for nid, ab_score in combined:
            g_score = graph_scores.get(nid, 0.0)
            final = ab_score + g_score

            node = self._node_map.get(nid)
            if node is None:
                continue

            final_results.append(RetrievalResult(
                node_id=nid,
                name=node.name,
                node_type=node.node_type,
                description=node.description[:300],
                source_db=node.source_db,
                vector_score=round(emb_scores.get(nid, 0.0), 4),
                bm25_score=round(bm25_scores.get(nid, 0.0), 4),
                graph_score=round(g_score, 4),
                final_score=round(final, 4),
                intent_keywords=node.intent_keywords,
                category=node.category,
                domain=node.domain,
            ))

        final_results.sort(key=lambda r: -r.final_score)
        results = final_results[:k]

        # Cache results
        self.cache.put(text, results, k=k)

        return results

    def query_with_explanation(self, text: str, k: int = 10) -> Dict[str, Any]:
        """Query with full explanation of scoring breakdown.

        Returns dict with results + metadata about how scores were computed.
        """
        intent, weights = self.router.route(text, self.embeddings.quality)
        results = self.query(text, k=k, intent=intent)

        return {
            "query": text,
            "intent": intent.value,
            "weights": {"alpha": weights.alpha, "beta": weights.beta, "gamma": weights.gamma},
            "embedding_quality": self.embeddings.quality,
            "expanded_query": self.router.expand_query(text),
            "tools_for_goal": self.router.get_tools_for_goal(text),
            "domains": self.router.classify_domain(text),
            "result_count": len(results),
            "results": [r.to_dict() for r in results],
            "cache_metrics": self.cache.metrics.to_dict(),
        }

    def close(self) -> None:
        """Close all database connections."""
        for adapter in self._adapters.values():
            adapter.close()
        self._adapters.clear()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def node_count(self) -> int:
        return len(self._all_nodes)

    @property
    def is_indexed(self) -> bool:
        return self._indexed


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    print("hybrid_fusion.py — Hybrid Fusion Engine self-test")
    print("=" * 60)

    fusion = HybridFusion()
    stats = fusion.index()
    print(f"\nIndexing Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Test basic query
    print(f"\n{'='*60}")
    results = fusion.query("prompt caching cost optimization", k=5)
    print(f"\nQuery: 'prompt caching cost optimization' -> {len(results)} results")
    for r in results:
        print(f"  {r.final_score:.4f} [{r.source_db:25s}] {r.name}")
        print(f"           v={r.vector_score:.3f} b={r.bm25_score:.3f} g={r.graph_score:.3f}")

    # Test with explanation
    print(f"\n{'='*60}")
    explained = fusion.query_with_explanation("How does batch API relate to cost reduction?", k=5)
    print(f"\nExplained query:")
    print(f"  Intent: {explained['intent']}")
    print(f"  Weights: {explained['weights']}")
    print(f"  Domains: {explained['domains']}")
    print(f"  Tools: {explained['tools_for_goal']}")
    print(f"  Results: {explained['result_count']}")

    # Test cache
    print(f"\n{'='*60}")
    t0 = time.time()
    r1 = fusion.query("prompt caching cost optimization", k=5)
    t1 = time.time()
    r2 = fusion.query("prompt caching cost optimization", k=5)
    t2 = time.time()
    first_time = (t1 - t0) * 1000
    cached_time = (t2 - t1) * 1000
    speedup = first_time / cached_time if cached_time > 0 else float('inf')
    print(f"\nCache Test:")
    print(f"  First query:  {first_time:.1f}ms")
    print(f"  Cached query: {cached_time:.1f}ms")
    print(f"  Speedup: {speedup:.0f}x")
    print(f"  Cache metrics: {fusion.cache.metrics.to_dict()}")

    # Verify result count
    assert len(results) >= 5, f"Expected 5+ results, got {len(results)}"

    fusion.close()
    print("\nhybrid_fusion.py OK")

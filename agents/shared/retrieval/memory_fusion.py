#!/usr/bin/env python3
"""
Memory Fusion Engine — Queryable Memory via 2-Path Hybrid Fusion

Composes BM25Index + EmbeddingManager + QueryCache into a unified
query interface for NLKE memory files (markdown).

    score = alpha * V(q,chunk) + beta * B(q,chunk)

Uses same scoring engines as HybridFusion but keeps independent
indexes. No graph path (memory has no edges).

Level 5 dependency — imports from L0-L2 modules + memory_parser.

Created: February 8, 2026
"""

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

try:
    from .config import RetrievalConfig, EmbeddingBackend
    from .bm25 import BM25Index
    from .embeddings import EmbeddingManager, HAS_NUMPY
    from .query_cache import QueryCache
    from .memory_parser import MemoryChunk, MemoryResult, scan_memory_directory
except ImportError:
    from config import RetrievalConfig, EmbeddingBackend
    from bm25 import BM25Index
    from embeddings import EmbeddingManager, HAS_NUMPY
    from query_cache import QueryCache
    from memory_parser import MemoryChunk, MemoryResult, scan_memory_directory


# ============================================================================
# Weight Profiles (2-path, no graph)
# ============================================================================

MEMORY_WEIGHTS = {
    "hash":      (0.35, 0.65),   # BM25 dominates with low-quality embeddings
    "semantic":  (0.50, 0.50),   # Equal blend with real embeddings
    "untrained": (0.30, 0.70),   # Almost all BM25
}


# ============================================================================
# Memory Fusion Engine
# ============================================================================

class MemoryFusion:
    """2-path hybrid fusion retrieval engine for memory files.

    Shares BM25Index, EmbeddingManager, and QueryCache component types
    with HybridFusion but maintains independent indexes. No graph scoring.

    Usage:
        mf = MemoryFusion("/path/to/memory")
        mf.index()
        results = mf.query("what decision about node IDs?")
    """

    def __init__(self, memory_root: str, config: Optional[RetrievalConfig] = None):
        self._memory_root = os.path.abspath(memory_root)
        self.config = config or RetrievalConfig()

        # Independent component instances
        self.bm25 = BM25Index(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b,
            boost_factor=self.config.intent_boost_factor,
        )
        self.embeddings = EmbeddingManager(config=self.config)
        self.cache = QueryCache(maxsize=200, ttl_seconds=300)

        # State
        self._chunks: List[MemoryChunk] = []
        self._chunk_map: Dict[str, MemoryChunk] = {}
        self._mtimes: Dict[str, float] = {}
        self._indexed = False
        self._index_time: float = 0.0

    @property
    def memory_root(self) -> str:
        return self._memory_root

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def is_indexed(self) -> bool:
        return self._indexed

    def index(self) -> Dict[str, Any]:
        """Index all memory files.

        Scans memory_root for .md files, parses into chunks,
        indexes into BM25 and embedding engines.

        Returns:
            Dict with indexing statistics.
        """
        t0 = time.time()

        chunks, mtimes = scan_memory_directory(self._memory_root)

        self._chunks = chunks
        self._chunk_map = {c.node_id: c for c in chunks}
        self._mtimes = mtimes

        # Index into scoring engines (duck-typing: MemoryChunk has
        # node_id, name, description, intent_keywords)
        bm25_count = self.bm25.index_nodes(chunks)
        emb_count = self.embeddings.index_nodes(chunks)

        self._index_time = time.time() - t0
        self._indexed = True

        # Collect directory stats
        dirs = set()
        for c in chunks:
            if c.directory:
                dirs.add(c.directory)

        return {
            "chunks_indexed": len(chunks),
            "files_scanned": len(mtimes),
            "directories": sorted(dirs),
            "bm25_indexed": bm25_count,
            "embedding_indexed": emb_count,
            "embedding_backend": self.embeddings.backend.value,
            "embedding_quality": self.embeddings.quality,
            "index_time_ms": round(self._index_time * 1000, 1),
        }

    def reindex(self) -> Dict[str, Any]:
        """Force re-index and clear cache."""
        self.cache.clear()
        return self.index()

    def _check_freshness(self) -> bool:
        """Check if any memory file has changed since last index.

        Compares stored mtimes with current filesystem state.
        If stale, triggers reindex and returns True.

        Returns:
            True if reindex was triggered, False if everything fresh.
        """
        if not self._indexed:
            return False

        stale = False

        # Check existing files for mtime changes
        for filepath, stored_mtime in self._mtimes.items():
            try:
                current_mtime = os.path.getmtime(filepath)
                if current_mtime != stored_mtime:
                    stale = True
                    break
            except OSError:
                stale = True
                break

        if not stale:
            # Check for new .md files not in our mtime dict
            _, current_mtimes = scan_memory_directory(self._memory_root)
            if set(current_mtimes.keys()) != set(self._mtimes.keys()):
                stale = True

        if stale:
            self.reindex()
            return True

        return False

    def query(self, text: str, k: int = 10) -> List[MemoryResult]:
        """Execute 2-path hybrid fusion query on memory.

        score = alpha * V(q,chunk) + beta * B(q,chunk)

        Auto-indexes on first call. Checks freshness before each query.

        Args:
            text: Query text
            k: Number of results to return

        Returns:
            List of MemoryResult sorted by final_score descending
        """
        if not self._indexed:
            self.index()

        self._check_freshness()

        # Check cache
        cached = self.cache.get(text, k=k)
        if cached is not None:
            return cached

        # Determine weights based on embedding quality
        quality = self.embeddings.quality
        alpha, beta = MEMORY_WEIGHTS.get(quality, (0.35, 0.65))

        # BM25 scoring
        bm25_results = self.bm25.search(text, k=min(k * 3, 100))
        bm25_scores: Dict[str, float] = {nid: score for nid, score in bm25_results}

        # Embedding scoring
        emb_scores: Dict[str, float] = {}
        if HAS_NUMPY:
            emb_results = self.embeddings.search(text, k=min(k * 3, 100))
            emb_scores = {nid: score for nid, score in emb_results}

        # Collect all candidates
        all_candidates = set(bm25_scores.keys()) | set(emb_scores.keys())
        if not all_candidates:
            self.cache.put(text, [], k=k)
            return []

        # 2-path fusion
        scored: List[Tuple[str, float, float, float]] = []
        for nid in all_candidates:
            v = emb_scores.get(nid, 0.0)
            b = bm25_scores.get(nid, 0.0)
            final = alpha * v + beta * b
            scored.append((nid, b, v, final))

        scored.sort(key=lambda x: -x[3])

        # Build results
        results: List[MemoryResult] = []
        for nid, b_score, v_score, final in scored[:k]:
            chunk = self._chunk_map.get(nid)
            if chunk is None:
                continue
            results.append(MemoryResult(
                chunk=chunk,
                bm25_score=round(b_score, 4),
                vector_score=round(v_score, 4),
                final_score=round(final, 4),
            ))

        self.cache.put(text, results, k=k)
        return results

    def query_with_context(self, text: str, k: int = 5) -> Dict[str, Any]:
        """Query with full metadata for debugging.

        Returns dict with results + scoring context.
        """
        quality = self.embeddings.quality
        alpha, beta = MEMORY_WEIGHTS.get(quality, (0.35, 0.65))

        results = self.query(text, k=k)

        return {
            "query": text,
            "result_count": len(results),
            "results": [r.to_dict() for r in results],
            "weights": {"alpha": alpha, "beta": beta},
            "embedding_quality": quality,
            "chunk_count": self.chunk_count,
            "files_tracked": len(self._mtimes),
            "cache_metrics": self.cache.metrics.to_dict(),
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __repr__(self) -> str:
        status = "indexed" if self._indexed else "not indexed"
        return f"MemoryFusion(root={self._memory_root!r}, chunks={self.chunk_count}, {status})"


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    print("memory_fusion.py — Memory Fusion Engine self-test")
    print("=" * 60)

    MEMORY_ROOT = "/storage/self/primary/Download/44nlke/NLKE/memory"

    mf = MemoryFusion(MEMORY_ROOT)
    stats = mf.index()

    print(f"\nIndexing Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Test query 1: specific decision
    print(f"\n{'=' * 60}")
    results = mf.query("node ID prefix decision", k=5)
    print(f"\nQuery: 'node ID prefix decision' -> {len(results)} results")
    for r in results[:5]:
        print(f"  {r.final_score:.4f} [{r.chunk.directory:30s}] {r.chunk.name}")
        print(f"           b={r.bm25_score:.3f} v={r.vector_score:.3f}")

    # Test query 2: broad topic
    print(f"\n{'=' * 60}")
    results2 = mf.query("retrieval layer architecture", k=5)
    print(f"\nQuery: 'retrieval layer architecture' -> {len(results2)} results")
    for r in results2[:5]:
        print(f"  {r.final_score:.4f} [{r.chunk.directory:30s}] {r.chunk.name}")

    # Test query 3: cross-project
    print(f"\n{'=' * 60}")
    results3 = mf.query("what is genuinely novel", k=5)
    print(f"\nQuery: 'what is genuinely novel' -> {len(results3)} results")
    for r in results3[:5]:
        print(f"  {r.final_score:.4f} [{r.chunk.source_file}]")
        print(f"           {r.chunk.name}")

    # Test query with context
    print(f"\n{'=' * 60}")
    ctx = mf.query_with_context("phase C memory system", k=3)
    print(f"\nQuery with context:")
    print(f"  Weights: {ctx['weights']}")
    print(f"  Quality: {ctx['embedding_quality']}")
    print(f"  Results: {ctx['result_count']}")

    # Test cache
    print(f"\n{'=' * 60}")
    t0 = time.time()
    r1 = mf.query("retrieval layer architecture", k=5)
    t1 = time.time()
    r2 = mf.query("retrieval layer architecture", k=5)
    t2 = time.time()
    first_ms = (t1 - t0) * 1000
    cached_ms = (t2 - t1) * 1000
    speedup = first_ms / cached_ms if cached_ms > 0 else float('inf')
    print(f"\nCache Test:")
    print(f"  First query:  {first_ms:.1f}ms")
    print(f"  Cached query: {cached_ms:.1f}ms")
    print(f"  Speedup: {speedup:.0f}x")
    print(f"  Metrics: {mf.cache.metrics.to_dict()}")

    # Test freshness
    print(f"\n{'=' * 60}")
    stale = mf._check_freshness()
    print(f"\nFreshness check: stale={stale} (expected False)")
    assert not stale, "Expected freshness check to return False"

    # Assertions
    assert len(results) >= 3, f"Expected 3+ results, got {len(results)}"
    assert mf.chunk_count >= 50, f"Expected 50+ chunks, got {mf.chunk_count}"

    print(f"\n{'=' * 60}")
    print(f"memory_fusion.py OK — {mf}")

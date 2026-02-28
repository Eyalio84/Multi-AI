#!/usr/bin/env python3
"""
Retrieval Configuration — Unified Retrieval Layer

Central configuration for hybrid fusion retrieval (vector + BM25 + graph).
Defines tunable parameters, embedding backends, edge weights, and KG paths.

Level 0 dependency — no internal imports.

Created: February 8, 2026
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


# ============================================================================
# Embedding Backend Selection
# ============================================================================

class EmbeddingBackend(Enum):
    """Available embedding backends in priority order."""
    HASH = "hash"              # Zero-cost character n-gram hashing (always available)
    CONTEXTUAL = "contextual"  # Pre-trained serialized embeddings (when available)
    FAISS = "faiss"            # FAISS index (requires faiss-cpu, unlikely on arm64)


# ============================================================================
# Main Configuration
# ============================================================================

@dataclass
class RetrievalConfig:
    """Tunable parameters for hybrid fusion retrieval.

    H(q,n) = alpha * V(q,n) + beta * B(q,n) + gamma * G(q,n)
    """

    # Fusion weights (must sum to 1.0)
    alpha: float = 0.40   # Vector/embedding similarity weight
    beta: float = 0.45    # BM25 keyword scoring weight
    gamma: float = 0.15   # Graph proximity boost weight

    # BM25 parameters
    bm25_k1: float = 1.5   # Term frequency saturation
    bm25_b: float = 0.75   # Document length normalization

    # Embedding parameters
    embedding_dim: int = 256      # Hash embedding dimensionality
    ngram_range: tuple = (2, 4)   # Character n-gram range for hashing

    # Cache parameters
    cache_maxsize: int = 500      # LRU cache max entries
    cache_ttl_seconds: int = 600  # TTL expiration (10 minutes)

    # Query parameters
    default_top_k: int = 10       # Default number of results
    max_keywords: int = 15        # Max keywords extracted per query
    intent_boost_factor: float = 5.0  # Multiplier for intent keyword matches

    # Graph scorer
    max_neighbor_depth: int = 2   # BFS depth for graph proximity
    max_neighbor_boost: int = 3   # Cap neighbor hits for bonus calculation

    # Embedding backend (auto-detected at runtime)
    embedding_backend: EmbeddingBackend = EmbeddingBackend.HASH

    def validate(self) -> bool:
        """Ensure weights sum to ~1.0."""
        total = self.alpha + self.beta + self.gamma
        return abs(total - 1.0) < 0.01

    def with_weights(self, alpha: float, beta: float, gamma: float) -> "RetrievalConfig":
        """Return a copy with adjusted weights."""
        cfg = RetrievalConfig(
            alpha=alpha, beta=beta, gamma=gamma,
            bm25_k1=self.bm25_k1, bm25_b=self.bm25_b,
            embedding_dim=self.embedding_dim, ngram_range=self.ngram_range,
            cache_maxsize=self.cache_maxsize, cache_ttl_seconds=self.cache_ttl_seconds,
            default_top_k=self.default_top_k, max_keywords=self.max_keywords,
            intent_boost_factor=self.intent_boost_factor,
            max_neighbor_depth=self.max_neighbor_depth,
            max_neighbor_boost=self.max_neighbor_boost,
            embedding_backend=self.embedding_backend,
        )
        return cfg


# ============================================================================
# KG Edge Type Weights
# ============================================================================

EDGE_WEIGHTS: Dict[str, float] = {
    "uses": 1.0,
    "implements": 0.95,
    "depends_on": 0.90,
    "extends": 0.85,
    "related_to": 0.70,
    "similar_to": 0.65,
    "part_of": 0.80,
    "belongs_to": 0.75,
    "references": 0.60,
    "alternatives": 0.55,
    "conflicts_with": 0.40,
    "precedes": 0.50,
    "follows": 0.50,
}


# ============================================================================
# KG Database Paths
# ============================================================================

NLKE_ROOT = "/storage/self/primary/Download/44nlke/NLKE"
AILAB_ROOT = "/storage/emulated/0/Download/gemini-3-pro/AI-LAB"
AILAB_HANDBOOKS = os.path.join(AILAB_ROOT, "tech-analysis", "handbooks")

KG_DATABASES: Dict[str, str] = {
    "claude_cookbook": os.path.join(NLKE_ROOT, "claude-cookbook-kg", "claude-cookbook-kg.db"),
    "handbooks": os.path.join(NLKE_ROOT, "handbooks", "handbooks-kg.db"),
    "handbooks_intent": os.path.join(AILAB_HANDBOOKS, "handbooks-kg.db"),
    "unified_77": "/storage/self/primary/Download/77/KGs/unified-complete.db",
    "unified_glassbox": "/storage/self/primary/Download/gemini-3-pro/glassbox-tui/KGS/unified-complete.db",
}

# Schema fingerprints for auto-detection (column sets)
KG_SCHEMAS = {
    "standard": {"id", "type", "name", "description"},
    "handbook_ext": {"id", "type", "name", "description", "source_handbook", "category"},
    "tools": {"node_id", "name", "title", "description", "intent_keywords", "node_type"},
}


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    cfg = RetrievalConfig()
    assert cfg.validate(), f"Weights don't sum to 1.0: {cfg.alpha + cfg.beta + cfg.gamma}"
    cfg2 = cfg.with_weights(0.30, 0.50, 0.20)
    assert cfg2.validate()
    assert len(EDGE_WEIGHTS) >= 11
    assert len(KG_DATABASES) >= 4
    print(f"config.py OK: alpha={cfg.alpha}, beta={cfg.beta}, gamma={cfg.gamma}")
    print(f"  {len(EDGE_WEIGHTS)} edge types, {len(KG_DATABASES)} KG databases")
    print(f"  Embedding backend: {cfg.embedding_backend.value}")
    print(f"  Schemas: {list(KG_SCHEMAS.keys())}")
